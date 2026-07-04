from services.liquidity_safety_service import LiquiditySafetyInput, LiquiditySafetyService


def test_liquidity_safety_review_runs():
    service = LiquiditySafetyService()
    review = service.review(LiquiditySafetyInput())

    assert "required_buffer" in review
    assert "scenario_review" in review
    assert "recommendation" in review
