from __future__ import annotations

import pandas as pd

from repositories.financial_repository import FinancialRepository


class FinancialService:
    """Financial domain service.

    This is the place for business logic:
    - dividend calculations
    - asset allocation
    - tax-loss harvesting
    - sell simulation
    - cash buffer analysis
    """

    def __init__(self, repository: FinancialRepository | None = None) -> None:
        self.repository = repository or FinancialRepository()

    def financial_summary(self) -> dict[str, float]:
        assets = self.repository.list_assets()
        if assets.empty:
            return {
                "total_assets": 0.0,
                "stock_value": 0.0,
                "cash_value": 0.0,
                "investment_value": 0.0,
                "annual_dividend": 0.0,
            }

        stock_value = float(assets.loc[assets["asset_type"].eq("stock"), "value"].sum())
        cash_value = float(
            assets.loc[assets["asset_type"].isin(["cash", "liability"]), "value"].sum()
        )
        investment_value = float(
            assets.loc[assets["asset_type"].isin(["fund", "robo", "pension"]), "value"].sum()
        )

        return {
            "total_assets": float(assets["value"].sum()),
            "stock_value": stock_value,
            "cash_value": cash_value,
            "investment_value": investment_value,
            "annual_dividend": float(assets["annual_dividend"].sum()),
        }

    def dividend_ranking(self) -> pd.DataFrame:
        stocks = self.repository.stock_holdings()
        if stocks.empty:
            return stocks
        return stocks.sort_values("annual_dividend", ascending=False)

    def tax_loss_candidates(self) -> pd.DataFrame:
        stocks = self.repository.stock_holdings()
        if stocks.empty:
            return stocks

        stocks["cost_value"] = stocks["quantity"] * stocks["cost_price"]
        stocks["gain_loss"] = stocks["value"] - stocks["cost_value"]
        return stocks[stocks["gain_loss"] < 0].sort_values("gain_loss")

    def sell_priority_candidates(self) -> pd.DataFrame:
        """Very early rule-based candidate ranking.

        This is intentionally simple and will be replaced by AI CFO logic.
        """
        stocks = self.repository.stock_holdings()
        if stocks.empty:
            return stocks

        policy_score = {
            "損益通算候補": 1,
            "整理候補": 2,
            "調整": 3,
            "準コア": 4,
            "コア": 5,
        }

        stocks["sell_priority_score"] = stocks["policy"].map(policy_score).fillna(3)
        return stocks.sort_values(["sell_priority_score", "annual_dividend"], ascending=[True, True])
