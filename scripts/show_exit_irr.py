from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.real_estate import ExitIRRInput, ExitIRRService


def main():
    service = ExitIRRService()
    result = service.evaluate(ExitIRRInput())

    keys = [
        "property_name",
        "holding_years",
        "exit_price",
        "remaining_loan_balance",
        "sale_cash_after_debt_tax",
        "cumulative_cash_flow",
        "total_recovery",
        "total_profit",
        "equity_multiple",
        "irr",
        "health",
    ]

    for key in keys:
        print(f"{key}: {result.get(key)}")


if __name__ == "__main__":
    main()
