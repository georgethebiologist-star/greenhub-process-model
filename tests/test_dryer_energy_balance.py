import pytest

from Greenhub.phase4_specifications import calculate_dryer_energy


def test_thermodynamic_dryer_energy_uses_one_selected_method():
    result = calculate_dryer_energy(
        calculation_method="thermodynamic",
        inlet_water_kg_hr=20.0,
        dry_solids_kg_hr=10.0,
        evaporated_water_kg_hr=15.0,
        inlet_temperature_K=298.15,
        product_temperature_K=333.15,
        thermal_efficiency=0.7,
    )
    assert result.external_heat_kj_hr == pytest.approx(result.useful_heat_kj_hr / 0.7)
    assert result.latent_heat_kj_hr > 0.0


def test_zero_water_removal_at_constant_temperature_has_zero_duty():
    result = calculate_dryer_energy(
        calculation_method="thermodynamic",
        inlet_water_kg_hr=1.0,
        dry_solids_kg_hr=9.0,
        evaporated_water_kg_hr=0.0,
        inlet_temperature_K=298.15,
        product_temperature_K=298.15,
        thermal_efficiency=0.7,
    )
    assert result.external_heat_kw == 0.0
