"""Integrated boundary and utility-interface tests for Phase 7."""

from __future__ import annotations

import pytest

from Greenhub.systems import create_phase7_scenario


def test_phase1_to_phase7_total_balance():
    model = create_phase7_scenario("NR7").simulate()
    assert model.validation.boundary_in_kg_hr == pytest.approx(
        model.validation.boundary_out_kg_hr, abs=1e-6
    )
    for element in (
        "carbon", "nitrogen", "phosphorus", "potassium",
        "magnesium", "calcium", "sulfur", "chloride",
    ):
        assert abs(model.validation.element_errors_kg_hr[element]) < 1e-6


def test_phase7_utility_integration():
    model = create_phase7_scenario(
        "NR7",
        parameter_overrides={
            "phase7_recovered_heat_available_kw": 5.0,
            "phase7_recovered_heat_temperature_c": 100.0,
            "phase7_heat_recovery_efficiency": 0.8,
            "phase7_chp_electricity_available_kw": 0.1,
        },
    ).simulate()
    assert 0.0 < model.metrics["recovered_heat_used_kw"] <= 4.0
    assert model.metrics["external_heat_kw"] < model.metrics["gross_heat_demand_kw"]
    assert model.metrics["chp_electricity_used_kw"] == pytest.approx(0.1)
