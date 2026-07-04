from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.integrated_ai_cfo_service import IntegratedAICFOService, IntegratedCFOInput


def main():
    service = IntegratedAICFOService()
    review = service.review(IntegratedCFOInput())

    print("Decision:")
    print(review["decision"])
    print("\nExecutive Summary:")
    print(review["executive_summary"])
    print("\nMust Check:")
    for item in review["must_check"]:
        print("-", item)

    best = review["best_scenario"]
    print("\nBest Scenario:")
    print(
        {
            "scenario": best.get("scenario"),
            "status": best.get("status"),
            "after_transaction_cash": best.get("after_transaction_cash"),
            "safety_surplus": best.get("safety_surplus"),
            "annual_cf_delta": best.get("annual_cf_delta"),
        }
    )


if __name__ == "__main__":
    main()
