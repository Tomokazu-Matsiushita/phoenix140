import pandas as pd

from services.financial.auto_sell_plan import AutoSellPlanGenerator
from services.financial.ai_cfo_commentary import AICFOCommentaryService


def test_ai_cfo_commentary_builds_review():
    assets = pd.DataFrame(
        [
            {
                "name": "LossStock",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 1000,
                "cost_price": 2000,
                "annual_dividend": 0,
                "policy": "損益通算候補",
                "value": 100000,
            },
            {
                "name": "TrimStock",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 5000,
                "cost_price": 1000,
                "annual_dividend": 10000,
                "policy": "整理候補",
                "value": 500000,
            },
        ]
    )

    scenarios = AutoSellPlanGenerator().generate(
        assets=assets,
        target_net_cash=100000,
        tax_rate=0.20315,
        preserve_names=[],
        preserve_core_policy=False,
    )

    review = AICFOCommentaryService().build_review(scenarios, target_net_cash=100000)

    assert review["recommended_name"]
    assert "scenario_comments" in review
    assert len(review["scenario_comments"]) > 0
