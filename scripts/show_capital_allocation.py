from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.capital_allocation_service import CapitalAllocationInput, CapitalAllocationService
from services.real_estate import AcquisitionInput


def main():
    service = CapitalAllocationService()
    review = service.review(
        CapitalAllocationInput(
            target_net_cash=3_500_000,
            acquisition_input=AcquisitionInput(),
        )
    )

    print("Recommendation:")
    print(review["recommendation"])

    print("\nAcquisition:")
    print(
        {
            "initial_cash_required": review["acquisition"].get("initial_cash_required"),
            "cash_flow_after_debt": review["acquisition"].get("cash_flow_after_debt"),
            "dscr": review["acquisition"].get("dscr"),
            "health": review["acquisition"].get("health"),
        }
    )

    print("\nComparison:")
    df = review["comparison"]
    if df.empty:
        print("No comparison rows.")
    else:
        cols = [
            "scenario",
            "net_proceeds",
            "dividend_loss",
            "initial_cash_required",
            "funding_gap",
            "annual_property_cf",
            "annual_cf_delta",
            "score",
        ]
        print(df[[c for c in cols if c in df.columns]].to_string(index=False))


if __name__ == "__main__":
    main()
