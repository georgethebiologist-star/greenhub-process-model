"""Select and re-evaluate 0..10 non-PEF BioSTEAM screening-front candidates.

Uses the saved backend batch and its exact configurations. The PR0 series is a
separate Pareto calculation over the 502 already simulated protein-bypass runs.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from Greenhub.application.decision_support_service import DecisionSupportService

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'biosteam_frontiers'
JOB_DIR=ROOT/'Greenhub/results/actual_pareto_2000/decision_batches'
JOB_ID=(JOB_DIR/'job.txt').read_text(encoding='utf-8').strip()
JOB=json.loads((JOB_DIR/f'{JOB_ID}.json').read_text(encoding='utf-8'))
assert JOB['status']=='completed' and len(JOB['samples'])==2000

def eligible(s):
    if s['status']!='evaluated':return False
    obj=s['outputs']['objectives'];return all(
        o.get('eligible') and isinstance(o.get('value'),(int,float)) and math.isfinite(o['value'])
        for o in (obj['operating_profit'],obj['climate']))

def xy(s):
    o=s['outputs']['objectives'];return o['operating_profit']['value'],o['climate']['value']

def frontier(samples):
    ordered=sorted((s for s in samples if eligible(s)),key=lambda s:(-xy(s)[0],xy(s)[1]))
    result=[];least=math.inf
    for s in ordered:
        climate=xy(s)[1]
        if climate<least:
            result.append(s);least=climate
    return result

def ranks(front,n=11):
    # Arc-length spacing on both objectives after normalization, with endpoints.
    assert len(front)>=n
    x=[xy(s)[0] for s in front];y=[xy(s)[1] for s in front]
    dx=max(x)-min(x) or 1;dy=max(y)-min(y) or 1
    cumulative=[0.0]
    for i in range(1,len(front)):
        cumulative.append(cumulative[-1]+math.hypot((x[i]-x[i-1])/dx,(y[i]-y[i-1])/dy))
    selected=[]
    for rank in range(n):
        target=cumulative[-1]*rank/(n-1)
        earliest=selected[-1]+1 if selected else 0
        latest=len(front)-(n-rank)
        options=range(earliest,latest+1)
        idx=min(options,key=lambda i:(abs(cumulative[i]-target),i))
        selected.append(idx)
    assert selected==sorted(selected)
    return [front[i] for i in selected]

all_samples=[s for s in JOB['samples'] if
             s['configuration']['simulation']['scenarios']['feed_preparation']=='F1']
groups={'all':all_samples,'protein_bypass':[s for s in all_samples if
         s['configuration']['simulation']['scenarios']['protein_recovery']=='PR0']}
OUT.mkdir(parents=True,exist_ok=True)
service=DecisionSupportService()
summary={'job_id':JOB_ID,'source_batch':str(JOB_DIR/f'{JOB_ID}.json'),
         'status':'Non-PEF (F1) BioSTEAM-evaluated process routes with screening TEA/LCA and candidate economic overlay',
         'feed_preparation_filter':'F1; PEF (F2) excluded before Pareto filtering',
         'rank_definition':'0 = highest annualized after-tax screening profit; 10 = lowest attributional climate load; intermediate ranks selected by normalized front arc length',
         'groups':{}}

for label,samples in groups.items():
    front=frontier(samples);chosen=ranks(front)
    group_dir=OUT/label;group_dir.mkdir(exist_ok=True)
    summary['groups'][label]={'eligible_count':sum(map(eligible,samples)),'front_count':len(front),
        'front':[{'sample_id':s['sample_id'],'profit_eur_y':xy(s)[0],'climate_kg_co2e_y':xy(s)[1]} for s in front],
        'ranks':[]}
    print(label,'eligible',sum(map(eligible,samples)),'front',len(front),flush=True)
    for rank,s in enumerate(chosen):
        dest=group_dir/f'rank_{rank:02d}.json'
        cached=json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else None
        if cached and cached['configuration']==s['configuration']:
            report=cached
        else:
            report=service.evaluate(s['configuration'])
            for objective in ('operating_profit','climate'):
                a=report['objectives'][objective]['value'];b=s['outputs']['objectives'][objective]['value']
                assert math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-5),(label,rank,objective,a,b)
            dest.write_text(json.dumps(report,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        row={'rank':rank,'sample_id':s['sample_id'],'source_sample_id':s.get('source_sample_id'),
             'run_id':report['run_id'],'report':str(dest),'configuration':s['configuration']['simulation']['scenarios'],
             'feed_rate_kg_h':s['configuration']['simulation']['wet_feed_rate_kg_hr'],
             'profit_eur_y':xy(s)[0],'climate_kg_co2e_y':xy(s)[1]}
        summary['groups'][label]['ranks'].append(row)
        print(label,rank,s['sample_id'],round(xy(s)[0]),round(xy(s)[1]),flush=True)
    (OUT/'selection_manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('Saved 22 full re-evaluated reports and selection_manifest.json')
