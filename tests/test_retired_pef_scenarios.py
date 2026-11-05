import pytest

from Greenhub.parameters.loaders import load_default_registry
from Greenhub.phase7_inputs import load_phase7_inputs
from Greenhub.systems import create_phase3_scenario


@pytest.mark.parametrize("scenario", ["F2", "F3"])
def test_retired_pef_routes_are_rejected_by_all_process_entry_points(scenario):
    with pytest.raises(ValueError, match="retired|disabled"):
        create_phase3_scenario(scenario)
    with pytest.raises(ValueError, match="retired"):
        load_phase7_inputs(phase3_scenario_id=scenario)


def test_retired_pef_parameters_remain_traceable_but_blocked():
    registry = load_default_registry()
    candidates = [
        candidate for candidate in registry.candidates
        if candidate.parameter_id == "phase3.specific_energy_kwh_per_t_wet"
        and set(candidate.applicability.scenario_ids) & {"F2", "F3"}
    ]
    assert candidates
    assert all(candidate.activation_state.value == "blocked" for candidate in candidates)
    assert all(
        "retained as blocked historical candidates" in " ".join(candidate.warnings)
        for candidate in candidates
    )
