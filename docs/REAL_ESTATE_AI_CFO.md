# Sprint 3.5 Real Estate AI CFO Commentary

## Purpose

Sprint 3.5 adds rule-based Real Estate AI CFO commentary.

It reviews:
- real estate portfolio
- individual properties
- acquisition scenario
- exit / IRR scenario

## New Page

```text
Real Estate AI CFO
```

## Current Design

This version is rule-based and does not call external AI APIs.

It converts existing real estate metrics into:
- executive summary
- strengths
- risks
- priority actions
- status
- score

## Status Logic

The service looks at:
- DSCR
- cash flow after debt
- occupancy rate
- break-even occupancy
- acquisition DSCR
- exit IRR
- sale cash after debt and tax
- total profit

## Future Enhancements

- connect to OpenAI API
- generate monthly real estate CFO report
- compare stock sale plan and property acquisition plan
- recommend buy / hold / sell
- integrate tax and depreciation model
