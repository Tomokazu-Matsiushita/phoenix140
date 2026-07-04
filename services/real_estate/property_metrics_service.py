from __future__ import annotations

from typing import Any

import pandas as pd

from repositories.real_estate_repository import RealEstateRepository


class PropertyMetricsService:
    def __init__(self, repository: RealEstateRepository | None = None) -> None:
        self.repository = repository or RealEstateRepository()

    def property_metrics(self) -> pd.DataFrame:
        properties = self.repository.properties()

        if properties.empty:
            return pd.DataFrame()

        df = properties.copy()

        for col in [
            "purchase_price",
            "loan_balance",
            "interest_rate",
            "loan_years",
            "monthly_payment",
            "units",
            "current_annual_income",
            "full_annual_income",
            "current_monthly_income",
            "full_monthly_income",
            "occupied_units",
            "vacant_units",
            "fixed_asset_tax_annual",
            "management_fee_monthly",
            "cleaning_fee_monthly",
            "insurance_annual",
        ]:
            if col not in df.columns:
                df[col] = None
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["annual_debt_service"] = df["monthly_payment"].fillna(0) * 12

        df["annual_income"] = df["current_annual_income"]
        df.loc[df["annual_income"].isna(), "annual_income"] = df["current_monthly_income"] * 12

        df["annual_management_fee"] = df["management_fee_monthly"].fillna(0) * 12
        df["annual_cleaning_fee"] = df["cleaning_fee_monthly"].fillna(0) * 12

        df["operating_expense"] = (
            df["fixed_asset_tax_annual"].fillna(0)
            + df["annual_management_fee"].fillna(0)
            + df["annual_cleaning_fee"].fillna(0)
            + df["insurance_annual"].fillna(0)
        )

        df["noi"] = df["annual_income"].fillna(0) - df["operating_expense"].fillna(0)
        df["cash_flow_after_debt"] = df["noi"] - df["annual_debt_service"].fillna(0)

        df["dscr"] = self._safe_div(df["noi"], df["annual_debt_service"])
        df["gross_yield"] = self._safe_div(df["annual_income"], df["purchase_price"])
        df["ltv"] = self._safe_div(df["loan_balance"], df["purchase_price"])
        df["occupancy_rate"] = self._safe_div(df["occupied_units"], df["units"])

        df["full_annual_income_estimate"] = df["full_annual_income"]
        missing_full = df["full_annual_income_estimate"].isna() & df["occupancy_rate"].gt(0)
        df.loc[missing_full, "full_annual_income_estimate"] = (
            df.loc[missing_full, "annual_income"] / df.loc[missing_full, "occupancy_rate"]
        )

        df["break_even_occupancy"] = self._safe_div(
            df["annual_debt_service"].fillna(0) + df["operating_expense"].fillna(0),
            df["full_annual_income_estimate"],
        )

        df["health"] = df.apply(self._health_label, axis=1)
        df["cfo_comment"] = df.apply(self._comment, axis=1)

        return df

    def vacancy_simulation(self, property_name: str, additional_vacancy: int) -> dict[str, Any]:
        metrics = self.property_metrics()
        if metrics.empty:
            return {}

        row = metrics[metrics["name"].astype(str).eq(str(property_name))]
        if row.empty:
            return {}

        r = row.iloc[0]
        occupied_units = float(r.get("occupied_units") or 0)
        current_monthly_income = float(r.get("current_monthly_income") or 0)

        if current_monthly_income <= 0 and pd.notna(r.get("annual_income")):
            current_monthly_income = float(r.get("annual_income")) / 12

        avg_rent = current_monthly_income / occupied_units if occupied_units else 0
        adjusted_monthly_income = max(current_monthly_income - avg_rent * additional_vacancy, 0)
        adjusted_annual_income = adjusted_monthly_income * 12

        operating_expense = float(r.get("operating_expense") or 0)
        annual_debt_service = float(r.get("annual_debt_service") or 0)

        adjusted_noi = adjusted_annual_income - operating_expense
        adjusted_cf = adjusted_noi - annual_debt_service
        adjusted_dscr = adjusted_noi / annual_debt_service if annual_debt_service else None

        return {
            "property": property_name,
            "additional_vacancy": additional_vacancy,
            "avg_rent": avg_rent,
            "adjusted_monthly_income": adjusted_monthly_income,
            "adjusted_annual_income": adjusted_annual_income,
            "adjusted_noi": adjusted_noi,
            "adjusted_cash_flow_after_debt": adjusted_cf,
            "adjusted_dscr": adjusted_dscr,
        }

    @staticmethod
    def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
        result = a / b.replace(0, pd.NA)
        return result.astype("float64")

    @staticmethod
    def _health_label(row: pd.Series) -> str:
        dscr = row.get("dscr")
        cf = row.get("cash_flow_after_debt")

        if pd.isna(dscr):
            return "要データ確認"
        if dscr >= 1.25 and cf >= 0:
            return "安定"
        if dscr >= 1.0 and cf >= 0:
            return "注意"
        return "要改善"

    @staticmethod
    def _comment(row: pd.Series) -> str:
        dscr = row.get("dscr")
        cf = row.get("cash_flow_after_debt")
        occupancy = row.get("occupancy_rate")

        comments = []

        if pd.notna(dscr):
            if dscr >= 1.25:
                comments.append("DSCRは比較的安定しています。")
            elif dscr >= 1.0:
                comments.append("DSCRは1.0倍台で、金利上昇や空室には注意が必要です。")
            else:
                comments.append("DSCRが1.0倍を下回っており、返済余力に注意が必要です。")
        else:
            comments.append("DSCR算出に必要な返済データを確認してください。")

        if pd.notna(cf):
            if cf >= 0:
                comments.append("返済後CFはプラスです。")
            else:
                comments.append("返済後CFがマイナスです。経費・空室・返済条件を確認してください。")

        if pd.notna(occupancy) and occupancy < 0.9:
            comments.append("稼働率が90%未満です。空室対策を優先してください。")

        return " ".join(comments)
