"""Generate paired no-PEF BioSTEAM Pareto screens for user-defined supports.

CAPEX grant levels, biomethane value and grass-use bonuses are user-defined
what-if assumptions, not awarded subsidies. Each process design is evaluated
once and paired with finance overlays for comparable scenarios.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import csv
import math
import multiprocessing
import os
import random
import sys
import tempfile
import time

# BioSTEAM workers each import numerical libraries; limiting their internal
# BLAS pools avoids multiplying threads/memory under process-level parallelism.
for _thread_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_thread_env] = '1'

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.pareto_reporting import pareto_ui_projection, write_pareto_ui_projection
from Greenhub.application.decision_support_service import _apply_candidate_economics
from Greenhub.scenario_exploration import pareto_front, pareto_front_3d

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results' / 'report_figures' / 'no_pef_F1.json'
OUT = Path(os.environ.get('GREENHUB_PARETO_OUTPUT_DIR', ROOT / 'Greenhub' / 'results' / 'pareto_rvo_2026'))
OUT.mkdir(parents=True, exist_ok=True)
ECONOMIC_DEFAULTS = json.loads((ROOT / 'Greenhub' / 'data' / 'greenhub_economic_defaults.json').read_text(encoding='utf-8'))
UI_FINANCE = ECONOMIC_DEFAULTS['economics']
FEED_PROFILE_PATH = ROOT / 'Greenhub' / 'data' / 'Pre-treatment' / 'Feedstock' / 'greenhub_feed_composition_defaults.json'
FEED_PROFILE = json.loads(FEED_PROFILE_PATH.read_text(encoding='utf-8'))
DEFAULT_FEED_COMPOSITION = {
    component: float(row['wet_mass_fraction'])
    for component, row in FEED_PROFILE['compounds'].items()
}
FEED_PROFILE_PROVENANCE = {
    'profile_id': FEED_PROFILE['profile_id'],
    'path': FEED_PROFILE_PATH.relative_to(ROOT).as_posix(),
    'sha256': sha256(FEED_PROFILE_PATH.read_bytes()).hexdigest(),
    'basis': FEED_PROFILE['basis'],
    'values_embedded_in_each_simulation_configuration': True,
}

SEED = 20261102
DESIGNS_PER_GROUP = int(__import__('os').environ.get('GREENHUB_PARETO_DESIGNS', '128'))
MAX_WORKERS = int(__import__('os').environ.get('GREENHUB_PARETO_WORKERS', '2'))

GRANT_AWARDER = 'User-defined hypothetical scenario; RVO eligibility and award not verified'
BIOMETHANE_DENSITY_KG_PER_NM3 = 0.716  # methane-equivalent at 0 °C, 101.325 kPa
BIOMETHANE_VALUE_RANGE_EUR_PER_NM3 = (1.28, 2.46)  # retained for later sensitivity analysis
BIOMETHANE_VALUE_AVERAGE_EUR_PER_NM3 = sum(BIOMETHANE_VALUE_RANGE_EUR_PER_NM3) / 2
SUPPORT_SCENARIOS = {
    'C30': {'name': 'C30 · hypothetical CAPEX grant 30%; biomethane value proxy €1.87/Nm³', 'grant_fraction': .30, 'opex_eur_nm3': BIOMETHANE_VALUE_AVERAGE_EUR_PER_NM3},
    'C45': {'name': 'C45 · hypothetical CAPEX grant 45%; biomethane value proxy €1.87/Nm³', 'grant_fraction': .45, 'opex_eur_nm3': BIOMETHANE_VALUE_AVERAGE_EUR_PER_NM3},
    'C60': {'name': 'C60 · hypothetical CAPEX grant 60%; biomethane value proxy €1.87/Nm³', 'grant_fraction': .60, 'opex_eur_nm3': BIOMETHANE_VALUE_AVERAGE_EUR_PER_NM3},
    'C0': {'name': 'C0 · no CAPEX grant; biomethane value proxy €1.87/Nm³', 'grant_fraction': 0.0, 'opex_eur_nm3': BIOMETHANE_VALUE_AVERAGE_EUR_PER_NM3},
}
FINANCIAL_BASIS = {
    'performance_improvements': 'None: original modeled sales and OPEX; no assumed cost reductions or revenue/yield uplifts.',
    'project_lifetime_years': UI_FINANCE['projectLifetimeYears'],
    'discount_rate': UI_FINANCE['discountRate'],
    'opex_support_years': UI_FINANCE['biomethaneBonusYears'],
    'tax_rate': UI_FINANCE['taxRate'],
    'capex_basis': 'high direct uninstalled equipment CAPEX from current cost register; digester tank at €1,800/m3',
    'operating_premium_basis': 'Dynamic per-candidate biomethane output (annual biomethane kg divided by 0.716 kg/Nm3 at 0 degC and 101.325 kPa) multiplied by the average user-specified value of €1.87/Nm3; nominal support applied for 15 years. This is a scenario proxy, not an official SDE++ award calculation; sensitivity range €1.28–€2.46/Nm3 is retained for later analysis.',
    'npv_basis': 'After-tax constant-account screening NPV using Configure defaults; no financing, escalation, replacement, working capital, residual value or installed-CAPEX factor unless explicitly entered.',
}
GRASS_BONUS_RATES_EUR_PER_WET_T = tuple(ECONOMIC_DEFAULTS['grass_utilization_bonus']['test_levels_eur_per_wet_tonne'])
SUPPORT_CASE_IDS = tuple(f'{grant}-GB{rate}' for grant in SUPPORT_SCENARIOS for rate in GRASS_BONUS_RATES_EUR_PER_WET_T)
UI_CANDIDATE_COUNT = 25
SALEABLE_PRODUCT_IDS = ('dry_protein_product', 'biostimulant_product', 'biomethane',
                        'phosphorus_product', 'ammonium_product', 'potassium_concentrate',
                        'nutrient_rich_solids')
UI_PRODUCT_PRICES = {key: row['value_eur_per_unit'] for key, row in ECONOMIC_DEFAULTS['product_prices'].items()}
CARBON_BASIS = {
    'boundary': 'operational process inventory plus upstream life-cycle utility supply-chain emissions',
    'electricity_factor_kg_co2e_kwh': ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['value'],
    'operational_electricity_proxy_range_kg_co2e_kwh': [.254, .274],
    'heat_factor_kg_co2e_kwh': 30.96 / 277.7777777778,
    'net_carbon_definition': 'Modeled inventory climate load × 12/44 minus retained product carbon, t C/year.',
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
        'materials': 'Upstream non-energy material production is outside the boundary; electricity supply-chain emissions are included in the JRC lifecycle factor.',
        'transport': 'Offsite feedstock and product transport is excluded.',
        'storage_emissions': 'Storage emissions are excluded from this operational boundary; separate storage modelling is not characterized here.',
        'waste': 'Downstream waste treatment is excluded.',
        'feedstock_production': 'Cultivation and land-use change are excluded.',
        'equipment': 'Embodied equipment is excluded.',
    },
    'inventory_completeness': {
        'electricity': {'status': 'complete', 'note': 'Modeled annual electricity activity; JRC 2021 Dutch lifecycle factor includes upstream electricity supply.'},
        'heat': {'status': 'complete', 'note': 'Modeled annual process heat activity; CE Delft 2022 Dutch end-user heat-grid average applied (literature evidence, not site-specific).'},
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
            'tax_rate': FINANCIAL_BASIS['tax_rate'],
            'project_lifetime_years': FINANCIAL_BASIS['project_lifetime_years'],
            'discount_rate': FINANCIAL_BASIS['discount_rate'],
            'opex_support_years': FINANCIAL_BASIS['opex_support_years'],
            'soil_carbon_retention_fraction': CARBON_BASIS['soil_carbon_retention_fraction'],
            'furniture_carbon_retention_fraction': 1.0,
            'staffing_people': UI_FINANCE['staffingPeople'], 'paid_hours_per_person': UI_FINANCE['paidHoursPerPerson'],
            'labor_cost_eur_per_person_hour': UI_FINANCE['laborCostEurPerHour'],
            'electricity_cost_eur_per_mwh': UI_FINANCE['electricityCostEurMWh'], 'heat_cost_eur_per_mwh': UI_FINANCE['heatCostEurMWh'],
            'logistics_cost_eur_per_t_km': float(UI_FINANCE['logisticsCostEurTkm']), 'logistics_distance_km': float(UI_FINANCE['logisticsDistanceKm']),
            'grass_utilization_bonus_eur_per_t_feed': 0.0,
            'grass_utilization_bonus_years': FINANCIAL_BASIS['project_lifetime_years'],
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
        case_id='C0';support=SUPPORT_SCENARIOS[case_id]
        config = deepcopy(base)
        config['simulation']['request_id'] = f"rvo_pf_{group}_{i+1:04d}_{case_id}"
        config['simulation']['scenarios'] = deepcopy(selected_scenarios)
        config['simulation']['wet_feed_rate_kg_hr'] = flow
        config['simulation']['plant_capacity_kg_hr'] = flow
        config['use_screening_process_assumptions'] = False
        config['use_screening_lca_factors'] = True
        config['financial_assumptions']['use_screening_price_benchmarks'] = True
        config['financial_assumptions']['product_prices'] = {
            key: {'value_eur_per_unit': value, 'unit': ECONOMIC_DEFAULTS['product_prices'][key]['unit'], 'source_status': 'user_screening_override',
                  'basis': 'Same explicit UI Configure > Economics screening price input.'}
            for key, value in UI_PRODUCT_PRICES.items()
        }
        config['tea'] = {**config.get('tea', {}), 'staffing_people': UI_FINANCE['staffingPeople'], 'paid_hours_per_person': UI_FINANCE['paidHoursPerPerson'], 'screening_estimates': True}
        config['climate_factors'] = {
            'electricity': {'factor_id':'electricity','value':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['value'],'quantity_unit':'kWh','source_status':'official_dataset','basis':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['basis'],'geography':'Netherlands','reference_year':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['reference_year'],'source_url':'; '.join(ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['source_urls']),'source_table_page':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['source_table_page'],'retrieval_date':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['retrieval_date'],'evidence_class':'official_dataset','applicability':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['applicability'],'conversion_method':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['conversion_method'],'uncertainty':ECONOMIC_DEFAULTS['environment']['electricityKgCo2eKwh']['uncertainty']},
            'heat': {'factor_id':'heat','value':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['value'],'quantity_unit':'kWh','source_status':'direct_literature','basis':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['basis'],'geography':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['geography'],'reference_year':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['reference_year'],'source_url':'; '.join(ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['source_urls']),'source_table_page':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['source_table_page'],'retrieval_date':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['retrieval_date'],'evidence_class':'B','applicability':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['applicability'],'conversion_method':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['conversion_method'],'uncertainty':ECONOMIC_DEFAULTS['environment']['heatKgCo2eKwh']['uncertainty']},
        }
        config['lca'] = deepcopy(LCA_BASIS)
        config['candidate_economics'] = {
            **economics_core,
            'grant_scenario_id': case_id,
            'grant_scenario_name': support['name'],
            'grant_awarding_organization': GRANT_AWARDER if support['grant_fraction'] else 'None (OPEX-only case)',
            'operating_support_scenario_name': support['name'],
            'operating_support_awarding_organization': GRANT_AWARDER,
            'capex_grant_fraction': support['grant_fraction'],
            'opex_premium_eur_per_t_feed': 0.0,
            'opex_support_years': FINANCIAL_BASIS['opex_support_years'],
        }
        designs.append({'sample_id': f'{group}-{i+1:04d}-C0', 'group': group,
                        'design_id': f'{group}-{i+1:04d}', 'support_case': 'C0',
                        'configuration': config})
    return designs


def pin_default_feed_profile(configuration):
    """Freeze default feed fractions into a scenario without overriding user feed inputs."""
    simulation = configuration.setdefault('simulation', {})
    if not simulation.get('feed_composition'):
        simulation['feed_composition'] = deepcopy(DEFAULT_FEED_COMPOSITION)
    return configuration


def _init_worker():
    global SERVICE
    SERVICE = DecisionSupportService()


def _saleable_products(annual):
    products = (annual or {}).get('products') or {}
    return [product_id for product_id in SALEABLE_PRODUCT_IDS
            if float((products.get(product_id) or {}).get('value') or 0.0) > 1e-9]


def _evaluate(item):
    try:
        pin_default_feed_profile(item['configuration'])
        report = SERVICE.evaluate(item['configuration'])
        saleable_products = _saleable_products(report.get('annual'))
        if not saleable_products:
            feasibility = dict(report.get('feasibility') or {})
            feasibility.update({'eligible_for_ranking': False,
                                'product_gate': {'eligible': False, 'saleable_products': []}})
            return {**{k: item[k] for k in ('sample_id', 'group', 'design_id', 'support_case')},
                    'status': 'rejected', 'configuration': item['configuration'],
                    'rejection_reason': 'No reported saleable recovery-product flow; route must produce at least one non-zero product.',
                    'product_gate': {'eligible': False, 'saleable_products': [],
                                     'threshold': 'annual flow > 1e-9 in the model-reported product basis'},
                    'annual': report.get('annual'), 'tea_totals': report.get('tea', {}).get('totals'),
                    'feasibility': feasibility}
        return {**{k: item[k] for k in ('sample_id', 'group', 'design_id', 'support_case')},
                'status': 'evaluated', 'configuration': item['configuration'],
                'run_id': report['run_id'], 'objectives': report['objectives'],
                'feasibility': report['feasibility'], 'carbon_assessment': report['carbon_assessment'],
                'tea_totals': report['tea']['totals'], 'candidate_economics': report['tea']['candidate_economics'],
                'lca_totals': report['lca']['totals'], 'lca_readiness': report['lca']['readiness'],
                'lca_missing_inputs': report['lca']['missing_inputs'], 'annual': report['annual'],
                'product_gate': {'eligible': True, 'saleable_products': saleable_products,
                                 'threshold': 'annual flow > 1e-9 in the model-reported product basis'},
                'warnings': report['warnings'], 'limitations': report['limitations']}
    except Exception as error:
        return {**{k: item[k] for k in ('sample_id', 'group', 'design_id', 'support_case')},
                'status': 'rejected', 'configuration': item['configuration'],
                'rejection_reason': f'{type(error).__name__}: {error}'}


def _paired_support_rows(base_row):
    """Recalculate financial scenarios without rerunning an identical process simulation."""
    if base_row.get('status')!='evaluated': return [base_row]
    rows=[]
    annual=base_row.get('annual') or {}
    products=annual.get('products') or {}
    biomethane_kg_year=float((products.get('biomethane') or {}).get('value') or 0.0)
    feed_kg_year=float((annual.get('feed_processed') or {}).get('value') or 0.0)
    biomethane_nm3_year=biomethane_kg_year/BIOMETHANE_DENSITY_KG_PER_NM3
    feed_t_year=feed_kg_year/1000.0
    for case_id,support in SUPPORT_SCENARIOS.items():
        for grass_rate in GRASS_BONUS_RATES_EUR_PER_WET_T:
            scenario_id=f'{case_id}-GB{grass_rate}'
            row=deepcopy(base_row);row['support_case']=scenario_id;row['grant_case']=case_id
            row['grass_utilization_bonus_eur_per_t_feed']=grass_rate
            row['sample_id']=f"{base_row['design_id']}-{case_id}" if grass_rate==0 else f"{base_row['design_id']}-{case_id}-GB{grass_rate}"
            row['paired_process_source_sample_id']=base_row['sample_id']
            row['paired_process_run_id']=base_row.get('run_id')
            config=row['configuration']
            pin_default_feed_profile(config)
            annual_biomethane_support=biomethane_nm3_year*support['opex_eur_nm3']
            dynamic_rate_per_t=annual_biomethane_support/feed_t_year if feed_t_year>0 else 0.0
            economics=config['candidate_economics'];economics.update({
                'grant_scenario_id':case_id,'grant_scenario_name':support['name']+f'; grass utilization/logistics bonus €{grass_rate}/wet t',
                'grant_awarding_organization':GRANT_AWARDER if support['grant_fraction'] else 'None (no CAPEX grant)',
                'operating_support_scenario_name':support['name'],'operating_support_awarding_organization':GRANT_AWARDER,
                'capex_grant_fraction':support['grant_fraction'],'opex_premium_eur_per_t_feed':0.0,
                'biomethane_bonus_enabled':True,'annual_biomethane_m3':biomethane_nm3_year,
                'biomethane_bonus_eur_per_m3':support['opex_eur_nm3'],
                'biomethane_bonus_years':FINANCIAL_BASIS['opex_support_years'],
                'grass_utilization_bonus_eur_per_t_feed':grass_rate,
                'grass_utilization_bonus_years':FINANCIAL_BASIS['project_lifetime_years'],
                'opex_premium_eur_per_nm3_biomethane':support['opex_eur_nm3'],
                'biomethane_density_kg_per_nm3':BIOMETHANE_DENSITY_KG_PER_NM3,
                'biomethane_support_volume_nm3_per_year':biomethane_nm3_year,
            })
            # The process row already includes its one-time UI labor/utility
            # overrides. Apply only finance/support fields to that annualized
            # subtotal; replaying UI rates here would double count OPEX.
            overlay_keys = {
                'tax_rate','project_lifetime_years','discount_rate','capex_grant_fraction',
                'opex_support_years','biomethane_bonus_enabled','annual_biomethane_m3',
                'biomethane_bonus_eur_per_m3','biomethane_bonus_years',
                'grass_utilization_bonus_eur_per_t_feed','grass_utilization_bonus_years',
                'additional_benefit_eur_per_year','additional_benefit_years',
                'working_capital_eur','residual_value_eur','opex_premium_eur_per_t_feed',
            }
            support_economics={key:value for key,value in economics.items() if key in overlay_keys}
            tea=_apply_candidate_economics({'totals':deepcopy(row['tea_totals'])},support_economics,row['annual'],())
            config['candidate_economics']=deepcopy(economics)
            row['tea_totals']=tea['totals'];row['candidate_economics']=tea['candidate_economics'];row['configuration']=config
            row['biomethane_support']={
                'biomethane_kg_per_year':biomethane_kg_year,'biomethane_nm3_per_year':biomethane_nm3_year,
                'value_eur_per_nm3':support['opex_eur_nm3'],'support_eur_per_year':annual_biomethane_support,
                'feed_t_per_year':feed_t_year,'equivalent_eur_per_t_feed':dynamic_rate_per_t,
                'volume_basis':'Biomethane product only; user-supplied screening value proxy, not an awarded tariff.',
            }
            row['objectives']['operating_profit']['value']=tea['totals']['annual_revenue_eur']-tea['totals']['annual_opex_eur']
            row['objectives']['operating_profit']['definition']='Original modeled annual sales minus partial OPEX, before support, tax and capital recovery; no assumed process performance improvements.'
            row['objectives']['npv']['value']=tea['totals'].get('proxy_npv_eur')
            row['objectives']['subsidy_granted']['value']=tea['totals'].get('total_public_support_pv_eur')
            row['objectives']['npv']['definition']=FINANCIAL_BASIS['npv_basis']
            row['objectives']['subsidy_granted']['definition']='Hypothetical upfront CAPEX grant plus discounted user-defined biomethane and grass-use support; not confirmed awards.'
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
                       'grant_case':r.get('grant_case'),
                       'grass_utilization_bonus_eur_per_t_feed':r.get('grass_utilization_bonus_eur_per_t_feed',0),
                       **{n:r['objectives'][n]['value'] for n in names},
                       'technical_eligible':r['feasibility']['eligible_for_ranking']} for r in front],
            'candidate_count':len(valid),'sample_bounded':True,
            'negative_profit_policy':'Unprofitable and dominated designs remain in the batch; nondominance is only the optimization selection rule.',
            'technical_evidence_policy':'Numerically complete candidates are included even if technical evidence gates remain conditional; each point carries the gate status.'}


def _candidate_payload(row, rank, selection_basis=None):
    payload={'rank':rank,'sample_id':row['sample_id'],'design_id':row['design_id'],
             'support_case':row['support_case'],'run_id':row.get('run_id'),
             'scenario_label':row['configuration']['candidate_economics']['grant_scenario_name'],
             'configuration':row['configuration'],
             'values':{name:spec['value'] for name,spec in row.get('objectives',{}).items()},
             'tea_totals':row.get('tea_totals',{}),'candidate_economics':row.get('candidate_economics',{}),
             'lca_totals':row.get('lca_totals',{}),'lca_readiness':row.get('lca_readiness',{}),
             'lca_missing_inputs':row.get('lca_missing_inputs',[]),
             'technical_eligible':row['feasibility']['eligible_for_ranking'],
             'product_gate':row.get('product_gate') or row.get('feasibility',{}).get('product_gate')}
    if selection_basis:
        payload['selection_basis']=selection_basis
    return payload


def _grass_bonus_sensitivity(rows):
    """Six exact post-route comparisons for one fixed sampled process design."""
    baseline=[r for r in rows if r.get('status')=='evaluated' and r.get('support_case')=='C0-GB0']
    if not baseline:
        return []
    anchor=max(baseline,key=lambda row:float(row['objectives']['npv']['value']))
    out=[]
    for rank,rate in enumerate(GRASS_BONUS_RATES_EUR_PER_WET_T):
        row=next((r for r in rows if r.get('status')=='evaluated' and r.get('design_id')==anchor['design_id'] and r.get('support_case')==f'C0-GB{rate}'),None)
        if row:
            out.append(_candidate_payload(row,rank,'Fixed process design; only grass utilization bonus rate varies. C0 has no CAPEX grant; biomethane value proxy remains unchanged.'))
    return out


def _atomic_json_write(target: Path, payload: dict) -> None:
    """Stream large generated artifacts to a sibling file, then atomically publish."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='',
                                         dir=target.parent, prefix=f'.{target.name}.',
                                         suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temporary, target)
        except PermissionError:
            # Some Windows readers open generated JSON without delete sharing.
            # Fall back to an in-place streamed refresh; the authoritative batch
            # files remain available to reconstruct this derived artifact.
            with target.open('w', encoding='utf-8', newline='') as handle:
                json.dump(payload, handle, ensure_ascii=False, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _manifest_for_groups(groups, workers, elapsed_seconds):
    return {
        'schema_version':'greenhub-rvo-pareto-1.0',
        'created_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'seed':SEED,'designs_per_protein_group':DESIGNS_PER_GROUP,'workers':workers,
        'elapsed_seconds':elapsed_seconds,'feed_preparation':'F1 only; PEF off',
        'optimization_objectives':{'net_carbon_vs_npv':['net_carbon lower is better','npv higher is better'],
                                   'subsidy_vs_npv':['subsidy_granted lower is better','npv higher is better'],
                                   'three_objective':['net_carbon lower is better','npv higher is better','subsidy_granted lower is better']},
        'support_scenarios':SUPPORT_SCENARIOS,'grant_awarding_organization':GRANT_AWARDER,
        'grass_utilization_bonus':{'label':'Grass utilization/logistics bonus','rates_eur_per_wet_tonne':list(GRASS_BONUS_RATES_EUR_PER_WET_T),'duration_years':FINANCIAL_BASIS['project_lifetime_years'],'status':'User-defined hypothetical support; not an awarded subsidy','basis':'Rate × annual wet tonnes actually processed; post-route economics only; no process chemistry, balances, or emissions change.'},
        'biomethane_support_conversion':{
            'average_value_eur_per_nm3':BIOMETHANE_VALUE_AVERAGE_EUR_PER_NM3,
            'sensitivity_range_eur_per_nm3':list(BIOMETHANE_VALUE_RANGE_EUR_PER_NM3),
            'density_kg_per_nm3':BIOMETHANE_DENSITY_KG_PER_NM3,
            'calculation':'candidate biomethane kg/year ÷ density × average value per Nm3; candidate-specific annual volume is used, with no feed-yield proxy',
            'standard_conditions':'Nm3 at 0 degC and 101.325 kPa; biomethane treated as methane for mass-volume conversion',
            'caveat':'Screening overlay only; actual SDE++ support depends on eligible biomethane injection and annual correction amounts.'},
        'financial_basis':FINANCIAL_BASIS,'carbon_basis':CARBON_BASIS,'lca_project_basis':LCA_BASIS,
        'input_provenance':{'economic_defaults':ECONOMIC_DEFAULTS['dataset_id'],'economic_defaults_path':'Greenhub/data/greenhub_economic_defaults.json','feed_composition_profile':FEED_PROFILE_PROVENANCE,'electricity_factor_doi':'10.2905/JRC.4800KC0','electricity_factor_file':'Greenhub/data/lca/source_data/JRC_electricity_emission_factors_2024.xlsx','finance_applied_after_process_simulation':True},
        'product_eligibility':{'rule':'At least one model-reported saleable recovery-product annual flow must exceed 1e-9 in the reported product basis. Productless route cases are retained as rejected samples and excluded from fronts.', 'checked_products':list(SALEABLE_PRODUCT_IDS)},
        'groups':{k:{'requested_designs':v['requested_designs'],'sample_count':v['sample_count'],
                     'evaluated_count':v['evaluated_count'],'rejected_count':v['rejected_count'],
                     'front_counts':{name:len(front.get('points',[])) for name,front in v['fronts'].items() if name!='by_support_case'},
                     'support_front_counts':{case:len(front.get('points',[])) for case,front in v['fronts']['by_support_case'].items()},
                     'selected_candidate_counts':{name:len(rows) for name,rows in v['selected_candidates'].items()}}
                  for k,v in groups.items()},
        'limitations':['C30/C45/C60/C0 CAPEX grant fractions and €0–50/wet t grass-use bonuses are user-defined what-if values, not awards or verified programme eligibility determinations.',
                       'The OPEX overlay multiplies each candidate\'s modeled biomethane volume by the average €1.87/Nm3 value; €1.28–€2.46/Nm3 is retained as a later sensitivity range. This is not a verified RVO tariff or guaranteed support.',
                       'RVO DEI+ eligibility, eligible cost base, grant ceiling and co-funding conditions are not assessed.',
                       'RVO SDE++ support is modeled from each candidate\'s biomethane output for 15 years without official annual market corrections or an eligibility test.',
                       'CAPEX is high direct uninstalled screening cost; installation and unpriced/uncosted components may be missing.',
                       'OPEX remains partial; NPV is an after-tax screening proxy using the shared Configure assumptions, not an investment-grade project forecast.',
                       'Climate inventory includes electricity, heat, and modeled process emissions; the JRC electricity factor includes upstream electricity supply, while most other upstream/downstream burdens remain excluded.',
                       'Net carbon includes assumed furniture and soil carbon retention; no manufacturing loss or end-of-life release is represented.',
                       'The fronts are bounded by the sampled configurations and are not global optima.'],
        'groups_payload':groups,
    }


def _write_support_ledger(groups, ledger_path=None, include_rejected=False):
    ledger_fields = ('sample_id','group','support_case','wet_feed_t_per_year','high_direct_capex_eur',
                     'original_sales_eur_per_year','original_partial_opex_eur_per_year',
                     'original_operating_profit_eur_per_year','capex_grant_eur',
                     'biomethane_support_eur_per_year','total_support_pv_eur','npv_eur','net_carbon_t_c_per_year')
    if include_rejected:
        ledger_fields += ('scenario_status','product_gate_eligible','saleable_products',
                          'rejection_reason','grass_utilization_bonus_eur_per_wet_tonne')
    ledger_path = ledger_path or OUT/'support_only_financial_ledger.csv'
    with ledger_path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=ledger_fields, lineterminator='\n')
        writer.writeheader()
        for group, pack in groups.items():
            for row in pack.get('samples', []):
                if row.get('status') != 'evaluated' and not include_rejected:
                    continue
                totals = row.get('tea_totals') or {}
                processed = ((row.get('annual') or {}).get('feed_processed') or {}).get('value')
                record = {
                    'sample_id':row['sample_id'],'group':group,'support_case':row['support_case'],
                    'wet_feed_t_per_year':processed/1000 if processed is not None else None,
                    'high_direct_capex_eur':totals.get('high_direct_capex_eur'),
                    'original_sales_eur_per_year':totals.get('annual_revenue_eur'),
                    'original_partial_opex_eur_per_year':totals.get('annual_opex_eur'),
                    'original_operating_profit_eur_per_year':(totals['annual_revenue_eur']-totals['annual_opex_eur']) if totals.get('annual_revenue_eur') is not None and totals.get('annual_opex_eur') is not None else None,
                    'capex_grant_eur':totals.get('subsidy_eur'),
                    'biomethane_support_eur_per_year':totals.get('opex_premium_eur_per_year'),
                    'total_support_pv_eur':totals.get('total_public_support_pv_eur'),
                    'npv_eur':totals.get('proxy_npv_eur'),
                    'net_carbon_t_c_per_year':(row.get('objectives') or {}).get('net_carbon', {}).get('value'),
                }
                if include_rejected:
                    bonus = ((row.get('configuration') or {}).get('candidate_economics') or {}).get('grass_utilization_bonus_eur_per_t_feed')
                    gate = row.get('product_gate') or {}
                    record.update({
                        'scenario_status':row.get('status'),
                        'product_gate_eligible':gate.get('eligible'),
                        'saleable_products':'|'.join(gate.get('saleable_products') or []),
                        'rejection_reason':row.get('rejection_reason'),
                        'grass_utilization_bonus_eur_per_wet_tonne':bonus,
                    })
                writer.writerow(record)


