from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from services.integrated_ai_cfo_service import IntegratedAICFOService
from services.scenario_assumptions_service import ScenarioAssumptionsService

try:
    from services.moneytree import MoneytreeDataService
except Exception:  # pragma: no cover
    MoneytreeDataService = None  # type: ignore


@dataclass
class CommandCenterSnapshot:
    scenario_name: str
    scenario_saved_at: str | None
    decision_label: str
    decision_score: float
    decision_headline: str
    current_cash: float
    moneytree_total_balance: float
    moneytree_account_count: int
    moneytree_transaction_count: int
    after_transaction_cash: float | None
    safety_surplus: float | None
    annual_cf_delta: float | None
    annual_property_cf: float | None
    dividend_loss: float | None
    acquisition_dscr: float | None
    exit_irr: float | None
    best_scenario_name: str | None
    sold_names: str | None
    monthly_living_expense: float
    emergency_months: float
    target_net_cash: float
    property_name: str
    purchase_price: float
    loan_amount: float
    interest_rate: float
    vacancy_rate: float
    exit_price: float
    annual_cash_flow: float
    sync_status: str


class PhoenixCommandCenterService:
    def __init__(self) -> None:
        self.assumptions_service = ScenarioAssumptionsService()
        self.integrated_service = IntegratedAICFOService()

    def build(self) -> dict[str, Any]:
        assumptions = self.assumptions_service.load()
        inputs = self.assumptions_service.to_integrated_input(assumptions)
        review = self.integrated_service.review(inputs)

        decision = review.get("decision", {})
        best = review.get("best_scenario") or {}
        exit_result = review.get("exit_result") or {}

        moneytree_summary = self._moneytree_summary()

        snapshot = CommandCenterSnapshot(
            scenario_name=str(assumptions.get("scenario_name", "Base Case")),
            scenario_saved_at=assumptions.get("saved_at"),
            decision_label=str(decision.get("label", "-")),
            decision_score=float(decision.get("score", 0) or 0),
            decision_headline=str(decision.get("headline", "")),
            current_cash=float(inputs.current_cash or 0),
            moneytree_total_balance=float(moneytree_summary.get("total_balance", 0) or 0),
            moneytree_account_count=int(moneytree_summary.get("account_count", 0) or 0),
            moneytree_transaction_count=int(moneytree_summary.get("transaction_count", 0) or 0),
            after_transaction_cash=self._maybe_float(best.get("after_transaction_cash")),
            safety_surplus=self._maybe_float(best.get("safety_surplus")),
            annual_cf_delta=self._maybe_float(best.get("annual_cf_delta")),
            annual_property_cf=self._maybe_float(best.get("annual_property_cf")),
            dividend_loss=self._maybe_float(best.get("dividend_loss")),
            acquisition_dscr=self._maybe_float(best.get("acquisition_dscr")),
            exit_irr=self._maybe_float(exit_result.get("irr")),
            best_scenario_name=best.get("scenario"),
            sold_names=best.get("sold_names"),
            monthly_living_expense=float(inputs.monthly_living_expense or 0),
            emergency_months=float(inputs.emergency_months or 0),
            target_net_cash=float(inputs.target_net_cash or 0),
            property_name=str(inputs.acquisition_input.property_name),
            purchase_price=float(inputs.acquisition_input.purchase_price or 0),
            loan_amount=float(inputs.acquisition_input.loan_amount or 0),
            interest_rate=float(inputs.acquisition_input.annual_interest_rate or 0),
            vacancy_rate=float(inputs.acquisition_input.vacancy_rate or 0),
            exit_price=float(inputs.exit_input.exit_price or 0),
            annual_cash_flow=float(inputs.exit_input.annual_cash_flow or 0),
            sync_status=self._sync_status(moneytree_summary),
        )

        return {
            "snapshot": snapshot,
            "review": review,
            "assumptions": assumptions,
            "inputs": inputs,
            "moneytree_summary": moneytree_summary,
            "health_summary": self._health_placeholder(),
            "action_cards": self._action_cards(snapshot),
            "quick_metrics": self._quick_metrics(snapshot),
            "risk_flags": self._risk_flags(snapshot),
        }

    def _moneytree_summary(self) -> dict[str, Any]:
        if MoneytreeDataService is None:
            return {
                "total_balance": 0,
                "account_count": 0,
                "transaction_count": 0,
                "by_institution": pd.DataFrame(),
                "by_type": pd.DataFrame(),
                "monthly_cashflow": pd.DataFrame(),
                "spending_by_category": pd.DataFrame(),
            }

        try:
            service = MoneytreeDataService()
            service.migrate()
            return service.portfolio_summary()
        except Exception:
            return {
                "total_balance": 0,
                "account_count": 0,
                "transaction_count": 0,
                "by_institution": pd.DataFrame(),
                "by_type": pd.DataFrame(),
                "monthly_cashflow": pd.DataFrame(),
                "spending_by_category": pd.DataFrame(),
            }

    def _sync_status(self, moneytree_summary: dict[str, Any]) -> str:
        if moneytree_summary.get("account_count", 0) > 0:
            return "Moneytree data loaded"
        return "Moneytree data not imported yet"

    def _quick_metrics(self, s: CommandCenterSnapshot) -> list[dict[str, Any]]:
        return [
            {"area": "Financial", "metric": "Moneytree total balance", "value": s.moneytree_total_balance, "unit": "JPY"},
            {"area": "Financial", "metric": "Scenario current cash", "value": s.current_cash, "unit": "JPY"},
            {"area": "Decision", "metric": "After transaction cash", "value": s.after_transaction_cash, "unit": "JPY"},
            {"area": "Decision", "metric": "Safety surplus", "value": s.safety_surplus, "unit": "JPY"},
            {"area": "Cashflow", "metric": "Annual CF delta", "value": s.annual_cf_delta, "unit": "JPY"},
            {"area": "Real Estate", "metric": "Acquisition DSCR", "value": s.acquisition_dscr, "unit": "x"},
            {"area": "Real Estate", "metric": "Exit IRR", "value": s.exit_irr, "unit": "%"},
            {"area": "Health", "metric": "Health score", "value": None, "unit": "coming soon"},
        ]

    def _risk_flags(self, s: CommandCenterSnapshot) -> list[dict[str, str]]:
        flags: list[dict[str, str]] = []

        if s.moneytree_account_count == 0:
            flags.append(
                {
                    "level": "info",
                    "area": "Data",
                    "message": "Moneytree CSV/APIデータが未反映です。実データ化すると一覧性と即時性が上がります。",
                }
            )

        if s.safety_surplus is not None and s.safety_surplus < 0:
            flags.append(
                {
                    "level": "danger",
                    "area": "Liquidity",
                    "message": "取得後の安全資金差額がマイナスです。売却額・取得条件・最低現金ラインを再確認してください。",
                }
            )
        elif s.safety_surplus is not None and s.safety_surplus < 1_000_000:
            flags.append(
                {
                    "level": "warning",
                    "area": "Liquidity",
                    "message": "安全資金差額が薄いです。想定外支出に備えた余白確認が必要です。",
                }
            )

        if s.acquisition_dscr is not None and s.acquisition_dscr < 1.2:
            flags.append(
                {
                    "level": "warning",
                    "area": "Real Estate",
                    "message": "DSCRが低めです。空室率・金利上昇・修繕費のストレスを確認してください。",
                }
            )

        if s.annual_cf_delta is not None and s.annual_cf_delta < 0:
            flags.append(
                {
                    "level": "warning",
                    "area": "Cashflow",
                    "message": "売却による配当減少が不動産CFを上回っています。年間CF改善効果を再確認してください。",
                }
            )

        if not flags:
            flags.append(
                {
                    "level": "success",
                    "area": "Overall",
                    "message": "現時点で大きな即時アラートはありません。詳細ページで前提条件を確認してください。",
                }
            )

        return flags

    def _action_cards(self, s: CommandCenterSnapshot) -> list[dict[str, str]]:
        cards = [
            {
                "title": "Scenario Assumptions",
                "status": "重要",
                "message": "判断条件の保存元です。まずここを整えると全ページの見通しが良くなります。",
                "page": "Scenario Assumptions Center",
            },
            {
                "title": "Integrated AI CFO",
                "status": s.decision_label,
                "message": s.decision_headline or "最終判断を確認します。",
                "page": "Integrated AI CFO",
            },
            {
                "title": "Moneytree Dashboard",
                "status": s.sync_status,
                "message": "実データの残高・支出・入出金を確認します。",
                "page": "Moneytree Dashboard",
            },
            {
                "title": "PDF Memo",
                "status": "Export",
                "message": "判断を残す場合はPDFメモとして保存します。",
                "page": "PDF Investment Memo",
            },
        ]
        return cards

    def _health_placeholder(self) -> dict[str, Any]:
        return {
            "status": "coming soon",
            "message": "健康データは将来Sprintで接続予定です。Oura/Apple Health/手入力から開始できます。",
            "candidate_metrics": ["VO2max", "resting heart rate", "sleep score", "HRV", "weekly running distance"],
        }

    @staticmethod
    def _maybe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
        try:
            return float(value)
        except Exception:
            return None
