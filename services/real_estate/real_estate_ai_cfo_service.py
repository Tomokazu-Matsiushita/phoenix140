from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd

from services.real_estate.property_metrics_service import PropertyMetricsService
from services.real_estate.property_acquisition_service import AcquisitionInput, PropertyAcquisitionService
from services.real_estate.exit_irr_service import ExitIRRInput, ExitIRRService


@dataclass
class CFOComment:
    area: str
    title: str
    status: str
    summary: str
    strengths: list[str]
    risks: list[str]
    actions: list[str]
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RealEstateAICFOService:
    def __init__(
        self,
        metrics_service: PropertyMetricsService | None = None,
        acquisition_service: PropertyAcquisitionService | None = None,
        exit_service: ExitIRRService | None = None,
    ) -> None:
        self.metrics_service = metrics_service or PropertyMetricsService()
        self.acquisition_service = acquisition_service or PropertyAcquisitionService()
        self.exit_service = exit_service or ExitIRRService()

    def full_review(
        self,
        acquisition_input: AcquisitionInput | dict[str, Any] | None = None,
        exit_input: ExitIRRInput | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        comments: list[CFOComment] = []

        comments.append(self.portfolio_review())
        comments.extend(self.property_reviews())

        if acquisition_input is not None:
            comments.append(self.acquisition_review(acquisition_input))

        if exit_input is not None:
            comments.append(self.exit_review(exit_input))

        ranked = sorted(comments, key=lambda x: x.score, reverse=True)

        return {
            "comments": [c.to_dict() for c in ranked],
            "executive_summary": self.executive_summary(ranked),
            "priority_actions": self.priority_actions(ranked),
        }

    def portfolio_review(self) -> CFOComment:
        metrics = self.metrics_service.property_metrics()

        if metrics.empty:
            return CFOComment(
                area="portfolio",
                title="不動産ポートフォリオ",
                status="要データ確認",
                summary="物件データが不足しています。まずProperty Metricsで物件データを確認してください。",
                strengths=[],
                risks=["物件別のNOI、返済額、DSCRが確認できません。"],
                actions=["propertiesテーブルと物件別入力値を確認する。"],
                score=0,
            )

        total_noi = float(metrics["noi"].fillna(0).sum()) if "noi" in metrics.columns else 0.0
        total_debt = float(metrics["annual_debt_service"].fillna(0).sum()) if "annual_debt_service" in metrics.columns else 0.0
        total_cf = float(metrics["cash_flow_after_debt"].fillna(0).sum()) if "cash_flow_after_debt" in metrics.columns else 0.0
        portfolio_dscr = total_noi / total_debt if total_debt else None

        weak_count = int((metrics.get("health", pd.Series(dtype=str)) == "要改善").sum())
        attention_count = int((metrics.get("health", pd.Series(dtype=str)) == "注意").sum())

        strengths: list[str] = []
        risks: list[str] = []
        actions: list[str] = []

        if portfolio_dscr is not None and portfolio_dscr >= 1.25:
            strengths.append(f"ポートフォリオDSCRは{portfolio_dscr:.2f}倍で、返済余力は比較的良好です。")
        elif portfolio_dscr is not None and portfolio_dscr >= 1.0:
            risks.append(f"ポートフォリオDSCRは{portfolio_dscr:.2f}倍で、余裕は限定的です。")
            actions.append("金利+1%と空室増加時の返済後CFを確認する。")
        else:
            risks.append("ポートフォリオDSCRが1.0倍未満、または算出不能です。")
            actions.append("返済額・賃料・経費データを確認し、弱い物件の改善策を検討する。")

        if total_cf >= 0:
            strengths.append(f"ポートフォリオ返済後CFはプラスです（{self._yen(total_cf)}）。")
        else:
            risks.append(f"ポートフォリオ返済後CFがマイナスです（{self._yen(total_cf)}）。")
            actions.append("返済条件、空室、管理費、修繕費を見直す。")

        if weak_count > 0:
            risks.append(f"要改善判定の物件が{weak_count}件あります。")
        if attention_count > 0:
            risks.append(f"注意判定の物件が{attention_count}件あります。")

        if not actions:
            actions.append("次の物件取得前に、既存物件の空室・金利ストレスを定期確認する。")

        score = self._score_from_dscr_cf(portfolio_dscr, total_cf)

        return CFOComment(
            area="portfolio",
            title="不動産ポートフォリオ",
            status=self._status_from_score(score),
            summary=self._portfolio_summary(portfolio_dscr, total_cf, len(metrics)),
            strengths=strengths,
            risks=risks,
            actions=actions,
            score=score,
        )

    def property_reviews(self) -> list[CFOComment]:
        metrics = self.metrics_service.property_metrics()
        if metrics.empty:
            return []

        comments: list[CFOComment] = []

        for _, row in metrics.iterrows():
            name = str(row.get("name", "Property"))
            dscr = self._num(row.get("dscr"))
            cf = self._num(row.get("cash_flow_after_debt"))
            occupancy = self._num(row.get("occupancy_rate"))
            break_even = self._num(row.get("break_even_occupancy"))
            gross_yield = self._num(row.get("gross_yield"))

            strengths: list[str] = []
            risks: list[str] = []
            actions: list[str] = []

            if dscr is not None:
                if dscr >= 1.25:
                    strengths.append(f"DSCRは{dscr:.2f}倍で安定感があります。")
                elif dscr >= 1.0:
                    risks.append(f"DSCRは{dscr:.2f}倍で、金利上昇時の余裕は限定的です。")
                    actions.append("Loan DSCR Simulatorで金利+1%、+2%を確認する。")
                else:
                    risks.append(f"DSCRが{dscr:.2f}倍で1.0倍を下回っています。")
                    actions.append("返済条件または空室・経費改善を検討する。")
            else:
                risks.append("DSCRが算出できません。")
                actions.append("ローン残高、金利、返済額を入力する。")

            if cf is not None and cf >= 0:
                strengths.append(f"返済後CFはプラスです（{self._yen(cf)}）。")
            elif cf is not None:
                risks.append(f"返済後CFがマイナスです（{self._yen(cf)}）。")
                actions.append("CF悪化の原因を家賃・空室・経費・返済額に分解する。")

            if occupancy is not None:
                if occupancy >= 0.95:
                    strengths.append(f"稼働率は{occupancy:.1%}で高水準です。")
                elif occupancy >= 0.90:
                    risks.append(f"稼働率は{occupancy:.1%}で、もう少し改善余地があります。")
                    actions.append("空室期間と募集条件を確認する。")
                else:
                    risks.append(f"稼働率が{occupancy:.1%}で低めです。")
                    actions.append("賃料設定、広告、管理会社対応を確認する。")

            if break_even is not None:
                if break_even <= 0.85:
                    strengths.append(f"損益分岐稼働率は{break_even:.1%}で空室耐性があります。")
                elif break_even <= 0.95:
                    risks.append(f"損益分岐稼働率は{break_even:.1%}でやや高めです。")
                else:
                    risks.append(f"損益分岐稼働率が{break_even:.1%}と高く、満室維持が重要です。")
                    actions.append("空室2室以上のストレスケースを確認する。")

            if gross_yield is not None and gross_yield >= 0.075:
                strengths.append(f"表面利回りは{gross_yield:.2%}です。")

            if not actions:
                actions.append("現在の条件では大きな問題は見えません。定期的に賃料・修繕・金利を更新する。")

            score = self._score_from_dscr_cf(dscr, cf)

            comments.append(
                CFOComment(
                    area="property",
                    title=name,
                    status=self._status_from_score(score),
                    summary=self._property_summary(name, dscr, cf, occupancy),
                    strengths=strengths,
                    risks=risks,
                    actions=actions,
                    score=score,
                )
            )

        return comments

    def acquisition_review(self, inputs: AcquisitionInput | dict[str, Any]) -> CFOComment:
        r = self.acquisition_service.evaluate(inputs)

        dscr = self._num(r.get("dscr"))
        cf = self._num(r.get("cash_flow_after_debt"))
        break_even = self._num(r.get("break_even_occupancy"))
        coc = self._num(r.get("cash_on_cash"))
        name = str(r.get("property_name", "Acquisition"))

        strengths: list[str] = []
        risks: list[str] = []
        actions: list[str] = []

        if dscr is not None and dscr >= 1.25:
            strengths.append(f"取得後DSCRは{dscr:.2f}倍で、返済余力は比較的良好です。")
        elif dscr is not None and dscr >= 1.0:
            risks.append(f"取得後DSCRは{dscr:.2f}倍で、金利上昇時には注意が必要です。")
            actions.append("金利+1%・空室率15%の条件で再確認する。")
        else:
            risks.append("取得後DSCRが1.0倍未満、または算出不能です。")
            actions.append("購入価格、借入額、家賃、管理費を見直す。")

        if cf is not None and cf >= 0:
            strengths.append(f"取得後の返済後CFはプラスです（{self._yen(cf)}）。")
        elif cf is not None:
            risks.append(f"取得後の返済後CFがマイナスです（{self._yen(cf)}）。")

        if break_even is not None:
            if break_even <= 0.85:
                strengths.append(f"損益分岐稼働率は{break_even:.1%}で、空室耐性があります。")
            elif break_even <= 0.95:
                risks.append(f"損益分岐稼働率は{break_even:.1%}でやや高めです。")
            else:
                risks.append(f"損益分岐稼働率が{break_even:.1%}と高く、満室前提に近い投資です。")
                actions.append("家賃下落・空室増加時にCFが残るか確認する。")

        if coc is not None and coc > 0:
            strengths.append(f"自己資金利回りは{coc:.2%}です。")

        if not actions:
            actions.append("レントロール、修繕履歴、近隣賃料、出口価格を確認してから最終判断する。")

        score = self._score_from_dscr_cf(dscr, cf)

        return CFOComment(
            area="acquisition",
            title=f"取得判断: {name}",
            status=self._status_from_score(score),
            summary=f"{name}の取得案は、DSCR {self._fmt_x(dscr)}、返済後CF {self._yen(cf)} の前提です。",
            strengths=strengths,
            risks=risks,
            actions=actions,
            score=score,
        )

    def exit_review(self, inputs: ExitIRRInput | dict[str, Any]) -> CFOComment:
        r = self.exit_service.evaluate(inputs)

        irr = self._num(r.get("irr"))
        profit = self._num(r.get("total_profit"))
        sale_cash = self._num(r.get("sale_cash_after_debt_tax"))
        multiple = self._num(r.get("equity_multiple"))
        name = str(r.get("property_name", "Exit"))

        strengths: list[str] = []
        risks: list[str] = []
        actions: list[str] = []

        if irr is not None:
            if irr >= 0.08:
                strengths.append(f"IRRは{irr:.2%}で、出口リターンは良好です。")
            elif irr >= 0.04:
                risks.append(f"IRRは{irr:.2%}で、リターンは中程度です。")
                actions.append("売却価格-10%ケースでも総損益が残るか確認する。")
            else:
                risks.append(f"IRRは{irr:.2%}で低めです。")
                actions.append("保有年数、売却価格、年間CFの前提を見直す。")
        else:
            risks.append("IRRを算出できません。")
            actions.append("初期必要資金、年間CF、売却価格を確認する。")

        if profit is not None and profit > 0:
            strengths.append(f"累積CF込みの総損益はプラスです（{self._yen(profit)}）。")
        elif profit is not None:
            risks.append(f"累積CF込みの総損益がマイナスです（{self._yen(profit)}）。")

        if sale_cash is not None and sale_cash > 0:
            strengths.append(f"売却後手残りはプラスです（{self._yen(sale_cash)}）。")
        elif sale_cash is not None:
            risks.append(f"売却後手残りがマイナスです（{self._yen(sale_cash)}）。")
            actions.append("残債と出口価格のバランスを確認する。")

        if multiple is not None:
            strengths.append(f"回収倍率は{multiple:.2f}倍です。")

        if not actions:
            actions.append("売却価格-10%・保有5年/10年/15年のIRRを比較する。")

        score = 0.0
        if irr is not None:
            score += min(max(irr * 500, -50), 80)
        if profit is not None and profit > 0:
            score += 10
        if sale_cash is not None and sale_cash > 0:
            score += 10

        return CFOComment(
            area="exit",
            title=f"出口判断: {name}",
            status=self._status_from_score(score),
            summary=f"{name}の出口案は、IRR {self._fmt_pct(irr)}、総損益 {self._yen(profit)} の前提です。",
            strengths=strengths,
            risks=risks,
            actions=actions,
            score=score,
        )

    def executive_summary(self, comments: list[CFOComment]) -> str:
        if not comments:
            return "レビュー対象がありません。"

        strong = [c for c in comments if c.status in ["良好", "有力"]]
        caution = [c for c in comments if c.status in ["注意", "条件付き"]]
        weak = [c for c in comments if c.status in ["要改善", "見送り"]]

        parts = [
            f"レビュー対象は{len(comments)}件です。",
            f"良好・有力: {len(strong)}件、注意・条件付き: {len(caution)}件、要改善・見送り: {len(weak)}件。",
        ]

        top_risks = []
        for c in comments:
            top_risks.extend(c.risks[:1])
        if top_risks:
            parts.append("主な確認ポイントは「" + "」「".join(top_risks[:3]) + "」です。")

        return " ".join(parts)

    def priority_actions(self, comments: list[CFOComment]) -> list[str]:
        actions: list[str] = []
        for c in sorted(comments, key=lambda x: x.score):
            for action in c.actions:
                if action not in actions:
                    actions.append(action)
        return actions[:5]

    @staticmethod
    def _score_from_dscr_cf(dscr: float | None, cf: float | None) -> float:
        score = 0.0

        if dscr is None:
            score -= 20
        elif dscr >= 1.25:
            score += 70
        elif dscr >= 1.0:
            score += 45
        else:
            score += 10

        if cf is None:
            score -= 10
        elif cf >= 0:
            score += 20
        else:
            score -= 30

        return score

    @staticmethod
    def _status_from_score(score: float) -> str:
        if score >= 85:
            return "良好"
        if score >= 65:
            return "有力"
        if score >= 45:
            return "条件付き"
        if score >= 20:
            return "注意"
        return "要改善"

    @staticmethod
    def _portfolio_summary(dscr: float | None, cf: float, count: int) -> str:
        return f"不動産ポートフォリオは{count}物件、DSCR {RealEstateAICFOService._fmt_x(dscr)}、返済後CF {RealEstateAICFOService._yen(cf)} の状態です。"

    @staticmethod
    def _property_summary(name: str, dscr: float | None, cf: float | None, occupancy: float | None) -> str:
        return f"{name}はDSCR {RealEstateAICFOService._fmt_x(dscr)}、返済後CF {RealEstateAICFOService._yen(cf)}、稼働率 {RealEstateAICFOService._fmt_pct(occupancy)} の状態です。"

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
