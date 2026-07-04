from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class SellSimulationResult:
    details: pd.DataFrame
    gross_proceeds: float
    realized_gain_loss: float
    taxable_gain: float
    tax: float
    net_proceeds: float
    dividend_loss: float
    target_net_cash: float
    surplus_shortfall: float
    tax_rate: float


class SellSimulator:
    """Tax-aware sell simulator for Japanese taxable accounts."""

    def simulate(
        self,
        assets: pd.DataFrame,
        sale_plan: list[dict[str, Any]],
        tax_rate: float = 0.20315,
        target_net_cash: float = 3_500_000,
    ) -> SellSimulationResult:
        rows = []

        if assets.empty or not sale_plan:
            empty = pd.DataFrame(
                columns=[
                    "name",
                    "sell_quantity",
                    "current_price",
                    "cost_price",
                    "gross_proceeds",
                    "cost_basis",
                    "realized_gain_loss",
                    "annual_dividend_loss",
                    "policy",
                ]
            )
            return SellSimulationResult(
                details=empty,
                gross_proceeds=0.0,
                realized_gain_loss=0.0,
                taxable_gain=0.0,
                tax=0.0,
                net_proceeds=0.0,
                dividend_loss=0.0,
                target_net_cash=target_net_cash,
                surplus_shortfall=-target_net_cash,
                tax_rate=tax_rate,
            )

        indexed = assets.set_index("name", drop=False)

        for item in sale_plan:
            name = item["name"]
            sell_quantity = float(item.get("sell_quantity", 0) or 0)

            if sell_quantity <= 0 or name not in indexed.index:
                continue

            row = indexed.loc[name]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]

            quantity = float(row.get("quantity", 0) or 0)
            current_price = float(row.get("current_price", 0) or 0)
            cost_price = float(row.get("cost_price", 0) or 0)
            annual_dividend = float(row.get("annual_dividend", 0) or 0)

            sell_quantity = min(sell_quantity, quantity)
            gross_proceeds = sell_quantity * current_price
            cost_basis = sell_quantity * cost_price
            realized_gain_loss = gross_proceeds - cost_basis
            annual_dividend_loss = annual_dividend * (sell_quantity / quantity) if quantity else 0

            rows.append(
                {
                    "name": name,
                    "sell_quantity": sell_quantity,
                    "current_price": current_price,
                    "cost_price": cost_price,
                    "gross_proceeds": gross_proceeds,
                    "cost_basis": cost_basis,
                    "realized_gain_loss": realized_gain_loss,
                    "annual_dividend_loss": annual_dividend_loss,
                    "policy": row.get("policy", ""),
                }
            )

        details = pd.DataFrame(rows)

        if details.empty:
            return self.simulate(pd.DataFrame(), [], tax_rate, target_net_cash)

        gross = float(details["gross_proceeds"].sum())
        realized = float(details["realized_gain_loss"].sum())
        taxable_gain = max(realized, 0.0)
        tax = taxable_gain * tax_rate
        net = gross - tax
        dividend_loss = float(details["annual_dividend_loss"].sum())

        return SellSimulationResult(
            details=details,
            gross_proceeds=gross,
            realized_gain_loss=realized,
            taxable_gain=taxable_gain,
            tax=tax,
            net_proceeds=net,
            dividend_loss=dividend_loss,
            target_net_cash=target_net_cash,
            surplus_shortfall=net - target_net_cash,
            tax_rate=tax_rate,
        )
