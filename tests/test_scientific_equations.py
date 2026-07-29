import pytest

from Greenhub.scientific_equations import (
    EQUATION_REGISTRY,
    protein_precipitation_mass_balance,
)


def test_eq_mb_001_source_fraction_reproduction_and_conservation():
    result = protein_precipitation_mass_balance(1.0, 0.34)
    assert result.protein_cake_kg_hr == pytest.approx(0.34)
    assert result.protein_supernatant_kg_hr == pytest.approx(0.66)
    assert result.residual_kg_hr == pytest.approx(0.0, abs=1e-15)
    assert EQUATION_REGISTRY["EQ-MB-001"].readiness_state == "D4"


def test_eq_mb_001_trends_boundaries_and_invalid_inputs():
    low = protein_precipitation_mass_balance(2.0, 0.2)
    high = protein_precipitation_mass_balance(2.0, 0.8)
    assert high.protein_cake_kg_hr > low.protein_cake_kg_hr
    assert protein_precipitation_mass_balance(2.0, 0.0).protein_cake_kg_hr == 0.0
    assert protein_precipitation_mass_balance(2.0, 1.0).protein_supernatant_kg_hr == 0.0
    with pytest.raises(ValueError):
        protein_precipitation_mass_balance(-1.0, 0.5)
    with pytest.raises(ValueError):
        protein_precipitation_mass_balance(1.0, 1.01)
