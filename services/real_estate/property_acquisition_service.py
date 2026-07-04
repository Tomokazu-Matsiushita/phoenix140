from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd


@dataclass
class AcquisitionInput:
    property_name: str = "oblige新田町"
    purchase_price: float = 76_000_000
    loan_amount: float = 76_000_000
    annual_interest_rate: float = 3.0
    loan_years: float = 34
    acquisition_cost_rate: float = 7.0
    renovation_cost: float = 0
    initial_cash_buffer: float = 0

    units: int = 12
    monthly_full_rent: float = 665_000
    vacancy_rate: float = 8.33

    fixed_asset_tax_annual: float = 618_429
    management_fee_monthly: float = 59_300
    cleaning_fee_monthly: float = 0
    insurance_annual: float = 0
    repair_reserve_monthly: float = 30_000
    other_expense_annual: float = 0


class PropertyAcquisitionService:
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

    def evaluate(self, inputs: AcquisitionInput | dict[str, Any]) -> dict[str, Any]:
        if isinstance(inputs, dict):
            i = AcquisitionInput(**inputs)
        else:
            i = inputs

        monthly_payment = self.payment(i.loan_amount, i.annual_interest_rate, i.loan_years)
        annual_debt_service = monthly_payment * 12

        acquisition_cost = i.purchase_price * i.acquisition_cost_rate / 100
        own_capital = max(i.purchase_price - i.loan_amount, 0)
        initial_cash_required = own_capital + acquisition_cost + i.renovation_cost + i.initial_cash_buffer

        full_annual_rent = i.monthly_full_rent * 12
        effective_annual_rent = full_annual_rent * (1 - i.vacancy_rate / 100)

        operating_expense = (
            i.fixed_asset_tax_annual
            + i.management_fee_monthly * 12
            + i.cleaning_fee_monthly * 12
            + i.insurance_annual
            + i.repair_reserve_monthly * 12
            + i.other_expense_annual
        )

        noi = effective_annual_rent - operating_expense
        cash_flow_after_debt = noi - annual_debt_service

        gross_yield_full = self._div(full_annual_rent, i.purchase_price)
        gross_yield_effective = self._div(effective_annual_rent, i.purchase_price)
        noi_yield = self._div(noi, i.purchase_price)
        dscr = self._div(noi, annual_debt_service)
        ltv = self._div(i.loan_amount, i.purchase_price)
        cash_on_cash = self._div(cash_flow_after_debt, initial_cash_required)
        break_even_occupancy = self._div(annual_debt_service + operating_expense, full_annual_rent)
        payback_years = self._div(initial_cash_required, cash_flow_after_debt) if cash_flow_after_debt > 0 else None

        result = {
            **asdict(i),
            "monthly_payment": monthly_payment,
            "annual_debt_service": annual_debt_service,
            "acquisition_cost": acquisition_cost,
            "own_capital": own_capital,
            "initial_cash_required": initial_cash_required,
            "full_annual_rent": full_annual_rent,
            "effective_annual_rent": effective_annual_rent,
            "operating_expense": operating_expense,
            "noi": noi,
            "cash_flow_after_debt": cash_flow_after_debt,
            "gross_yield_full": gross_yield_full,
            "gross_yield_effective": gross_yield_effective,
            "noi_yield": noi_yield,
            "dscr": dscr,
            "ltv": ltv,
            "cash_on_cash": cash_on_cash,
            "break_even_occupancy": break_even_occupancy,
            "payback_years": payback_years,
        }

        result["health"] = self._health_label(result)
        result["cfo_comment"] = self._comment(result)

        return result

    def sensitivity_table(
        self,
        inputs: AcquisitionInput | dict[str, Any],
        rate_additions: list[float] | None = None,
        vacancy_rates: list[float] | None = None,
    ) -> pd.DataFrame:
        base = inputs if isinstance(inputs, AcquisitionInput) else AcquisitionInput(**inputs)

        if rate_additions is None:
            rate_additions = [0.0, 0.5, 1.0, 1.5, 2.0]

        if vacancy_rates is None:
            vacancy_rates = [0.0, 5.0, 8.33, 10.0, 15.0, 20.0]

        rows = []
        for add in rate_additions:
            for vacancy in vacancy_rates:
                scenario = AcquisitionInput(**asdict(base))
                scenario.annual_interest_rate = base.annual_interest_rate + add
                scenario.vacancy_rate = vacancy
                result = self.evaluate(scenario)
                rows.append(
                    {
                        "interest_rate": result["annual_interest_rate"],
                        "rate_addition": add,
                        "vacancy_rate": vacancy,
                        "monthly_payment": result["monthly_payment"],
                        "annual_debt_service": result["annual_debt_service"],
                        "effective_annual_rent": result["effective_annual_rent"],
                        "noi": result["noi"],
                        "cash_flow_after_debt": result["cash_flow_after_debt"],
                        "dscr": result["dscr"],
                        "cash_on_cash": result["cash_on_cash"],
                        "health": result["health"],
                    }
                )

        return pd.DataFrame(rows)

    @staticmethod
    def _div(a: float, b: float) -> float | None:
        try:
            if b in (0, None):
                return None
            return float(a) / float(b)
        except Exception:
            return None

    @staticmethod
    def _health_label(r: dict[str, Any]) -> str:
        dscr = r.get("dscr")
        cf = r.get("cash_flow_after_debt")
        break_even = r.get("break_even_occupancy")

        if dscr is None:
            return "要データ確認"
        if dscr >= 1.25 and cf >= 0 and (break_even is None or break_even <= 0.85):
            return "有力候補"
        if dscr >= 1.10 and cf >= 0:
            return "条件付き候補"
        if dscr >= 1.0:
            return "慎重検討"
        return "見送り候補"

    @staticmethod
    def _comment(r: dict[str, Any]) -> str:
        comments: list[str] = []

        dscr = r.get("dscr")
        cf = r.get("cash_flow_after_debt")
        break_even = r.get("break_even_occupancy")
        coc = r.get("cash_on_cash")

        if dscr is not None:
            if dscr >= 1.25:
                comments.append("DSCRは1.25倍以上で、返済余力は比較的良好です。")
            elif dscr >= 1.0:
                comments.append("DSCRは1.0倍以上ですが、金利上昇や空室には注意が必要です。")
            else:
                comments.append("DSCRが1.0倍未満で、返済余力に不安があります。")

        if cf is not None:
            if cf >= 0:
                comments.append("返済後CFはプラスです。")
            else:
                comments.append("返済後CFがマイナスです。購入条件または借入条件の見直しが必要です。")

        if break_even is not None:
            if break_even <= 0.85:
                comments.append("損益分岐稼働率は低めで、空室耐性があります。")
            elif break_even <= 0.95:
                comments.append("損益分岐稼働率はやや高めです。空室が増えるとCFが圧迫されます。")
            else:
                comments.append("損益分岐稼働率が高く、満室に近い稼働を維持する必要があります。")

        if coc is not None and coc > 0:
            comments.append(f"自己資金利回りは約{coc:.1%}です。")

        return " ".join(comments)
