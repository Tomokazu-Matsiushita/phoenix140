from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.liquidity_safety_service import LiquiditySafetyInput, LiquiditySafetyService


def main():
    service = LiquiditySafetyService()
    review = service.review(LiquiditySafetyInput())

    print("Recommendation:")
    print(review["recommendation"])

    print("\nRequired buffer:", review["required_buffer"])
    print("Current months covered:", review["current_months_covered"])

    print("\nScenario Review:")
    df = review["scenario_review"]
    if df.empty:
        print("No scenarios.")
    else:
        cols = [
            "scenario",
            "status",
            "after_transaction_cash",
            "required_buffer",
            "safety_surplus",
            "months_covered_after",
            "monthly_cf_delta",
            "liquidity_score",
        ]
        print(df[[c for c in cols if c in df.columns]].to_string(index=False))


if __name__ == "__main__":
    main()
