import pytest

from Greenhub.systems import simulate_phase3_season


def test_seasonal_aggregation_uses_month_specific_availability():
    result = simulate_phase3_season("F2", months=("January", "July"))
    assert len(result.monthly_rows) == 2
    assert result.monthly_rows[1]["wet_grass_mass_kg"] == pytest.approx(420000)
    assert result.annual_totals["wet_grass_mass_kg"] == pytest.approx(165000 + 420000)
    assert result.annual_totals["electricity_kwh"] > 0.0

