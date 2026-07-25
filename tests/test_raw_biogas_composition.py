import pytest

from Greenhub.component_groups import COMPONENT_GROUPS


def test_raw_biogas_wet_and_dry_composition(representative_phase5_separator):
    gas = representative_phase5_separator.outs[0]
    dry_kmol = sum(float(gas.imol[ID]) for ID in COMPONENT_GROUPS["biogas_components"])
    wet_kmol = dry_kmol + float(gas.imol["Water"])
    assert wet_kmol > dry_kmol > 0.0
    dry_sum = sum(
        float(gas.imol[ID]) / dry_kmol
        for ID in COMPONENT_GROUPS["biogas_components"]
    )
    assert dry_sum == pytest.approx(1.0)
    assert 0.0 < float(gas.imol["Water"]) / wet_kmol < 1.0
