import pytest

from Greenhub.phase5_specifications import ammonia_inhibition_factor


def test_ammonia_inhibition_is_disabled_without_invented_threshold():
    assert ammonia_inhibition_factor(100.0, enabled=False, inhibition_constant_kg_n_m3=None) == 1.0
    with pytest.raises(ValueError, match="requires an inhibition constant"):
        ammonia_inhibition_factor(1.0, enabled=True, inhibition_constant_kg_n_m3=None)
    assert 0.0 < ammonia_inhibition_factor(1.0, enabled=True, inhibition_constant_kg_n_m3=0.5) < 1.0
