# Sprint 2.3 Price History & Last Updated

## Purpose

Sprint 2.3 stores market price update history.

Before Sprint 2.3, market price updates overwrote `current_price`.
After Sprint 2.3, each successful update is also stored in `price_history`.

## Added Fields

`financial_assets` now includes:

- `last_price_updated_at`
- `last_price_source`
- `previous_price`
- `price_change`
- `price_change_rate`

## Added Table

```text
price_history
```

Fields:

- id
- asset_id
- name
- ticker
- price
- source
- recorded_at

## New Page

```text
Price History
```

The page shows:

- latest price by stock
- price history chart
- raw history table
- manual update button

## Why This Matters

This enables future features:

- last-updated visibility
- change from previous update
- sell trigger based on price
- historical valuation
- target cash alert
- AI CFO decision timing
