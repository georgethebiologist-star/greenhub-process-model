import pytest

from Greenhub.reactions import buswell


@pytest.mark.parametrize("formula", ["C6H12O6", "C5H7O2N", "C5H7O2NS"])
def test_extended_buswell_closes_CHONS(formula):
    result = buswell(formula)
    assert result.methane >= 0.0
    assert result.carbon_dioxide >= 0.0
    assert max(abs(value) for value in result.atom_residuals.values()) < 1e-9
