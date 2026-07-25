from Greenhub.phase3_metrics import aggregate_monthly_metrics
from Greenhub.phase3_reporting import save_phase3_reports
from Greenhub.systems import create_phase3_scenario


def test_phase3_reports_are_generated(tmp_path):
    model = create_phase3_scenario("F2").simulate()
    seasonal = aggregate_monthly_metrics([model])
    outputs = save_phase3_reports(
        model,
        flowsheet_path=tmp_path / "not_generated.png",
        scenario_models=(model,),
        seasonal_result=seasonal,
        results_dir=tmp_path,
    )
    required = {
        "phase3_monthly_results.csv",
        "phase3_mass_balance.csv",
        "phase3_elemental_balance.csv",
        "phase3_energy_summary.csv",
        "scenario_comparison",
        "front_end_report",
    }
    assert required <= set(outputs)
    assert all(outputs[name].exists() for name in required)

