import pytest

from Greenhub.equilibria import phosphate_speciation


def test_phosphate_fractions_sum_to_one():
    fractions = phosphate_speciation(7.2)
    assert sum(fractions.values()) == pytest.approx(1.0)
    assert fractions["H2PO4-"] > 0.4
    assert fractions["HPO4-2"] > 0.4
