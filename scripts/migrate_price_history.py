from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from db.database import Base, SessionLocal
from models.tables import PriceHistory  # noqa: F401


def get_engine():
    with SessionLocal() as session:
        return session.get_bind()


def add_column_if_missing(conn, table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(conn)
    columns = {col["name"] for col in inspector.get_columns(table_name)}

    if column_name not in columns:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))
        print(f"Added column: {table_name}.{column_name}")
    else:
        print(f"Column already exists: {table_name}.{column_name}")


def main() -> None:
    engine = get_engine()

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        add_column_if_missing(conn, "financial_assets", "last_price_updated_at", "last_price_updated_at DATETIME")
        add_column_if_missing(conn, "financial_assets", "last_price_source", "last_price_source VARCHAR")
        add_column_if_missing(conn, "financial_assets", "previous_price", "previous_price FLOAT")
        add_column_if_missing(conn, "financial_assets", "price_change", "price_change FLOAT")
        add_column_if_missing(conn, "financial_assets", "price_change_rate", "price_change_rate FLOAT")

    print("Price history migration completed.")


if __name__ == "__main__":
    main()
