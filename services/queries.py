import pandas as pd
from sqlalchemy import select
from db.database import SessionLocal
from models.tables import FinancialAsset, Property, RentalUnit, MonthlyPropertyCF

ANNUAL_LIVING_COST = 7000000

def df_from_query(model):
    with SessionLocal() as s:
        rows = s.execute(select(model)).scalars().all()
        return pd.DataFrame([r.__dict__ for r in rows]).drop(columns=["_sa_instance_state"], errors="ignore")

def financial_assets_df():
    return df_from_query(FinancialAsset)

def properties_df():
    return df_from_query(Property)

def units_df():
    return df_from_query(RentalUnit)

def monthly_cf_df():
    return df_from_query(MonthlyPropertyCF)

def get_dashboard_metrics():
    fa = financial_assets_df()
    props = properties_df()
    units = units_df()

    def sum_type(t):
        if fa.empty:
            return 0
        return float(fa.loc[fa["asset_type"].eq(t), "value"].sum())

    stocks = sum_type("stock")
    cash = sum_type("cash") + sum_type("liability")
    investments = sum_type("fund") + sum_type("robo") + sum_type("pension")
    annual_dividend = 0 if fa.empty else float(fa["annual_dividend"].sum())

    if units.empty:
        annual_property_income = 0
        occupied = 0
        total_units = 0
    else:
        units["monthly_total"] = units["rent"] + units["management_fee"] + units["parking_fee"]
        annual_property_income = float(units.loc[units["occupied"] == True, "monthly_total"].sum() * 12)
        occupied = int(units["occupied"].sum())
        total_units = int(len(units))

    annual_property_cf = annual_property_income
    if not props.empty:
        annual_property_cf -= float(props["monthly_payment"].sum() * 12)
        # rough default operating cost buffer
        annual_property_cf -= annual_property_income * 0.12

    financial_assets = stocks + cash + investments
    annual_cf = annual_dividend + annual_property_cf
    fire_rate = annual_cf / ANNUAL_LIVING_COST * 100 if ANNUAL_LIVING_COST else 0
    occupancy_rate = occupied / total_units * 100 if total_units else 0

    return {
        "stocks": stocks,
        "cash": cash,
        "investments": investments,
        "financial_assets": financial_assets,
        "annual_dividend": annual_dividend,
        "annual_property_cf": annual_property_cf,
        "annual_cf": annual_cf,
        "annual_living_cost": ANNUAL_LIVING_COST,
        "fire_rate": fire_rate,
        "properties": 0 if props.empty else len(props),
        "units": total_units,
        "occupied": occupied,
        "occupancy_rate": occupancy_rate,
    }
