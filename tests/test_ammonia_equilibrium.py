import pytest

from Greenhub.equilibria import ammonia_equilibrium


def test_unionized_ammonia_increases_with_ph():
    low = ammonia_equilibrium(100.0, 7.0, 298.15)
    high = ammonia_equilibrium(100.0, 10.0, 298.15)
    assert high.unionized_fraction > low.unionized_fraction
    assert low.ammonia_n + low.ammonium_n == pytest.approx(100.0)


def test_invalid_ph_raises():
    with pytest.raises(ValueError, match="pH"):
        ammonia_equilibrium(1.0, 15.0, 298.15)
