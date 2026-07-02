# API Connectors

## Connector Philosophy
External data sources must be isolated from the core app.

All external APIs should be implemented under `connectors/`.

## Financial Providers
Target structure:

```text
FinancialProvider
    ├── ManualProvider
    ├── MoneytreeProvider
    ├── SBIProvider
    ├── CSVProvider
    └── MarketDataProvider
```

## Moneytree
Moneytree should eventually provide bank balances, securities balances, credit card liabilities, and account-level financial data.

Credentials should be stored in `.env`. Never commit `.env` to GitHub.

## Health Providers
Future structure:

```text
HealthProvider
    ├── OuraProvider
    ├── GarminProvider
    └── AppleHealthProvider
```
