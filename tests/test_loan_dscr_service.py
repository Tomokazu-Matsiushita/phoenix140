from services.real_estate.loan_dscr_service import LoanDSCRService


def test_payment_positive():
    service = LoanDSCRService()
    payment = service.payment(principal=10000000, annual_rate_percent=3.0, years=30)
    assert payment > 0


def test_zero_rate_payment():
    service = LoanDSCRService()
    payment = service.payment(principal=12000000, annual_rate_percent=0.0, years=10)
    assert round(payment) == 100000
