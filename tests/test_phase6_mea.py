"""Solvent, loading, regeneration, and heat tests for BG5 MEA."""

import pytest

from Greenhub.chemicals import chemicals
from Greenhub.systems import create_phase6_scenario


def test_mea_solvent_balance():
    model = create_phase6_scenario("BG5").simulate()

    assert abs(model.validation.component_errors_kg_hr["Monoethanolamine"]) < 1e-6
    assert model.streams["fresh_mea_solution_makeup"].imass["Monoethanolamine"] > 0.0
    assert model.streams["phase6_spent_material"].imass["MEADegradationProducts"] > 0.0


def test_mea_carbon_loading():
    model = create_phase6_scenario("BG5").simulate()
    absorber = model.units["A641"]
    parameters = absorber.parameters
    circulation_kmol = absorber.design_results["MEA circulation"] / chemicals.Monoethanolamine.MW
    loading_capture = (
        circulation_kmol
        * (
            parameters.rich_loading_mol_co2_per_mol_mea
            - parameters.lean_loading_mol_co2_per_mol_mea
        )
        * chemicals.CarbonDioxide.MW
    )

    assert absorber.rich_loading > absorber.lean_loading >= 0.0
    assert loading_capture == pytest.approx(absorber.co2_captured_kg_hr, rel=1e-9)


def test_mea_regeneration_closure():
    model = create_phase6_scenario("BG5").simulate()
    stripper = model.units["A642"]

    assert stripper.co2_released_kg_hr > 0.0
    assert stripper.ins[0].imass["CarbonDioxide"] == pytest.approx(
        sum(stream.imass["CarbonDioxide"] for stream in stripper.outs),
        abs=1e-9,
    )
    assert abs(model.validation.component_errors_kg_hr["CarbonDioxide"]) < 1e-6


def test_mea_heat_duty():
    model = create_phase6_scenario("BG5").simulate()

    assert model.units["H641"].reboiler_duty_kw > 0.0
    assert model.units["V641"].cooling_duty_kw > 0.0
    assert model.units["E641"].recovered_heat_kw == pytest.approx(
        model.units["E643"].transferred_heat_kw,
        rel=1e-12,
    )


def test_mea_working_capacity_response():
    low_capacity = create_phase6_scenario(
        "BG5",
        parameter_overrides={"mea_rich_loading_mol_co2_per_mol_mea": 0.35},
    ).simulate()
    high_capacity = create_phase6_scenario(
        "BG5",
        parameter_overrides={"mea_rich_loading_mol_co2_per_mol_mea": 0.55},
    ).simulate()

    assert high_capacity.metrics["mea_circulation_kg_hr"] < low_capacity.metrics["mea_circulation_kg_hr"]
