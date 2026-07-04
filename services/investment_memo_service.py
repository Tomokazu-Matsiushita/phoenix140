from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from services.integrated_ai_cfo_service import IntegratedAICFOService, IntegratedCFOInput
from services.real_estate import AcquisitionInput, ExitIRRInput


@dataclass
class InvestmentMemoInput:
    title: str = "Phoenix 140 Investment Decision Memo"
    author: str = "Phoenix AI CFO"
    purpose: str = "株式売却による資金確保と不動産取得の可否を総合判断する。"
    memo_date: str | None = None
    integrated_input: IntegratedCFOInput | None = None


class InvestmentMemoService:
    def __init__(self, integrated_service: IntegratedAICFOService | None = None) -> None:
        self.integrated_service = integrated_service or IntegratedAICFOService()

    def build(self, inputs: InvestmentMemoInput | dict[str, Any] | None = None) -> dict[str, Any]:
        if inputs is None:
            inputs = InvestmentMemoInput()
        elif isinstance(inputs, dict):
            inputs = InvestmentMemoInput(**inputs)

        memo_date = inputs.memo_date or datetime.now().strftime("%Y-%m-%d %H:%M")
        integrated_input = inputs.integrated_input or IntegratedCFOInput(
            acquisition_input=AcquisitionInput(),
            exit_input=ExitIRRInput(),
        )

        review = self.integrated_service.review(integrated_input)
        markdown = self.to_markdown(
            title=inputs.title,
            author=inputs.author,
            purpose=inputs.purpose,
            memo_date=memo_date,
            review=review,
            integrated_input=integrated_input,
        )

        tables = self.to_tables(review)

        return {
            "title": inputs.title,
            "author": inputs.author,
            "purpose": inputs.purpose,
            "memo_date": memo_date,
            "review": review,
            "markdown": markdown,
            "tables": tables,
        }

    def to_markdown(
        self,
        title: str,
        author: str,
        purpose: str,
        memo_date: str,
        review: dict[str, Any],
        integrated_input: IntegratedCFOInput,
    ) -> str:
        decision = review.get("decision", {})
        best = review.get("best_scenario", {}) or {}
        exit_result = review.get("exit_result", {}) or {}
        liquidity_review = review.get("liquidity_review", {}) or {}
        allocation = liquidity_review.get("allocation", {}) or {}
        acquisition = allocation.get("acquisition", {}) or {}

        decision_factors = review.get("decision_factors", [])
        must_check = review.get("must_check", [])
        scenario_review = liquidity_review.get("scenario_review", pd.DataFrame())

        lines: list[str] = []

        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"- 作成日: {memo_date}")
        lines.append(f"- 作成者: {author}")
        lines.append(f"- 目的: {purpose}")
        lines.append("")

        lines.append("## 1. Final Recommendation")
        lines.append("")
        lines.append(f"**判断:** {decision.get('label', '-')}")
        lines.append("")
        lines.append(f"**スコア:** {self._fmt_num(decision.get('score'))}")
        lines.append("")
        lines.append(f"**結論:** {decision.get('headline', '-')}")
        lines.append("")
        lines.append(review.get("executive_summary", "-"))
        lines.append("")

        lines.append("## 2. Best Scenario Snapshot")
        lines.append("")
        lines.append("| 項目 | 内容 |")
        lines.append("|---|---:|")
        snapshot = [
            ("最有力シナリオ", best.get("scenario", "-")),
            ("売却銘柄", best.get("sold_names", "-")),
            ("税引後売却資金", self._yen(best.get("net_proceeds"))),
            ("配当減少/年", self._yen(best.get("dividend_loss"))),
            ("取得初期必要資金", self._yen(best.get("initial_cash_required"))),
            ("取得後現金", self._yen(best.get("after_transaction_cash"))),
            ("安全資金差額", self._yen(best.get("safety_surplus"))),
            ("年間CF差分", self._yen(best.get("annual_cf_delta"))),
            ("月次CF差分", self._yen(best.get("monthly_cf_delta"))),
            ("取得DSCR", self._fmt_x(best.get("acquisition_dscr"))),
            ("出口IRR", self._fmt_pct(exit_result.get("irr"))),
            ("出口総損益", self._yen(exit_result.get("total_profit"))),
        ]

        for k, v in snapshot:
            lines.append(f"| {k} | {v} |")
        lines.append("")

        lines.append("## 3. Decision Factors")
        lines.append("")
        lines.append("| 判断項目 | ステータス | コメント |")
        lines.append("|---|---|---|")
        for factor in decision_factors:
            lines.append(
                f"| {factor.get('factor', '-')} | {factor.get('status', '-')} | {factor.get('comment', '-')} |"
            )
        lines.append("")

        lines.append("## 4. Acquisition Summary")
        lines.append("")
        lines.append("| 項目 | 内容 |")
        lines.append("|---|---:|")
        acquisition_rows = [
            ("物件名", getattr(integrated_input.acquisition_input, "property_name", "-") if integrated_input.acquisition_input else "-"),
            ("購入価格", self._yen(acquisition.get("purchase_price"))),
            ("借入額", self._yen(acquisition.get("loan_amount"))),
            ("初期必要資金", self._yen(acquisition.get("initial_cash_required"))),
            ("月額返済", self._yen(acquisition.get("monthly_payment"))),
            ("返済後CF/年", self._yen(acquisition.get("cash_flow_after_debt"))),
            ("DSCR", self._fmt_x(acquisition.get("dscr"))),
            ("表面利回り", self._fmt_pct(acquisition.get("gross_yield_full"))),
            ("NOI利回り", self._fmt_pct(acquisition.get("noi_yield"))),
            ("損益分岐稼働率", self._fmt_pct(acquisition.get("break_even_occupancy"))),
            ("取得判定", acquisition.get("health", "-")),
        ]
        for k, v in acquisition_rows:
            lines.append(f"| {k} | {v} |")
        lines.append("")

        lines.append("## 5. Exit / IRR Summary")
        lines.append("")
        lines.append("| 項目 | 内容 |")
        lines.append("|---|---:|")
        exit_rows = [
            ("保有年数", exit_result.get("holding_years", "-")),
            ("売却価格", self._yen(exit_result.get("exit_price"))),
            ("売却時残債", self._yen(exit_result.get("remaining_loan_balance"))),
            ("売却後手残り", self._yen(exit_result.get("sale_cash_after_debt_tax"))),
            ("累積CF", self._yen(exit_result.get("cumulative_cash_flow"))),
            ("総回収額", self._yen(exit_result.get("total_recovery"))),
            ("総損益", self._yen(exit_result.get("total_profit"))),
            ("回収倍率", self._fmt_multiple(exit_result.get("equity_multiple"))),
            ("IRR", self._fmt_pct(exit_result.get("irr"))),
            ("出口判定", exit_result.get("health", "-")),
        ]
        for k, v in exit_rows:
            lines.append(f"| {k} | {v} |")
        lines.append("")

        lines.append("## 6. Liquidity & Safety")
        lines.append("")
        lines.append("| 項目 | 内容 |")
        lines.append("|---|---:|")
        liquidity_rows = [
            ("現在現金", self._yen(integrated_input.current_cash)),
            ("月間生活費", self._yen(integrated_input.monthly_living_expense)),
            ("生活防衛資金 月数", f"{integrated_input.emergency_months:.1f}か月"),
            ("必要安全資金", self._yen(liquidity_review.get("required_buffer"))),
            ("最低現金ライン", self._yen(integrated_input.minimum_cash_floor)),
            ("現在の生活費月数", self._fmt_months(liquidity_review.get("current_months_covered"))),
        ]
        for k, v in liquidity_rows:
            lines.append(f"| {k} | {v} |")
        lines.append("")

        lines.append("## 7. Scenario Comparison")
        lines.append("")
        if isinstance(scenario_review, pd.DataFrame) and not scenario_review.empty:
            cols = [
                "scenario",
                "status",
                "net_proceeds",
                "dividend_loss",
                "initial_cash_required",
                "after_transaction_cash",
                "safety_surplus",
                "annual_cf_delta",
                "liquidity_score",
            ]
            scenario_table = scenario_review[[c for c in cols if c in scenario_review.columns]].copy()
            lines.append(scenario_table.to_markdown(index=False))
        else:
            lines.append("シナリオ比較データがありません。")
        lines.append("")

        lines.append("## 8. Must Check Before Action")
        lines.append("")
        for item in must_check:
            lines.append(f"- {item}")
        lines.append("")

        lines.append("## 9. CFO Note")
        lines.append("")
        lines.append(
            "この投資判断メモはPhoenix 140のルールベース計算に基づくドラフトです。"
            "実行前には、税務、融資承認、物件調査、修繕見積、火災保険、レントロール、"
            "売却時税金、生活資金を必ず別途確認してください。"
        )
        lines.append("")

        return "\n".join(lines)

    def to_tables(self, review: dict[str, Any]) -> dict[str, pd.DataFrame]:
        liquidity_review = review.get("liquidity_review", {}) or {}
        scenario_review = liquidity_review.get("scenario_review", pd.DataFrame())

        decision_factors = pd.DataFrame(review.get("decision_factors", []))
        must_check = pd.DataFrame({"must_check": review.get("must_check", [])})

        if not isinstance(scenario_review, pd.DataFrame):
            scenario_review = pd.DataFrame()

        best = review.get("best_scenario", {}) or {}
        best_df = pd.DataFrame([best]) if best else pd.DataFrame()

        return {
            "decision_factors": decision_factors,
            "must_check": must_check,
            "scenario_review": scenario_review,
            "best_scenario": best_df,
        }

    def save_markdown(self, markdown: str, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        return path

    def save_tables(self, tables: dict[str, pd.DataFrame], output_dir: str | Path) -> list[Path]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for name, df in tables.items():
            path = out / f"{name}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            paths.append(path)
        return paths

    @staticmethod
    def _yen(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"¥{float(value):,.0f}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_pct(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.2%}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_x(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.2f}x"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_multiple(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.2f}x"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_num(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.1f}"
        except Exception:
            return "-"

    @staticmethod
    def _fmt_months(value: Any) -> str:
        try:
            if value is None or pd.isna(value):
                return "-"
            return f"{float(value):.1f}か月"
        except Exception:
            return "-"
