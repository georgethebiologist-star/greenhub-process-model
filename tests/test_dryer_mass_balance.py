import pytest

from Greenhub.phase4_specifications import solve_dryer_mass_balance


def test_dryer_mass_equation_closes():
    result = solve_dryer_mass_balance(
        inlet_dry_matter_kg_hr=10.0,
        inlet_water_kg_hr=20.0,
        target_product_moisture_fraction=0.1,
    )
    assert result.target_product_mass_kg_hr + result.evaporated_water_kg_hr == pytest.approx(30.0)
    assert result.product_moisture_fraction == pytest.approx(0.1)


def test_impossible_dryer_moisture_above_inlet_raises():
    with pytest.raises(ValueError, match="exceeds inlet cake moisture"):
        solve_dryer_mass_balance(
            inlet_dry_matter_kg_hr=90.0,
            inlet_water_kg_hr=10.0,
            target_product_moisture_fraction=0.2,
        )
