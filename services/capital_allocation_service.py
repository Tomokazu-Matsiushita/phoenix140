from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from services.financial import AutoSellPlanGenerator, FinancialService
from services.real_estate import AcquisitionInput, PropertyAcquisitionService


@dataclass
class CapitalAllocationInput:
    target_net_cash: float = 3_500_000
    tax_rate: float = 0.20315
    preserve_names: list[str] | None = None
    preserve_core_policy: bool = True
    shipping_max_sell_ratio: float = 0.5
    acquisition_input: AcquisitionInput | None = None


class CapitalAllocationService:
    def __init__(
        self,
        financial_service: FinancialService | None = None,
        acquisition_service: PropertyAcquisitionService | None = None,
        sell_plan_generator: AutoSellPlanGenerator | None = None,
    ) -> None:
        self.financial_service = financial_service or FinancialService()
        self.acquisition_service = acquisition_service or PropertyAcquisitionService()
        self.sell_plan_generator = sell_plan_generator or AutoSellPlanGenerator()

    def review(self, inputs: CapitalAllocationInput | dict[str, Any]) -> dict[str, Any]:
        if isinstance(inputs, dict):
            inputs = CapitalAllocationInput(**inputs)

        acquisition_input = inputs.acquisition_input or AcquisitionInput()
        acquisition = self.acquisition_service.evaluate(acquisition_input)

        assets = self.financial_service.repository.list_assets()
        scenarios = self.sell_plan_generator.generate(
            assets=assets,
            target_net_cash=float(inputs.target_net_cash),
            tax_rate=float(inputs.tax_rate),
            preserve_names=inputs.preserve_names,
            preserve_core_policy=bool(inputs.preserve_core_policy),
            shipping_max_sell_ratio=float(inputs.shipping_max_sell_ratio),
        )

        rows: list[dict[str, Any]] = []

        for scenario in scenarios:
            result = scenario.result
            sold_names = []
            if result.details is not None and not result.details.empty and "name" in result.details.columns:
                sold_names = result.details["name"].dropna().astype(str).tolist()

            net_proceeds = float(result.net_proceeds)
            dividend_loss = float(result.dividend_loss)
            annual_property_cf = float(acquisition.get("cash_flow_after_debt") or 0)
            initial_cash_required = float(acquisition.get("initial_cash_required") or 0)
            funding_gap = initial_cash_required - net_proceeds
            after_allocation_cash = net_proceeds - initial_cash_required
            annual_cf_delta = annual_property_cf - dividend_loss

            rows.append(
                {
                    "scenario": scenario.name,
                    "description": scenario.description,
                    "net_proceeds": net_proceeds,
                    "tax": float(result.tax),
                    "dividend_loss": dividend_loss,
                    "sold_names": "、".join(sold_names),
                    "initial_cash_required": initial_cash_required,
                    "funding_gap": funding_gap,
                    "after_allocation_cash": after_allocation_cash,
                    "annual_property_cf": annual_property_cf,
                    "annual_cf_delta": annual_cf_delta,
                    "acquisition_dscr": acquisition.get("dscr"),
                    "acquisition_health": acquisition.get("health"),
                    "achieves_sale_target": net_proceeds >= float(inputs.target_net_cash),
                    "funds_acquisition": net_proceeds >= initial_cash_required,
                    "score": self._score(
                        net_proceeds=net_proceeds,
                        target_net_cash=float(inputs.target_net_cash),
                        initial_cash_required=initial_cash_required,
                        dividend_loss=dividend_loss,
                        annual_property_cf=annual_property_cf,
                        acquisition_dscr=acquisition.get("dscr"),
                    ),
                }
            )

        comparison = pd.DataFrame(rows)
        if not comparison.empty:
            comparison = comparison.sort_values("score", ascending=False).reset_index(drop=True)

        return {
            "acquisition": acquisition,
            "comparison": comparison,
            "recommendation": self._recommendation(comparison, acquisition),
            "portfolio_comment": self._portfolio_comment(comparison, acquisition),
        }

    def _score(
        self,
        net_proceeds: float,
        target_net_cash: float,
        initial_cash_required: float,
        dividend_loss: float,
        annual_property_cf: float,
        acquisition_dscr: float | None,
    ) -> float:
        score = 0.0

        if net_proceeds >= target_net_cash:
            score += 25
        else:
            score -= min((target_net_cash - net_proceeds) / 100_000, 25)

        if net_proceeds >= initial_cash_required:
            score += 25
        else:
            score -= min((initial_cash_required - net_proceeds) / 100_000, 25)

        annual_cf_delta = annual_property_cf - dividend_loss
        if annual_cf_delta >= 0:
            score += min(annual_cf_delta / 100_000, 25)
        else:
            score -= min(abs(annual_cf_delta) / 100_000, 25)

        if acquisition_dscr is not None:
            try:
                dscr = float(acquisition_dscr)
                if dscr >= 1.25:
                    score += 20
                elif dscr >= 1.0:
                    score += 10
                else:
                    score -= 15
            except Exception:
                score -= 5

        return score

    def _recommendation(self, comparison: pd.DataFrame, acquisition: dict[str, Any]) -> dict[str, Any]:
        if comparison.empty:
            return {
                "scenario": "",
                "status": "要データ確認",
                "summary": "売却シナリオを作成できませんでした。金融資産データを確認してください。",
            }

        best = comparison.iloc[0].to_dict()

        if best["funds_acquisition"] and best["annual_cf_delta"] > 0:
            status = "実行候補"
            summary = (
                f"最有力は「{best['scenario']}」です。"
                f"税引後売却資金で初期必要資金を賄え、年間CFは差し引きで{self._yen(best['annual_cf_delta'])}改善します。"
            )
        elif best["achieves_sale_target"] and best["annual_cf_delta"] > 0:
            status = "条件付き候補"
            summary = (
                f"「{best['scenario']}」は売却目標を達成し、年間CFも改善します。"
                f"ただし物件取得に必要な資金に対して{self._yen(max(best['funding_gap'], 0))}の不足があります。"
            )
        elif best["annual_cf_delta"] > 0:
            status = "資金不足"
            summary = (
                f"年間CFは改善しますが、売却資金が不足しています。"
                f"追加資金または取得条件の見直しが必要です。"
            )
        else:
            status = "慎重検討"
            summary = (
                "株式配当減少に対して不動産CFの増加が十分ではありません。"
                "売却銘柄、物件条件、借入条件を見直してください。"
            )

        return {
            "scenario": best["scenario"],
            "status": status,
            "summary": summary,
            "score": best["score"],
        }

    def _portfolio_comment(self, comparison: pd.DataFrame, acquisition: dict[str, Any]) -> list[str]:
        comments: list[str] = []

        if acquisition.get("dscr") is not None:
            dscr = float(acquisition["dscr"])
            if dscr >= 1.25:
                comments.append("取得物件のDSCRは1.25倍以上で、返済余力は比較的良好です。")
            elif dscr >= 1.0:
                comments.append("取得物件のDSCRは1.0倍以上ですが、金利上昇・空室増加には注意が必要です。")
            else:
                comments.append("取得物件のDSCRが1.0倍未満です。購入条件の見直しが必要です。")

        if comparison.empty:
            comments.append("売却案がないため、資金調達案を作成できません。")
            return comments

        funded = int(comparison["funds_acquisition"].sum())
        positive_cf = int((comparison["annual_cf_delta"] > 0).sum())

        if funded:
            comments.append(f"初期必要資金を売却資金で賄える案が{funded}件あります。")
        else:
            comments.append("現条件では、売却資金だけで初期必要資金を賄える案はありません。")

        if positive_cf:
            comments.append(f"株式配当減少を不動産CFで上回る案が{positive_cf}件あります。")
        else:
            comments.append("株式配当減少を不動産CFで上回る案がありません。")

        return comments

    @staticmethod
    def _yen(value: float | None) -> str:
        if value is None:
            return "-"
        return f"¥{value:,.0f}"
