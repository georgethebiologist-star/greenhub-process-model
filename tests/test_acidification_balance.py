import pytest


def test_acidification_mixer_closes_material(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["M401"]
    assert sum(stream.F_mass for stream in unit.ins) == pytest.approx(unit.outs[0].F_mass)
    assert unit.acid_demand.pure_acid_kg_hr > 0.0
