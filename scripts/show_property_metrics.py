from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.real_estate import PropertyMetricsService


def main():
    df = PropertyMetricsService().property_metrics()
    if df.empty:
        print("No property metrics.")
    else:
        cols = [
            "name",
            "annual_income",
            "operating_expense",
            "noi",
            "annual_debt_service",
            "cash_flow_after_debt",
            "dscr",
            "gross_yield",
            "ltv",
            "occupancy_rate",
            "health",
        ]
        print(df[[c for c in cols if c in df.columns]].to_string(index=False))


if __name__ == "__main__":
    main()
