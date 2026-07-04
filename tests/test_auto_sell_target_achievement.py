import pandas as pd

from services.financial.auto_sell_plan import AutoSellPlanGenerator


def test_target_achievement_relaxes_shipping_ratio():
    assets = pd.DataFrame(
        [
            {
                "name": "日本郵船",
                "asset_type": "stock",
                "quantity": 200,
                "current_price": 5000,
                "cost_price": 5000,
                "annual_dividend": 40000,
                "policy": "調整",
                "value": 1000000,
            },
        ]
    )

    scenarios = AutoSellPlanGenerator().generate(
        assets,
        target_net_cash=900000,
        tax_rate=0.20315,
        preserve_names=[],
        preserve_core_policy=False,
        shipping_max_sell_ratio=0.5,
    )

    target = [s for s in scenarios if s.name == "目標達成優先"][0]
    assert target.result.net_proceeds >= 900000


def test_target_achievement_respects_exclusions_even_when_target_not_met():
    assets = pd.DataFrame(
        [
            {
                "name": "日本郵船",
                "asset_type": "stock",
                "quantity": 200,
                "current_price": 5000,
                "cost_price": 5000,
                "annual_dividend": 40000,
                "policy": "調整",
                "value": 1000000,
            },
        ]
    )

    scenarios = AutoSellPlanGenerator().generate(
        assets,
        target_net_cash=900000,
        tax_rate=0.20315,
        preserve_names=["日本郵船"],
        preserve_core_policy=False,
        shipping_max_sell_ratio=0.5,
    )

    target = [s for s in scenarios if s.name == "目標達成優先"][0]
    assert target.result.net_proceeds == 0
