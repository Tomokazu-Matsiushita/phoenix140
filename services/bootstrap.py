from db.database import Base, ENGINE, SessionLocal
from models.tables import FinancialAsset, Property, RentalUnit, MonthlyPropertyCF

def bootstrap():
    Base.metadata.create_all(bind=ENGINE)
    with SessionLocal() as s:
        if s.query(FinancialAsset).count() == 0:
            seed_financial_assets(s)
        if s.query(Property).count() == 0:
            seed_properties(s)
        s.commit()

def seed_financial_assets(s):
    rows = [
        ("SBI証券", "株式(特定)", "stock", "三菱商事", "商社", 600, 946, 4344, 2606400, 60000, "コア"),
        ("SBI証券", "株式(特定)", "stock", "三井住友FG", "銀行", 600, 1039, 6433, 3859800, 94800, "コア"),
        ("SBI証券", "株式(特定)", "stock", "武田薬品", "医薬品", 200, 3359, 4859, 971800, 40000, "コア"),
        ("SBI証券", "株式(特定)", "stock", "日本郵船", "海運", 200, 3182, 5080, 1016000, 46000, "調整"),
        ("SBI証券", "株式(特定)", "stock", "商船三井", "海運", 200, 3384, 5031, 1006200, 46000, "調整"),
        ("SBI証券", "株式(特定)", "stock", "電源開発", "電力", 400, 1483, 3635, 1454000, 40000, "準コア"),
        ("SBI証券", "株式(特定)", "stock", "小松製作所", "機械", 200, 3833, 6259, 1251800, 38000, "準コア"),
        ("SBI証券", "株式(特定)", "stock", "大紀アルミ", "素材", 300, 734, 1570, 471000, 18000, "準コア"),
        ("SBI証券", "株式(特定)", "stock", "セルソース", "医療サービス", 100, 5266, 314, 31400, 0, "損益通算候補"),
        ("SBI証券", "投資信託", "fund", "SBI投資信託", "", 1, 0, 0, 3898903, 0, ""),
        ("WealthNavi", "ロボアド", "robo", "WealthNavi", "", 1, 0, 0, 984578, 0, ""),
        ("NRKN", "確定拠出年金", "pension", "ホンダ確定拠出年金", "", 1, 0, 0, 5011158, 0, ""),
        ("三井住友銀行", "銀行", "cash", "三井住友銀行", "", 1, 0, 0, 2962973, 0, ""),
        ("SBJ銀行", "銀行", "cash", "SBJ銀行", "", 1, 0, 0, 1672736, 0, ""),
        ("ソニー銀行", "銀行", "cash", "ソニー銀行", "", 1, 0, 0, 526997, 0, ""),
        ("カード", "負債", "liability", "クレジットカード控除", "", 1, 0, 0, -788947, 0, ""),
    ]
    for r in rows:
        s.add(FinancialAsset(
            institution=r[0], account_name=r[1], asset_type=r[2], name=r[3], sector=r[4],
            quantity=r[5], cost_price=r[6], current_price=r[7], value=r[8],
            annual_dividend=r[9], policy=r[10], source="seed"
        ))

def seed_properties(s):
    alba = Property(
        name="Alba港栄", location="名古屋市港区", purchase_price=66000000,
        loan_balance=40000000, interest_rate=2.0, loan_years=25,
        monthly_payment=183333, units=8, memo="ダミー。実績に合わせて修正"
    )
    oblige = Property(
        name="oblige新田町", location="常滑市新田町", purchase_price=76000000,
        loan_balance=75000000, interest_rate=3.0, loan_years=34,
        monthly_payment=293452, units=12, memo="1室空室前提。実績に合わせて修正"
    )
    s.add_all([alba, oblige])
    s.flush()

    for room in ["101","102","103","105","201","202","203","205"]:
        s.add(RentalUnit(property_id=alba.id, room_no=room, rent=49000, management_fee=3000, occupied=(room!="103")))
    for i in range(1,13):
        s.add(RentalUnit(property_id=oblige.id, room_no=f"{100+i}", rent=50885, management_fee=0, occupied=(i!=3)))
