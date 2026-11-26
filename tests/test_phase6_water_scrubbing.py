"""Physical and conservation tests for BG2 water scrubbing."""

import csv
from math import exp, log
from pathlib import Path

from Greenhub.systems import create_phase6_scenario
from Greenhub.application.water_reporting import fresh_water_kg_per_hour_from_model, kg_to_m3
from Greenhub.parameters import (
    CalculationMode,
    ParameterResolver,
    SelectionContext,
    load_default_registry,
)
from Greenhub.phase6_specifications import h2s_solubility_temperature_ratio


def test_water_scrubbing_mass_balance():
    model = create_phase6_scenario("BG2").simulate()

    assert abs(model.validation.overall_error_kg_hr) < 1e-6
    assert max(abs(value) for value in model.validation.component_errors_kg_hr.values()) < 1e-6


def test_water_scrubbing_methane_recovery():
    model = create_phase6_scenario("BG2").simulate()

    assert 0.0 < model.metrics["methane_recovery_fraction"] <= 1.0
    assert model.metrics["methane_to_reject_kg_hr"] > 0.0
    assert abs(model.metrics["methane_unassigned_kg_hr"]) < 1e-6
    assert abs(model.metrics["phase6_methane_unassigned_from_raw_kg_hr"]) < 1e-6
    assert (
        model.metrics["product_gas_co2_mol_fraction_dry"]
        < model.metrics["conditioned_biogas_co2_mol_fraction_dry"]
    )


def test_water_scrubbing_water_balance():
    model = create_phase6_scenario("BG2").simulate()

    assert abs(model.validation.component_errors_kg_hr["Water"]) < 1e-6
    assert model.metrics["fresh_water_kg_hr"] > 0.0
    assert model.streams["phase6_wastewater"].imass["Water"] > 0.0
    assert fresh_water_kg_per_hour_from_model(model) == model.metrics["fresh_water_kg_hr"]
    assert kg_to_m3(fresh_water_kg_per_hour_from_model(model) * 8760) == model.metrics["fresh_water_kg_hr"] * 8.76


def test_absorber_specific_fresh_water_is_reported_against_literature_range_only():
    model = create_phase6_scenario("BG2").simulate()
    absorber = model.units["A611"]
    reported = absorber.design_results["Fresh-water makeup per raw gas"]

    assert reported == absorber.design_results["Fresh-water makeup"] / (
        absorber.parameters.water_density_kg_m3
        * absorber.design_results["Gas feed"]
    )
    assert absorber.design_results["Literature fresh-water lower bound"] == 4.0e-5
    assert absorber.design_results["Literature fresh-water upper bound"] == 4.0e-4
    assert 4.0e-5 <= reported <= 4.0e-4
    # This comparison is report-only: it neither replaces the purge assumption
    # nor changes the simulated process balance.
    assert abs(model.validation.component_errors_kg_hr["Water"]) < 1e-6
    assert absorber.parameters.purge_water_fraction == 0.05
    assert absorber._units["Fresh-water makeup per raw gas"] == "m3/Nm3"


def test_water_scrubbing_dataset_manifest_routes_resolve():
    repository_root = Path(__file__).resolve().parents[1]
    manifest = repository_root / "Greenhub/data/Bigas production + upgrade/Water_Scrubbing/dataset_manifest.csv"
    with manifest.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    assert len(rows) == 22
    assert any(row["filename"] == "wantz_2023_hpsw_experiment_energy_points_reference.csv" for row in rows)
    assert all((repository_root / row["relative_path"]).is_file() for row in rows)


