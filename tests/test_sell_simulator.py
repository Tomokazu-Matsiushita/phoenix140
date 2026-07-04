import pandas as pd

from services.financial import SellSimulator


def test_sell_simulator_offsets_loss():
    assets = pd.DataFrame(
        [
            {
                "name": "GainStock",
                "quantity": 100,
                "current_price": 2000,
                "cost_price": 1000,
                "annual_dividend": 10000,
                "policy": "調整",
                "value": 200000,
            },
            {
                "name": "LossStock",
                "quantity": 100,
                "current_price": 500,
                "cost_price": 1000,
                "annual_dividend": 0,
                "policy": "損益通算候補",
                "value": 50000,
            },
        ]
    )

    result = SellSimulator().simulate(
        assets,
        [
            {"name": "GainStock", "sell_quantity": 100},
            {"name": "LossStock", "sell_quantity": 100},
        ],
        tax_rate=0.2,
        target_net_cash=0,
    )

    assert result.realized_gain_loss == 50000
    assert result.tax == 10000
    assert result.net_proceeds == 240000
