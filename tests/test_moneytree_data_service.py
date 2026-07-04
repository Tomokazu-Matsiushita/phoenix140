import pandas as pd

from services.moneytree import MoneytreeDataService


def test_moneytree_import_accounts_df():
    service = MoneytreeDataService()
    df = pd.DataFrame(
        [
            {
                "金融機関": "Test Bank",
                "口座名": "普通",
                "口座番号": "****0001",
                "口座種別": "bank",
                "残高": 1000,
                "残高日": "2026-07-04",
            }
        ]
    )

    result = service.import_accounts_df(df)
    assert result.inserted >= 1
    assert result.errors == []


def test_moneytree_import_transactions_df():
    service = MoneytreeDataService()
    df = pd.DataFrame(
        [
            {
                "日付": "2026-07-04",
                "摘要": "Test Expense",
                "カテゴリ": "Test",
                "金額": -500,
            }
        ]
    )

    result = service.import_transactions_df(df)
    assert result.errors == []


def test_moneytree_summary_runs():
    service = MoneytreeDataService()
    summary = service.portfolio_summary()
    assert "total_balance" in summary
    assert "account_count" in summary
