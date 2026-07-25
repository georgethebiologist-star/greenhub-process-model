"""Integrated and alternative-mechanism Phase 7 scenario tests."""

from __future__ import annotations

import pytest

from Greenhub.systems import create_phase7_scenario


@pytest.mark.parametrize("scenario_id", ["NR4", "NR5", "NR6", "NR7"])
def test_phase7_integrated_scenarios_simulate(scenario_id):
    model = create_phase7_scenario(scenario_id).simulate()
    assert abs(model.validation.overall_error_kg_hr) < 1e-6
    assert all(stream.F_mass >= 0.0 for stream in model.boundary_outputs)
