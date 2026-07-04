from services.scenario_assumptions_service import ScenarioAssumptionsService


def test_scenario_assumptions_load_and_convert(tmp_path):
    path = tmp_path / "scenario_assumptions.json"
    service = ScenarioAssumptionsService(path)

    assumptions = service.load()
    assert assumptions["scenario_name"] == "Base Case"

    integrated = service.to_integrated_input(assumptions)
    assert integrated.current_cash > 0
    assert integrated.acquisition_input.property_name
    assert integrated.exit_input.holding_years > 0


def test_scenario_assumptions_save(tmp_path):
    path = tmp_path / "scenario_assumptions.json"
    service = ScenarioAssumptionsService(path)

    assumptions = service.load()
    assumptions["scenario_name"] = "Test Case"
    service.save(assumptions)

    loaded = service.load()
    assert loaded["scenario_name"] == "Test Case"
    assert loaded["saved_at"] is not None
