from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from db.database import SessionLocal


def get_engine():
    with SessionLocal() as session:
        return session.get_bind()


def table_exists(conn, table_name: str) -> bool:
    return table_name in inspect(conn).get_table_names()


def add_column_if_missing(conn, table_name: str, column_name: str, ddl: str) -> None:
    columns = {col["name"] for col in inspect(conn).get_columns(table_name)}
    if column_name not in columns:
        conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN {ddl}'))
        print(f"Added column: {table_name}.{column_name}")
    else:
        print(f"Column already exists: {table_name}.{column_name}")


def ensure_monthly_property_cf(conn) -> None:
    if not table_exists(conn, "monthly_property_cf"):
        conn.execute(
            text(
                '''
                CREATE TABLE monthly_property_cf (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id INTEGER,
                    year_month VARCHAR,
                    rent_income FLOAT,
                    loan_payment FLOAT,
                    management_fee FLOAT,
                    cleaning_fee FLOAT,
                    fixed_asset_tax FLOAT,
                    insurance FLOAT,
                    repair FLOAT,
                    other_expense FLOAT,
                    net_cf FLOAT,
                    memo TEXT
                )
                '''
            )
        )
        print("Created table: monthly_property_cf")


def update_known_property_data(conn) -> None:
    conn.execute(
        text(
            '''
            UPDATE properties
            SET
                purchase_price = COALESCE(purchase_price, 66000000),
                loan_balance = COALESCE(loan_balance, 40000000),
                interest_rate = COALESCE(interest_rate, 2),
                loan_years = COALESCE(loan_years, 25),
                monthly_payment = COALESCE(monthly_payment, 183333),
                units = COALESCE(units, 8),
                current_annual_income = 4498800,
                full_annual_income = 5122800,
                current_monthly_income = 374900,
                full_monthly_income = 426900,
                occupied_units = 7,
                vacant_units = 1,
                fixed_asset_tax_annual = 346194,
                management_fee_monthly = 14434,
                cleaning_fee_monthly = 14080,
                data_quality_note = 'Seeded from known Alba港栄 property data. Verify against latest actuals.'
            WHERE name LIKE '%Alba%'
            '''
        )
    )

    conn.execute(
        text(
            '''
            UPDATE properties
            SET
                purchase_price = 76000000,
                loan_balance = COALESCE(loan_balance, 75000000),
                interest_rate = COALESCE(interest_rate, 3),
                loan_years = COALESCE(loan_years, 34),
                monthly_payment = COALESCE(monthly_payment, 293452),
                units = COALESCE(units, 12),
                current_annual_income = 7327440,
                current_monthly_income = 610620,
                occupied_units = 11,
                vacant_units = 1,
                fixed_asset_tax_annual = 618429,
                management_fee_monthly = 59300,
                data_quality_note = 'Seeded from known oblige新田町 business plan. Full occupancy income should be verified.'
            WHERE name LIKE '%oblige%' OR name LIKE '%新田町%'
            '''
        )
    )


def main() -> None:
    engine = get_engine()

    with engine.begin() as conn:
        if not table_exists(conn, "properties"):
            raise RuntimeError("properties table not found. Please create properties first.")

        ensure_monthly_property_cf(conn)

        property_columns = [
            ("current_annual_income", "current_annual_income FLOAT"),
            ("full_annual_income", "full_annual_income FLOAT"),
            ("current_monthly_income", "current_monthly_income FLOAT"),
            ("full_monthly_income", "full_monthly_income FLOAT"),
            ("occupied_units", "occupied_units INTEGER"),
            ("vacant_units", "vacant_units INTEGER"),
            ("fixed_asset_tax_annual", "fixed_asset_tax_annual FLOAT"),
            ("management_fee_monthly", "management_fee_monthly FLOAT"),
            ("cleaning_fee_monthly", "cleaning_fee_monthly FLOAT"),
            ("insurance_annual", "insurance_annual FLOAT"),
            ("data_quality_note", "data_quality_note TEXT"),
        ]

        for column_name, ddl in property_columns:
            add_column_if_missing(conn, "properties", column_name, ddl)

        if table_exists(conn, "rental_units"):
            for column_name, ddl in [("rent", "rent FLOAT"), ("status", "status VARCHAR"), ("memo", "memo TEXT")]:
                add_column_if_missing(conn, "rental_units", column_name, ddl)

        monthly_columns = [
            ("property_id", "property_id INTEGER"),
            ("year_month", "year_month VARCHAR"),
            ("rent_income", "rent_income FLOAT"),
            ("loan_payment", "loan_payment FLOAT"),
            ("management_fee", "management_fee FLOAT"),
            ("cleaning_fee", "cleaning_fee FLOAT"),
            ("fixed_asset_tax", "fixed_asset_tax FLOAT"),
            ("insurance", "insurance FLOAT"),
            ("repair", "repair FLOAT"),
            ("other_expense", "other_expense FLOAT"),
            ("net_cf", "net_cf FLOAT"),
            ("memo", "memo TEXT"),
        ]

        for column_name, ddl in monthly_columns:
            add_column_if_missing(conn, "monthly_property_cf", column_name, ddl)

        update_known_property_data(conn)

    print("Real estate model migration completed.")


if __name__ == "__main__":
    main()