def test_water_scrubbing_flash_recycle():
    model = create_phase6_scenario("BG2").simulate()
    recycle = model.units["M610"].ins[1]
    splitter = model.units["S610"]

    assert recycle.F_mass > 0.0
    assert model.parameters["has_recycle"] is True
    assert model.system.subsystems
    assert model.system.subsystems[0]._mol_error < 1e-8
    assert splitter.design_results["Actual recycle"] <= splitter.design_results["Target recycle"]
    assert splitter.design_results["Actual recycle"] <= splitter.design_results["Available flash gas"]
    assert model.metrics["flash_gas_recycle_raw_gas_ratio"] == splitter.design_results[
        "Actual recycle / raw gas"
    ]
    assert model.metrics["flash_gas_fraction_recycled"] == splitter.design_results[
        "Flash gas recycled"
    ]


def test_water_scrubbing_recycle_parameter_uses_raw_gas_flow_basis():
    fraction = 0.2
    model = create_phase6_scenario(
        "BG2",
        parameter_overrides={"water_scrubber_flash_gas_recycle_fraction": fraction},
    ).simulate()
    splitter = model.units["S610"]
    expected_target = model.metrics["conditioned_biogas_dry_nm3_hr"] * fraction

    assert abs(splitter.design_results["Target recycle"] - expected_target) < 1e-9
    assert splitter.design_results["Actual recycle"] <= expected_target + 1e-9
    assert splitter.design_results["Actual recycle"] <= splitter.design_results[
        "Available flash gas"
    ] + 1e-9


def test_water_scrubbing_zero_recycle_target_disables_recycle_unit():
    model = create_phase6_scenario(
        "BG2",
        parameter_overrides={"water_scrubber_flash_gas_recycle_fraction": 0.0},
    ).simulate()

    assert "S610" not in model.units
    assert model.metrics["flash_gas_recycle_target_nm3_hr"] == 0.0
    assert model.metrics["flash_gas_recycle_actual_nm3_hr"] == 0.0
    assert model.metrics["flash_gas_recycle_raw_gas_ratio"] == 0.0


def test_water_scrubbing_circulation_response():
    low = create_phase6_scenario(
        "BG2",
        parameter_overrides={"water_scrubber_water_to_gas_kg_nm3": 2.0},
    ).simulate()
    high = create_phase6_scenario(
        "BG2",
        parameter_overrides={"water_scrubber_water_to_gas_kg_nm3": 4.0},
    ).simulate()

    assert high.metrics["co2_removal_fraction"] >= low.metrics["co2_removal_fraction"]


def test_h2s_solubility_temperature_ratio_is_relative_and_directionally_correct():
    fit = (-14.761, 2507.2, -24.912, 3477.1, 0.3993, 0.0157, 283.2, 273.2, 603.2)
    at_reference = h2s_solubility_temperature_ratio(25.0, 25.0, *fit)
    cooler = h2s_solubility_temperature_ratio(5.0, 25.0, *fit)
    warmer = h2s_solubility_temperature_ratio(35.0, 25.0, *fit)
    low_t = 5.0 + 273.15
    reference_t = 25.0 + 273.15
    expected_cool_ratio = exp(
        (-14.761 + 2507.2 / low_t)
        - (-24.912 + 3477.1 / reference_t + 0.3993 * log(reference_t) + 0.0157 * reference_t)
    )

    assert abs(at_reference - 1.0) < 1e-12
    assert abs(cooler - expected_cool_ratio) < 1e-12
    assert cooler > 1.0 > warmer


