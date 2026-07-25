import subprocess
import sys


def test_phase5_reports_are_written(tmp_path):
    script = f"""
from pathlib import Path
from Greenhub.phase5_metrics import aggregate_monthly_phase5_metrics
from Greenhub.phase5_reporting import save_phase5_reports
from Greenhub.systems import create_phase5_scenario
output = Path(r'{tmp_path}')
model = create_phase5_scenario('AD1').simulate()
seasonal = aggregate_monthly_phase5_metrics([model])
save_phase5_reports(
    model,
    flowsheet_path=output / 'not_generated.png',
    scenario_models=(model,),
    seasonal_result=seasonal,
    results_dir=output,
)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    required = {
        "phase5_anaerobic_digestion_report.xlsx",
        "phase5_scenario_comparison.xlsx",
        "phase5_limitations_and_data_needs.xlsx",
        "digester_feed_characterization.csv",
        "raw_biogas_composition.csv",
        "digestate_composition.csv",
        "phase5_mass_balance.csv",
        "phase5_COD_balance.csv",
        "model_limitations.csv",
    }
    assert required.issubset({path.name for path in tmp_path.iterdir()})
