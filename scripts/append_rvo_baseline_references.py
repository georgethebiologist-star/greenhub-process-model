"""Evaluate paired no-PEF baseline routes and attach them to the latest Pareto fronts."""
from __future__ import annotations
from copy import deepcopy
import json, math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.pareto_reporting import write_pareto_ui_projection
import scripts.run_rvo_pareto_analysis as runner
ROOT,SOURCE,OUT=runner.ROOT,runner.SOURCE,runner.OUT
GRANT_AWARDER,SUPPORT_SCENARIOS=runner.GRANT_AWARDER,runner.SUPPORT_SCENARIOS
FINANCIAL_BASIS,CARBON_BASIS,LCA_BASIS=runner.FINANCIAL_BASIS,runner.CARBON_BASIS,runner.LCA_BASIS
_evaluate,_pareto,_select_ranked,_select_3d_ranked=runner._evaluate,runner._pareto,runner._select_ranked,runner._select_3d_ranked
UI_CANDIDATE_COUNT=runner.UI_CANDIDATE_COUNT

def _atomic_write_json(target, payload):
    runner._atomic_json_write(target,payload)

def main():
    runner.SERVICE=DecisionSupportService()
    base=json.loads(SOURCE.read_text(encoding='utf-8'))['configuration']
    groups={}
    for group,protein in [('protein_enabled',base['simulation']['scenarios']['protein_recovery']),('protein_bypass','PR0')]:
        batch_path=OUT/f'{group}_batch.json'
        if batch_path.exists():
            existing_batch=json.loads(batch_path.read_text(encoding='utf-8'))
            existing_cases=[r for r in existing_batch.get('samples',[]) if r.get('baseline_reference') and r.get('status')=='evaluated']
            if len(existing_cases)==len(runner.SUPPORT_CASE_IDS):
                groups[group]=existing_cases
                print(group,'reusing',len(existing_cases),'validated baseline overlay rows',flush=True)
                continue
        case_id='C0';support=SUPPORT_SCENARIOS[case_id]
        config=deepcopy(base);scenarios=config['simulation']['scenarios'];scenarios['feed_preparation']='F1';scenarios['protein_recovery']=protein
        config['simulation']['request_id']=f'rvo_pareto_baseline_{group}_{case_id}'
        config['project_basis']['screening_estimates']=True;config['use_screening_process_assumptions']=False;config['use_screening_lca_factors']=True
        config['financial_assumptions']['use_screening_price_benchmarks']=True;config['lca']=deepcopy(LCA_BASIS)
        config['financial_assumptions']['product_prices']={key:{'value_eur_per_unit':value,'unit':runner.ECONOMIC_DEFAULTS['product_prices'][key]['unit'],'source_status':'user_screening_override','basis':'Same explicit UI Configure > Economics screening price input.'} for key,value in runner.UI_PRODUCT_PRICES.items()}
        config['tea']={**config.get('tea',{}),'staffing_people':runner.UI_FINANCE['staffingPeople'],'paid_hours_per_person':runner.UI_FINANCE['paidHoursPerPerson'],'screening_estimates':True}
        config['climate_factors']={
            'electricity':{'factor_id':'electricity','value':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['value'],'quantity_unit':'kWh','source_status':'official_dataset','basis':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['basis'],'geography':'Netherlands','reference_year':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['reference_year'],'source_url':'; '.join(runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['source_urls']),'source_table_page':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['source_table_page'],'retrieval_date':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['retrieval_date'],'evidence_class':'official_dataset','applicability':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['applicability'],'conversion_method':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['conversion_method'],'uncertainty':runner.ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['uncertainty']},
            'heat':{'factor_id':'heat','value':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['value'],'quantity_unit':'kWh','source_status':'direct_literature','basis':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['basis'],'geography':'Netherlands','reference_year':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['reference_year'],'source_url':'; '.join(runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['source_urls']),'source_table_page':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['source_table_page'],'retrieval_date':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['retrieval_date'],'applicability':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['applicability'],'conversion_method':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['conversion_method'],'evidence_class':'B','uncertainty':runner.ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['uncertainty']},
        }
        config['candidate_economics']={
            'tax_rate':FINANCIAL_BASIS['tax_rate'],'project_lifetime_years':FINANCIAL_BASIS['project_lifetime_years'],'discount_rate':FINANCIAL_BASIS['discount_rate'],'opex_support_years':FINANCIAL_BASIS['opex_support_years'],
            'soil_carbon_retention_fraction':CARBON_BASIS['soil_carbon_retention_fraction'],'furniture_carbon_retention_fraction':1.0,
            'grant_scenario_id':case_id,'grant_scenario_name':support['name'],'grant_awarding_organization':'None (zero CAPEX grant)',
            'operating_support_scenario_name':support['name'],'operating_support_awarding_organization':GRANT_AWARDER,
            'capex_grant_fraction':0.0,'opex_premium_eur_per_t_feed':0.0,
            'staffing_people':runner.UI_FINANCE['staffingPeople'],'paid_hours_per_person':runner.UI_FINANCE['paidHoursPerPerson'],
            'labor_cost_eur_per_person_hour':runner.UI_FINANCE['laborCostEurPerHour'],
            'electricity_cost_eur_per_mwh':runner.UI_FINANCE['electricityCostEurMWh'],'heat_cost_eur_per_mwh':runner.UI_FINANCE['heatCostEurMWh'],
            'grass_utilization_bonus_eur_per_t_feed':0.0,'grass_utilization_bonus_years':runner.UI_FINANCE['grassUtilizationBonusYears'],
            'logistics_cost_eur_per_t_km':float(runner.UI_FINANCE['logisticsCostEurTkm']),'logistics_distance_km':float(runner.UI_FINANCE['logisticsDistanceKm'])}
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
        batch['support_cases']=list(runner.SUPPORT_CASE_IDS)
        batch['fronts']['by_support_case']={cid:_pareto([r for r in rows if r.get('support_case')==cid],('net_carbon','npv')) for cid in runner.SUPPORT_CASE_IDS}
        batch['selected_candidates']['net_carbon_vs_npv']=_select_3d_ranked(three,rows,UI_CANDIDATE_COUNT)
        batch['selected_candidates']['net_carbon_npv_subsidy']=batch['selected_candidates']['net_carbon_vs_npv']
        batch['selected_candidates']['subsidy_vs_npv']=_select_ranked(subsidy,rows,UI_CANDIDATE_COUNT,True)
        batch['selected_candidates']['grass_bonus_sensitivity']=runner._grass_bonus_sensitivity(rows)
        for cid,front in batch['fronts']['by_support_case'].items():batch['selected_candidates'][f'net_carbon_vs_npv_{cid}']=_select_ranked(front,[r for r in rows if r.get('support_case')==cid],UI_CANDIDATE_COUNT,True)
        manifest['groups'][group].update({'sample_count':batch['sample_count'],'evaluated_count':batch['evaluated_count'],'rejected_count':batch['rejected_count'],
            'front_counts':{name:len(front.get('points',[])) for name,front in batch['fronts'].items() if name!='by_support_case'},
            'support_front_counts':{case:len(front.get('points',[])) for case,front in batch['fronts']['by_support_case'].items()}})
        _atomic_write_json(OUT/f'{group}_batch.json',batch)
    for target in (manifest_path, OUT/'latest.json'):
        _atomic_write_json(target,manifest)
    write_pareto_ui_projection(manifest, OUT/'latest_ui.json')
    print('Updated Pareto batches with explicit baseline references.')

if __name__=='__main__':main()