def _publish_saved_batches():
    groups = {}
    for group in ('protein_enabled','protein_bypass'):
        path = OUT / f'{group}_batch.json'
        if not path.exists():
            raise FileNotFoundError(f'Cannot publish Pareto manifest; saved batch missing: {path}')
        groups[group] = json.loads(path.read_text(encoding='utf-8'))
        expected_cases = set(SUPPORT_CASE_IDS)
        actual_cases = set(groups[group]['fronts'].get('by_support_case', {}))
        if actual_cases != expected_cases:
            raise ValueError(f'{group} batch support fronts mismatch: missing={sorted(expected_cases-actual_cases)} extra={sorted(actual_cases-expected_cases)}')
        pack = groups[group]
        rows = pack.get('samples', [])
        for row in rows:
            if row.get('status') != 'evaluated':
                continue
            present = _saleable_products(row.get('annual'))
            row['product_gate'] = {'eligible': bool(present), 'saleable_products': present,
                                   'threshold': 'annual flow > 1e-9 in the model-reported product basis'}
            if not present:
                row['status'] = 'rejected'
                row['rejection_reason'] = 'No reported saleable recovery-product flow; route must produce at least one non-zero product.'
                row.setdefault('feasibility', {})['eligible_for_ranking'] = False
                row['feasibility']['product_gate'] = {'eligible': False, 'saleable_products': []}
        pack['sample_count'] = len(rows)
        pack['evaluated_count'] = sum(row.get('status') == 'evaluated' for row in rows)
        pack['rejected_count'] = sum(row.get('status') != 'evaluated' for row in rows)
        pack['fronts'] = {
            'net_carbon_vs_npv': _pareto(rows, ('net_carbon','npv')),
            'subsidy_vs_npv': _pareto(rows, ('subsidy_granted','npv')),
            'net_carbon_npv_subsidy': _pareto(rows, ('net_carbon','npv','subsidy_granted')),
            'by_support_case': {case: _pareto([row for row in rows if row.get('support_case') == case], ('net_carbon','npv'))
                                for case in SUPPORT_CASE_IDS},
        }
        pack['support_cases'] = list(SUPPORT_CASE_IDS)
        three = pack['fronts']['net_carbon_npv_subsidy']
        subsidy = pack['fronts']['subsidy_vs_npv']
        pack['selected_candidates'] = {
            'net_carbon_vs_npv': _select_3d_ranked(three, rows, UI_CANDIDATE_COUNT),
            'net_carbon_npv_subsidy': _select_3d_ranked(three, rows, UI_CANDIDATE_COUNT),
            'subsidy_vs_npv': _select_ranked(subsidy, rows, UI_CANDIDATE_COUNT, economic_first=True),
            'grass_bonus_sensitivity': _grass_bonus_sensitivity(rows),
            **{f'net_carbon_vs_npv_{case}': _select_ranked(front, [row for row in rows if row.get('support_case') == case], UI_CANDIDATE_COUNT, economic_first=True)
               for case, front in pack['fronts']['by_support_case'].items()},
        }
        # If a previous publication already saved every product-gate decision
        # and the expanded representative sets, leave the large batch file in
        # place. This also avoids rewriting user-open generated artifacts.
        already_published = all(row.get('product_gate') is not None for row in rows) and all(
            len(pack.get('selected_candidates', {}).get(key, [])) >= min(UI_CANDIDATE_COUNT, len(pack.get('fronts', {}).get(front, {}).get('points', [])))
            for key, front in (('net_carbon_vs_npv','net_carbon_npv_subsidy'), ('subsidy_vs_npv','subsidy_vs_npv'))
        )
        if not already_published and os.environ.get('GREENHUB_PARETO_REPUBLISH_BATCHES') == '1':
            _atomic_json_write(path, pack)
    manifest = _manifest_for_groups(groups, MAX_WORKERS, 0.0)
    if os.environ.get('GREENHUB_PARETO_PUBLISH_UI_ONLY') == '1':
        _atomic_json_write(OUT/'latest_ui.json', pareto_ui_projection(manifest))
        print('Published baseline-aware product-filtered UI projection from saved batches.', flush=True)
        return
    if os.environ.get('GREENHUB_PARETO_PUBLISH_LATEST_ONLY') == '1':
        # Full scenario ledgers are hundreds of MB. Permit a metadata/ledger
        # refresh when the active JSON is already current and the disk cannot
        # safely stage another full copy.
        generation = str(manifest.get('created_at_utc', ''))[:10].replace('-', '') or 'undated'
        ledger = OUT / f'scenario_financial_eligibility_ledger_{generation}.csv'
        _write_support_ledger(groups, ledger_path=ledger, include_rejected=True)
        if os.environ.get('GREENHUB_PARETO_NO_FULL_JSON_WRITE') == '1':
            active = OUT/'latest.json'
            digest = sha256(active.read_bytes()).hexdigest() if active.exists() else None
            pointer = {
                'schema_version': 'greenhub-pareto-generation-pointer-1.0',
                'created_at_utc': manifest.get('created_at_utc'),
                'active_full_ledger': active.name,
                'active_ui_projection': 'latest_ui.json',
                'active_full_ledger_sha256': digest,
                'dated_scenario_ledger': ledger.name,
                'product_eligibility': manifest.get('product_eligibility'),
                'groups': manifest.get('groups'),
                'note': 'Full JSON ledger was not rewritten to avoid duplicating a large artifact; active latest.json remains authoritative.'
            }
            _atomic_json_write(OUT/f'current_generation_{generation}.json', pointer)
            print(f'Published additive generation pointer and scenario ledger: current_generation_{generation}.json, {ledger.name}.', flush=True)
        else:
            _atomic_json_write(OUT/'latest.json', manifest)
            _atomic_json_write(OUT/'latest_ui.json', pareto_ui_projection(manifest))
            print('Published product-filtered latest/UI projection and dated scenario ledger.', flush=True)
        return
    _write_support_ledger(groups)
    _atomic_json_write(OUT/'rvo_pareto_manifest.json', manifest)
    _atomic_json_write(OUT/'latest.json', manifest)
    write_pareto_ui_projection(manifest, OUT/'latest_ui.json')
    print('Published manifest, latest JSON and UI projection from saved scenario batches.', flush=True)


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
        result.append(_candidate_payload(row,rank))
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
        result.append(_candidate_payload(row,rank,'Three-objective Pareto; rank 0 maximizes NPV, final rank minimizes net carbon.'))
    return result


