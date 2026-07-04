from services.real_estate.property_acquisition_service import AcquisitionInput, PropertyAcquisitionService


def test_property_acquisition_evaluate():
    service = PropertyAcquisitionService()
    result = service.evaluate(AcquisitionInput())
    assert result["monthly_payment"] > 0
    assert result["full_annual_rent"] > 0
    assert "dscr" in result
    assert "health" in result


def test_property_acquisition_sensitivity():
    service = PropertyAcquisitionService()
    df = service.sensitivity_table(AcquisitionInput())
    assert not df.empty
    assert "cash_flow_after_debt" in df.columns
