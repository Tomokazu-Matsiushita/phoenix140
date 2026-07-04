from services.real_estate import AcquisitionInput, ExitIRRInput, RealEstateAICFOService


def test_real_estate_ai_cfo_full_review():
    service = RealEstateAICFOService()
    review = service.full_review(
        acquisition_input=AcquisitionInput(),
        exit_input=ExitIRRInput(),
    )

    assert "executive_summary" in review
    assert "comments" in review
    assert "priority_actions" in review
    assert len(review["comments"]) >= 1
