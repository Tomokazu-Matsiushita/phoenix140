from __future__ import annotations

import pandas as pd
from sqlalchemy import inspect, text

from db.database import SessionLocal


class RealEstateRepository:
    """Read-only repository for real estate tables."""

    TABLE_CANDIDATES = {
        "properties": ["properties", "real_estate_properties", "property"],
        "units": ["units", "rental_units", "property_units"],
        "monthly_cashflows": ["monthly_property_cf", "monthly_cashflows", "monthly_cash_flows", "cashflows", "cash_flows"],
        "loans": ["loans", "property_loans", "real_estate_loans"],
        "repairs": ["repairs", "property_repairs", "maintenance"],
    }

    def _engine(self):
        with SessionLocal() as session:
            return session.get_bind()

    def available_tables(self) -> list[str]:
        engine = self._engine()
        inspector = inspect(engine)
        return inspector.get_table_names()

    def first_existing_table(self, logical_name: str) -> str | None:
        tables = set(self.available_tables())
        for candidate in self.TABLE_CANDIDATES.get(logical_name, []):
            if candidate in tables:
                return candidate
        return None

    def read_table(self, table_name: str | None) -> pd.DataFrame:
        if not table_name:
            return pd.DataFrame()

        engine = self._engine()
        available = set(self.available_tables())
        if table_name not in available:
            return pd.DataFrame()

        with engine.connect() as conn:
            return pd.read_sql_query(text(f'SELECT * FROM "{table_name}"'), conn)

    def properties(self) -> pd.DataFrame:
        return self.read_table(self.first_existing_table("properties"))

    def units(self) -> pd.DataFrame:
        return self.read_table(self.first_existing_table("units"))

    def monthly_cashflows(self) -> pd.DataFrame:
        return self.read_table(self.first_existing_table("monthly_cashflows"))

    def loans(self) -> pd.DataFrame:
        return self.read_table(self.first_existing_table("loans"))

    def repairs(self) -> pd.DataFrame:
        return self.read_table(self.first_existing_table("repairs"))
