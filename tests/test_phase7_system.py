"""Reference and single-route Phase 7 scenario tests."""

from __future__ import annotations

import pytest

from Greenhub.systems import create_phase7_scenario


@pytest.mark.parametrize("scenario_id", ["NR0", "NR1", "NR2", "NR3"])
def test_phase7_reference_scenarios_simulate(scenario_id):
    model = create_phase7_scenario(scenario_id).simulate()
    assert abs(model.validation.overall_error_kg_hr) < 1e-6
    assert all(stream.F_mass >= 0.0 for stream in model.boundary_outputs)
    if scenario_id == "NR1":
        equalization = model.units["T701"].design_results
        assert equalization["Tank diameter"] > 0.0
        assert equalization["Tank height"] > 0.0
        assert equalization["Heat-transfer area"] > 0.0
        assert equalization["Heat loss at feed temperature"] >= 0.0
        assert model.units["S701"].technology in {
            "screw_press",
            "decanter_centrifuge",
            "belt_filter",
        }
