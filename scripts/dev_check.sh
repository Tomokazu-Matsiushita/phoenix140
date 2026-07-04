#!/bin/bash
set -e

echo "Running Phoenix 140 development check..."

python3 -m compileall app.py pages services repositories models db connectors utils ai

echo "Compile check passed."

python3 - << 'PY'
from services.financial import FinancialService, SellSimulator

service = FinancialService()
summary = service.financial_summary()
print("Financial summary:", summary)

assets = service.repository.list_assets()
result = SellSimulator().simulate(
    assets=assets,
    sale_plan=[],
)
print("Sell simulator empty result:", result.net_proceeds)
PY

echo "Service check passed."
