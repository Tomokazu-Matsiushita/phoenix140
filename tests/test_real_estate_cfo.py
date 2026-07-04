from services.real_estate import RealEstateCFOService


def test_real_estate_snapshot_has_summary():
    snapshot = RealEstateCFOService().snapshot()
    assert "summary" in snapshot
    assert "property_count" in snapshot["summary"]
    assert "available_tables" in snapshot