def test_h2s_literature_parameter_is_registered_and_mode_gated():
    registry = load_default_registry()
    parameter_ids = (
        "phase6.water_scrubber_h2s_solubility_fit_low_a",
        "phase6.water_scrubber_h2s_solubility_fit_low_b_k",
        "phase6.water_scrubber_h2s_solubility_fit_high_a",
        "phase6.water_scrubber_h2s_solubility_fit_high_b_k",
        "phase6.water_scrubber_h2s_solubility_fit_high_c",
        "phase6.water_scrubber_h2s_solubility_fit_high_d_per_k",
        "phase6.water_scrubber_h2s_solubility_fit_transition_temperature_k",
        "phase6.water_scrubber_h2s_solubility_fit_minimum_temperature_k",
        "phase6.water_scrubber_h2s_solubility_fit_maximum_temperature_k",
    )
    definitions = [registry.get(parameter_id) for parameter_id in parameter_ids]
    resolver = ParameterResolver(registry)
    structural = resolver.resolve(
        SelectionContext(CalculationMode.STRUCTURAL, ("BG2",), None)
    )
    literature = resolver.resolve(
        SelectionContext(CalculationMode.LITERATURE_DEFAULT, ("BG2",), None)
    )
    structural_values = [next(item for item in structural if item.parameter_id == pid) for pid in parameter_ids]
    literature_values = [next(item for item in literature if item.parameter_id == pid) for pid in parameter_ids]

    assert all(item.quality_class == "B" and item.readiness_state.value == "D4" for item in definitions)
    assert all(item.uncertainty and item.uncertainty.description for item in definitions)
    assert all(item.blocked for item in structural_values)
    assert all(not item.blocked for item in literature_values)
    assert [item.active_value for item in literature_values] == [
        -14.761, 2507.2, -24.912, 3477.1, 0.3993, 0.0157, 283.2, 273.2, 603.2
    ]
    assert all(item.selected_candidate.stable_identifier == "10.1016/C2009-0-00348-1" for item in literature_values)
    assert all(
        item.selected_candidate.uncertainty
        and item.selected_candidate.uncertainty.description
        for item in literature_values
    )
    model_overrides = resolver.model_overrides(literature)
    assert len(model_overrides) == len(parameter_ids)
    model = create_phase6_scenario("BG2", parameter_overrides=model_overrides).simulate()
    structural_model = create_phase6_scenario("BG2").simulate()
    from Greenhub.state_engine import build_state_outputs

    equation = next(
        item for item in build_state_outputs(model, literature)["equation_usage"]
        if item["equation_id"] == "EQ-P6-WS-H2S-001"
    )
    assert equation["used"]
    assert not equation["fallback"]
    structural_h2s = float(structural_model.units["A611"].outs[0].imass["HydrogenSulfide"])
    literature_h2s = float(model.units["A611"].outs[0].imass["HydrogenSulfide"])
    assert abs(structural_h2s - literature_h2s) < 1e-9


def test_literature_h2s_temperature_response_changes_only_from_reference_state():
    fit = {
        "water_scrubber_h2s_solubility_fit_low_a": -14.761,
        "water_scrubber_h2s_solubility_fit_low_b_k": 2507.2,
        "water_scrubber_h2s_solubility_fit_high_a": -24.912,
        "water_scrubber_h2s_solubility_fit_high_b_k": 3477.1,
        "water_scrubber_h2s_solubility_fit_high_c": 0.3993,
        "water_scrubber_h2s_solubility_fit_high_d_per_k": 0.0157,
        "water_scrubber_h2s_solubility_fit_transition_temperature_k": 283.2,
        "water_scrubber_h2s_solubility_fit_minimum_temperature_k": 273.2,
        "water_scrubber_h2s_solubility_fit_maximum_temperature_k": 603.2,
    }
    cool = create_phase6_scenario(
        "BG2",
        parameter_overrides={
            "water_scrubber_absorber_temperature_c": 5.0,
            **fit,
        },
    ).simulate()
    reference = create_phase6_scenario(
        "BG2",
        parameter_overrides={
            "water_scrubber_absorber_temperature_c": 15.0,
            **fit,
        },
    ).simulate()
    warm = create_phase6_scenario(
        "BG2",
        parameter_overrides={
            "water_scrubber_absorber_temperature_c": 25.0,
            **fit,
        },
    ).simulate()

    cool_factor = cool.units["A611"].design_results["H2S temperature response factor"]
    reference_factor = reference.units["A611"].design_results["H2S temperature response factor"]
    warm_factor = warm.units["A611"].design_results["H2S temperature response factor"]
    assert cool_factor > reference_factor > warm_factor
    assert abs(reference_factor - 1.0) < 1e-12
