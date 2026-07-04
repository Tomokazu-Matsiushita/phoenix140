from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


JAPAN_TICKER_MAP = {
    "三菱商事": "8058.T",
    "三井住友FG": "8316.T",
    "武田薬品": "4502.T",
    "日本郵船": "9101.T",
    "商船三井": "9104.T",
    "電源開発": "9513.T",
    "小松製作所": "6301.T",
    "大紀アルミ": "5702.T",
    "セルソース": "4880.T",
    "あおぞら銀行": "8304.T",
    "トヨタ自動車": "7203.T",
    "明和産業": "8103.T",
    "JT": "2914.T",
    "JPMC": "3276.T",
}


@dataclass
class MarketPrice:
    name: str
    ticker: str
    price: Optional[float]
    source: str
    error: str = ""


class YahooMarketDataProvider:
    # Yahoo Finance based market data provider through yfinance.

    def __init__(self, ticker_map: dict[str, str] | None = None) -> None:
        self.ticker_map = ticker_map or JAPAN_TICKER_MAP

    def ticker_for(self, name: str) -> str | None:
        return self.ticker_map.get(name)

    def get_latest_price(self, name: str) -> MarketPrice:
        ticker = self.ticker_for(name)
        if not ticker:
            return MarketPrice(name=name, ticker="", price=None, source="Yahoo Finance", error="ticker not mapped")

        if yf is None:
            return MarketPrice(name=name, ticker=ticker, price=None, source="Yahoo Finance", error="yfinance not installed")

        try:
            t = yf.Ticker(ticker)
            price = None

            try:
                fast = t.fast_info
                price = getattr(fast, "last_price", None)
                if price is None and isinstance(fast, dict):
                    price = fast.get("last_price")
            except Exception:
                price = None

            if price is None:
                hist = t.history(period="5d")
                if not hist.empty:
                    price = float(hist["Close"].dropna().iloc[-1])

            if price is None:
                return MarketPrice(name=name, ticker=ticker, price=None, source="Yahoo Finance", error="price not found")

            return MarketPrice(name=name, ticker=ticker, price=float(price), source="Yahoo Finance")

        except Exception as e:
            return MarketPrice(name=name, ticker=ticker, price=None, source="Yahoo Finance", error=str(e))
