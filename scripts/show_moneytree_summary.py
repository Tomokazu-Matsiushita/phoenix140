from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.moneytree import MoneytreeDataService


def main():
    service = MoneytreeDataService()
    service.migrate()
    summary = service.portfolio_summary()

    print("Moneytree summary:")
    print("total_balance:", summary["total_balance"])
    print("account_count:", summary["account_count"])
    print("transaction_count:", summary["transaction_count"])

    print("\nBy institution:")
    print(summary["by_institution"].to_string(index=False) if not summary["by_institution"].empty else "No data")

    print("\nSpending by category:")
    print(summary["spending_by_category"].head(10).to_string(index=False) if not summary["spending_by_category"].empty else "No data")


if __name__ == "__main__":
    main()
