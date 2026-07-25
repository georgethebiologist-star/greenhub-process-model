"""Monthly aggregation and peak sizing tests for Phase 7."""

from __future__ import annotations

from Greenhub.phase7_metrics import aggregate_monthly_phase7_metrics
from Greenhub.systems import create_phase7_scenario


def test_phase7_monthly_aggregation():
    june = create_phase7_scenario("NR4", selected_month="June").simulate()
    july = create_phase7_scenario("NR4", selected_month="July").simulate()
    result = aggregate_monthly_phase7_metrics([june, july])
    assert len(result.monthly_rows) == 2
    assert result.annual_totals["digestate_processed_kg"] > 0.0
    assert result.annual_totals["ammonium_product_kg"] > 0.0


def test_phase7_peak_sizing_from_months():
    june = create_phase7_scenario("NR7", selected_month="June").simulate()
    july = create_phase7_scenario("NR7", selected_month="July").simulate()
    result = aggregate_monthly_phase7_metrics([june, july])
    design_values = [
        value for key, value in result.peak_design.items() if key.endswith("_design")
    ]
    assert design_values
    assert all(value >= 0.0 for value in design_values)
