from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from services.capital_allocation_service import CapitalAllocationInput, CapitalAllocationService
from services.real_estate import AcquisitionInput


@dataclass
class LiquiditySafetyInput:
    current_cash: float = 4_856_312
    monthly_living_expense: float = 700_000
    emergency_months: float = 6
    property_repair_reserve: float = 1_500_000
    tax_reserve: float = 500_000
    other_commitments: float = 0
    minimum_cash_floor: float = 2_000_000
    capital_allocation_input: CapitalAllocationInput | None = None


class LiquiditySafetyService:
    def __init__(self, capital_allocation_service: CapitalAllocationService | None = None) -> None:
        self.capital_allocation_service = capital_allocation_service or CapitalAllocationService()

    def required_buffer(self, inputs: LiquiditySafetyInput) -> float:
        emergency_buffer = float(inputs.monthly_living_expense) * float(inputs.emergency_months)
        return (
            emergency_buffer
            + float(inputs.property_repair_reserve)
            + float(inputs.tax_reserve)
            + float(inputs.other_commitments)
        )

    def review(self, inputs: LiquiditySafetyInput | dict[str, Any]) -> dict[str, Any]:
        if isinstance(inputs, dict):
            inputs = LiquiditySafetyInput(**inputs)

        allocation_input = inputs.capital_allocation_input or CapitalAllocationInput(
            target_net_cash=3_500_000,
            acquisition_input=AcquisitionInput(),
        )

        allocation = self.capital_allocation_service.review(allocation_input)
        comparison = allocation["comparison"].copy()

        required_buffer = self.required_buffer(inputs)
        current_months_covered = self._safe_div(inputs.current_cash, inputs.monthly_living_expense)

        if comparison.empty:
            return {
                "required_buffer": required_buffer,
                "current_months_covered": current_months_covered,
                "allocation": allocation,
                "scenario_review": pd.DataFrame(),
                "recommendation": {
                    "status": "要データ確認",
                    "summary": "資本配分シナリオを作成できませんでした。",
                },
                "actions": ["金融資産データと不動産取得条件を確認する。"],
            }

        comparison["current_cash"] = float(inputs.current_cash)
        comparison["required_buffer"] = required_buffer
        comparison["after_transaction_cash"] = (
            comparison["current_cash"]
            + comparison["net_proceeds"].fillna(0)
            - comparison["initial_cash_required"].fillna(0)
        )
        comparison["safety_surplus"] = comparison["after_transaction_cash"] - comparison["required_buffer"]
        comparison["cash_floor_surplus"] = comparison["after_transaction_cash"] - float(inputs.minimum_cash_floor)
        comparison["months_covered_after"] = comparison["after_transaction_cash"].apply(
            lambda x: self._safe_div(x, inputs.monthly_living_expense)
        )
        comparison["monthly_cf_delta"] = comparison["annual_cf_delta"].fillna(0) / 12
        comparison["status"] = comparison.apply(lambda row: self._status(row, inputs), axis=1)
        comparison["liquidity_score"] = comparison.apply(lambda row: self._score(row, inputs), axis=1)
        comparison["cfo_comment"] = comparison.apply(lambda row: self._comment(row, inputs), axis=1)

        scenario_review = comparison.sort_values("liquidity_score", ascending=False).reset_index(drop=True)

        return {
            "required_buffer": required_buffer,
            "current_months_covered": current_months_covered,
            "allocation": allocation,
            "scenario_review": scenario_review,
            "recommendation": self._recommendation(scenario_review, inputs),
            "actions": self._actions(scenario_review, inputs),
        }

    def _status(self, row: pd.Series, inputs: LiquiditySafetyInput) -> str:
        after_cash = float(row.get("after_transaction_cash") or 0)
        safety_surplus = float(row.get("safety_surplus") or 0)
        months = row.get("months_covered_after")
        monthly_delta = float(row.get("monthly_cf_delta") or 0)

        if after_cash < float(inputs.minimum_cash_floor):
            return "危険"
        if safety_surplus >= 0 and months is not None and months >= inputs.emergency_months and monthly_delta >= 0:
            return "安全"
        if safety_surplus >= 0 and months is not None and months >= inputs.emergency_months:
            return "注意"
        if after_cash >= float(inputs.minimum_cash_floor):
            return "要改善"
        return "危険"

    def _score(self, row: pd.Series, inputs: LiquiditySafetyInput) -> float:
        after_cash = float(row.get("after_transaction_cash") or 0)
        safety_surplus = float(row.get("safety_surplus") or 0)
        cash_floor_surplus = float(row.get("cash_floor_surplus") or 0)
        monthly_delta = float(row.get("monthly_cf_delta") or 0)
        funds_acquisition = bool(row.get("funds_acquisition"))

        score = 0.0

        if funds_acquisition:
            score += 20
        else:
            score -= 20

        score += min(max(safety_surplus / 100_000, -30), 30)
        score += min(max(cash_floor_surplus / 100_000, -20), 20)
        score += min(max(monthly_delta / 10_000, -20), 20)

        if after_cash >= float(inputs.minimum_cash_floor):
            score += 10
        else:
            score -= 30

        return score

    def _comment(self, row: pd.Series, inputs: LiquiditySafetyInput) -> str:
        status = row.get("status")
        after_cash = float(row.get("after_transaction_cash") or 0)
        safety_surplus = float(row.get("safety_surplus") or 0)
        months = row.get("months_covered_after")
        monthly_delta = float(row.get("monthly_cf_delta") or 0)

        parts: list[str] = []

        if status == "安全":
            parts.append("取得後も必要安全資金を上回り、流動性は比較的安全です。")
        elif status == "注意":
            parts.append("安全資金は確保できますが、月次CF差分または余裕幅に注意が必要です。")
        elif status == "要改善":
            parts.append("最低現金ラインは超えますが、必要安全資金には不足します。")
        else:
            parts.append("取得後現金が最低ラインを下回るため、実行は危険です。")

        parts.append(f"取得後現金は{self._yen(after_cash)}、安全資金との差額は{self._yen(safety_surplus)}です。")

        if months is not None:
            parts.append(f"生活費換算では約{months:.1f}か月分です。")

        if monthly_delta >= 0:
            parts.append(f"月次CF差分はプラス{self._yen(monthly_delta)}です。")
        else:
            parts.append(f"月次CF差分はマイナス{self._yen(abs(monthly_delta))}です。")

        return " ".join(parts)

    def _recommendation(self, scenario_review: pd.DataFrame, inputs: LiquiditySafetyInput) -> dict[str, Any]:
        if scenario_review.empty:
            return {
                "status": "要データ確認",
                "scenario": "",
                "summary": "シナリオがありません。",
            }

        best = scenario_review.iloc[0].to_dict()
        safe_rows = scenario_review[scenario_review["status"].eq("安全")]

        if not safe_rows.empty:
            best_safe = safe_rows.iloc[0].to_dict()
            return {
                "status": "実行候補",
                "scenario": best_safe["scenario"],
                "summary": (
                    f"最も安全性が高い実行候補は「{best_safe['scenario']}」です。"
                    f"取得後現金は{self._yen(best_safe['after_transaction_cash'])}、"
                    f"安全資金余剰は{self._yen(best_safe['safety_surplus'])}です。"
                ),
            }

        if best["status"] == "注意":
            return {
                "status": "条件付き候補",
                "scenario": best["scenario"],
                "summary": (
                    f"最上位は「{best['scenario']}」ですが、実行前に安全資金の余裕を確認してください。"
                    f"取得後現金は{self._yen(best['after_transaction_cash'])}です。"
                ),
            }

        return {
            "status": "見送り推奨",
            "scenario": best["scenario"],
            "summary": (
                "現条件では流動性が不足します。"
                "売却額を増やす、取得条件を見直す、手元現金を積み増す、または購入を延期してください。"
            ),
        }

    def _actions(self, scenario_review: pd.DataFrame, inputs: LiquiditySafetyInput) -> list[str]:
        actions: list[str] = []

        if scenario_review.empty:
            return ["金融資産データ、売却条件、物件取得条件を確認する。"]

        best = scenario_review.iloc[0]

        if best["status"] != "安全":
            actions.append("購入実行前に、最低でも安全資金を満たす売却額または現金追加を確認する。")

        if float(best.get("monthly_cf_delta") or 0) < 0:
            actions.append("株式配当減少を不動産CFで補えないため、取得条件または売却銘柄を見直す。")

        if float(best.get("after_transaction_cash") or 0) < float(inputs.minimum_cash_floor):
            actions.append("取得後現金が最低ラインを下回るため、購入を延期するか自己資金計画を修正する。")

        if not actions:
            actions.append("実行前に融資承認、火災保険、修繕見積、税金、生活資金を最終確認する。")

        return actions[:5]

    @staticmethod
    def _safe_div(a: float | None, b: float | None) -> float | None:
        try:
            if b in (0, None):
                return None
            return float(a or 0) / float(b)
        except Exception:
            return None

    @staticmethod
    def _yen(value: float | None) -> str:
        if value is None:
            return "-"
        return f"¥{value:,.0f}"
