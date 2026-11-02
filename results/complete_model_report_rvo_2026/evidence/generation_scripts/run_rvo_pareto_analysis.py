"""Generate paired no-PEF BioSTEAM Pareto screens for RVO support cases.

The RVO percentages and €/t feed premiums are user-supplied what-if cases,
not statements of programme eligibility or awarded tariffs. Each process design
is evaluated once under each case for paired comparisons.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from pathlib import Path
import json
import math
import multiprocessing
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.application.decision_support_service import _apply_candidate_economics
from Greenhub.scenario_exploration import pareto_front, pareto_front_3d

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results' / 'report_figures' / 'no_pef_F1.json'
OUT = ROOT / 'Greenhub' / 'results' / 'pareto_rvo_2026'
OUT.mkdir(parents=True, exist_ok=True)

SEED = 20261102
DESIGNS_PER_GROUP = int(__import__('os').environ.get('GREENHUB_PARETO_DESIGNS', '128'))
MAX_WORKERS = int(__import__('os').environ.get('GREENHUB_PARETO_WORKERS', '8'))

GRANT_AWARDER = 'Netherlands Enterprise Agency (RVO)'
SUPPORT_SCENARIOS = {
    'A': {'name': 'A · RVO DEI+ 30% + RVO SDE++ €20/t feed proxy', 'grant_fraction': .30, 'opex_eur_t': 20.0, 'grant_awarder':'Netherlands Enterprise Agency (RVO)', 'opex_awarder':'Netherlands Enterprise Agency (RVO)'},
    'B': {'name': 'B · RVO DEI+ 45% + RVO SDE++ €40/t feed proxy', 'grant_fraction': .45, 'opex_eur_t': 40.0, 'grant_awarder':'Netherlands Enterprise Agency (RVO)', 'opex_awarder':'Netherlands Enterprise Agency (RVO)'},
    'C': {'name': 'C · RVO DEI+ 60% + RVO SDE++ €60/t feed proxy', 'grant_fraction': .60, 'opex_eur_t': 60.0, 'grant_awarder':'Netherlands Enterprise Agency (RVO)', 'opex_awarder':'Netherlands Enterprise Agency (RVO)'},
    'D': {'name': 'D · RVO SDE++ €50/t feed proxy (OPEX only)', 'grant_fraction': 0.0, 'opex_eur_t': 50.0, 'grant_awarder':None, 'opex_awarder':'Netherlands Enterprise Agency (RVO)'},
}
FINANCIAL_BASIS = {
    'project_lifetime_years': 20,
    'discount_rate': .08,
    'opex_support_years': 15,
    'tax_rate': 0.0,
    'capex_basis': 'high direct uninstalled equipment CAPEX from current cost register; digester tank at €1,800/m3',
    'operating_premium_basis': 'user-specified €/t wet feed proxy; nominal support applied for 15 years, no annual market correction or eligibility test',
    'npv_basis': 'pre-tax constant-account screening NPV; no financing, escalation, replacement, working capital, residual value or installation CAPEX',
}
CARBON_BASIS = {
    'boundary': 'factory gate-to-gate operational climate screening',
    'electricity_factor_kg_co2e_kwh': .264,
    'electricity_sensitivity_kg_co2e_kwh': [.254, .274],
    'heat_factor_kg_co2e_kwh': 30.96 / 277.7777777778,
    'net_carbon_definition': 'Operational climate load × 12/44 minus retained product carbon, t C/year.',
    'fiber_fate': '100% of modeled press-cake carbon assumed in furniture over 20 years; manufacturing loss and end-of-life excluded.',
    'soil_carbon_retention_fraction': .10,
    'soil_fate': '10% of modeled nutrient-rich-solids carbon retained in soil as an explicit screening assumption.',
    'protein_carbon_credit': 'none; protein may be fed or used as biostimulant and no split/retention rate is specified.',
    'excluded': ['upstream feedstock production', 'equipment manufacture', 'materials supply chain', 'transport', 'storage emissions', 'downstream product use except stated product-carbon stock'],
}

LCA_BASIS = {
    'boundary': CARBON_BASIS['boundary'],
    'included_groups': ['electricity', 'heat', 'process_emissions'],
    'exclusions': {
        'materials': 'Upstream material production is outside this factory-operational boundary; no zero-burden claim.',
        'transport': 'Offsite feedstock and product transport is excluded.',
        'storage_emissions': 'Storage emissions are excluded from this operational boundary; separate storage modelling is not characterized here.',
        'waste': 'Downstream waste treatment is excluded.',
        'feedstock_production': 'Cultivation and land-use change are excluded.',
        'equipment': 'Embodied equipment is excluded.',
    },
    'inventory_completeness': {
        'electricity': {'status': 'complete', 'note': 'Modeled annual electricity activity; Dutch average factor and stated sensitivity applied.'},
        'heat': {'status': 'complete', 'note': 'Modeled annual process heat activity; user-supplied Dutch heat-network average applied.'},
        'process_emissions': {'status': 'complete', 'note': 'Modeled vented process methane and gas flows; terminal gas fate set to emitted for this screening case.'},
    },
    'terminal_gas_fate': 'emitted',
}


def make_designs(base, group: str, count: int, seed: int):
    rng = random.Random(seed)
    designs = []
    protein_choices = ('PR1', 'PR2', 'PR3') if group == 'protein_enabled' else ('PR0',)
    log_min, log_max = math.log10(1000_000 / 8760), math.log10(30000_000 / 8760)
    for i in range(count):
        digestion = rng.choice(('AD0', 'AD1', 'AD3'))
        gas = rng.choice(('BG0', 'BG2', 'BG3', 'BG4')) if digestion != 'AD0' else 'BG0'
        nutrients = rng.choice(('NR0', 'NR1', 'NR2', 'NR3', 'NR4', 'NR6', 'NR7')) if digestion != 'AD0' else 'NR0'
        flow = 10 ** rng.uniform(log_min, log_max)
        process_order = rng.choice(('A', 'B', 'C')) if nutrients in ('NR4', 'NR7') else 'A'
        economics_core = {
            'labour_reduction': rng.uniform(0.0, 0.30),
            'logistics_reduction': rng.uniform(0.0, 0.25),
            'energy_reduction': rng.uniform(0.0, 0.25),
            'protein_yield_uplift': rng.uniform(0.0, 0.20) if group == 'protein_enabled' else 0.0,
            'nutrient_recovery_uplift': rng.uniform(0.0, 0.15),
            'tax_rate': FINANCIAL_BASIS['tax_rate'],
            'project_lifetime_years': FINANCIAL_BASIS['project_lifetime_years'],
            'discount_rate': FINANCIAL_BASIS['discount_rate'],
            'opex_support_years': FINANCIAL_BASIS['opex_support_years'],
            'soil_carbon_retention_fraction': CARBON_BASIS['soil_carbon_retention_fraction'],
            'furniture_carbon_retention_fraction': 1.0,
        }
        selected_protein = rng.choice(protein_choices) if group == 'protein_enabled' else 'PR0'
        selected_scenarios = {
            'feed_preparation': 'F1',  # PEF disabled in all cases
            'protein_recovery': selected_protein,
            'anaerobic_digestion': digestion,
            'biogas_upgrading': gas,
            'nutrient_recovery': nutrients,
            'process_order': process_order,
        }
        case_id='A';support=SUPPORT_SCENARIOS[case_id]
        config = deepcopy(base)
        config['simulation']['request_id'] = f"rvo_pf_{group}_{i+1:04d}_{case_id}"
        config['simulation']['scenarios'] = deepcopy(selected_scenarios)
        config['simulation']['wet_feed_rate_kg_hr'] = flow
        config['simulation']['plant_capacity_kg_hr'] = flow
        config['project_basis']['screening_estimates'] = True
        config['use_screening_process_assumptions'] = True
        config['use_screening_lca_factors'] = True
        config['financial_assumptions']['use_screening_price_benchmarks'] = True
        config['lca'] = deepcopy(LCA_BASIS)
        config['candidate_economics'] = {
            **economics_core,
            'grant_scenario_id': case_id,
            'grant_scenario_name': support['name'],
            'grant_awarding_organization': GRANT_AWARDER if support['grant_fraction'] else 'None (OPEX-only case)',
            'operating_support_scenario_name': support['name'],
            'operating_support_awarding_organization': 'Netherlands Enterprise Agency (RVO)',
            'capex_grant_fraction': support['grant_fraction'],
            'opex_premium_eur_per_t_feed': support['opex_eur_t'],
            'opex_support_years': FINANCIAL_BASIS['opex_support_years'],
        }
        designs.append({'sample_id': f'{group}-{i+1:04d}-A', 'group': group,
                        'design_id': f'{group}-{i+1:04d}', 'support_case': 'A',
                        'configuration': config})
    return designs


def _init_worker():
    global SERVICE
    SERVICE = DecisionSupportService()


def _evaluate(item):
    try:
        report = SERVICE.evaluate(item['configuration'])
        return {**{k: item[k] for k in ('sample_id', 'group', 'design_id', 'support_case')},
                'status': 'evaluated', 'configuration': item['configuration'],
                'run_id': report['run_id'], 'objectives': report['objectives'],
                'feasibility': report['feasibility'], 'carbon_assessment': report['carbon_assessment'],
                'tea_totals': report['tea']['totals'], 'candidate_economics': report['tea']['candidate_economics'],
                'lca_totals': report['lca']['totals'], 'lca_readiness': report['lca']['readiness'],
                'lca_missing_inputs': report['lca']['missing_inputs'], 'annual': report['annual'],
                'warnings': report['warnings'], 'limitations': report['limitations']}
    except Exception as error:
        return {**{k: item[k] for k in ('sample_id', 'group', 'design_id', 'support_case')},
                'status': 'rejected', 'configuration': item['configuration'],
                'rejection_reason': f'{type(error).__name__}: {error}'}


def _paired_support_rows(base_row):
    """Recalculate financial scenarios without rerunning an identical process simulation."""
    if base_row.get('status')!='evaluated': return [base_row]
    rows=[]
    for case_id,support in SUPPORT_SCENARIOS.items():
        row=deepcopy(base_row);row['support_case']=case_id
        row['sample_id']=f"{base_row['design_id']}-{case_id}"
        row['paired_process_source_sample_id']=base_row['sample_id']
        row['paired_process_run_id']=base_row.get('run_id')
        config=row['configuration']
        economics=config['candidate_economics'];economics.update({
            'grant_scenario_id':case_id,'grant_scenario_name':support['name'],
            'grant_awarding_organization':GRANT_AWARDER if support['grant_fraction'] else 'None (OPEX-only case)',
            'operating_support_scenario_name':support['name'],'operating_support_awarding_organization':GRANT_AWARDER,
            'capex_grant_fraction':support['grant_fraction'],'opex_premium_eur_per_t_feed':support['opex_eur_t'],
        })
        tea=_apply_candidate_economics({'totals':deepcopy(row['tea_totals'])},economics,row['annual'],())
        row['tea_totals']=tea['totals'];row['candidate_economics']=tea['candidate_economics'];row['configuration']=config
        row['objectives']['operating_profit']['value']=tea['totals'].get('optimized_after_tax_profit_eur_per_year')
        row['objectives']['npv']['value']=tea['totals'].get('proxy_npv_eur')
        row['objectives']['subsidy_granted']['value']=tea['totals'].get('total_public_support_pv_eur')
        rows.append(row)
    return rows


def _dominates(a, b, names):
    values_a=[]; values_b=[]
    for name in names:
        obj_a=a['objectives'][name]; obj_b=b['objectives'][name]
        sign=-1 if obj_a['direction']=='maximize' else 1
        values_a.append(float(obj_a['value'])*sign); values_b.append(float(obj_b['value'])*sign)
    return all(x <= y for x,y in zip(values_a,values_b)) and any(x < y for x,y in zip(values_a,values_b))


def _pareto(rows, names):
    valid=[r for r in rows if r.get('status')=='evaluated' and all(
        r.get('objectives',{}).get(name,{}).get('eligible') and
        isinstance(r['objectives'][name].get('value'),(int,float)) and
        math.isfinite(r['objectives'][name]['value']) for name in names)]
    front=[r for r in valid if not any(_dominates(other,r,names) for other in valid if other is not r)]
    return {'objectives':list(names),'objective_metadata':{n:{k:r['objectives'][n].get(k) for k in ('direction','unit','definition')} for n in names for r in front[:1]},
            'points':[{'sample_id':r['sample_id'],'design_id':r['design_id'],'support_case':r['support_case'],
                       **{n:r['objectives'][n]['value'] for n in names},
                       'technical_eligible':r['feasibility']['eligible_for_ranking']} for r in front],
            'candidate_count':len(valid),'sample_bounded':True,
            'negative_profit_policy':'Unprofitable and dominated designs remain in the batch; nondominance is only the optimization selection rule.',
            'technical_evidence_policy':'Numerically complete candidates are included even if technical evidence gates remain conditional; each point carries the gate status.'}


def _select_ranked(front, rows, n=11, economic_first=True):
    points=front.get('points',[])
    if not points:
        return []
    row_map={r['sample_id']:r for r in rows}
    name_x,name_y=front['objectives'][0],front['objectives'][1]
    xmeta=front['objective_metadata'][name_x]; ymeta=front['objective_metadata'][name_y]
    direction_key=(name_y if economic_first else name_x)
    maximize=front['objective_metadata'][direction_key]['direction']=='maximize'
    ordered=sorted(points,key=lambda p:p[direction_key],reverse=maximize)
    if len(ordered)<=n:
        selected=ordered
    else:
        xs=[float(p[name_x]) for p in ordered]; ys=[float(p[name_y]) for p in ordered]
        sx=max(xs)-min(xs) or 1.0; sy=max(ys)-min(ys) or 1.0
        cumulative=[0.0]
        for i in range(1,len(ordered)):
            cumulative.append(cumulative[-1]+math.hypot((xs[i]-xs[i-1])/sx,(ys[i]-ys[i-1])/sy))
        selected=[]
        for rank in range(n):
            target=cumulative[-1]*rank/(n-1)
            lower=selected[-1]+1 if selected else 0
            upper=len(ordered)-(n-rank)
            idx=min(range(lower,upper+1),key=lambda j:(abs(cumulative[j]-target),j))
            selected.append(idx)
        selected=[ordered[i] for i in selected]
    result=[]
    for rank,point in enumerate(selected):
        row=row_map[point['sample_id']]
        result.append({'rank':rank,'sample_id':row['sample_id'],'design_id':row['design_id'],
                       'support_case':row['support_case'],'run_id':row.get('run_id'),
                       'scenario_label':row['configuration']['candidate_economics']['grant_scenario_name'],
                       'configuration':row['configuration'],'values':{n:row['objectives'][n]['value'] for n in row['objectives']},
                       'technical_eligible':row['feasibility']['eligible_for_ranking']})
    return result


def _select_3d_ranked(front, rows, n=11):
    """Select 11 3-objective candidates from highest-NPV endpoint to lowest-carbon endpoint."""
    points=front.get('points',[])
    if not points:return []
    economic=max(points,key=lambda p:(p['npv'],-p['subsidy_granted']))
    environmental=min(points,key=lambda p:(p['net_carbon'],-p['npv']))
    names=('net_carbon','npv','subsidy_granted')
    lo={name:min(float(p[name]) for p in points) for name in names}
    hi={name:max(float(p[name]) for p in points) for name in names}
    def vector(p):
        return [(float(p['net_carbon'])-lo['net_carbon'])/(hi['net_carbon']-lo['net_carbon'] or 1),
                (hi['npv']-float(p['npv']))/(hi['npv']-lo['npv'] or 1),
                (float(p['subsidy_granted'])-lo['subsidy_granted'])/(hi['subsidy_granted']-lo['subsidy_granted'] or 1)]
    start,end=vector(economic),vector(environmental)
    chosen=[economic]
    for rank in range(1,n-1):
        t=rank/(n-1);target=[a+(b-a)*t for a,b in zip(start,end)]
        remaining=[p for p in points if p['sample_id'] not in {v['sample_id'] for v in chosen} and p['sample_id']!=environmental['sample_id']]
        if not remaining:break
        chosen.append(min(remaining,key=lambda p:(sum((a-b)**2 for a,b in zip(vector(p),target)),p['sample_id'])))
    if environmental['sample_id'] not in {v['sample_id'] for v in chosen}:chosen.append(environmental)
    row_map={r['sample_id']:r for r in rows};result=[]
    for rank,point in enumerate(chosen):
        row=row_map[point['sample_id']]
        result.append({'rank':rank,'sample_id':row['sample_id'],'design_id':row['design_id'],'support_case':row['support_case'],
            'run_id':row.get('run_id'),'scenario_label':row['configuration']['candidate_economics']['grant_scenario_name'],
            'configuration':row['configuration'],'values':{name:row['objectives'][name]['value'] for name in row['objectives']},
            'technical_eligible':row['feasibility']['eligible_for_ranking'],'selection_basis':'Three-objective Pareto; rank 0 maximizes NPV, final rank minimizes net carbon.'})
    return result


def main():
    base = json.loads(SOURCE.read_text(encoding='utf-8'))['configuration']
    base['project_basis']['screening_estimates'] = True
    groups={}
    start=time.time()
    ctx=multiprocessing.get_context('spawn')
    workers=max(1,min(MAX_WORKERS,os_cpu_count(),DESIGNS_PER_GROUP*len(SUPPORT_SCENARIOS)*2))
    for group_index,group in enumerate(('protein_enabled','protein_bypass')):
        designs=make_designs(base,group,DESIGNS_PER_GROUP,SEED+group_index)
        rows=[]
        with ProcessPoolExecutor(max_workers=workers,mp_context=ctx,initializer=_init_worker) as pool:
            futures=[pool.submit(_evaluate,item) for item in designs]
            for n,future in enumerate(as_completed(futures),1):
                row=future.result(); rows.append(row)
                if n%25==0 or n==len(futures):
                    print(f'{group}: {n}/{len(futures)} unique process simulations',flush=True)
        rows=[paired for row in rows for paired in _paired_support_rows(row)]
        rows.sort(key=lambda r:r['sample_id'])
        group_result={'group':group,'requested_designs':DESIGNS_PER_GROUP,'support_cases':list(SUPPORT_SCENARIOS),
                      'sample_count':len(rows),'evaluated_count':sum(r['status']=='evaluated' for r in rows),
                      'rejected_count':sum(r['status']!='evaluated' for r in rows),
                      'samples':rows,'fronts':{},'selected_candidates':{}}
        primary=_pareto(rows,('net_carbon','npv'))
        subsidy=_pareto(rows,('subsidy_granted','npv'))
        three=_pareto(rows,('net_carbon','npv','subsidy_granted'))
        group_result['fronts']={'net_carbon_vs_npv':primary,'subsidy_vs_npv':subsidy,'net_carbon_npv_subsidy':three,'by_support_case':{}}
        group_result['selected_candidates']['net_carbon_vs_npv'] = _select_3d_ranked(three,rows,11)
        group_result['selected_candidates']['net_carbon_npv_subsidy'] = group_result['selected_candidates']['net_carbon_vs_npv']
        group_result['selected_candidates']['subsidy_vs_npv'] = _select_ranked(subsidy,rows,11,economic_first=True)
        for case_id in SUPPORT_SCENARIOS:
            case_rows=[r for r in rows if r.get('support_case')==case_id]
            front=_pareto(case_rows,('net_carbon','npv'))
            group_result['fronts']['by_support_case'][case_id]=front
            group_result['selected_candidates'][f'net_carbon_vs_npv_{case_id}']=_select_ranked(front,case_rows,11,economic_first=True)
        groups[group]=group_result
        job_path=OUT/f'{group}_batch.json'
        job_path.write_text(json.dumps(group_result,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print(group,'evaluated',group_result['evaluated_count'],'rejected',group_result['rejected_count'],
              '2D front',len(primary['points']),'3D front',len(three['points']),flush=True)
    manifest={
        'schema_version':'greenhub-rvo-pareto-1.0',
        'created_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'seed':SEED,'designs_per_protein_group':DESIGNS_PER_GROUP,'workers':workers,
        'elapsed_seconds':time.time()-start,'feed_preparation':'F1 only; PEF off',
        'optimization_objectives':{'net_carbon_vs_npv':['net_carbon lower is better','npv higher is better'],
                                   'subsidy_vs_npv':['subsidy_granted lower is better','npv higher is better'],
                                   'three_objective':['net_carbon lower is better','npv higher is better','subsidy_granted lower is better']},
        'support_scenarios':SUPPORT_SCENARIOS,'grant_awarding_organization':GRANT_AWARDER,
        'financial_basis':FINANCIAL_BASIS,'carbon_basis':CARBON_BASIS,'lca_project_basis':LCA_BASIS,
        'groups':{k:{'requested_designs':v['requested_designs'],'sample_count':v['sample_count'],
                     'evaluated_count':v['evaluated_count'],'rejected_count':v['rejected_count'],
                     'front_counts':{name:len(front.get('points',[])) for name,front in v['fronts'].items() if name!='by_support_case'},
                     'support_front_counts':{case:len(front.get('points',[])) for case,front in v['fronts']['by_support_case'].items()},
                     'selected_candidate_counts':{name:len(rows) for name,rows in v['selected_candidates'].items()}}
                  for k,v in groups.items()},
        'limitations':['DEI+ 30/45/60% and SDE++ €/t-feed amounts are user-defined what-if values, not awarded or verified RVO tariffs.',
                       'RVO DEI+ eligibility, eligible cost base, grant ceiling and co-funding conditions are not assessed.',
                       'RVO SDE++ in-kind support is modeled as user-specified €/t wet feed for 15 years; official tariffs are tied to eligible renewable-gas grid injection and annual corrections.',
                       'CAPEX is high direct uninstalled screening cost; installation and unpriced/uncosted components may be missing.',
                       'OPEX remains partial; NPV is a pre-tax screening calculation, not the model financial NPV.',
                       'Operational climate inventory is limited to electricity, heat, and modeled process emissions at the stated factors.',
                       'Net carbon includes assumed furniture and soil carbon retention; no manufacturing loss or end-of-life release is represented.',
                       'The fronts are bounded by the sampled configurations and are not global optima.'],
        'groups_payload':groups,
    }
    (OUT/'rvo_pareto_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    (OUT/'latest.json').write_text(json.dumps(manifest,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print('Saved',OUT/'rvo_pareto_manifest.json',flush=True)


def os_cpu_count():
    import os
    return os.cpu_count() or 1


if __name__=='__main__':
    main()
