import pytest

from Greenhub.phase5_specifications import calculate_mixing_power


def test_mixing_power_respects_schedule_and_motor_efficiency():
    shaft, electrical = calculate_mixing_power(
        working_volume_m3=1000.0,
        specific_mixing_power_kw_m3=0.005,
        mixing_schedule_fraction=0.5,
        motor_efficiency=0.8,
    )
    assert shaft == pytest.approx(5.0)
    assert electrical == pytest.approx(3.125)
