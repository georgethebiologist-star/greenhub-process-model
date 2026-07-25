import pytest


def test_digestate_is_nonnegative_and_persistent_pools_are_conserved(
    representative_phase5_reactor,
    representative_phase5_separator,
):
    digestate = representative_phase5_separator.outs[1]
    assert digestate.F_mass > 0.0
    assert all(float(digestate.imass[ID]) >= 0.0 for ID in digestate.chemicals.IDs)
    for ID in ("HeavyMetals", "PersistentOrganics", "Pesticides", "Microplastics", "PathogenIndicators"):
        assert digestate.imass[ID] == pytest.approx(representative_phase5_reactor.ins[0].imass[ID])
