# Sprint 3.2 Loan & DSCR Deep Dive

## Purpose

Sprint 3.2 adds loan and DSCR stress testing.

The goal is to understand how the real estate portfolio behaves under:
- higher interest rates
- changed loan terms
- additional vacancies
- portfolio-level interest stress

## New Page

```text
Loan & DSCR Simulator
```

## Key Metrics

- monthly payment
- annual debt service
- adjusted NOI
- adjusted cash flow after debt
- adjusted DSCR
- portfolio DSCR

## Current Assumptions

- Loan payment is calculated by standard amortization formula.
- Additional vacancy reduces current rent by average occupied rent.
- Operating expenses are held constant.
- Taxes and insurance are annualized from property metrics.
- This is a planning simulator, not a bank calculation engine.

## Future Enhancements

- refinance simulator
- principal repayment schedule
- balloon payment
- variable/fixed rate separation
- property acquisition funding plan
- AI CFO real estate commentary
