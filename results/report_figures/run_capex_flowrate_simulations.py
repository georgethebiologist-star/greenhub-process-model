"""Run the F1/no-PEF BioSTEAM model at the CAPEX comparison flow rates."""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from Greenhub.application.decision_support_service import DecisionSupportService

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORT_DIR = OUT / 'capex_flow_runs'
REPORT_DIR.mkdir(parents=True, exist_ok=True)
base = json.loads((OUT / 'baseline_no_pef_screening.json').read_text(encoding='utf-8'))
assert base['configuration']['simulation']['scenarios']['feed_preparation'] == 'F1'
service = DecisionSupportService()

for flow in (500, 1000, 2000, 3000):
    target = REPORT_DIR / f'f1_{flow:04d}kg_h.json'
    cfg = deepcopy(base['configuration'])
    cfg['simulation']['wet_feed_rate_kg_hr'] = flow
    cfg['simulation']['plant_capacity_kg_hr'] = flow
    result = service.evaluate(cfg)
    if result['configuration']['simulation']['scenarios']['feed_preparation'] != 'F1':
        raise RuntimeError(f'Unexpected feed-preparation route at {flow} kg/h')
    target.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    print(f'Saved F1 {flow} kg/h: {result["run_id"]}')