def main():
    if os.environ.get('GREENHUB_PARETO_PUBLISH_SAVED_BATCHES') == '1':
        _publish_saved_batches()
        return
    base = json.loads(SOURCE.read_text(encoding='utf-8'))['configuration']
    pin_default_feed_profile(base)
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
        group_result={'group':group,'requested_designs':DESIGNS_PER_GROUP,'support_cases':list(SUPPORT_CASE_IDS),
                      'sample_count':len(rows),'evaluated_count':sum(r['status']=='evaluated' for r in rows),
                      'rejected_count':sum(r['status']!='evaluated' for r in rows),
                      'samples':rows,'fronts':{},'selected_candidates':{}}
        primary=_pareto(rows,('net_carbon','npv'))
        subsidy=_pareto(rows,('subsidy_granted','npv'))
        three=_pareto(rows,('net_carbon','npv','subsidy_granted'))
        group_result['fronts']={'net_carbon_vs_npv':primary,'subsidy_vs_npv':subsidy,'net_carbon_npv_subsidy':three,'by_support_case':{}}
        group_result['selected_candidates']['net_carbon_vs_npv'] = _select_3d_ranked(three,rows,UI_CANDIDATE_COUNT)
        group_result['selected_candidates']['net_carbon_npv_subsidy'] = group_result['selected_candidates']['net_carbon_vs_npv']
        group_result['selected_candidates']['subsidy_vs_npv'] = _select_ranked(subsidy,rows,UI_CANDIDATE_COUNT,economic_first=True)
        group_result['selected_candidates']['grass_bonus_sensitivity'] = _grass_bonus_sensitivity(rows)
        for case_id in SUPPORT_CASE_IDS:
            case_rows=[r for r in rows if r.get('support_case')==case_id]
            front=_pareto(case_rows,('net_carbon','npv'))
            group_result['fronts']['by_support_case'][case_id]=front
            group_result['selected_candidates'][f'net_carbon_vs_npv_{case_id}']=_select_ranked(front,case_rows,UI_CANDIDATE_COUNT,economic_first=True)
        groups[group]=group_result
        job_path=OUT/f'{group}_batch.json'
        job_path.write_text(json.dumps(group_result,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print(group,'evaluated',group_result['evaluated_count'],'rejected',group_result['rejected_count'],
              '2D front',len(primary['points']),'3D front',len(three['points']),flush=True)
    manifest = _manifest_for_groups(groups, workers, time.time()-start)
    _atomic_json_write(OUT/'rvo_pareto_manifest.json', manifest)
    _atomic_json_write(OUT/'latest.json', manifest)
    write_pareto_ui_projection(manifest, OUT/'latest_ui.json')
    print('Saved',OUT/'rvo_pareto_manifest.json',flush=True)


def os_cpu_count():
    import os
    return os.cpu_count() or 1


if __name__=='__main__':
    main()
