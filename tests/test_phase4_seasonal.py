import pytest

from Greenhub.systems import simulate_phase4_season


def test_phase4_annual_totals_equal_monthly_sum():
    result = simulate_phase4_season("PR3", months=("January", "July"))
    monthly = sum(float(row["protein_product_kg"]) for row in result.monthly_rows)
    assert result.annual_totals["protein_product_kg"] == pytest.approx(monthly)
    assert len(result.monthly_rows) == 2
