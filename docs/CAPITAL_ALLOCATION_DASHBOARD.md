# Sprint 4.0 Integrated Capital Allocation Dashboard

## Purpose

Sprint 4.0 connects the financial CFO layer and the real estate CFO layer.

It answers the core question:

```text
Should we sell stocks to fund a property acquisition?
```

## New Page

```text
Integrated Capital Allocation Dashboard
```

## It Compares

- stock sale scenarios
- after-tax net proceeds
- tax impact
- annual dividend loss
- property acquisition initial cash required
- property DSCR
- property cash flow after debt
- annual cash flow delta
- funding gap / surplus

## Key Metric

```text
Annual CF Delta = Property CF after debt - Stock dividend loss
```

If this is positive, the acquisition improves annual cash flow after replacing dividends with property cash flow.

## Current Design

This version is rule-based.

It uses:
- AutoSellPlanGenerator
- PropertyAcquisitionService
- FinancialService asset data

## Future Enhancements

- include current bank cash and emergency buffer
- include Moneytree balances
- compare multiple acquisition candidates
- tax loss harvesting optimization
- liquidity stress check
- AI CFO integrated recommendation
