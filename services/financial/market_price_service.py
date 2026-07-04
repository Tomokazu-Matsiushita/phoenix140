from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from connectors.market_data_yahoo import YahooMarketDataProvider
from db.database import SessionLocal
from models.tables import FinancialAsset, PriceHistory


class MarketPriceService:
    # Updates current prices and stores price history.

    def __init__(self, provider: YahooMarketDataProvider | None = None) -> None:
        self.provider = provider or YahooMarketDataProvider()

    def update_stock_prices(self) -> pd.DataFrame:
        results = []
        recorded_at = datetime.now(timezone.utc).replace(tzinfo=None)

        with SessionLocal() as session:
            assets = (
                session.query(FinancialAsset)
                .filter(FinancialAsset.asset_type == "stock")
                .all()
            )

            for asset in assets:
                quote = self.provider.get_latest_price(asset.name)
                old_price = asset.current_price

                if quote.price is not None:
                    old_price_value = float(old_price or 0)
                    new_price = float(quote.price)
                    price_change = new_price - old_price_value if old_price is not None else None
                    price_change_rate = (
                        price_change / old_price_value * 100
                        if old_price_value and price_change is not None
                        else None
                    )

                    asset.previous_price = old_price
                    asset.current_price = new_price
                    asset.value = new_price * asset.quantity
                    asset.last_price_updated_at = recorded_at
                    asset.last_price_source = quote.source
                    asset.price_change = price_change
                    asset.price_change_rate = price_change_rate

                    session.add(
                        PriceHistory(
                            asset_id=asset.id,
                            name=asset.name,
                            ticker=quote.ticker,
                            price=new_price,
                            source=quote.source,
                            recorded_at=recorded_at,
                        )
                    )

                    status = "updated"
                else:
                    new_price = None
                    price_change = None
                    price_change_rate = None
                    status = "skipped"

                results.append(
                    {
                        "name": asset.name,
                        "ticker": quote.ticker,
                        "old_price": old_price,
                        "new_price": new_price,
                        "price_change": price_change,
                        "price_change_rate": price_change_rate,
                        "quantity": asset.quantity,
                        "status": status,
                        "recorded_at": recorded_at,
                        "error": quote.error,
                    }
                )

            session.commit()

        return pd.DataFrame(results)
