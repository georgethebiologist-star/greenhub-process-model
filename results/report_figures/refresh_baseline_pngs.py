"""Refresh the six existing baseline composite PNGs from the current F1 run.

Graph functions and styling are reused verbatim from the figure generator.
"""
import csv
import json
from pathlib import Path
from results.report_figures import generate_dense_candidate_pngs as figures

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results' / 'report_figures'
report = json.loads((OUT / 'baseline_no_pef_screening.json').read_text(encoding='utf-8'))
assert report['configuration']['simulation']['scenarios']['feed_preparation'] == 'F1'
streams = figures.streams(report)
folder = '01_baseline/combined'
scenario = f"F1 PR3 AD1 BG2 NR4 A baseline; {report['run_id']}; screening CAPEX updated; PEF disabled"
figures.INDEX.clear()
figures.flow_map('baseline', 0, report, streams, folder, scenario)
figures.material_dashboard(report, streams, folder, scenario)
figures.energy_dashboard(report, folder, scenario)
figures.finance_dashboard(report, folder, scenario)
figures.projection_dashboard(report, folder, scenario)
figures.quality_dashboard(report, folder, scenario)
fields = ['figure', 'description', 'source_dataset', 'scenario', 'units', 'file_location', 'notes']
new = figures.INDEX
for name in ['figure_index.csv', 'dense_figure_index.csv', 'biosteam_figure_index.csv']:
    path = OUT / name
    prior = list(csv.DictReader(path.open(encoding='utf-8-sig', newline=''))) if path.exists() else []
    replace_names = {row['figure'] for row in new}
    kept = [row for row in prior if row.get('figure') not in replace_names]
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept + new)
print(f"Refreshed {len(new)} baseline PNGs from {report['run_id']}")
