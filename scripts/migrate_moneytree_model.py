from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from db.database import SessionLocal


ACCOUNT_SQL = """
CREATE TABLE IF NOT EXISTS moneytree_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT,
    account_name TEXT,
    account_number TEXT,
    account_type TEXT,
    currency TEXT DEFAULT 'JPY',
    balance REAL DEFAULT 0,
    balance_date TEXT,
    source TEXT DEFAULT 'manual_csv',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution, account_name, account_number)
);
"""

TRANSACTION_SQL = """
CREATE TABLE IF NOT EXISTS moneytree_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    institution TEXT,
    account_name TEXT,
    account_number TEXT,
    transaction_date TEXT,
    description TEXT,
    category TEXT,
    subcategory TEXT,
    amount REAL DEFAULT 0,
    transaction_type TEXT,
    currency TEXT DEFAULT 'JPY',
    memo TEXT,
    source TEXT DEFAULT 'manual_csv',
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(transaction_id)
);
"""

BALANCE_SNAPSHOT_SQL = """
CREATE TABLE IF NOT EXISTS moneytree_balance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT,
    account_name TEXT,
    account_number TEXT,
    balance REAL DEFAULT 0,
    currency TEXT DEFAULT 'JPY',
    snapshot_date TEXT,
    source TEXT DEFAULT 'manual_csv',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

SYNC_LOG_SQL = """
CREATE TABLE IF NOT EXISTS moneytree_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT,
    status TEXT,
    message TEXT,
    records_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def main():
    with SessionLocal() as session:
        engine = session.get_bind()

        with engine.begin() as conn:
            conn.execute(text(ACCOUNT_SQL))
            conn.execute(text(TRANSACTION_SQL))
            conn.execute(text(BALANCE_SNAPSHOT_SQL))
            conn.execute(text(SYNC_LOG_SQL))

            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_moneytree_accounts_number ON moneytree_accounts(account_number);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_moneytree_accounts_institution ON moneytree_accounts(institution);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_moneytree_transactions_date ON moneytree_transactions(transaction_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_moneytree_transactions_account ON moneytree_transactions(account_number);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_moneytree_transactions_category ON moneytree_transactions(category);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_moneytree_balance_snapshots_date ON moneytree_balance_snapshots(snapshot_date);"))

    print("Moneytree tables migrated.")


if __name__ == "__main__":
    main()
