from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from services.capital_allocation_service import CapitalAllocationInput
from services.liquidity_safety_service import LiquiditySafetyInput, LiquiditySafetyService
from services.real_estate import AcquisitionInput, ExitIRRInput, ExitIRRService


@dataclass
class IntegratedCFOInput:
    current_cash: float = 4_856_312
    monthly_living_expense: float = 700_000
    emergency_months: float = 6
    property_repair_reserve: float = 1_500_000
    tax_reserve: float = 500_000
    other_commitments: float = 0
    minimum_cash_floor: float = 2_000_000

    target_net_cash: float = 3_500_000
    tax_rate: float = 0.20315
    preserve_names: list[str] | None = None
    preserve_core_policy: bool = True
    shipping_max_sell_ratio: float = 0.5

    acquisition_input: AcquisitionInput | None = None
    exit_input: ExitIRRInput | None = None


class IntegratedAICFOService:
    def __init__(
        self,
        liquidity_service: LiquiditySafetyService | None = None,
        exit_service: ExitIRRService | None = None,
    ) -> None:
        self.liquidity_service = liquidity_service or LiquiditySafetyService()
        self.exit_service = exit_service or ExitIRRService()

    def review(self, inputs: IntegratedCFOInput | dict[str, Any]) -> dict[str, Any]:
        if isinstance(inputs, dict):
            inputs = IntegratedCFOInput(**inputs)

        acquisition_input = inputs.acquisition_input or AcquisitionInput()
        exit_input = inputs.exit_input or ExitIRRInput()

        capital_input = CapitalAllocationInput(
            target_net_cash=float(inputs.target_net_cash),
            tax_rate=float(inputs.tax_rate),
            preserve_names=inputs.preserve_names,
            preserve_core_policy=bool(inputs.preserve_core_policy),
            shipping_max_sell_ratio=float(inputs.shipping_max_sell_ratio),
            acquisition_input=acquisition_input,
        )

        liquidity_input = LiquiditySafetyInput(
            current_cash=float(inputs.current_cash),
            monthly_living_expense=float(inputs.monthly_living_expense),
            emergency_months=float(inputs.emergency_months),
            property_repair_reserve=float(inputs.property_repair_reserve),
            tax_reserve=float(inputs.tax_reserve),
            other_commitments=float(inputs.other_commitments),
            minimum_cash_floor=float(inputs.minimum_cash_floor),
            capital_allocation_input=capital_input,
        )

        liquidity_review = self.liquidity_service.review(liquidity_input)
        scenario_review = liquidity_review["scenario_review"]

        exit_result = self.exit_service.evaluate(exit_input)

        best_scenario = self._best_scenario(scenario_review)
        decision = self._decision(best_scenario, liquidity_review, exit_result)

        return {
            "decision": decision,
            "best_scenario": best_scenario,
            "liquidity_review": liquidity_review,
            "exit_result": exit_result,
            "executive_summary": self._executive_summary(decision, best_scenario, liquidity_review, exit_result),
            "decision_factors": self._decision_factors(best_scenario, liquidity_review, exit_result),
            "must_check": self._must_check(decision, best_scenario, liquidity_review, exit_result),
        }

    def _best_scenario(self, scenario_review: pd.DataFrame) -> dict[str, Any]:
        if scenario_review is None or scenario_review.empty:
            return {}

        safe = scenario_review[scenario_review["status"].eq("安全")]
        if not safe.empty:
            return safe.sort_values("liquidity_score", ascending=False).iloc[0].to_dict()

        return scenario_review.sort_values("liquidity_score", ascending=False).iloc[0].to_dict()

    def _decision(
        self,
        best: dict[str, Any],
        liquidity_review: dict[str, Any],
        exit_result: dict[str, Any],
    ) -> dict[str, Any]:
        if not best:
            return {
                "label": "要データ確認",
                "headline": "判断に必要なシナリオが不足しています。",
                "score": 0,
            }

        status = str(best.get("status", ""))
        annual_cf_delta = self._num(best.get("annual_cf_delta")) or 0
        monthly_cf_delta = self._num(best.get("monthly_cf_delta")) or 0
        funds_acquisition = bool(best.get("funds_acquisition"))
        after_cash = self._num(best.get("after_transaction_cash")) or 0
        safety_surplus = self._num(best.get("safety_surplus")) or 0
        acquisition_dscr = self._num(best.get("acquisition_dscr"))
        exit_irr = self._num(exit_result.get("irr"))
        exit_profit = self._num(exit_result.get("total_profit")) or 0
        sale_cash = self._num(exit_result.get("sale_cash_after_debt_tax")) or 0

        score = 0.0

        if status == "安全":
            score += 30
        elif status == "注意":
            score += 15
        elif status == "要改善":
            score -= 10
        else:
            score -= 30

        if funds_acquisition:
            score += 20
        else:
            score -= 25

        if annual_cf_delta > 0:
            score += min(annual_cf_delta / 100_000, 25)
        else:
            score -= min(abs(annual_cf_delta) / 100_000, 25)

        if safety_surplus >= 0:
            score += min(safety_surplus / 200_000, 20)
        else:
            score -= min(abs(safety_surplus) / 100_000, 30)

        if acquisition_dscr is not None:
            if acquisition_dscr >= 1.25:
                score += 15
            elif acquisition_dscr >= 1.0:
                score += 5
            else:
                score -= 20

        if exit_irr is not None:
            if exit_irr >= 0.08:
                score += 15
            elif exit_irr >= 0.04:
                score += 5
            else:
                score -= 10

        if exit_profit > 0 and sale_cash > 0:
            score += 10
        elif exit_profit < 0 or sale_cash < 0:
            score -= 15

        if score >= 75:
            label = "実行候補"
            headline = "現条件では、実行を前向きに検討できる水準です。"
        elif score >= 45:
            label = "条件付き実行"
            headline = "実行は可能性がありますが、いくつかの条件確認が必要です。"
        elif score >= 20:
            label = "待つ"
            headline = "今すぐ実行せず、資金・条件・出口の改善を待つ判断が妥当です。"
        else:
            label = "見送り"
            headline = "現条件ではリスクが大きく、見送りまたは大幅な条件修正を推奨します。"

        if after_cash <= 0:
            label = "見送り"
            headline = "取得後現金が不足するため、現条件での実行は避けるべきです。"

        if monthly_cf_delta < 0 and safety_surplus < 0:
            label = "待つ"
            headline = "年間CFと安全資金の両方に課題があるため、今は待つ判断が妥当です。"

        return {
            "label": label,
            "headline": headline,
            "score": score,
        }

    def _executive_summary(
        self,
        decision: dict[str, Any],
        best: dict[str, Any],
        liquidity_review: dict[str, Any],
        exit_result: dict[str, Any],
    ) -> str:
        if not best:
            return decision["headline"]

        scenario = best.get("scenario", "-")
        after_cash = self._yen(self._num(best.get("after_transaction_cash")))
        safety_surplus = self._yen(self._num(best.get("safety_surplus")))
        annual_cf_delta = self._yen(self._num(best.get("annual_cf_delta")))
        dscr = self._fmt_x(self._num(best.get("acquisition_dscr")))
        irr = self._fmt_pct(self._num(exit_result.get("irr")))

        return (
            f"最終判断は「{decision['label']}」です。"
            f"最有力シナリオは「{scenario}」。"
            f"取得後現金は{after_cash}、安全資金との差額は{safety_surplus}、"
            f"年間CF差分は{annual_cf_delta}です。"
            f"取得DSCRは{dscr}、出口IRRは{irr}です。"
        )

    def _decision_factors(
        self,
        best: dict[str, Any],
        liquidity_review: dict[str, Any],
        exit_result: dict[str, Any],
    ) -> list[dict[str, str]]:
        if not best:
            return [
                {
                    "factor": "データ",
                    "status": "要確認",
                    "comment": "シナリオが作成できませんでした。",
                }
            ]

        factors: list[dict[str, str]] = []

        factors.append(
            self._factor(
                "売却資金",
                bool(best.get("funds_acquisition")),
                "税引後売却資金で初期必要資金を賄えます。",
                "税引後売却資金だけでは初期必要資金に届きません。",
            )
        )

        safety_surplus = self._num(best.get("safety_surplus")) or 0
        factors.append(
            self._factor(
                "安全資金",
                safety_surplus >= 0,
                f"安全資金を{self._yen(safety_surplus)}上回ります。",
                f"安全資金に対して{self._yen(abs(safety_surplus))}不足します。",
            )
        )

        annual_cf_delta = self._num(best.get("annual_cf_delta")) or 0
        factors.append(
            self._factor(
                "年間CF",
                annual_cf_delta >= 0,
                f"株式配当減少後でも年間CFは{self._yen(annual_cf_delta)}改善します。",
                f"株式配当減少後の年間CFは{self._yen(abs(annual_cf_delta))}悪化します。",
            )
        )

        dscr = self._num(best.get("acquisition_dscr"))
        factors.append(
            self._factor(
                "DSCR",
                dscr is not None and dscr >= 1.0,
                f"取得DSCRは{self._fmt_x(dscr)}です。",
                f"取得DSCRは{self._fmt_x(dscr)}で返済余力に注意が必要です。",
            )
        )

        irr = self._num(exit_result.get("irr"))
        factors.append(
            self._factor(
                "出口IRR",
                irr is not None and irr >= 0.04,
                f"出口IRRは{self._fmt_pct(irr)}です。",
                f"出口IRRは{self._fmt_pct(irr)}で低めです。",
            )
        )

        return factors

    def _must_check(
        self,
        decision: dict[str, Any],
        best: dict[str, Any],
        liquidity_review: dict[str, Any],
        exit_result: dict[str, Any],
    ) -> list[str]:
        checks: list[str] = []

        if not best:
            return ["金融資産データ、物件取得条件、流動性条件を確認する。"]

        if not bool(best.get("funds_acquisition")):
            checks.append("初期必要資金に対する不足額を、追加売却・現金・購入条件見直しで埋める。")

        if (self._num(best.get("safety_surplus")) or 0) < 0:
            checks.append("安全資金不足を解消するまで実行しない。")

        if (self._num(best.get("annual_cf_delta")) or 0) < 0:
            checks.append("配当減少を不動産CFで補えないため、売却銘柄または物件条件を見直す。")

        dscr = self._num(best.get("acquisition_dscr"))
        if dscr is None or dscr < 1.25:
            checks.append("金利+1%・空室率15%のストレス条件でDSCRを再確認する。")

        irr = self._num(exit_result.get("irr"))
        if irr is None or irr < 0.04:
            checks.append("売却価格-10%ケースと保有年数別IRRを確認する。")

        checks.append("融資承認、火災保険、修繕見積、税金、レントロールを実行前に最終確認する。")

        return checks[:6]

    @staticmethod
    def _factor(factor: str, ok: bool, ok_comment: str, ng_comment: str) -> dict[str, str]:
        return {
            "factor": factor,
            "status": "OK" if ok else "要確認",
            "comment": ok_comment if ok else ng_comment,
        }

    @staticmethod
    def _num(value: Any) -> float | None:
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _yen(value: float | None) -> str:
        if value is None:
            return "-"
        return f"¥{value:,.0f}"

    @staticmethod
    def _fmt_pct(value: float | None) -> str:
        if value is None:
            return "-"
        return f"{value:.2%}"

    @staticmethod
    def _fmt_x(value: float | None) -> str:
        if value is None:
            return "-"
        return f"{value:.2f}x"
