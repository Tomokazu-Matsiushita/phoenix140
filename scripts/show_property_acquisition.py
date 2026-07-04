from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.real_estate import AcquisitionInput, PropertyAcquisitionService


def main():
    service = PropertyAcquisitionService()
    result = service.evaluate(AcquisitionInput())

    keys = [
        "property_name",
        "purchase_price",
        "loan_amount",
        "monthly_payment",
        "full_annual_rent",
        "effective_annual_rent",
        "noi",
        "annual_debt_service",
        "cash_flow_after_debt",
        "dscr",
        "gross_yield_full",
        "noi_yield",
        "break_even_occupancy",
        "health",
    ]

    for key in keys:
        print(f"{key}: {result.get(key)}")


if __name__ == "__main__":
    main()
