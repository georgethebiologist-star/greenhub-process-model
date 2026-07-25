import pytest

from Greenhub.systems import create_phase3_scenario


def test_pef_power_uses_wet_throughput_times_specific_energy():
    model = create_phase3_scenario("F2").simulate()
    unit = model.units["U201"]
    expected = unit.ins[0].F_mass / 1000.0 * unit.parameters.specific_energy_kwh_per_t_wet
    assert unit.power_utility.consumption == pytest.approx(expected)

