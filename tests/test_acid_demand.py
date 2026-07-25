import pytest

from Greenhub.phase4_specifications import calculate_acid_demand


def test_empirical_acid_demand_uses_liquid_volume():
    result = calculate_acid_demand(
        method="empirical_dose",
        acid_type="HydrochloricAcid",
        liquid_flow_m3_hr=2.0,
        initial_pH=6.5,
        target_pH=4.5,
        acid_solution_mass_fraction=0.32,
        acid_purity=1.0,
        empirical_dose_kg_per_m3=1.5,
    )
    assert result.pure_acid_kg_hr == pytest.approx(3.0)
    assert result.pure_acid_dose_kg_m3 == pytest.approx(1.5)


def test_no_pH_change_requires_no_acid():
    result = calculate_acid_demand(
        method="empirical_dose",
        acid_type="HydrochloricAcid",
        liquid_flow_m3_hr=2.0,
        initial_pH=6.5,
        target_pH=6.5,
        acid_solution_mass_fraction=0.32,
        acid_purity=1.0,
        empirical_dose_kg_per_m3=1.5,
    )
    assert result.pure_acid_kg_hr == 0.0
    assert result.acid_solution_kg_hr == 0.0


def test_acidification_rejects_target_above_feed_pH():
    with pytest.raises(ValueError, match="exceeds inlet pH"):
        calculate_acid_demand(
            method="empirical_dose",
            acid_type="HydrochloricAcid",
            liquid_flow_m3_hr=1.0,
            initial_pH=6.0,
            target_pH=7.0,
            acid_solution_mass_fraction=0.32,
            acid_purity=1.0,
            empirical_dose_kg_per_m3=1.0,
        )
