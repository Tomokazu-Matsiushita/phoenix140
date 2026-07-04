from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.scenario_assumptions_service import ScenarioAssumptionsService


def main():
    service = ScenarioAssumptionsService()
    assumptions = service.load()
    integrated = service.to_integrated_input(assumptions)

    print("Scenario Assumptions:")
    print(json.dumps(assumptions, ensure_ascii=False, indent=2))

    print("\nIntegrated input check:")
    print({
        "current_cash": integrated.current_cash,
        "target_net_cash": integrated.target_net_cash,
        "property_name": integrated.acquisition_input.property_name,
        "purchase_price": integrated.acquisition_input.purchase_price,
        "exit_price": integrated.exit_input.exit_price,
    })


if __name__ == "__main__":
    main()
