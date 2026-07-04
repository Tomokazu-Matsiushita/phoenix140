from __future__ import annotations

import pandas as pd

from repositories.price_history_repository import PriceHistoryRepository


class PriceHistoryService:
    def __init__(self, repository: PriceHistoryRepository | None = None) -> None:
        self.repository = repository or PriceHistoryRepository()

    def latest_history(self, limit: int = 500) -> pd.DataFrame:
        return self.repository.list_history(limit=limit)

    def latest_by_name(self) -> pd.DataFrame:
        df = self.repository.list_history(limit=2000)
        if df.empty:
            return df

        ordered = df.sort_values(["name", "recorded_at"], ascending=[True, False])
        return ordered.groupby("name", as_index=False).head(1).reset_index(drop=True)

    def history_for(self, name: str, limit: int = 100) -> pd.DataFrame:
        return self.repository.history_for(name=name, limit=limit)
