# Sprint 2.4 Auto Sell Plan Generator

## Purpose

Sprint 2.4 adds a rule-based sell plan generator.

The goal is to support decisions such as:

```text
Target after-tax cash: 3.5M JPY
Protect core holdings
Use tax-loss harvesting candidates
Minimize dividend loss
Preserve part of shipping exposure
```

## Scenarios

The generator creates three scenarios:

### Tax Efficient

Prioritizes:
- loss positions
- lower taxable gain
- non-core policy

### Dividend Preservation

Prioritizes:
- low annual dividend loss
- cash creation with less income damage

### Balanced

Prioritizes:
- policy
- dividend loss
- tax efficiency

## Inputs

- target net cash
- tax rate
- preserve names
- preserve core policy
- shipping max sell ratio

## Current Limitations

- Rule-based, not AI-generated yet
- Uses current DB prices
- Transaction fees ignored
- NISA classification ignored
- Tax loss carryforward ignored
- Dividend record date ignored

## Future

This is the base for Phoenix AI CFO.

Future enhancements:

- AI explanation
- Scenario comparison ranking
- Cash buffer integration
- Real estate acquisition funding plan
- Tax-year planning
