from __future__ import annotations

import pandas as pd
from sqlalchemy import select

from db.database import SessionLocal
from models.tables import PriceHistory


class PriceHistoryRepository:
    def list_history(self, limit: int = 500) -> pd.DataFrame:
        with SessionLocal() as session:
            rows = (
                session.execute(
                    select(PriceHistory)
                    .order_by(PriceHistory.recorded_at.desc(), PriceHistory.id.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )

        if not rows:
            return pd.DataFrame(
                columns=["id", "asset_id", "name", "ticker", "price", "source", "recorded_at"]
            )

        return pd.DataFrame(
            [
                {
                    "id": row.id,
                    "asset_id": row.asset_id,
                    "name": row.name,
                    "ticker": row.ticker,
                    "price": row.price,
                    "source": row.source,
                    "recorded_at": row.recorded_at,
                }
                for row in rows
            ]
        )

    def history_for(self, name: str, limit: int = 100) -> pd.DataFrame:
        df = self.list_history(limit=1000)
        if df.empty:
            return df
        return df[df["name"].eq(name)].head(limit).copy()
