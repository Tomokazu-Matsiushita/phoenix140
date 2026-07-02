# Database Design

## Current Stage
SQLite is used for local development. The DB file `phoenix140.db` is intentionally excluded from Git.

## Future Target
SQLite should be replaceable with PostgreSQL.

## Financial Domain
Target model:

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

## Real Estate Domain
Target model:

```text
Property
    ↓
Unit
    ↓
Tenant
    ↓
Contract
    ↓
MonthlyCashFlow
    ↓
Repair
    ↓
Loan
```

## Health Domain
Future model:

```text
HealthMetric
    ↓
Sleep
    ↓
VO2max
    ↓
Running
    ↓
Body
```
