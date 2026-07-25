import pytest

from Greenhub.phase5_specifications import NORMAL_M3_PER_KMOL, normal_volume_m3


def test_normal_gas_volume_uses_declared_conditions():
    assert normal_volume_m3(1.0) == pytest.approx(NORMAL_M3_PER_KMOL)
    assert normal_volume_m3(0.0) == 0.0
    with pytest.raises(ValueError):
        normal_volume_m3(-1.0)
