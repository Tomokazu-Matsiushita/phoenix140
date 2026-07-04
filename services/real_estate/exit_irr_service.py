from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass
class ExitIRRInput:
    property_name: str = "oblige新田町"
    purchase_price: float = 76_000_000
    loan_amount: float = 76_000_000
    annual_interest_rate: float = 3.0
    loan_years: float = 34

    initial_cash_required: float = 5_320_000
    annual_cash_flow: float = 2_475_987
    annual_cash_flow_growth_rate: float = 0.0

    holding_years: int = 10
    exit_price: float = 76_000_000
    selling_cost_rate: float = 4.0

    annual_depreciation: float = 0.0
    capital_gain_tax_rate: float = 20.315


class ExitIRRService:
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

    def remaining_balance(
        self,
        principal: float,
        annual_rate_percent: float,
        years: float,
        months_elapsed: int,
    ) -> float:
        principal = float(principal or 0)
        annual_rate_percent = float(annual_rate_percent or 0)
        years = float(years or 0)
        months_elapsed = int(months_elapsed or 0)

        if principal <= 0 or years <= 0:
            return 0.0

        total_months = int(round(years * 12))
        months_elapsed = max(0, min(months_elapsed, total_months))
        monthly_payment = self.payment(principal, annual_rate_percent, years)
        monthly_rate = annual_rate_percent / 100 / 12

        if monthly_rate == 0:
            return max(principal - monthly_payment * months_elapsed, 0.0)

        balance = principal * (1 + monthly_rate) ** months_elapsed - monthly_payment * (
            ((1 + monthly_rate) ** months_elapsed - 1) / monthly_rate
        )
        return max(balance, 0.0)

    def evaluate(self, inputs: ExitIRRInput | dict[str, Any]) -> dict[str, Any]:
        i = inputs if isinstance(inputs, ExitIRRInput) else ExitIRRInput(**inputs)

        holding_years = int(max(i.holding_years, 1))
        months_elapsed = holding_years * 12

        monthly_payment = self.payment(i.loan_amount, i.annual_interest_rate, i.loan_years)
        annual_debt_service = monthly_payment * 12
        remaining_loan = self.remaining_balance(
            principal=i.loan_amount,
            annual_rate_percent=i.annual_interest_rate,
            years=i.loan_years,
            months_elapsed=months_elapsed,
        )

        annual_cash_flows = []
        for year in range(1, holding_years + 1):
            cf = i.annual_cash_flow * ((1 + i.annual_cash_flow_growth_rate / 100) ** (year - 1))
            annual_cash_flows.append(cf)

        cumulative_cash_flow = sum(annual_cash_flows)

        selling_cost = i.exit_price * i.selling_cost_rate / 100
        adjusted_basis = max(i.purchase_price - i.annual_depreciation * holding_years, 0)
        taxable_gain = max(i.exit_price - selling_cost - adjusted_basis, 0)
        capital_gain_tax = taxable_gain * i.capital_gain_tax_rate / 100

        sale_cash_after_debt_tax = i.exit_price - selling_cost - remaining_loan - capital_gain_tax
        total_recovery = cumulative_cash_flow + sale_cash_after_debt_tax
        total_profit = total_recovery - i.initial_cash_required

        equity_multiple = self._div(total_recovery, i.initial_cash_required)
        simple_annual_return = self._div(total_profit, i.initial_cash_required * holding_years)

        cash_flows = [-i.initial_cash_required]
        if holding_years > 1:
            cash_flows.extend(annual_cash_flows[:-1])
        cash_flows.append(annual_cash_flows[-1] + sale_cash_after_debt_tax)

        irr = self.irr(cash_flows)

        result = {
            **asdict(i),
            "monthly_payment": monthly_payment,
            "annual_debt_service": annual_debt_service,
            "remaining_loan_balance": remaining_loan,
            "selling_cost": selling_cost,
            "adjusted_basis": adjusted_basis,
            "taxable_gain": taxable_gain,
            "capital_gain_tax": capital_gain_tax,
            "sale_cash_after_debt_tax": sale_cash_after_debt_tax,
            "cumulative_cash_flow": cumulative_cash_flow,
            "total_recovery": total_recovery,
            "total_profit": total_profit,
            "equity_multiple": equity_multiple,
            "simple_annual_return": simple_annual_return,
            "irr": irr,
            "cash_flows": cash_flows,
        }

        result["health"] = self._health_label(result)
        result["cfo_comment"] = self._comment(result)

        return result

    def sensitivity_table(
        self,
        inputs: ExitIRRInput | dict[str, Any],
        holding_years_list: list[int] | None = None,
        exit_price_change_rates: list[float] | None = None,
    ) -> pd.DataFrame:
        base = inputs if isinstance(inputs, ExitIRRInput) else ExitIRRInput(**inputs)

        if holding_years_list is None:
            holding_years_list = [3, 5, 7, 10, 15, 20]

        if exit_price_change_rates is None:
            exit_price_change_rates = [-20, -10, -5, 0, 5, 10, 20, 30]

        rows = []
        for years in holding_years_list:
            for change_rate in exit_price_change_rates:
                scenario = ExitIRRInput(**asdict(base))
                scenario.holding_years = int(years)
                scenario.exit_price = base.purchase_price * (1 + change_rate / 100)
                r = self.evaluate(scenario)

                rows.append(
                    {
                        "holding_years": years,
                        "exit_price_change_rate": change_rate,
                        "exit_price": r["exit_price"],
                        "remaining_loan_balance": r["remaining_loan_balance"],
                        "sale_cash_after_debt_tax": r["sale_cash_after_debt_tax"],
                        "cumulative_cash_flow": r["cumulative_cash_flow"],
                        "total_recovery": r["total_recovery"],
                        "total_profit": r["total_profit"],
                        "equity_multiple": r["equity_multiple"],
                        "simple_annual_return": r["simple_annual_return"],
                        "irr": r["irr"],
                        "health": r["health"],
                    }
                )

        return pd.DataFrame(rows)

    def irr(self, cash_flows: list[float]) -> float | None:
        if not cash_flows:
            return None

        if not any(cf < 0 for cf in cash_flows) or not any(cf > 0 for cf in cash_flows):
            return None

        def npv(rate: float) -> float:
            total = 0.0
            for t, cf in enumerate(cash_flows):
                total += cf / ((1 + rate) ** t)
            return total

        low = -0.9999
        high = 10.0

        try:
            low_npv = npv(low)
            high_npv = npv(high)
        except Exception:
            return None

        if low_npv == 0:
            return low
        if high_npv == 0:
            return high

        if low_npv * high_npv > 0:
            return None

        for _ in range(200):
            mid = (low + high) / 2
            mid_npv = npv(mid)

            if abs(mid_npv) < 1e-7:
                return mid

            if low_npv * mid_npv <= 0:
                high = mid
                high_npv = mid_npv
            else:
                low = mid
                low_npv = mid_npv

        return (low + high) / 2

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
        irr = r.get("irr")
        profit = r.get("total_profit")
        sale_cash = r.get("sale_cash_after_debt_tax")

        if irr is None:
            return "要確認"
        if irr >= 0.08 and profit > 0 and sale_cash > 0:
            return "有力"
        if irr >= 0.04 and profit > 0:
            return "条件付き"
        if profit > 0:
            return "低リターン"
        return "見送り"

    @staticmethod
    def _comment(r: dict[str, Any]) -> str:
        comments: list[str] = []

        irr = r.get("irr")
        profit = r.get("total_profit")
        equity_multiple = r.get("equity_multiple")
        sale_cash = r.get("sale_cash_after_debt_tax")

        if irr is None:
            comments.append("IRRを計算できません。初期投資額、年間CF、売却後手残りを確認してください。")
        elif irr >= 0.08:
            comments.append("IRRは8%以上で、投資リターンは比較的良好です。")
        elif irr >= 0.04:
            comments.append("IRRは4%以上ですが、出口価格や空室の前提確認が必要です。")
        else:
            comments.append("IRRは低めです。購入価格、家賃、出口価格の見直し余地があります。")

        if profit is not None:
            if profit > 0:
                comments.append("累積CFと売却後手残りを含めた総損益はプラスです。")
            else:
                comments.append("総損益がマイナスです。出口価格または借入条件に注意してください。")

        if sale_cash is not None and sale_cash < 0:
            comments.append("売却時の手残りがマイナスです。残債と売却価格のバランスに注意が必要です。")

        if equity_multiple is not None:
            comments.append(f"投下自己資金に対する回収倍率は約{equity_multiple:.2f}倍です。")

        return " ".join(comments)
