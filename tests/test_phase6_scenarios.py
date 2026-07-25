"""Isolation, repeatability, quality, and data-gate tests for Phase 6."""

import pytest

from Greenhub.systems import create_phase6_scenario


def test_upgrading_scenario_isolation():
    water = create_phase6_scenario("BG2").simulate()
    water_purity = water.metrics["methane_purity_dry_fraction"]
    membrane = create_phase6_scenario("BG3").simulate()

    assert "A611" in water.units and "M621" not in water.units
    assert "M621" in membrane.units and "A611" not in membrane.units
    assert water.metrics["methane_purity_dry_fraction"] == water_purity


def test_upgrading_deterministic_rebuild():
    first = create_phase6_scenario("BG4").simulate()
    first_metrics = dict(first.metrics)
    second = create_phase6_scenario("BG4").simulate()

    for name in (
        "methane_purity_dry_fraction",
        "methane_recovery_fraction",
        "co2_removal_fraction",
        "electricity_use_kw",
    ):
        assert second.metrics[name] == pytest.approx(first_metrics[name], rel=1e-12)


def test_biomethane_quality_reporting():
    model = create_phase6_scenario("BG2").simulate()

    assert model.metrics["product_gas_methane_mol_fraction_dry"] > 0.0
    assert model.metrics["product_gas_methane_mol_fraction_wet"] > 0.0
    assert model.metrics["product_gas_methane_mol_fraction_dry"] >= model.metrics["product_gas_methane_mol_fraction_wet"]
    assert len(model.validation.feed_quality_checks) == 9
    assert all(check.passed for check in model.validation.feed_quality_checks)


@pytest.mark.parametrize("scenario_id", ["BG1", "BG6"])
def test_inactive_phase6_scenarios_are_data_gated(scenario_id):
    with pytest.raises(NotImplementedError, match="inactive"):
        create_phase6_scenario(scenario_id)


@pytest.mark.parametrize("scenario_id", ["BG0", "BG2", "BG3", "BG4", "BG5"])
def test_all_active_upgrading_pathways_simulate(scenario_id):
    model = create_phase6_scenario(scenario_id).simulate()

    assert model.streams["primary_gas_product"].F_mass >= 0.0
    assert abs(model.validation.overall_error_kg_hr) < 1e-6
