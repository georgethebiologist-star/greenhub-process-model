import pytest


def test_dewatering_reaches_target_dryer_feed_solids(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["D401"]
    cake = unit.outs[0]
    solids = (cake.F_mass - float(cake.imass["Water"])) / cake.F_mass
    assert solids == pytest.approx(unit.parameters.target_solids_fraction)
    assert sum(stream.F_mass for stream in unit.outs) == pytest.approx(unit.ins[0].F_mass)
