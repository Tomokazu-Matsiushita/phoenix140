import pandas as pd

from services.financial.auto_sell_plan import AutoSellPlanGenerator


def test_added_exclusion_is_respected():
    assets = pd.DataFrame(
        [
            {
                "name": "A",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 5000,
                "cost_price": 1000,
                "annual_dividend": 0,
                "policy": "整理候補",
                "value": 500000,
            },
            {
                "name": "B",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 5000,
                "cost_price": 1000,
                "annual_dividend": 0,
                "policy": "整理候補",
                "value": 500000,
            },
        ]
    )

    scenarios = AutoSellPlanGenerator().generate(
        assets,
        target_net_cash=100000,
        preserve_names=["A"],
        preserve_core_policy=False,
    )

    assert scenarios
    for scenario in scenarios:
        sold_names = {p["name"] for p in scenario.plan}
        assert "A" not in sold_names


def test_empty_preserve_list_means_exclude_nothing():
    assets = pd.DataFrame(
        [
            {
                "name": "三菱商事",
                "asset_type": "stock",
                "quantity": 100,
                "current_price": 5000,
                "cost_price": 1000,
                "annual_dividend": 0,
                "policy": "整理候補",
                "value": 500000,
            },
        ]
    )

    scenarios = AutoSellPlanGenerator().generate(
        assets,
        target_net_cash=100000,
        preserve_names=[],
        preserve_core_policy=False,
    )

    assert scenarios
    assert any("三菱商事" in {p["name"] for p in scenario.plan} for scenario in scenarios)
