from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.moneytree import MoneytreeDataService


def main():
    parser = argparse.ArgumentParser(description="Import Moneytree CSV into Phoenix 140.")
    parser.add_argument("--type", choices=["accounts", "transactions"], required=True)
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    service = MoneytreeDataService()

    if args.type == "accounts":
        result = service.import_accounts_csv(args.file)
    else:
        result = service.import_transactions_csv(args.file)

    print(result)


if __name__ == "__main__":
    main()
