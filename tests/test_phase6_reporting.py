"""Artifact tests for the Phase 6 selected and comparison reports."""

import pandas as pd

from Greenhub.phase6_reporting import save_phase6_reports
from Greenhub.systems import create_phase6_scenario


def test_phase6_reporting(tmp_path):
    model = create_phase6_scenario("BG2").simulate()
    outputs = save_phase6_reports(
        model,
        flowsheet_path=tmp_path / "diagram_not_generated.png",
        scenario_models=(model,),
        results_dir=tmp_path,
    )

    assert outputs["biomethane_upgrading_report"].exists()
    assert outputs["upgrading_comparison"].exists()
    assert outputs["limitations_and_data_needs"].exists()
    assert (tmp_path / "phase6_mass_balance.csv").exists()
    comparison = pd.read_excel(
        outputs["upgrading_comparison"],
        sheet_name="Engineering comparison",
    )
    assert comparison.loc[0, "ranking_status"] == "not ranked"
    assert comparison.loc[0, "input_quality_class"] == "E structural baseline"
