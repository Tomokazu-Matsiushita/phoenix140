from services.capital_allocation_service import CapitalAllocationInput, CapitalAllocationService
from services.real_estate import AcquisitionInput


def test_capital_allocation_review_runs():
    service = CapitalAllocationService()
    review = service.review(
        CapitalAllocationInput(
            target_net_cash=100000,
            acquisition_input=AcquisitionInput(),
        )
    )

    assert "acquisition" in review
    assert "comparison" in review
    assert "recommendation" in review
