import pytest


def test_single_stage_wash_conserves_cake_and_wash_water(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["W401"]
    inlet = sum(stream.F_mass for stream in unit.ins)
    outlet = sum(stream.F_mass for stream in unit.outs)
    assert outlet == pytest.approx(inlet)
    assert unit.outs[1].F_mass > 0.0
    assert unit.ins[1].F_mass > 0.0
    assert sum(
        float(unit.outs[1].imass[ID])
        for ID in ("PrecipitatedProtein", "HeatCoagulatedProtein")
    ) > 0.0
