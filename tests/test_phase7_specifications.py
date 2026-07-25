"""Pure-equation and monotonic-trend tests for Phase 7."""

from __future__ import annotations

import pytest

from Greenhub.phase7_specifications import (
    acid_capture_extent,
    ammonia_stripping_fraction,
    calcium_phosphate_extent,
    ion_exchange_design,
    membrane_water_recovery,
    peak_sizing,
    struvite_extent,
)


def test_struvite_stoichiometric_limit():
    result = struvite_extent(
        magnesium_kmol_hr=2.0,
        ammonium_kmol_hr=2.0,
        phosphate_kmol_hr=2.0,
        target_phosphate_recovery_fraction=0.8,
    )
    assert result.product_kmol_hr == pytest.approx(1.6)
    assert result.magnesium_consumed_kmol_hr == pytest.approx(1.6)
    assert result.ammonium_consumed_kmol_hr == pytest.approx(1.6)
    assert result.phosphate_consumed_kmol_hr == pytest.approx(1.6)


def test_struvite_magnesium_limit():
    result = struvite_extent(
        magnesium_kmol_hr=0.2,
        ammonium_kmol_hr=1.0,
        phosphate_kmol_hr=1.0,
        target_phosphate_recovery_fraction=1.0,
    )
    assert result.product_kmol_hr == pytest.approx(0.2)
    assert result.limiting_reagent == "magnesium"


def test_struvite_phosphate_limit():
    result = struvite_extent(
        magnesium_kmol_hr=2.0,
        ammonium_kmol_hr=2.0,
        phosphate_kmol_hr=0.3,
        target_phosphate_recovery_fraction=1.0,
    )
    assert result.product_kmol_hr == pytest.approx(0.3)


def test_struvite_ammonium_limit():
    result = struvite_extent(
        magnesium_kmol_hr=2.0,
        ammonium_kmol_hr=0.4,
        phosphate_kmol_hr=1.0,
        target_phosphate_recovery_fraction=1.0,
    )
    assert result.product_kmol_hr == pytest.approx(0.4)
    assert result.limiting_reagent == "ammonium"


def test_calcium_phosphate_stoichiometry():
    result = calcium_phosphate_extent(
        product_id="CalciumPhosphate",
        calcium_kmol_hr=3.0,
        phosphate_kmol_hr=2.0,
        hydroxide_kmol_hr=0.0,
        target_phosphate_recovery_fraction=1.0,
    )
    assert result.product_kmol_hr == pytest.approx(1.0)
    assert result.calcium_consumed_kmol_hr == pytest.approx(3.0)
    assert result.phosphate_consumed_kmol_hr == pytest.approx(2.0)


def test_ammonia_fraction_increases_with_pH():
    low = ammonia_stripping_fraction(
        pH=8.0,
        temperature_k=333.15,
        pressure_pa=101325.0,
        gas_to_liquid_ratio=500.0,
        packing_height_m=6.0,
        transfer_coefficient=4.0,
    )
    high = ammonia_stripping_fraction(
        pH=11.0,
        temperature_k=333.15,
        pressure_pa=101325.0,
        gas_to_liquid_ratio=500.0,
        packing_height_m=6.0,
        transfer_coefficient=4.0,
    )
    assert high.free_ammonia_fraction > low.free_ammonia_fraction
    assert high.removal_fraction > low.removal_fraction


def test_ammonia_fraction_increases_with_temperature():
    cold = ammonia_stripping_fraction(
        pH=10.0,
        temperature_k=293.15,
        pressure_pa=101325.0,
        gas_to_liquid_ratio=500.0,
        packing_height_m=6.0,
        transfer_coefficient=4.0,
    )
    hot = ammonia_stripping_fraction(
        pH=10.0,
        temperature_k=353.15,
        pressure_pa=101325.0,
        gas_to_liquid_ratio=500.0,
        packing_height_m=6.0,
        transfer_coefficient=4.0,
    )
    assert hot.free_ammonia_fraction > cold.free_ammonia_fraction
    assert hot.removal_fraction > cold.removal_fraction


def test_ammonium_sulphate_stoichiometry():
    result = acid_capture_extent(
        acid_id="SulfuricAcid",
        ammonia_kmol_hr=2.0,
        acid_kmol_hr=1.0,
        absorber_efficiency=1.0,
    )
    assert result.product_id == "AmmoniumSulfate"
    assert result.product_kmol_hr == pytest.approx(1.0)
    assert result.ammonia_captured_kmol_hr == pytest.approx(2.0)


def test_ammonium_chloride_stoichiometry():
    result = acid_capture_extent(
        acid_id="HydrochloricAcid",
        ammonia_kmol_hr=1.0,
        acid_kmol_hr=1.0,
        absorber_efficiency=1.0,
    )
    assert result.product_id == "AmmoniumChloride"
    assert result.product_kmol_hr == pytest.approx(1.0)


def test_acid_capture_cannot_exceed_ammonia():
    result = acid_capture_extent(
        acid_id="SulfuricAcid",
        ammonia_kmol_hr=0.5,
        acid_kmol_hr=10.0,
        absorber_efficiency=1.0,
    )
    assert result.ammonia_captured_kmol_hr == pytest.approx(0.5)


def test_ion_exchange_capacity():
    result = ion_exchange_design(
        ammonium_feed_kg_hr=1.0,
        recovery_fraction=0.8,
        capacity_kg_nh4_per_kg_media=0.04,
        breakthrough_fraction=0.5,
        service_time_h=10.0,
        bed_bulk_density_kg_m3=700.0,
        nacl_molar_ratio=1.2,
    )
    assert result.recovered_ammonium_kg_hr == pytest.approx(0.8)
    assert result.bed_media_kg == pytest.approx(400.0)
    assert result.bed_volume_m3 == pytest.approx(400.0 / 700.0)


def test_membrane_water_recovery_increases_with_pressure():
    low = membrane_water_recovery(
        feed_water_kg_hr=100.0,
        applied_pressure_bar=10.0,
        osmotic_pressure_bar=5.0,
        reference_net_pressure_bar=15.0,
        reference_water_recovery_fraction=0.6,
        water_flux_l_m2_hr=20.0,
    )
    high = membrane_water_recovery(
        feed_water_kg_hr=100.0,
        applied_pressure_bar=20.0,
        osmotic_pressure_bar=5.0,
        reference_net_pressure_bar=15.0,
        reference_water_recovery_fraction=0.6,
        water_flux_l_m2_hr=20.0,
    )
    assert high.water_recovery_fraction > low.water_recovery_fraction
    assert high.membrane_area_m2 > low.membrane_area_m2


def test_phase7_peak_sizing():
    result = peak_sizing([2.0, 4.0, 1.0], safety_factor=1.2)
    assert result.peak_value == pytest.approx(4.0)
    assert result.design_value == pytest.approx(4.8)
    assert result.minimum_turndown_fraction == pytest.approx(0.25)
