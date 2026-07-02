from services.financial import FinancialService


def test_financial_summary_keys():
    service = FinancialService()
    summary = service.financial_summary()

    assert "total_assets" in summary
    assert "annual_dividend" in summary
