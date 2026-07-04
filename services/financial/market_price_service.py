from __future__ import annotations

import pandas as pd

from connectors.market_data_yahoo import YahooMarketDataProvider
from db.database import SessionLocal
from models.tables import FinancialAsset


class MarketPriceService:
    # Updates current prices for mapped listed stocks.

    def __init__(self, provider: YahooMarketDataProvider | None = None) -> None:
        self.provider = provider or YahooMarketDataProvider()

    def update_stock_prices(self) -> pd.DataFrame:
        results = []

        with SessionLocal() as session:
            assets = (
                session.query(FinancialAsset)
                .filter(FinancialAsset.asset_type == "stock")
                .all()
            )

            for asset in assets:
                quote = self.provider.get_latest_price(asset.name)

                if quote.price is not None:
                    old_price = asset.current_price
                    asset.current_price = quote.price
                    asset.value = quote.price * asset.quantity
                    status = "updated"
                else:
                    old_price = asset.current_price
                    status = "skipped"

                results.append(
                    {
                        "name": asset.name,
                        "ticker": quote.ticker,
                        "old_price": old_price,
                        "new_price": quote.price,
                        "quantity": asset.quantity,
                        "status": status,
                        "error": quote.error,
                    }
                )

            session.commit()

        return pd.DataFrame(results)
