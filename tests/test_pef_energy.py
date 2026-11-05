import pytest

from Greenhub.systems import create_phase3_scenario


def test_pef_power_uses_wet_throughput_times_specific_energy():
    with pytest.raises(ValueError, match="retired|disabled"):
        create_phase3_scenario("F2")

