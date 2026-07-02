# Sprint 2 – Financial Core

## Goal

Make financial assets manageable through a normalized financial domain model.

Sprint 2 is the foundation for:
- Moneytree integration
- SBI data integration
- Dividend tracking
- Price updates
- Tax-loss harvesting
- Sell simulation
- AI CFO financial analysis

## Target Domain Model

```text
Institution
    ↓
Account
    ↓
Holding
    ↓
Transaction
    ↓
Dividend
    ↓
Price
```

## Key Concepts

### Institution

The financial company or data source.

Examples:
- SBI Securities
- SMBC
- SBJ Bank
- Sony Bank
- WealthNavi
- Moneytree

### Account

A specific account under an institution.

Examples:
- SBI 特定口座
- SBI 投資信託
- 三井住友銀行 普通預金
- WealthNavi
- 確定拠出年金

### Holding

A current position.

Examples:
- 三菱商事 600株
- 三井住友FG 600株
- SBI投資信託
- WealthNavi

### Transaction

A historical movement.

Examples:
- Buy
- Sell
- Deposit
- Withdrawal
- Dividend received
- Fee

### Dividend

Dividend records should be separated from holdings.

This allows:
- Monthly dividend calendar
- Yearly dividend trend
- Dividend growth tracking
- Post-sell dividend impact analysis

### Price

Price records should be separated from holdings.

This allows:
- Daily valuation
- Performance history
- Drawdown analysis
- Sell timing review

## Sprint 2 Completion Criteria

- Financial repository layer created
- Financial service layer created
- Current financial summary still works
- Code is ready for normalized financial model migration
- App remains runnable on main
