from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.financial.price_history_service import PriceHistoryService


def main():
    df = PriceHistoryService().latest_history(limit=100)
    if df.empty:
        print("No price history yet.")
    else:
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
