from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from db.database import SessionLocal


@dataclass
class ImportResult:
    import_type: str
    inserted: int
    skipped: int
    errors: list[str]

    @property
    def total(self) -> int:
        return self.inserted + self.skipped + len(self.errors)


class MoneytreeDataService:
    ACCOUNT_COLUMN_ALIASES = {
        "institution": ["institution", "金融機関", "金融機関名", "bank", "銀行", "証券会社"],
        "account_name": ["account_name", "口座名", "口座", "name", "account", "account name"],
        "account_number": ["account_number", "口座番号", "番号", "account no", "account_number_masked"],
        "account_type": ["account_type", "種別", "口座種別", "type"],
        "currency": ["currency", "通貨", "ccy"],
        "balance": ["balance", "残高", "評価額", "amount", "金額"],
        "balance_date": ["balance_date", "残高日", "基準日", "date", "日付"],
    }

    TRANSACTION_COLUMN_ALIASES = {
        "transaction_id": ["transaction_id", "取引ID", "id", "ID"],
        "institution": ["institution", "金融機関", "金融機関名", "bank", "銀行", "証券会社"],
        "account_name": ["account_name", "口座名", "口座", "name", "account", "account name"],
        "account_number": ["account_number", "口座番号", "番号", "account no", "account_number_masked"],
        "transaction_date": ["transaction_date", "date", "日付", "取引日", "利用日"],
        "description": ["description", "摘要", "内容", "明細", "取引内容", "支払先", "merchant"],
        "category": ["category", "カテゴリ", "大分類"],
        "subcategory": ["subcategory", "サブカテゴリ", "小分類"],
        "amount": ["amount", "金額", "出金額", "入金額", "利用金額"],
        "transaction_type": ["transaction_type", "type", "収支", "入出金", "区分"],
        "currency": ["currency", "通貨", "ccy"],
        "memo": ["memo", "メモ", "備考", "note"],
    }

    def __init__(self) -> None:
        pass

    def migrate(self) -> None:
        from scripts.migrate_moneytree_model import main as migrate_main
        migrate_main()

    def read_accounts(self) -> pd.DataFrame:
        with SessionLocal() as session:
            engine = session.get_bind()
            try:
                return pd.read_sql_query("SELECT * FROM moneytree_accounts ORDER BY institution, account_name", engine)
            except Exception:
                return pd.DataFrame()

    def read_transactions(self, limit: int | None = 500) -> pd.DataFrame:
        with SessionLocal() as session:
            engine = session.get_bind()
            try:
                sql = "SELECT * FROM moneytree_transactions ORDER BY transaction_date DESC, id DESC"
                if limit:
                    sql += f" LIMIT {int(limit)}"
                return pd.read_sql_query(sql, engine)
            except Exception:
                return pd.DataFrame()

    def read_balance_snapshots(self) -> pd.DataFrame:
        with SessionLocal() as session:
            engine = session.get_bind()
            try:
                return pd.read_sql_query(
                    "SELECT * FROM moneytree_balance_snapshots ORDER BY snapshot_date DESC, institution, account_name",
                    engine,
                )
            except Exception:
                return pd.DataFrame()

    def read_sync_log(self, limit: int = 50) -> pd.DataFrame:
        with SessionLocal() as session:
            engine = session.get_bind()
            try:
                return pd.read_sql_query(
                    f"SELECT * FROM moneytree_sync_log ORDER BY created_at DESC LIMIT {int(limit)}",
                    engine,
                )
            except Exception:
                return pd.DataFrame()

    def portfolio_summary(self) -> dict[str, Any]:
        accounts = self.read_accounts()
        transactions = self.read_transactions(limit=None)

        total_balance = float(accounts["balance"].fillna(0).sum()) if not accounts.empty and "balance" in accounts else 0.0

        by_institution = pd.DataFrame()
        by_type = pd.DataFrame()
        monthly_cashflow = pd.DataFrame()
        spending_by_category = pd.DataFrame()

        if not accounts.empty:
            if "institution" in accounts.columns:
                by_institution = (
                    accounts.groupby("institution", dropna=False)["balance"]
                    .sum()
                    .reset_index()
                    .sort_values("balance", ascending=False)
                )
            if "account_type" in accounts.columns:
                by_type = (
                    accounts.groupby("account_type", dropna=False)["balance"]
                    .sum()
                    .reset_index()
                    .sort_values("balance", ascending=False)
                )

        if not transactions.empty:
            tx = transactions.copy()
            tx["transaction_date"] = pd.to_datetime(tx["transaction_date"], errors="coerce")
            tx["month"] = tx["transaction_date"].dt.to_period("M").astype(str)
            tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce").fillna(0)

            monthly_cashflow = (
                tx.groupby("month")["amount"]
                .sum()
                .reset_index()
                .sort_values("month")
            )

            expense = tx[tx["amount"] < 0].copy()
            if not expense.empty:
                expense["expense_amount"] = expense["amount"].abs()
                spending_by_category = (
                    expense.groupby("category", dropna=False)["expense_amount"]
                    .sum()
                    .reset_index()
                    .sort_values("expense_amount", ascending=False)
                )

        return {
            "total_balance": total_balance,
            "account_count": int(len(accounts)),
            "transaction_count": int(len(transactions)),
            "by_institution": by_institution,
            "by_type": by_type,
            "monthly_cashflow": monthly_cashflow,
            "spending_by_category": spending_by_category,
        }

    def import_accounts_csv(self, path: str | Path) -> ImportResult:
        df = self._read_csv(path)
        return self.import_accounts_df(df)

    def import_transactions_csv(self, path: str | Path) -> ImportResult:
        df = self._read_csv(path)
        return self.import_transactions_df(df)

    def import_accounts_df(self, df: pd.DataFrame) -> ImportResult:
        self.migrate()
        normalized = self._normalize_columns(df, self.ACCOUNT_COLUMN_ALIASES)

        required = ["institution", "account_name", "account_number", "balance"]
        missing = [c for c in required if c not in normalized.columns]
        if missing:
            return ImportResult("accounts", 0, 0, [f"Missing required columns: {missing}"])

        normalized["balance"] = normalized["balance"].map(self._to_number)
        normalized["currency"] = normalized.get("currency", "JPY")
        normalized["balance_date"] = normalized.get("balance_date", pd.Timestamp.today().strftime("%Y-%m-%d"))
        normalized["account_type"] = normalized.get("account_type", "unknown")
        normalized["source"] = "manual_csv"

        inserted = 0
        skipped = 0
        errors: list[str] = []

        with SessionLocal() as session:
            engine = session.get_bind()
            with engine.begin() as conn:
                for idx, row in normalized.iterrows():
                    try:
                        payload = {
                            "institution": self._clean(row.get("institution")),
                            "account_name": self._clean(row.get("account_name")),
                            "account_number": self._clean(row.get("account_number")),
                            "account_type": self._clean(row.get("account_type", "unknown")),
                            "currency": self._clean(row.get("currency", "JPY")),
                            "balance": float(row.get("balance") or 0),
                            "balance_date": self._date_text(row.get("balance_date")),
                        }

                        result = conn.execute(
                            text(
                                """
                                INSERT OR REPLACE INTO moneytree_accounts
                                (institution, account_name, account_number, account_type, currency, balance, balance_date, source, updated_at)
                                VALUES
                                (:institution, :account_name, :account_number, :account_type, :currency, :balance, :balance_date, 'manual_csv', CURRENT_TIMESTAMP)
                                """
                            ),
                            payload,
                        )

                        conn.execute(
                            text(
                                """
                                INSERT INTO moneytree_balance_snapshots
                                (institution, account_name, account_number, balance, currency, snapshot_date, source)
                                VALUES
                                (:institution, :account_name, :account_number, :balance, :currency, :balance_date, 'manual_csv')
                                """
                            ),
                            payload,
                        )

                        inserted += int(result.rowcount or 1)
                    except Exception as exc:
                        errors.append(f"row {idx}: {exc}")

                self._log(conn, "accounts_csv", "success" if not errors else "partial", f"inserted={inserted}, skipped={skipped}, errors={len(errors)}", inserted)

        return ImportResult("accounts", inserted, skipped, errors)

    def import_transactions_df(self, df: pd.DataFrame) -> ImportResult:
        self.migrate()
        normalized = self._normalize_columns(df, self.TRANSACTION_COLUMN_ALIASES)

        required = ["transaction_date", "description", "amount"]
        missing = [c for c in required if c not in normalized.columns]
        if missing:
            return ImportResult("transactions", 0, 0, [f"Missing required columns: {missing}"])

        defaults = {
            "institution": "",
            "account_name": "",
            "account_number": "",
            "category": "未分類",
            "subcategory": "",
            "transaction_type": "",
            "currency": "JPY",
            "memo": "",
        }
        for col, value in defaults.items():
            if col not in normalized.columns:
                normalized[col] = value

        normalized["amount"] = normalized["amount"].map(self._to_number)
        normalized["transaction_date"] = normalized["transaction_date"].map(self._date_text)

        if "transaction_id" not in normalized.columns:
            normalized["transaction_id"] = normalized.apply(self._generate_transaction_id, axis=1)
        else:
            normalized["transaction_id"] = normalized.apply(
                lambda row: self._clean(row.get("transaction_id")) or self._generate_transaction_id(row),
                axis=1,
            )

        normalized["transaction_type"] = normalized.apply(self._infer_transaction_type, axis=1)

        inserted = 0
        skipped = 0
        errors: list[str] = []

        with SessionLocal() as session:
            engine = session.get_bind()
            with engine.begin() as conn:
                for idx, row in normalized.iterrows():
                    try:
                        payload = {
                            "transaction_id": self._clean(row.get("transaction_id")),
                            "institution": self._clean(row.get("institution")),
                            "account_name": self._clean(row.get("account_name")),
                            "account_number": self._clean(row.get("account_number")),
                            "transaction_date": self._date_text(row.get("transaction_date")),
                            "description": self._clean(row.get("description")),
                            "category": self._clean(row.get("category", "未分類")),
                            "subcategory": self._clean(row.get("subcategory", "")),
                            "amount": float(row.get("amount") or 0),
                            "transaction_type": self._clean(row.get("transaction_type")),
                            "currency": self._clean(row.get("currency", "JPY")),
                            "memo": self._clean(row.get("memo", "")),
                        }

                        exists = conn.execute(
                            text("SELECT 1 FROM moneytree_transactions WHERE transaction_id = :transaction_id"),
                            {"transaction_id": payload["transaction_id"]},
                        ).fetchone()

                        if exists:
                            skipped += 1
                            continue

                        conn.execute(
                            text(
                                """
                                INSERT INTO moneytree_transactions
                                (transaction_id, institution, account_name, account_number, transaction_date, description,
                                 category, subcategory, amount, transaction_type, currency, memo, source)
                                VALUES
                                (:transaction_id, :institution, :account_name, :account_number, :transaction_date, :description,
                                 :category, :subcategory, :amount, :transaction_type, :currency, :memo, 'manual_csv')
                                """
                            ),
                            payload,
                        )
                        inserted += 1
                    except Exception as exc:
                        errors.append(f"row {idx}: {exc}")

                self._log(conn, "transactions_csv", "success" if not errors else "partial", f"inserted={inserted}, skipped={skipped}, errors={len(errors)}", inserted)

        return ImportResult("transactions", inserted, skipped, errors)

    def clear_manual_data(self) -> None:
        with SessionLocal() as session:
            engine = session.get_bind()
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM moneytree_transactions WHERE source = 'manual_csv'"))
                conn.execute(text("DELETE FROM moneytree_balance_snapshots WHERE source = 'manual_csv'"))
                conn.execute(text("DELETE FROM moneytree_accounts WHERE source = 'manual_csv'"))
                self._log(conn, "clear_manual_data", "success", "manual_csv data cleared", 0)

    def _read_csv(self, path: str | Path) -> pd.DataFrame:
        path = Path(path)
        for encoding in ["utf-8-sig", "utf-8", "cp932"]:
            try:
                return pd.read_csv(path, encoding=encoding)
            except Exception:
                continue
        return pd.read_csv(path)

    def _normalize_columns(self, df: pd.DataFrame, aliases: dict[str, list[str]]) -> pd.DataFrame:
        result = df.copy()
        result.columns = [str(c).strip() for c in result.columns]

        rename_map: dict[str, str] = {}
        lower_to_original = {str(c).strip().lower(): c for c in result.columns}

        for canonical, candidates in aliases.items():
            for candidate in candidates:
                key = str(candidate).strip().lower()
                if key in lower_to_original:
                    rename_map[lower_to_original[key]] = canonical
                    break

        result = result.rename(columns=rename_map)

        # Keep only first duplicated canonical column
        result = result.loc[:, ~result.columns.duplicated()]
        return result

    def _generate_transaction_id(self, row: pd.Series) -> str:
        raw = "|".join(
            [
                self._date_text(row.get("transaction_date")),
                self._clean(row.get("institution")),
                self._clean(row.get("account_number")),
                self._clean(row.get("description")),
                str(self._to_number(row.get("amount"))),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def _infer_transaction_type(self, row: pd.Series) -> str:
        t = self._clean(row.get("transaction_type"))
        if t:
            if t.lower() in ["income", "入金", "収入"]:
                return "income"
            if t.lower() in ["expense", "出金", "支出"]:
                return "expense"

        amount = self._to_number(row.get("amount"))
        return "income" if amount >= 0 else "expense"

    @staticmethod
    def _to_number(value: Any) -> float:
        if value is None:
            return 0.0
        text_value = str(value).strip()
        if text_value == "" or text_value.lower() == "nan":
            return 0.0

        negative = False
        if text_value.startswith("(") and text_value.endswith(")"):
            negative = True

        cleaned = (
            text_value.replace(",", "")
            .replace("¥", "")
            .replace("円", "")
            .replace("JPY", "")
            .replace("jpy", "")
            .replace("(", "")
            .replace(")", "")
            .strip()
        )

        try:
            number = float(cleaned)
            return -number if negative else number
        except Exception:
            return 0.0

    @staticmethod
    def _date_text(value: Any) -> str:
        if value is None:
            return ""
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass

        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return str(value)
        return parsed.strftime("%Y-%m-%d")

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass
        return str(value).strip()

    @staticmethod
    def _log(conn, sync_type: str, status: str, message: str, records_count: int) -> None:
        conn.execute(
            text(
                """
                INSERT INTO moneytree_sync_log
                (sync_type, status, message, records_count)
                VALUES
                (:sync_type, :status, :message, :records_count)
                """
            ),
            {
                "sync_type": sync_type,
                "status": status,
                "message": message,
                "records_count": int(records_count),
            },
        )
