from services.integrated_ai_cfo_service import IntegratedAICFOService, IntegratedCFOInput


def test_integrated_ai_cfo_review_runs():
    service = IntegratedAICFOService()
    review = service.review(IntegratedCFOInput())

    assert "decision" in review
    assert "executive_summary" in review
    assert "decision_factors" in review
    assert "must_check" in review
