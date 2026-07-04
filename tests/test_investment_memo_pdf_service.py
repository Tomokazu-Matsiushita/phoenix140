from services.investment_memo_pdf_service import InvestmentMemoPDFService
from services.investment_memo_service import InvestmentMemoInput, InvestmentMemoService


def test_investment_memo_pdf_build_runs():
    memo = InvestmentMemoService().build(InvestmentMemoInput())
    pdf_bytes = InvestmentMemoPDFService().build_pdf_bytes(memo)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000
