from db.database import SessionLocal
from models.tables import FinancialAsset


EXTRA_ASSETS = [
    {
        "institution": "SBI証券",
        "account_name": "投資信託",
        "asset_type": "fund",
        "name": "NZAMカーボン",
        "sector": "投資信託",
        "quantity": 1,
        "cost_price": 421500,
        "current_price": 805500,
        "value": 805500,
        "annual_dividend": 0,
        "policy": "整理候補",
        "source": "manual_seed",
    },
    {
        "institution": "SBI証券",
        "account_name": "株式(特定)",
        "asset_type": "stock",
        "name": "あおぞら銀行",
        "sector": "銀行",
        "quantity": 100,
        "cost_price": 2650,
        "current_price": 2760,
        "value": 276000,
        "annual_dividend": 5000,
        "policy": "整理候補",
        "source": "manual_seed",
    },
    {
        "institution": "SBI証券",
        "account_name": "株式(特定)",
        "asset_type": "stock",
        "name": "トヨタ自動車",
        "sector": "自動車",
        "quantity": 100,
        "cost_price": 2450,
        "current_price": 2738,
        "value": 273800,
        "annual_dividend": 10000,
        "policy": "整理候補",
        "source": "manual_seed",
    },
    {
        "institution": "SBI証券",
        "account_name": "株式(特定)",
        "asset_type": "stock",
        "name": "明和産業",
        "sector": "商社",
        "quantity": 300,
        "cost_price": 703,
        "current_price": 859,
        "value": 257700,
        "annual_dividend": 25200,
        "policy": "整理候補",
        "source": "manual_seed",
    },
    {
        "institution": "SBI証券",
        "account_name": "株式(特定)",
        "asset_type": "stock",
        "name": "JT",
        "sector": "たばこ",
        "quantity": 100,
        "cost_price": 3800,
        "current_price": 4040,
        "value": 404000,
        "annual_dividend": 20800,
        "policy": "コア",
        "source": "manual_seed",
    },
]


def main():
    with SessionLocal() as session:
        existing = {name for (name,) in session.query(FinancialAsset.name).all()}

        added = 0
        for payload in EXTRA_ASSETS:
            if payload["name"] in existing:
                continue
            session.add(FinancialAsset(**payload))
            added += 1

        session.commit()

    print(f"Extra financial assets added: {added}")


if __name__ == "__main__":
    main()
