#!/bin/bash
set -e

echo "Running Phoenix 140 development check..."

if [ -f scripts/migrate_price_history.py ]; then
  python3 scripts/migrate_price_history.py
fi

python3 -m compileall app.py pages services repositories models db connectors utils ai

echo "Compile check passed."

python3 - << 'PY'
from services.financial import (
    FinancialService,
    SellSimulator,
    MarketPriceService,
    PriceHistoryService,
    AutoSellPlanGenerator,
    AICFOCommentaryService,
)

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

review = AICFOCommentaryService().build_review(scenarios, target_net_cash=3500000)
print("AI CFO recommendation:", review["recommended_name"])
PY

echo "Service check passed."

exit_result = ExitIRRService().evaluate(ExitIRRInput())
print("Exit IRR sample:", exit_result["irr"])

real_estate_ai_review = RealEstateAICFOService().full_review()
print("Real Estate AI CFO comments:", len(real_estate_ai_review["comments"]))

from services.capital_allocation_service import CapitalAllocationInput, CapitalAllocationService
capital_review = CapitalAllocationService().review(CapitalAllocationInput(target_net_cash=100000))
print("Capital allocation rows:", len(capital_review["comparison"]))

from services.liquidity_safety_service import LiquiditySafetyInput, LiquiditySafetyService
liquidity_review = LiquiditySafetyService().review(LiquiditySafetyInput())
print("Liquidity scenarios:", len(liquidity_review["scenario_review"]))

from services.integrated_ai_cfo_service import IntegratedAICFOService, IntegratedCFOInput
integrated_review = IntegratedAICFOService().review(IntegratedCFOInput())
print("Integrated AI CFO decision:", integrated_review["decision"]["label"])

from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService
memo = InvestmentMemoService().build(InvestmentMemoInput())
print("Investment memo chars:", len(memo["markdown"]))

from services.investment_memo_pdf_service import InvestmentMemoPDFService
from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService
pdf_memo = InvestmentMemoService().build(InvestmentMemoInput())
pdf_bytes = InvestmentMemoPDFService().build_pdf_bytes(pdf_memo)
print("PDF memo bytes:", len(pdf_bytes))
