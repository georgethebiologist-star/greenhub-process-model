import pytest

from Greenhub.phase4_validation import PROTEIN_POOL_IDS


def test_precipitation_redistributes_but_does_not_create_protein(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["R401"]
    inlet = sum(float(unit.ins[0].imass[ID]) for ID in PROTEIN_POOL_IDS)
    outlet = sum(float(unit.outs[0].imass[ID]) for ID in PROTEIN_POOL_IDS)
    assert outlet == pytest.approx(inlet)
