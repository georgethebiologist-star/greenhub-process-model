"""Evaluate the saved F1 reference process with an explicit price-only screen.

Process settings come from no_pef_F1.json. Candidate savings and subsidy are
set to zero; benchmark prices are enabled only for the figure financial page.
"""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from Greenhub.application.decision_support_service import DecisionSupportService

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SOURCE=json.loads((OUT/'no_pef_F1.json').read_text(encoding='utf-8'))
config=deepcopy(SOURCE['configuration'])
config['financial_assumptions']['use_screening_price_benchmarks']=True
config['project_basis']['screening_estimates']=True
config['candidate_economics']={**config.get('candidate_economics',{}),
    'capex_grant_fraction':0,
    'tax_rate':0.258,'project_lifetime_years':20,'discount_rate':0.08}
assert config['simulation']==SOURCE['configuration']['simulation']
dest=OUT/'baseline_no_pef_screening.json'
report=DecisionSupportService().evaluate(config)
assert report['configuration']['simulation']['scenarios']['feed_preparation']=='F1'
dest.write_text(json.dumps(report,ensure_ascii=False,allow_nan=False),encoding='utf-8')
print('Saved F1 baseline screening report',report['run_id'])
