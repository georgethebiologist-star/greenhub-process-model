import pytest

from Greenhub.phase4_specifications import calculate_acid_demand


def test_commercial_acid_solution_includes_reagent_water():
    result = calculate_acid_demand(
        method="empirical_dose",
        acid_type="HydrochloricAcid",
        liquid_flow_m3_hr=1.0,
        initial_pH=6.5,
        target_pH=4.5,
        acid_solution_mass_fraction=0.25,
        acid_purity=0.8,
        empirical_dose_kg_per_m3=2.0,
    )
    assert result.acid_solution_kg_hr == pytest.approx(10.0)
    assert result.reagent_water_kg_hr == pytest.approx(8.0)
