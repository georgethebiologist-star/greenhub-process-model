"""Evaluate paired no-PEF baseline routes and attach them to the latest Pareto fronts."""
from __future__ import annotations
from copy import deepcopy
import json, math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from Greenhub.application.decision_support_service import DecisionSupportService
import scripts.run_rvo_pareto_analysis as runner
ROOT,SOURCE,OUT=runner.ROOT,runner.SOURCE,runner.OUT
GRANT_AWARDER,SUPPORT_SCENARIOS=runner.GRANT_AWARDER,runner.SUPPORT_SCENARIOS
FINANCIAL_BASIS,CARBON_BASIS,LCA_BASIS=runner.FINANCIAL_BASIS,runner.CARBON_BASIS,runner.LCA_BASIS
_evaluate,_pareto,_select_ranked,_select_3d_ranked=runner._evaluate,runner._pareto,runner._select_ranked,runner._select_3d_ranked

def main():
    runner.SERVICE=DecisionSupportService()
    base=json.loads(SOURCE.read_text(encoding='utf-8'))['configuration']
    groups={}
    for group,protein in [('protein_enabled',base['simulation']['scenarios']['protein_recovery']),('protein_bypass','PR0')]:
        case_id='C0';support=SUPPORT_SCENARIOS[case_id]
        config=deepcopy(base);scenarios=config['simulation']['scenarios'];scenarios['feed_preparation']='F1';scenarios['protein_recovery']=protein
        config['simulation']['request_id']=f'rvo_pareto_baseline_{group}_{case_id}'
        config['project_basis']['screening_estimates']=True;config['use_screening_process_assumptions']=True;config['use_screening_lca_factors']=True
        config['financial_assumptions']['use_screening_price_benchmarks']=True;config['lca']=deepcopy(LCA_BASIS)
        config['candidate_economics']={
            'tax_rate':0.0,'project_lifetime_years':FINANCIAL_BASIS['project_lifetime_years'],'discount_rate':FINANCIAL_BASIS['discount_rate'],'opex_support_years':FINANCIAL_BASIS['opex_support_years'],
            'soil_carbon_retention_fraction':CARBON_BASIS['soil_carbon_retention_fraction'],'furniture_carbon_retention_fraction':1.0,
            'grant_scenario_id':case_id,'grant_scenario_name':support['name'],'grant_awarding_organization':'None (zero CAPEX grant)',
            'operating_support_scenario_name':support['name'],'operating_support_awarding_organization':GRANT_AWARDER,
            'capex_grant_fraction':0.0,'opex_premium_eur_per_t_feed':0.0}
        item={'sample_id':f'baseline_reference_{group}_{case_id}','group':group,'design_id':f'baseline_reference_{group}','support_case':case_id,'configuration':config}
        base_row=_evaluate(item)
        cases=runner._paired_support_rows(base_row)
        for row in cases: row['baseline_reference']=True
        groups[group]=cases
        print(group,'paired baseline routes',base_row['status'],flush=True)
    manifest_path=OUT/'rvo_pareto_manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    for group,cases in groups.items():
        batch=manifest['groups_payload'][group];rows=batch['samples']
        rows=[r for r in rows if not r.get('baseline_reference')]+cases
        rows.sort(key=lambda r:r['sample_id']);batch['samples']=rows;batch['baseline_references']=[r['sample_id'] for r in cases]
        batch['sample_count']=len(rows);batch['evaluated_count']=sum(r.get('status')=='evaluated' for r in rows);batch['rejected_count']=sum(r.get('status')!='evaluated' for r in rows)
        primary=_pareto(rows,('net_carbon','npv'));subsidy=_pareto(rows,('subsidy_granted','npv'));three=_pareto(rows,('net_carbon','npv','subsidy_granted'))
        batch['fronts']['net_carbon_vs_npv']=primary;batch['fronts']['subsidy_vs_npv']=subsidy;batch['fronts']['net_carbon_npv_subsidy']=three
        batch['fronts']['by_support_case']={cid:_pareto([r for r in rows if r.get('support_case')==cid],('net_carbon','npv')) for cid in SUPPORT_SCENARIOS}
        batch['selected_candidates']['net_carbon_vs_npv']=_select_3d_ranked(three,rows,11)
        batch['selected_candidates']['net_carbon_npv_subsidy']=batch['selected_candidates']['net_carbon_vs_npv']
        batch['selected_candidates']['subsidy_vs_npv']=_select_ranked(subsidy,rows,11,True)
        for cid,front in batch['fronts']['by_support_case'].items():batch['selected_candidates'][f'net_carbon_vs_npv_{cid}']=_select_ranked(front,[r for r in rows if r.get('support_case')==cid],11,True)
        manifest['groups'][group].update({'sample_count':batch['sample_count'],'evaluated_count':batch['evaluated_count'],'rejected_count':batch['rejected_count'],
            'front_counts':{name:len(front.get('points',[])) for name,front in batch['fronts'].items() if name!='by_support_case'},
            'support_front_counts':{case:len(front.get('points',[])) for case,front in batch['fronts']['by_support_case'].items()}})
        (OUT/f'{group}_batch.json').write_text(json.dumps(batch,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    encoded=json.dumps(manifest,ensure_ascii=False,allow_nan=False)
    manifest_path.write_text(encoded,encoding='utf-8');(OUT/'latest.json').write_text(encoded,encoding='utf-8')
    print('Updated Pareto batches with explicit baseline references.')

if __name__=='__main__':main()
