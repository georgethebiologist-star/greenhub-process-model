"""Re-evaluate full-front ranks with only protein recovery switched to PR0."""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from Greenhub.application.decision_support_service import DecisionSupportService

OUT=Path(__file__).resolve().parent/'biosteam_frontiers'
SELECTION=json.loads((OUT/'selection_manifest.json').read_text(encoding='utf-8'))
BATCH=json.loads(Path(SELECTION['source_batch']).read_text(encoding='utf-8'))
SAMPLES={s['sample_id']:s for s in BATCH['samples']}
dest=OUT/'matched_protein_bypass';dest.mkdir(exist_ok=True)
service=DecisionSupportService();pairs=[]
for selected in SELECTION['groups']['all']['ranks']:
    rank=selected['rank'];original=json.loads(Path(selected['report']).read_text(encoding='utf-8'))
    config=deepcopy(SAMPLES[selected['sample_id']]['configuration'])
    original_route=config['simulation']['scenarios']['protein_recovery']
    config['simulation']['scenarios']['protein_recovery']='PR0'
    path=dest/f'rank_{rank:02d}.json'
    cached=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
    report=cached if cached and cached['configuration']==config and cached['objectives']['climate']['eligible'] else service.evaluate(config)
    if report is not cached:path.write_text(json.dumps(report,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    assert report['configuration']['simulation']['scenarios']['protein_recovery']=='PR0'
    pair={'rank':rank,'source_sample_id':selected['sample_id'],'original_protein_route':original_route,
          'original_report':selected['report'],'matched_report':str(path),
          'original_profit_eur_y':original['objectives']['operating_profit']['value'],
          'matched_profit_eur_y':report['objectives']['operating_profit']['value'],
          'original_climate_kg_co2e_y':original['objectives']['climate']['value'],
          'matched_climate_kg_co2e_y':report['objectives']['climate']['value'],
          'feed_rate_kg_h':config['simulation']['wet_feed_rate_kg_hr'],
          'same_economic_assumptions':config['candidate_economics']==original['configuration']['candidate_economics'],
          'eligible_for_ranking':report['feasibility']['eligible_for_ranking']}
    pairs.append(pair)
    print(rank,original_route,'-> PR0',round(pair['matched_profit_eur_y']),round(pair['matched_climate_kg_co2e_y']),flush=True)
(OUT/'matched_protein_bypass_manifest.json').write_text(json.dumps({
    'method':'For each full-front rank, change only simulation.scenarios.protein_recovery to PR0; rerun BioSTEAM/TEA/LCA with identical feed and candidate economics',
    'pairs':pairs},indent=2),encoding='utf-8')
print('Saved',len(pairs),'matched PR0 reports')
