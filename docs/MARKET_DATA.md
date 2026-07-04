# Market Data Connector

## Purpose

Sprint 2.2 adds a market price update path for the Sell Simulator.

The current Sell Simulator originally used `current_price` stored in the local SQLite database.
Sprint 2.2 adds the ability to update those prices from Yahoo Finance through `yfinance`.

## Provider

Current provider:

```text
connectors/market_data_yahoo.py
```

## Japanese Stock Ticker Format

Japanese equities use Yahoo Finance tickers with `.T`.

Examples:

| Name | Ticker |
|---|---|
| 三菱商事 | 8058.T |
| 三井住友FG | 8316.T |
| 武田薬品 | 4502.T |
| 日本郵船 | 9101.T |
| 商船三井 | 9104.T |
| トヨタ自動車 | 7203.T |

## Usage

Command line:

```bash
python3 scripts/update_market_prices.py
```

Streamlit:

Open Sell Simulator and press:

```text
現在株価を更新
```

## Limitations

- Yahoo Finance data is best-effort.
- It may be delayed.
- It should be used for dashboard estimation, not trade execution.
- Investment trusts may not be mapped.
- If a ticker is not mapped, the provider skips it.

## Future Enhancements

- Add ticker column to normalized holdings table
- Use official market data APIs
- Store price history
- Show last updated timestamp
- Add automatic scheduled updates
