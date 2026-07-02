from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from db.database import Base

class FinancialAsset(Base):
    __tablename__ = "financial_assets"
    id = Column(Integer, primary_key=True)
    source = Column(String, default="manual")
    institution = Column(String)
    account_name = Column(String)
    asset_type = Column(String)  # cash, stock, fund, pension, robo, liability
    name = Column(String)
    sector = Column(String, default="")
    quantity = Column(Float, default=0)
    cost_price = Column(Float, default=0)
    current_price = Column(Float, default=0)
    value = Column(Float, default=0)
    annual_dividend = Column(Float, default=0)
    policy = Column(String, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    location = Column(String)
    purchase_price = Column(Float, default=0)
    loan_balance = Column(Float, default=0)
    interest_rate = Column(Float, default=0)
    loan_years = Column(Integer, default=0)
    monthly_payment = Column(Float, default=0)
    units = Column(Integer, default=0)
    memo = Column(String, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class RentalUnit(Base):
    __tablename__ = "rental_units"
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    room_no = Column(String)
    rent = Column(Float, default=0)
    management_fee = Column(Float, default=0)
    parking_fee = Column(Float, default=0)
    occupied = Column(Boolean, default=True)

class MonthlyPropertyCF(Base):
    __tablename__ = "monthly_property_cf"
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    month = Column(String)  # YYYY-MM
    rent_income = Column(Float, default=0)
    loan_payment = Column(Float, default=0)
    management_fee = Column(Float, default=0)
    repair_cost = Column(Float, default=0)
    tax_cost = Column(Float, default=0)
    other_cost = Column(Float, default=0)
    memo = Column(String, default="")
