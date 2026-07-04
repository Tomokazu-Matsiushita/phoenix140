from __future__ import annotations

from typing import Any

import pandas as pd

from services.real_estate.property_metrics_service import PropertyMetricsService


class LoanDSCRService:
    def __init__(self, property_metrics_service: PropertyMetricsService | None = None) -> None:
        self.property_metrics_service = property_metrics_service or PropertyMetricsService()

    def payment(self, principal: float, annual_rate_percent: float, years: float) -> float:
        principal = float(principal or 0)
        years = float(years or 0)
        annual_rate_percent = float(annual_rate_percent or 0)

        if principal <= 0 or years <= 0:
            return 0.0

        n = int(round(years * 12))
        monthly_rate = annual_rate_percent / 100 / 12

        if monthly_rate == 0:
            return principal / n

        return principal * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)

    def property_base(self, property_name: str) -> dict[str, Any]:
        metrics = self.property_metrics_service.property_metrics()
        if metrics.empty:
            return {}

        row = metrics[metrics["name"].astype(str).eq(str(property_name))]
        if row.empty:
            return {}

        r = row.iloc[0]
        return {
            "name": r.get("name"),
            "loan_balance": self._num(r.get("loan_balance")),
            "interest_rate": self._num(r.get("interest_rate")),
            "loan_years": self._num(r.get("loan_years")),
            "monthly_payment": self._num(r.get("monthly_payment")),
            "annual_income": self._num(r.get("annual_income")),
            "current_monthly_income": self._num(r.get("current_monthly_income")),
            "operating_expense": self._num(r.get("operating_expense")),
            "noi": self._num(r.get("noi")),
            "annual_debt_service": self._num(r.get("annual_debt_service")),
            "cash_flow_after_debt": self._num(r.get("cash_flow_after_debt")),
            "dscr": self._num(r.get("dscr")),
            "occupied_units": self._num(r.get("occupied_units")),
            "units": self._num(r.get("units")),
        }

    def simulate(
        self,
        property_name: str,
        annual_rate_percent: float | None = None,
        years: float | None = None,
        loan_balance: float | None = None,
        additional_vacancy: int = 0,
        use_formula_payment: bool = True,
    ) -> dict[str, Any]:
        base = self.property_base(property_name)
        if not base:
            return {}

        principal = float(loan_balance if loan_balance is not None else base.get("loan_balance") or 0)
        rate = float(annual_rate_percent if annual_rate_percent is not None else base.get("interest_rate") or 0)
        term_years = float(years if years is not None else base.get("loan_years") or 0)

        if use_formula_payment:
            monthly_payment = self.payment(principal, rate, term_years)
        else:
            monthly_payment = float(base.get("monthly_payment") or 0)

        current_monthly_income = float(base.get("current_monthly_income") or 0)
        if current_monthly_income <= 0:
            current_monthly_income = float(base.get("annual_income") or 0) / 12

        occupied_units = float(base.get("occupied_units") or 0)
        avg_rent = current_monthly_income / occupied_units if occupied_units else 0

        adjusted_monthly_income = max(current_monthly_income - avg_rent * additional_vacancy, 0)
        adjusted_annual_income = adjusted_monthly_income * 12

        operating_expense = float(base.get("operating_expense") or 0)
        adjusted_noi = adjusted_annual_income - operating_expense
        annual_debt_service = monthly_payment * 12
        adjusted_cf = adjusted_noi - annual_debt_service
        adjusted_dscr = adjusted_noi / annual_debt_service if annual_debt_service else None

        return {
            "property": property_name,
            "loan_balance": principal,
            "interest_rate": rate,
            "loan_years": term_years,
            "monthly_payment": monthly_payment,
            "annual_debt_service": annual_debt_service,
            "additional_vacancy": additional_vacancy,
            "avg_rent": avg_rent,
            "adjusted_monthly_income": adjusted_monthly_income,
            "adjusted_annual_income": adjusted_annual_income,
            "operating_expense": operating_expense,
            "adjusted_noi": adjusted_noi,
            "adjusted_cash_flow_after_debt": adjusted_cf,
            "adjusted_dscr": adjusted_dscr,
        }

    def rate_sensitivity(
        self,
        property_name: str,
        rate_steps: list[float] | None = None,
        additional_vacancy: int = 0,
    ) -> pd.DataFrame:
        base = self.property_base(property_name)
        if not base:
            return pd.DataFrame()

        current_rate = float(base.get("interest_rate") or 0)
        if rate_steps is None:
            rate_steps = [current_rate, current_rate + 0.5, current_rate + 1.0, current_rate + 1.5, current_rate + 2.0]

        rows = []
        for rate in rate_steps:
            sim = self.simulate(
                property_name=property_name,
                annual_rate_percent=rate,
                years=base.get("loan_years"),
                loan_balance=base.get("loan_balance"),
                additional_vacancy=additional_vacancy,
                use_formula_payment=True,
            )
            if sim:
                rows.append(sim)

        return pd.DataFrame(rows)

    def portfolio_rate_sensitivity(
        self,
        rate_additions: list[float] | None = None,
        additional_vacancy: int = 0,
    ) -> pd.DataFrame:
        metrics = self.property_metrics_service.property_metrics()
        if metrics.empty:
            return pd.DataFrame()

        if rate_additions is None:
            rate_additions = [0.0, 0.5, 1.0, 1.5, 2.0]

        rows = []
        for addition in rate_additions:
            total_noi = 0.0
            total_debt = 0.0
            total_cf = 0.0

            for _, row in metrics.iterrows():
                name = str(row.get("name"))
                base_rate = self._num(row.get("interest_rate")) or 0
                sim = self.simulate(
                    property_name=name,
                    annual_rate_percent=base_rate + addition,
                    years=self._num(row.get("loan_years")),
                    loan_balance=self._num(row.get("loan_balance")),
                    additional_vacancy=additional_vacancy,
                    use_formula_payment=True,
                )
                if not sim:
                    continue

                total_noi += float(sim["adjusted_noi"] or 0)
                total_debt += float(sim["annual_debt_service"] or 0)
                total_cf += float(sim["adjusted_cash_flow_after_debt"] or 0)

            rows.append(
                {
                    "rate_addition": addition,
                    "portfolio_noi": total_noi,
                    "portfolio_debt_service": total_debt,
                    "portfolio_cash_flow_after_debt": total_cf,
                    "portfolio_dscr": total_noi / total_debt if total_debt else None,
                }
            )

        return pd.DataFrame(rows)

    @staticmethod
    def _num(value: Any) -> float | None:
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None
