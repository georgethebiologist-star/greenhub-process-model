import pytest

from Greenhub.phase4_specifications import calculate_stoichiometric_base_demand


def test_hcl_naoh_demand_identifies_sodium_chloride():
    result = calculate_stoichiometric_base_demand(
        acid_type="HydrochloricAcid",
        base_type="SodiumHydroxide",
        acid_kg_hr=1.0,
        base_solution_mass_fraction=0.5,
        base_purity=1.0,
    )
    assert result.salt_type == "SodiumChloride"
    assert result.base_solution_kg_hr == pytest.approx(2.0 * result.pure_base_kg_hr)


def test_baseline_sodium_and_chloride_elements_close(simulated_phase4_pr3):
    errors = simulated_phase4_pr3.validation.element_errors_kg_hr
    assert abs(errors["sodium"]) < 1e-6
    assert abs(errors["chloride"]) < 1e-6
