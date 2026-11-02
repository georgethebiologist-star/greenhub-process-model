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
JOB=ROOT/'Greenhub/results/actual_pareto_2000/decision_batches'
BATCH=json.loads((JOB/((JOB/'job.txt').read_text(encoding='utf-8').strip()+'.json')).read_text(encoding='utf-8'))
EXAMPLE=next(s for s in BATCH['samples'] if
             s['configuration']['simulation']['scenarios']['feed_preparation']=='F1')
config=deepcopy(SOURCE['configuration'])
config['financial_assumptions']['use_screening_price_benchmarks']=True
config['candidate_economics']={**EXAMPLE['configuration']['candidate_economics'],
    **{k:0 for k in ('labour_reduction','logistics_reduction','energy_reduction',
                    'protein_yield_uplift','nutrient_recovery_uplift','subsidy_rate')}}
config['candidate_economics']['subsidy_cap_eur']=0
assert config['simulation']==SOURCE['configuration']['simulation']
dest=OUT/'baseline_no_pef_screening.json'
cached=json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else None
report=cached if cached and cached['configuration']==config else DecisionSupportService().evaluate(config)
assert report['configuration']['simulation']['scenarios']['feed_preparation']=='F1'
dest.write_text(json.dumps(report,ensure_ascii=False,allow_nan=False),encoding='utf-8')
print('Saved F1 baseline screening report',report['run_id'])
