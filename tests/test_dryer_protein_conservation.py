from dataclasses import replace

import biosteam as bst
import pytest

from Greenhub.phase4_units import ProteinDryer
from Greenhub.phase4_validation import PROTEIN_POOL_IDS


def test_dryer_routes_all_protein_to_product_or_exhaust(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["DR401"]
    inlet = sum(float(unit.ins[0].imass[ID]) for ID in PROTEIN_POOL_IDS)
    outlet = sum(
        float(stream.imass[ID])
        for stream in unit.outs
        for ID in PROTEIN_POOL_IDS
    )
    assert outlet == pytest.approx(inlet)


def test_dryer_dust_is_routed_and_baseline_degradation_is_disabled(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["DR401"]
    assert unit.outs[1].F_mass - float(unit.outs[1].imass["Water"]) > 0.0
    assert sum(unit.transfers_kg_hr.values()) == 0.0


def test_enabled_thermal_degradation_changes_pool_without_losing_protein(simulated_phase4_pr3):
    parameters = replace(
        simulated_phase4_pr3.parameters["drying"],
        thermal_protein_degradation_fraction=0.2,
        dust_loss_fraction=0.0,
        protein_entrainment_loss_fraction=0.0,
    )
    feed = bst.Stream(
        "degradation_test_cake",
        Water=10.0,
        PrecipitatedProtein=10.0,
        units="kg/hr",
    )
    unit = ProteinDryer(
        "DR499",
        ins=feed,
        outs=("degradation_product", "degradation_exhaust"),
        parameters=parameters,
    )
    unit.simulate()
    assert unit.outs[0].imass["DegradedProtein"] == pytest.approx(2.0)
    assert sum(float(unit.outs[0].imass[ID]) for ID in PROTEIN_POOL_IDS) == pytest.approx(10.0)
