import pytest

from Greenhub.phase5_metrics import aggregate_monthly_phase5_metrics


def test_seasonal_quantities_use_month_specific_hours(simulated_phase5_ad1):
    result = aggregate_monthly_phase5_metrics([simulated_phase5_ad1])
    assert len(result.monthly_rows) == 1
    assert result.annual_totals["methane_nm3"] == pytest.approx(
        sum(float(row["methane_nm3"]) for row in result.monthly_rows)
    )
    assert result.peak_design["month"] == simulated_phase5_ad1.input_bundle.selected_month
    assert result.peak_design["working_volume_m3"] == max(
        float(row["working_volume_m3"]) for row in result.monthly_rows
    )
