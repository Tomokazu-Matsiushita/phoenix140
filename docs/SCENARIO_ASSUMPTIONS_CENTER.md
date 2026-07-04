# Sprint 4.5 Scenario Assumptions Center

## Purpose

Sprint 4.5 centralizes decision parameters.

Before this sprint, each decision page had its own sidebar values.
That made it hard to know which assumptions were being used.

## New Page

```text
Scenario Assumptions Center
```

## Shared Config

```text
config/scenario_assumptions.json
```

## Covered Assumptions

- memo information
- safety buffer
- sale conditions
- acquisition conditions
- exit / IRR conditions

## Pages Updated

The following pages now read the saved assumptions as initial values:

- Integrated AI CFO
- Investment Memo Export
- PDF Investment Memo Export

Each page can still temporarily modify values in its own sidebar.
If the user wants the changed values to become shared defaults, press:

```text
このページの条件をCenterに保存
```

## Design Rule

Scenario Assumptions Center is the source of truth for final decision/export pages.

## Future Enhancements

- connect Capital Allocation and Liquidity pages to the same center
- save multiple named scenarios
- scenario history and comparison
- import/export assumptions JSON
