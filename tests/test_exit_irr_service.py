from services.real_estate.exit_irr_service import ExitIRRInput, ExitIRRService


def test_exit_irr_evaluate():
    service = ExitIRRService()
    result = service.evaluate(ExitIRRInput())
    assert "irr" in result
    assert "total_profit" in result
    assert "health" in result


def test_remaining_balance_declines():
    service = ExitIRRService()
    balance_0 = service.remaining_balance(10000000, 3.0, 30, 0)
    balance_120 = service.remaining_balance(10000000, 3.0, 30, 120)
    assert balance_120 < balance_0


def test_exit_irr_sensitivity():
    service = ExitIRRService()
    df = service.sensitivity_table(ExitIRRInput())
    assert not df.empty
    assert "irr" in df.columns
