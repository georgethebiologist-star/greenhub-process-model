import pytest

from Greenhub.phase4_specifications import solve_liquid_entrainment_for_cake_moisture


def test_separator_hits_wet_cake_moisture(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["C401"]
    cake = unit.outs[0]
    moisture = float(cake.imass["Water"]) / cake.F_mass
    assert moisture == pytest.approx(unit.parameters.cake_moisture_fraction)


def test_impossible_cake_moisture_raises():
    with pytest.raises(ValueError, match="more liquid than is available"):
        solve_liquid_entrainment_for_cake_moisture(
            fixed_cake_dry_solids_kg_hr=10.0,
            dissolved_solids_available_kg_hr=0.0,
            water_available_kg_hr=1.0,
            target_cake_moisture_fraction=0.9,
        )
