from services.phoenix_command_center_service import PhoenixCommandCenterService


def test_phoenix_command_center_build_runs():
    service = PhoenixCommandCenterService()
    data = service.build()

    assert "snapshot" in data
    assert "risk_flags" in data
    assert "action_cards" in data

    snapshot = data["snapshot"]
    assert snapshot.scenario_name
    assert snapshot.decision_label
