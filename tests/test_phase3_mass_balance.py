import pytest

from Greenhub.systems import create_phase3_scenario


@pytest.mark.parametrize("scenario", ["F0", "F1", "F2", "F3"])
def test_phase3_scenarios_close_total_and_component_mass(scenario):
    model = create_phase3_scenario(scenario).simulate()
    assert model.validation.overall_error_kg_hr == pytest.approx(0.0, abs=1e-9)
    assert max(abs(value) for value in model.validation.component_errors_kg_hr.values()) <= 1e-9

