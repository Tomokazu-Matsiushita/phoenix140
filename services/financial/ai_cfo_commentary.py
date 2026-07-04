from __future__ import annotations

from typing import Any


class AICFOCommentaryService:
    # Rule-based commentary engine for Phoenix AI CFO.
    #
    # This version does not call any external AI API.
    # It creates explainable comments from sell-plan simulation results.

    def build_review(self, scenarios: list[Any], target_net_cash: float) -> dict[str, Any]:
        if not scenarios:
            return {
                "recommended_name": "",
                "executive_summary": "売却案がありません。条件を見直してください。",
                "scenario_comments": [],
            }

        metrics = [self._metrics(scenario, target_net_cash) for scenario in scenarios]
        ranked = sorted(metrics, key=self._score)
        recommended = ranked[0]

        achieved = [m for m in metrics if m["achieved"]]
        if achieved:
            headline = (
                f"目標税引後手取り {self._yen(target_net_cash)} を達成する案があります。"
                f" 現時点の推奨は「{recommended['name']}」です。"
            )
        else:
            best = max(metrics, key=lambda x: x["net_proceeds"])
            headline = (
                f"現在の条件では目標税引後手取り {self._yen(target_net_cash)} に届いていません。"
                f" 最も近い案は「{best['name']}」で、不足額は {self._yen(abs(best['surplus_shortfall']))} です。"
            )

        executive_summary = (
            headline
            + "\n\n"
            + self._recommendation_reason(recommended)
        )

        return {
            "recommended_name": recommended["name"],
            "executive_summary": executive_summary,
            "scenario_comments": [
                {
                    "name": m["name"],
                    "comment": self._scenario_comment(m, target_net_cash),
                    "score": m["score"],
                    "achieved": m["achieved"],
                }
                for m in ranked
            ],
        }

    def _metrics(self, scenario: Any, target_net_cash: float) -> dict[str, Any]:
        r = scenario.result
        details = r.details

        sold_names: list[str] = []
        position_count = 0

        if details is not None and not details.empty and "name" in details.columns:
            sold_names = details["name"].dropna().astype(str).str.strip().tolist()
            position_count = len(sold_names)

        surplus_shortfall = float(r.net_proceeds - target_net_cash)
        achieved = surplus_shortfall >= 0

        metrics = {
            "name": scenario.name,
            "description": scenario.description,
            "gross_proceeds": float(r.gross_proceeds),
            "net_proceeds": float(r.net_proceeds),
            "surplus_shortfall": surplus_shortfall,
            "realized_gain_loss": float(r.realized_gain_loss),
            "tax": float(r.tax),
            "taxable_gain": float(r.taxable_gain),
            "dividend_loss": float(r.dividend_loss),
            "sold_names": sold_names,
            "position_count": position_count,
            "achieved": achieved,
        }
        metrics["score"] = self._score(metrics)
        return metrics

    def _score(self, m: dict[str, Any]) -> float:
        # Lower is better.
        if m["achieved"]:
            surplus_penalty = max(m["surplus_shortfall"], 0) * 0.05
            return (
                m["dividend_loss"] * 3.0
                + m["tax"] * 0.4
                + surplus_penalty
                + m["position_count"] * 5_000
            )

        return (
            10_000_000_000
            + abs(m["surplus_shortfall"]) * 10
            + m["dividend_loss"] * 3.0
            + m["tax"] * 0.4
        )

    def _recommendation_reason(self, m: dict[str, Any]) -> str:
        if m["achieved"]:
            return (
                f"この案は目標を {self._yen(m['surplus_shortfall'])} 上回っています。"
                f" 税額は {self._yen(m['tax'])}、年間配当減少は {self._yen(m['dividend_loss'])} です。"
                " 目標達成と配当影響のバランスを見て、現時点では最も現実的な候補です。"
            )

        return (
            f"この案は目標まで {self._yen(abs(m['surplus_shortfall']))} 不足しています。"
            " 除外銘柄を減らす、海運株の売却比率を上げる、またはpolicy=コア除外をOFFにする余地があります。"
        )

    def _scenario_comment(self, m: dict[str, Any], target_net_cash: float) -> str:
        if m["achieved"]:
            status = (
                f"目標 {self._yen(target_net_cash)} に対して、"
                f"税引後手取りは {self._yen(m['net_proceeds'])} で達成しています。"
            )
        else:
            status = (
                f"税引後手取りは {self._yen(m['net_proceeds'])} で、"
                f"目標まで {self._yen(abs(m['surplus_shortfall']))} 不足しています。"
            )

        sold = "、".join(m["sold_names"]) if m["sold_names"] else "なし"

        if m["realized_gain_loss"] < 0:
            tax_comment = (
                "譲渡損が出ているため、税負担を抑える効果があります。"
                " 損益通算候補を使う案としては良い方向です。"
            )
        elif m["tax"] == 0:
            tax_comment = "課税対象利益がほぼないため、税負担は限定的です。"
        else:
            tax_comment = (
                f"譲渡益があり、税額は {self._yen(m['tax'])} です。"
                " 税引後手取りは十分か、配当減少とのバランス確認が必要です。"
            )

        if m["dividend_loss"] <= 10_000:
            dividend_comment = "年間配当への影響は小さめです。"
        elif m["dividend_loss"] <= 50_000:
            dividend_comment = "年間配当への影響は中程度です。売却後の配当計画を確認してください。"
        else:
            dividend_comment = "年間配当への影響が大きめです。手取り確保を優先する局面か再確認してください。"

        return (
            f"{status}\n\n"
            f"- 売却対象: {sold}\n"
            f"- 譲渡損益: {self._yen(m['realized_gain_loss'])}\n"
            f"- 税額: {self._yen(m['tax'])}\n"
            f"- 年間配当減少: {self._yen(m['dividend_loss'])}\n\n"
            f"{tax_comment}\n\n"
            f"{dividend_comment}"
        )

    @staticmethod
    def _yen(value: float) -> str:
        return f"¥{value:,.0f}"
