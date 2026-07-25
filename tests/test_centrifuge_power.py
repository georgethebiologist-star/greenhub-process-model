import pytest

from Greenhub.systems import create_phase3_scenario


def test_centrifuge_power_uses_hydraulic_throughput():
    model = create_phase3_scenario("F2").simulate()
    unit = model.units["C301"]
    volume = sum(stream.F_mass for stream in unit.ins) / unit.parameters.feed_density_kg_m3
    expected = volume * unit.parameters.centrifuge_electricity_kwh_per_m3
    assert unit.power_utility.consumption == pytest.approx(expected)

