import pytest

from Greenhub.phase5_specifications import calculate_digester_heat


def test_digester_heat_separates_feed_heating_and_vessel_loss():
    result = calculate_digester_heat(
        feed_mass_kg_hr=100.0,
        heat_capacity_kj_kg_k=4.0,
        feed_temperature_k=293.15,
        digester_temperature_k=308.15,
        ambient_temperature_k=283.15,
        insulation_u_value_w_m2_k=0.5,
        insulation_area_m2=100.0,
        feed_heating_efficiency=0.8,
    )
    assert result.feed_sensible_heat_kw == pytest.approx(100.0 * 4.0 * 15.0 / 3600.0)
    assert result.vessel_heat_loss_kw == pytest.approx(1.25)
    assert result.total_external_heat_kw == pytest.approx(
        result.feed_sensible_heat_kw / 0.8 + result.vessel_heat_loss_kw
    )
