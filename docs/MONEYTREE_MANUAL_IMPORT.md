# Sprint 5.0 Moneytree Data Model & Manual Import

## Purpose

Sprint 5.0 prepares Phoenix 140 for Moneytree integration.

It adds:
- Moneytree account table
- Moneytree transaction table
- balance snapshots
- sync log
- manual CSV import
- Moneytree dashboard

## Why manual import first?

Direct Moneytree API sync requires:
- API / Moneytree LINK developer access
- Client ID
- Client Secret
- OAuth redirect URI
- access token / refresh token handling

Before that is ready, Phoenix 140 can still prepare the data model and import flow.

## Tables

```text
moneytree_accounts
moneytree_transactions
moneytree_balance_snapshots
moneytree_sync_log
```

## Pages

```text
Moneytree Manual Import
Moneytree Dashboard
```

## CSV columns

Accounts required:
- 金融機関 / institution
- 口座名 / account_name
- 口座番号 / account_number
- 残高 / balance

Transactions required:
- 日付 / transaction_date
- 摘要 / description
- 金額 / amount

## Next Sprint

Sprint 5.1 should add:

```text
connectors/moneytree_connector.py
.env settings
API connector skeleton
sync command
mock adapter
```

Then Sprint 5.2 can implement OAuth sync once official credentials are available.
