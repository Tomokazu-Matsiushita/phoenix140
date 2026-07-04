# Sprint 4.1 Liquidity & Safety Buffer Check

## Purpose

Sprint 4.1 adds a liquidity safety layer to capital allocation.

It checks whether enough cash remains after:
- selling stocks
- paying tax
- funding a property acquisition
- losing stock dividends
- gaining property cash flow

## New Page

```text
Liquidity & Safety Buffer Check
```

## Key Inputs

- current cash / bank balance
- monthly living expense
- emergency months
- property repair reserve
- tax reserve
- other planned commitments
- minimum cash floor
- stock sale conditions
- property acquisition conditions

## Key Outputs

- required safety buffer
- after-transaction cash
- safety surplus / deficit
- months of living expenses covered
- monthly cash flow delta
- liquidity score
- CFO safety recommendation

## Current Design

This service sits on top of Sprint 4.0.

It uses:
- CapitalAllocationService
- AutoSellPlanGenerator
- PropertyAcquisitionService

## Future Enhancements

- connect actual Moneytree cash balances
- credit card payment forecast
- tax calendar
- repair reserve per property
- monthly cash runway chart
- integrated AI CFO recommendation
