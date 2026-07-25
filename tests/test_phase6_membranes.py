"""Transport, balance, and recycle tests for BG3 membranes."""

import pytest

from Greenhub.chemicals import chemicals
from Greenhub.systems import create_phase6_scenario


def test_membrane_single_stage_balance():
    model = create_phase6_scenario(
        "BG3",
        parameter_overrides={
            "membrane_number_of_stages": 1,
            "membrane_recycle_fraction": 0.0,
        },
    ).simulate()
    stage = model.units["M621"]

    for component_id in chemicals.IDs:
        assert stage.ins[0].imol[component_id] == pytest.approx(
            stage.outs[0].imol[component_id] + stage.outs[1].imol[component_id],
            abs=1e-12,
        )


def test_membrane_stage_cut():
    model = create_phase6_scenario("BG3").simulate()

    for unit_id in ("M621", "M622"):
        stage_cut = model.units[unit_id].calculation.stage_cut
        assert 0.0 <= stage_cut <= 1.0


def test_membrane_area_response():
    low = create_phase6_scenario(
        "BG3",
        parameter_overrides={"membrane_area_stage1_m2": 0.01},
    ).simulate()
    high = create_phase6_scenario(
        "BG3",
        parameter_overrides={"membrane_area_stage1_m2": 0.04},
    ).simulate()

    assert high.metrics["co2_removal_fraction"] >= low.metrics["co2_removal_fraction"]


def test_membrane_recycle_convergence():
    model = create_phase6_scenario(
        "BG3",
        parameter_overrides={"membrane_recycle_fraction": 0.5},
    ).simulate()

    assert model.streams["membrane_permeate_recycle"].F_mass > 0.0
    assert model.system.subsystems[0]._mol_error < 1e-8
    assert abs(model.validation.overall_error_kg_hr) < 1e-6
