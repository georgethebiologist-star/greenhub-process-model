"""Cycle-average material and trend tests for BG4 PSA."""

from Greenhub.systems import create_phase6_scenario


def test_psa_cycle_average_balance():
    model = create_phase6_scenario("BG4").simulate()

    assert abs(model.validation.overall_error_kg_hr) < 1e-6
    assert max(abs(value) for value in model.validation.component_errors_kg_hr.values()) < 1e-6


def test_psa_adsorbent_capacity():
    low_capacity = create_phase6_scenario(
        "BG4",
        parameter_overrides={
            "psa_working_capacity_kg_co2_per_kg_adsorbent": 0.05
        },
    ).simulate()
    high_capacity = create_phase6_scenario(
        "BG4",
        parameter_overrides={
            "psa_working_capacity_kg_co2_per_kg_adsorbent": 0.12
        },
    ).simulate()

    assert (
        low_capacity.units["A631"].adsorbent_inventory_kg
        > high_capacity.units["A631"].adsorbent_inventory_kg
        > 0.0
    )


def test_psa_purge_methane_accounting():
    low = create_phase6_scenario(
        "BG4",
        parameter_overrides={"psa_purge_fraction": 0.02},
    ).simulate()
    high = create_phase6_scenario(
        "BG4",
        parameter_overrides={"psa_purge_fraction": 0.08},
    ).simulate()

    assert high.streams["psa_purge_gas"].imass["Methane"] > low.streams["psa_purge_gas"].imass["Methane"]
    assert high.metrics["methane_recovery_fraction"] < low.metrics["methane_recovery_fraction"]
