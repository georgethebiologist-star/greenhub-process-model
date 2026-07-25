from Greenhub.phase4_metrics import aggregate_monthly_phase4_metrics
from Greenhub.phase4_reporting import save_phase4_reports


def test_phase4_reports_are_generated(tmp_path, simulated_phase4_pr3):
    model = simulated_phase4_pr3
    seasonal = aggregate_monthly_phase4_metrics([model])
    outputs = save_phase4_reports(
        model,
        flowsheet_path=tmp_path / "phase4_flowsheet.png",
        scenario_models=(model,),
        seasonal_result=seasonal,
        results_dir=tmp_path,
    )
    required = {
        "phase4_protein_recovery_report.xlsx",
        "phase4_scenario_comparison.xlsx",
        "phase4_mass_balance.csv",
        "dryer_energy_balance.csv",
        "phase4_data_gaps.csv",
    }
    assert required <= {path.name for path in outputs.values() if path.exists()}
