from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService


def test_investment_memo_build_runs():
    service = InvestmentMemoService()
    memo = service.build(InvestmentMemoInput())

    assert "markdown" in memo
    assert "review" in memo
    assert "tables" in memo
    assert "# Phoenix 140 Investment Decision Memo" in memo["markdown"]
    assert "decision_factors" in memo["tables"]
