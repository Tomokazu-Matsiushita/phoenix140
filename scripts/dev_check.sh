#!/bin/bash
set -e

echo "Running Phoenix 140 development check..."

if [ -f scripts/migrate_price_history.py ]; then
  python3 scripts/migrate_price_history.py
fi

python3 -m compileall app.py pages services repositories models db connectors utils ai

echo "Compile check passed."

python3 - << 'PY'
from services.financial import FinancialService, SellSimulator, MarketPriceService, PriceHistoryService, AutoSellPlanGenerator

service = FinancialService()
summary = service.financial_summary()
print("Financial summary:", summary)

assets = service.repository.list_assets()
result = SellSimulator().simulate(
    assets=assets,
    sale_plan=[],
)
print("Sell simulator empty result:", result.net_proceeds)

market_service = MarketPriceService()
print("Market price service ready:", type(market_service).__name__)

history_service = PriceHistoryService()
history = history_service.latest_history(limit=5)
print("Price history rows:", len(history))

scenarios = AutoSellPlanGenerator().generate(assets=assets, target_net_cash=3500000)
print("Auto sell scenarios:", len(scenarios))
PY

echo "Service check passed."
