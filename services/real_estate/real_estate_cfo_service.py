from __future__ import annotations

from typing import Any

import pandas as pd

from repositories.real_estate_repository import RealEstateRepository


class RealEstateCFOService:
    """Real estate cash flow analysis service."""

    def __init__(self, repository: RealEstateRepository | None = None) -> None:
        self.repository = repository or RealEstateRepository()

    def snapshot(self) -> dict[str, Any]:
        properties = self.repository.properties()
        units = self.repository.units()
        monthly_cf = self.repository.monthly_cashflows()
        loans = self.repository.loans()
        repairs = self.repository.repairs()

        summary = self._summary(properties, units, monthly_cf, loans, repairs)

        return {
            "summary": summary,
            "properties": properties,
            "units": units,
            "monthly_cashflows": monthly_cf,
            "loans": loans,
            "repairs": repairs,
            "available_tables": self.repository.available_tables(),
        }

    def _summary(
        self,
        properties: pd.DataFrame,
        units: pd.DataFrame,
        monthly_cf: pd.DataFrame,
        loans: pd.DataFrame,
        repairs: pd.DataFrame,
    ) -> dict[str, float | int | None]:
        property_count = len(properties) if not properties.empty else 0

        total_units = self._unit_count(properties, units)
        occupied_units = self._occupied_count(units)
        vacancy_count = max(total_units - occupied_units, 0) if total_units is not None else 0
        occupancy_rate = occupied_units / total_units if total_units else None

        monthly_rent = self._monthly_rent(properties, units, monthly_cf)
        annual_rent = monthly_rent * 12 if monthly_rent is not None else self._annual_rent_from_properties(properties)

        annual_debt_service = self._annual_debt_service(properties, loans, monthly_cf)
        annual_expense = self._annual_expense(properties, monthly_cf, repairs)

        noi = annual_rent - (annual_expense or 0) if annual_rent is not None else None
        cash_flow_after_debt = noi - (annual_debt_service or 0) if noi is not None else None
        dscr = noi / annual_debt_service if noi is not None and annual_debt_service else None

        return {
            "property_count": int(property_count),
            "total_units": int(total_units or 0),
            "occupied_units": int(occupied_units or 0),
            "vacancy_count": int(vacancy_count or 0),
            "occupancy_rate": occupancy_rate,
            "monthly_rent": monthly_rent,
            "annual_rent": annual_rent,
            "annual_expense": annual_expense,
            "noi": noi,
            "annual_debt_service": annual_debt_service,
            "cash_flow_after_debt": cash_flow_after_debt,
            "dscr": dscr,
        }

    def property_summary(self) -> pd.DataFrame:
        properties = self.repository.properties()
        units = self.repository.units()

        rows: list[dict[str, Any]] = []

        if not properties.empty:
            prop_name_col = self._find_col(properties, ["name", "property_name", "title", "物件名"])
            annual_income_col = self._find_col(
                properties,
                ["annual_income", "current_annual_income", "full_annual_income", "年間収入", "年収"],
            )
            price_col = self._find_col(properties, ["price", "purchase_price", "property_price", "取得価格", "価格"])

            for _, row in properties.iterrows():
                name = row.get(prop_name_col, "Property") if prop_name_col else "Property"
                annual_income = self._num(row.get(annual_income_col)) if annual_income_col else None
                price = self._num(row.get(price_col)) if price_col else None
                yield_rate = annual_income / price if annual_income and price else None
                rows.append(
                    {
                        "property": name,
                        "annual_income": annual_income,
                        "price": price,
                        "gross_yield": yield_rate,
                    }
                )

        if rows:
            return pd.DataFrame(rows)

        if not units.empty:
            name_col = self._find_col(units, ["property_name", "property", "building", "物件名"])
            rent_col = self._find_col(units, ["rent", "monthly_rent", "家賃", "賃料"])
            if name_col and rent_col:
                grouped = units.copy()
                grouped[rent_col] = pd.to_numeric(grouped[rent_col], errors="coerce").fillna(0)
                return (
                    grouped.groupby(name_col, as_index=False)[rent_col]
                    .sum()
                    .rename(columns={name_col: "property", rent_col: "monthly_rent"})
                )

        return pd.DataFrame(columns=["property", "annual_income", "price", "gross_yield"])

    def _unit_count(self, properties: pd.DataFrame, units: pd.DataFrame) -> int:
        if not units.empty:
            return len(units)

        if not properties.empty:
            col = self._find_col(properties, ["total_units", "unit_count", "rooms", "units", "戸数", "総戸数"])
            if col:
                return int(pd.to_numeric(properties[col], errors="coerce").fillna(0).sum())

        return 0

    def _occupied_count(self, units: pd.DataFrame) -> int:
        if units.empty:
            return 0

        bool_col = self._find_col(units, ["is_occupied", "occupied"])
        if bool_col:
            values = units[bool_col]
            if values.dtype == bool:
                return int(values.sum())
            return int(values.astype(str).str.lower().isin(["true", "1", "yes", "occupied", "入居", "入居中"]).sum())

        status_col = self._find_col(units, ["status", "occupancy_status", "入居状況"])
        if status_col:
            s = units[status_col].astype(str)
            vacant = s.str.contains("vacant|空室|empty", case=False, regex=True, na=False)
            return int((~vacant).sum())

        tenant_col = self._find_col(units, ["tenant", "tenant_name", "入居者"])
        if tenant_col:
            return int(units[tenant_col].notna().sum())

        return len(units)

    def _monthly_rent(
        self,
        properties: pd.DataFrame,
        units: pd.DataFrame,
        monthly_cf: pd.DataFrame,
    ) -> float | None:
        if not units.empty:
            rent_col = self._find_col(units, ["rent", "monthly_rent", "家賃", "賃料"])
            if rent_col:
                df = units.copy()
                df[rent_col] = pd.to_numeric(df[rent_col], errors="coerce").fillna(0)

                status_col = self._find_col(df, ["status", "occupancy_status", "入居状況"])
                if status_col:
                    vacant = df[status_col].astype(str).str.contains("vacant|空室|empty", case=False, regex=True, na=False)
                    df = df[~vacant]

                return float(df[rent_col].sum())

        if not monthly_cf.empty:
            col = self._find_col(monthly_cf, ["rent_income", "income", "monthly_income", "家賃収入", "収入"])
            if col:
                values = pd.to_numeric(monthly_cf[col], errors="coerce").dropna()
                if not values.empty:
                    return float(values.tail(1).sum())

        if not properties.empty:
            col = self._find_col(properties, ["monthly_income", "current_monthly_income", "月収", "月額収入"])
            if col:
                return float(pd.to_numeric(properties[col], errors="coerce").fillna(0).sum())

        return None

    def _annual_rent_from_properties(self, properties: pd.DataFrame) -> float | None:
        if properties.empty:
            return None

        col = self._find_col(properties, ["annual_income", "current_annual_income", "full_annual_income", "年間収入", "年収"])
        if col:
            return float(pd.to_numeric(properties[col], errors="coerce").fillna(0).sum())

        return None

    def _annual_debt_service(self, properties: pd.DataFrame, loans: pd.DataFrame, monthly_cf: pd.DataFrame) -> float | None:
        if not properties.empty:
            monthly_col = self._find_col(properties, ["monthly_payment", "loan_payment", "返済月額", "月額返済"])
            annual_col = self._find_col(properties, ["annual_payment", "annual_debt_service", "年間返済額"])

            if annual_col:
                return float(pd.to_numeric(properties[annual_col], errors="coerce").fillna(0).sum())
            if monthly_col:
                return float(pd.to_numeric(properties[monthly_col], errors="coerce").fillna(0).sum() * 12)

        if not loans.empty:
            monthly_col = self._find_col(loans, ["monthly_payment", "payment", "loan_payment", "返済月額"])
            annual_col = self._find_col(loans, ["annual_payment", "annual_debt_service", "年間返済額"])

            if annual_col:
                return float(pd.to_numeric(loans[annual_col], errors="coerce").fillna(0).sum())
            if monthly_col:
                return float(pd.to_numeric(loans[monthly_col], errors="coerce").fillna(0).sum() * 12)

        if not monthly_cf.empty:
            col = self._find_col(monthly_cf, ["loan_payment", "debt_service", "返済", "ローン"])
            if col:
                values = pd.to_numeric(monthly_cf[col], errors="coerce").dropna()
                if not values.empty:
                    return float(values.tail(1).sum() * 12)

        return None

    def _annual_expense(
        self,
        properties: pd.DataFrame,
        monthly_cf: pd.DataFrame,
        repairs: pd.DataFrame,
    ) -> float | None:
        total = 0.0
        found = False

        if not properties.empty:
            for candidates in [
                ["annual_expense", "年間経費"],
                ["management_fee_annual", "管理費年間"],
                ["property_tax", "fixed_asset_tax", "固定資産税"],
            ]:
                col = self._find_col(properties, candidates)
                if col:
                    total += float(pd.to_numeric(properties[col], errors="coerce").fillna(0).sum())
                    found = True

        if not monthly_cf.empty:
            for candidates in [["expense", "monthly_expense", "経費"], ["management_fee", "管理費"]]:
                col = self._find_col(monthly_cf, candidates)
                if col:
                    values = pd.to_numeric(monthly_cf[col], errors="coerce").dropna()
                    if not values.empty:
                        total += float(values.tail(1).sum() * 12)
                        found = True

        if not repairs.empty:
            col = self._find_col(repairs, ["cost", "amount", "repair_cost", "修繕費", "金額"])
            if col:
                total += float(pd.to_numeric(repairs[col], errors="coerce").fillna(0).sum())
                found = True

        return total if found else None

    @staticmethod
    def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
        if df.empty:
            return None

        cols = list(df.columns)
        lowered = {str(c).lower(): c for c in cols}

        for c in candidates:
            if c.lower() in lowered:
                return lowered[c.lower()]

        for candidate in candidates:
            c_low = candidate.lower()
            for col in cols:
                if c_low in str(col).lower():
                    return col

        return None

    @staticmethod
    def _num(value: Any) -> float | None:
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None
