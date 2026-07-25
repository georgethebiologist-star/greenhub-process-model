"""Physical and conservation tests for BG2 water scrubbing."""

from Greenhub.systems import create_phase6_scenario


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


def test_water_scrubbing_flash_recycle():
    model = create_phase6_scenario("BG2").simulate()
    recycle = model.units["M610"].ins[1]

    assert recycle.F_mass > 0.0
    assert model.parameters["has_recycle"] is True
    assert model.system.subsystems
    assert model.system.subsystems[0]._mol_error < 1e-8


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
