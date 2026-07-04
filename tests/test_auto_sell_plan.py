import pandas as pd

from services.financial.auto_sell_plan import AutoSellPlanGenerator


def test_auto_sell_plan_generates_scenarios():
    assets = pd.DataFrame(
        [
            {
                "name": "CoreStock",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 10000,
                "cost_price": 1000,
                "annual_dividend": 10000,
                "policy": "コア",
                "value": 1000000,
            },
            {
                "name": "LossStock",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 500,
                "cost_price": 1000,
                "annual_dividend": 0,
                "policy": "損益通算候補",
                "value": 50000,
            },
            {
                "name": "TrimStock",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 2000,
                "cost_price": 1000,
                "annual_dividend": 5000,
                "policy": "整理候補",
                "value": 200000,
            },
        ]
    )

    scenarios = AutoSellPlanGenerator().generate(
        assets,
        target_net_cash=100000,
        tax_rate=0.2,
        preserve_names=["CoreStock"],
    )

    assert len(scenarios) == 3
    assert all(s.result.net_proceeds > 0 for s in scenarios)
    assert all("CoreStock" not in [p["name"] for p in s.plan] for s in scenarios)
