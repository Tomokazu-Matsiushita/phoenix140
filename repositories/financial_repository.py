from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import select

from db.database import SessionLocal
from models.tables import FinancialAsset


class FinancialRepository:
    """Repository for financial asset records.

    This class is intentionally built around the current FinancialAsset table.
    Sprint 2 will later migrate this to normalized tables:
    Institution, Account, Holding, Transaction, Dividend, Price.

    UI pages should call services, and services should call this repository.
    """

    def list_assets(self) -> pd.DataFrame:
        with SessionLocal() as session:
            rows = session.execute(select(FinancialAsset)).scalars().all()

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {
                    "id": row.id,
                    "source": row.source,
                    "institution": row.institution,
                    "account_name": row.account_name,
                    "asset_type": row.asset_type,
                    "name": row.name,
                    "sector": row.sector,
                    "quantity": row.quantity,
                    "cost_price": row.cost_price,
                    "current_price": row.current_price,
                    "value": row.value,
                    "annual_dividend": row.annual_dividend,
                    "policy": row.policy,
                }
                for row in rows
            ]
        )

    def summary_by_asset_type(self) -> pd.DataFrame:
        df = self.list_assets()
        if df.empty:
            return pd.DataFrame(columns=["asset_type", "value", "annual_dividend"])

        return (
            df.groupby("asset_type", as_index=False)
            .agg(value=("value", "sum"), annual_dividend=("annual_dividend", "sum"))
            .sort_values("value", ascending=False)
        )

    def stock_holdings(self) -> pd.DataFrame:
        df = self.list_assets()
        if df.empty:
            return df
        return df[df["asset_type"].eq("stock")].copy()

    def total_value(self) -> float:
        df = self.list_assets()
        if df.empty:
            return 0.0
        return float(df["value"].sum())

    def annual_dividend(self) -> float:
        df = self.list_assets()
        if df.empty:
            return 0.0
        return float(df["annual_dividend"].sum())

    def upsert_manual_asset(self, payload: dict[str, Any]) -> None:
        """Placeholder for manual asset upsert.

        Version 2/3 idea:
        - use id when editing
        - validate payload
        - normalize institution/account/holding
        """
        raise NotImplementedError("Manual upsert will be implemented in Sprint 2.2.")
