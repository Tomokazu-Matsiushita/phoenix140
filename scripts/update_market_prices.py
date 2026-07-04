from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.financial.market_price_service import MarketPriceService


def main():
    result = MarketPriceService().update_stock_prices()
    if result.empty:
        print("No stock prices updated.")
    else:
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
