from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.real_estate import LoanDSCRService, PropertyMetricsService


def main():
    metrics = PropertyMetricsService().property_metrics()
    service = LoanDSCRService()

    if metrics.empty:
        print("No property metrics.")
        return

    for name in metrics["name"].dropna().astype(str).tolist():
        df = service.rate_sensitivity(name)
        print(f"\n=== {name} ===")
        print(df[["interest_rate", "monthly_payment", "adjusted_dscr", "adjusted_cash_flow_after_debt"]].to_string(index=False))


if __name__ == "__main__":
    main()
