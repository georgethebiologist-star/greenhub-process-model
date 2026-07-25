"""Phase 7 workbook, report, and limitation export tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from Greenhub.input_data import INPUT_WORKBOOK_PATH
from Greenhub.phase7_metrics import aggregate_monthly_phase7_metrics
from Greenhub.phase7_reporting import save_phase7_reports
from Greenhub.systems import create_phase7_scenario


def test_master_workbook_contains_phase7_controls():
    workbook = pd.ExcelFile(INPUT_WORKBOOK_PATH)
    assert "Phase7Parameters" in workbook.sheet_names
    control = pd.read_excel(INPUT_WORKBOOK_PATH, sheet_name="ModelControl")
    parameters = pd.read_excel(INPUT_WORKBOOK_PATH, sheet_name="Phase7Parameters")
    assert "selected_phase7_scenario" in set(control["parameter"])
    assert "selected_phase7_process_order" in set(control["parameter"])
    assert len(parameters) >= 100
    assert parameters["python_name"].is_unique


def test_phase7_reports_are_generated(tmp_path: Path):
    model = create_phase7_scenario("NR4").simulate()
    seasonal = aggregate_monthly_phase7_metrics([model])
    outputs = save_phase7_reports(
        model,
        flowsheet_path=tmp_path / "phase7_flowsheet.png",
        scenario_models=(model,),
        seasonal_result=seasonal,
        results_dir=tmp_path,
    )
    required = (
        "nutrient_recovery_report",
        "scenario_comparison",
        "limitations_and_data_needs",
        "phase7_mass_balance.csv",
        "phase7_product_quality.csv",
        "phase7_utility_summary.csv",
    )
    for name in required:
        assert outputs[name].exists()
    inactive = pd.read_csv(outputs["phase7_calcium_phosphate_report.csv"])
    assert inactive.loc[0, "status"] == "not active in selected scenario"


def test_phase7_report_has_required_sheets(tmp_path: Path):
    model = create_phase7_scenario("NR4").simulate()
    seasonal = aggregate_monthly_phase7_metrics([model])
    outputs = save_phase7_reports(
        model,
        flowsheet_path=tmp_path / "phase7_flowsheet.png",
        scenario_models=(model,),
        seasonal_result=seasonal,
        results_dir=tmp_path,
    )
    workbook = pd.ExcelFile(outputs["nutrient_recovery_report"])
    for sheet in (
        "Overview",
        "Scenario",
        "Digestate feed",
        "Separation",
        "Phosphorus recovery",
        "Ammonia recovery",
        "Products",
        "Utilities",
        "Mass balances",
        "Elemental balances",
        "Seasonal results",
        "Warnings",
        "Assumptions",
    ):
        assert sheet in workbook.sheet_names


def test_phase7_comparison_is_not_ranked(tmp_path: Path):
    model = create_phase7_scenario("NR4").simulate()
    seasonal = aggregate_monthly_phase7_metrics([model])
    outputs = save_phase7_reports(
        model,
        flowsheet_path=tmp_path / "phase7_flowsheet.png",
        scenario_models=(model,),
        seasonal_result=seasonal,
        results_dir=tmp_path,
    )
    comparison = pd.read_excel(outputs["scenario_comparison"], sheet_name="Engineering comparison")
    assert set(comparison["ranking_status"]) == {"not ranked"}
