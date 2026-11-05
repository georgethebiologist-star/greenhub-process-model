"""Compose existing process services with read-only post-route analyses."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
import math
from collections import Counter
from pathlib import Path

from .contracts import SimulationRequest
from .simulation_service import SimulationService
from .annual_service import build_annual_summary
from .tea_service import calculate_empirical_tea, TEAProjectBasis
from .lca_service import calculate_empirical_lca, lca_options
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.tea_finance import _irr, _payback

ECONOMIC_DEFAULTS = json.loads((Path(__file__).parents[1] / 'data' / 'greenhub_economic_defaults.json').read_text(encoding='utf-8'))
UI_FINANCE_DEFAULTS = ECONOMIC_DEFAULTS['economics']
DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3 = float(UI_FINANCE_DEFAULTS['biomethaneBonusEurM3'])
DEFAULT_BIOMETHANE_BONUS_YEARS = int(UI_FINANCE_DEFAULTS['biomethaneBonusYears'])
GRASS_BONUS_DEFAULTS = ECONOMIC_DEFAULTS['grass_utilization_bonus']
MAX_GRASS_UTILIZATION_BONUS_EUR_PER_T = float(GRASS_BONUS_DEFAULTS['maximum_eur_per_wet_tonne'])
DEFAULT_GRASS_UTILIZATION_BONUS_EUR_PER_T = float(GRASS_BONUS_DEFAULTS['default_eur_per_wet_tonne'])
DEFAULT_GRASS_UTILIZATION_BONUS_YEARS = int(GRASS_BONUS_DEFAULTS['default_duration_years'])


def _high_direct_capex_basis(tea: dict, units=()) -> float:
    """Build the existing GreenHub high screening CAPEX basis (direct, uninstalled)."""
    lines = tea.get('capex_lines') or []
    total = 0.0
    for line in lines:
        value = line.get('direct_cost_eur')
        if isinstance(value, (int, float)):
            total += float(value)
    r501 = next((unit for unit in units if getattr(unit, 'unit_id', None) == 'R501'), None)
    volume = None
    if r501 is not None:
        item = (getattr(r501, 'design_results', {}) or {}).get('Working volume')
        volume = getattr(item, 'value', None)
    if isinstance(volume, (int, float)):
        # The recorded resolver is at the Dutch tank-cost midpoint (€1,500/m3).
        total += float(volume) * 300.0
    return total


def _annuity_factor(rate: float, years: int) -> float:
    if years <= 0:
        return 0.0
    return float(years) if rate == 0 else (1.0 - (1.0 + rate) ** (-years)) / rate


def _apply_candidate_economics(tea: dict, economics: dict, annual=None, units=()) -> dict:
    """Apply explicit cost, price, tax, capital and support assumptions post-route."""
    # Old saved configurations may still contain improvement knobs. Ignore them
    # rather than allowing historical requests to alter modeled costs or sales.
    economics = {key: value for key, value in economics.items() if key not in {
        'labour_reduction', 'logistics_reduction', 'energy_reduction',
        'protein_yield_uplift', 'nutrient_recovery_uplift',
        'subsidy_rate', 'subsidy_cap_eur', 'eligible_capex_fraction',
    }}
    economics.setdefault('biomethane_bonus_eur_per_m3', DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3)
    economics.setdefault('biomethane_bonus_years', DEFAULT_BIOMETHANE_BONUS_YEARS)
    economics.setdefault('grass_utilization_bonus_eur_per_t_feed', DEFAULT_GRASS_UTILIZATION_BONUS_EUR_PER_T)
    economics.setdefault('grass_utilization_bonus_years', DEFAULT_GRASS_UTILIZATION_BONUS_YEARS)
    economics.setdefault('logistics_cost_eur_per_t_km', 0.0)
    economics.setdefault('logistics_distance_km', 0.0)
    totals = tea.get('totals') or {}
    annual = annual or {}
    original_revenue = float(totals.get('annual_revenue_eur') or 0.0)
    stored_opex_lines = list(tea.get('opex_lines') or [])
    prior_user_cost_lines = [line for line in stored_opex_lines if str(line.get('cost_id') or '').startswith('USER-')]
    base_opex_lines = [line for line in stored_opex_lines if not str(line.get('cost_id') or '').startswith('USER-')]
    # Candidate overlays can be reapplied when a Pareto run pairs the same
    # process result with several support cases. Remove prior user-entered lines
    # from the subtotal first so repeated evaluation is deterministic.
    prior_user_cost_total = sum(float(line.get('annual_cost_eur') or 0.0) for line in prior_user_cost_lines)
    original_opex = max(0.0, float(totals.get('annual_opex_eur') or 0.0) - prior_user_cost_total)
    original_capex = float(totals.get('screening_capital_basis_eur') or totals.get('partial_direct_capex_eur') or 0.0)
    capex_override = economics.get('total_capex_override_eur')
    capex_estimate = _high_direct_capex_basis(tea, units) or totals.get('high_direct_capex_eur') or original_capex
    high_capex = max(0.0, float(capex_override)) if capex_override not in (None, '') else float(capex_estimate)
    annual_feed_t = max(0.0, float((annual.get('feed_processed') or {}).get('value') or 0.0) / 1000.0)
    utility_rows = annual.get('utilities') or {}

    def annual_mwh(name):
        row = utility_rows.get(name) or {}
        value = row.get('value')
        if value is None:
            return None
        unit = str(row.get('unit') or '').lower()
        if 'kwh' in unit:
            return max(0.0, float(value) / 1000.0)
        if 'mwh' in unit:
            return max(0.0, float(value))
        return None

    # Optional rate entries replace the corresponding source-register rows. A
    # missing rate preserves the source model's original item and is never read as zero.
    has_cost_register = bool(base_opex_lines)
    staff_cost = max(0.0, float(economics.get('staffing_people', 5))) * max(0.0, float(economics.get('paid_hours_per_person', 1500))) * max(0.0, float(economics.get('labor_cost_eur_per_person_hour', 47.9)))
    replacements = {'TEA-033': 0.0}
    if has_cost_register:
        replacements['TEA-029'] = 0.0
    user_cost_lines = ([{'cost_id':'USER-LABOR','process_area':'operations','process_step':'Labor',
                        'equipment_or_cost_item':'Staffing at user-entered headcount, paid hours and rate',
                        'annual_cost_eur':staff_cost,'quantity':max(0.0,float(economics.get('staffing_people',5)))*max(0.0,float(economics.get('paid_hours_per_person',1500))),
                        'quantity_unit':'person·hours/year','unit_cost_eur':max(0.0,float(economics.get('labor_cost_eur_per_person_hour',47.9))),
                        'calculation_status':'user_headcount_times_hours_times_hourly_rate'}] if has_cost_register else [])
    electricity_mwh = annual_mwh('electricity')
    heat_mwh = annual_mwh('heating')
    cooling_mwh = annual_mwh('cooling')
    rate_specs = (
        ('electricity_cost_eur_per_mwh', electricity_mwh, ('TEA-036',), 'Electricity', 'MWh/year'),
        ('heat_cost_eur_per_mwh', heat_mwh, ('TEA-037', 'TEA-038'), 'Process heat', 'MWh/year'),
        ('cooling_cost_eur_per_mwh', cooling_mwh, (), 'Cooling', 'MWh/year'),
    )
    for key, quantity, replaced_ids, label, unit in rate_specs:
        rate = economics.get(key)
        if rate not in (None, '') and quantity is not None:
            amount = quantity * max(0.0, float(rate))
            replacements.update({cost_id: 0.0 for cost_id in replaced_ids})
            user_cost_lines.append({'cost_id': f'USER-{key.upper()}', 'process_area': 'utilities', 'process_step': label,
                                    'equipment_or_cost_item': f'{label} at user-entered rate', 'annual_cost_eur': amount,
                                    'quantity': quantity, 'quantity_unit': unit, 'unit_cost_eur': float(rate),
                                    'calculation_status': 'user_rate_times_simulated_demand'})
    logistic_rate = economics.get('logistics_cost_eur_per_t_km')
    logistic_distance = economics.get('logistics_distance_km')
    if (logistic_rate in (None, '')) != (logistic_distance in (None, '')):
        raise ValueError('Logistics override needs both a €/t·km rate and a haul distance in km.')
    if logistic_rate not in (None, '') and logistic_distance not in (None, ''):
        logistics_evidence_present = any(
            line.get('cost_id') == 'TEA-032'
            and line.get('calculation_status') == 'calculated_from_logistics_result'
            for line in base_opex_lines
        )
        explicit_nonzero_override = float(logistic_rate) > 0 or float(logistic_distance) > 0
        if not logistics_evidence_present or explicit_nonzero_override:
            logistics_cost = annual_feed_t * max(0.0, float(logistic_rate)) * max(0.0, float(logistic_distance))
            replacements.update({'TEA-032': 0.0})
            user_cost_lines.append({'cost_id':'USER-LOGISTICS', 'process_area':'feedstock logistics',
                                    'process_step':'Grass transport', 'equipment_or_cost_item':'Wet grass haulage at user-entered rate and distance',
                                    'annual_cost_eur':logistics_cost, 'quantity':annual_feed_t*float(logistic_distance),
                                    'quantity_unit':'wet t·km/year', 'unit_cost_eur':float(logistic_rate),
                                    'calculation_status':'user_rate_times_simulated_tonnes_and_distance'})
    original_lines = base_opex_lines
    replaced_cost = 0.0
    for line in original_lines:
        cost_id = line.get('cost_id')
        if cost_id in replacements:
            replaced_cost += float(line.get('annual_cost_eur') or 0.0)
            line['annual_cost_eur'] = replacements[cost_id]
            line['calculation_status'] = 'replaced_by_user_opex_inputs'
    adjusted_opex = max(0.0, original_opex - replaced_cost + sum(float(row['annual_cost_eur']) for row in user_cost_lines))
    tea['opex_lines'] = [*original_lines, *user_cost_lines]

    base_revenue = original_revenue
    operating_profit = base_revenue - adjusted_opex
    tax_rate = max(0.0, min(1.0, float(economics.get('tax_rate', 0.258))))
    lifetime = max(1, min(200, int(economics.get('project_lifetime_years', 20) or 20)))
    discount = max(0.0, float(economics.get('discount_rate', 0.08)))
    grant_fraction = max(0.0, min(0.60, float(economics.get('capex_grant_fraction', 0.0) or 0.0)))
    capex_grant = high_capex * grant_fraction
    support_years = max(0, min(lifetime, int(economics.get('opex_support_years', 0) or 0)))
    gas_bonus_enabled = bool(economics.get('biomethane_bonus_enabled', False))
    raw_gas_volume = economics.get('annual_biomethane_m3')
    if gas_bonus_enabled and raw_gas_volume in (None, ''):
        raise ValueError('Biomethane bonus requires the simulated annual biomethane volume in m³/year.')
    gas_volume = max(0.0, float(raw_gas_volume or 0.0)) if gas_bonus_enabled else 0.0
    gas_bonus_rate = max(0.0, float(economics.get('biomethane_bonus_eur_per_m3', DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3) or 0.0)) if gas_bonus_enabled else 0.0
    gas_bonus_years = max(0, min(lifetime, int(economics.get('biomethane_bonus_years', DEFAULT_BIOMETHANE_BONUS_YEARS) or 0)))
    gas_bonus_annual = gas_volume * gas_bonus_rate
    additional_annual = max(0.0, float(economics.get('additional_benefit_eur_per_year') or 0.0))
    additional_years = max(0, min(lifetime, int(economics.get('additional_benefit_years', 0) or 0)))
    legacy_premium_per_t = max(0.0, float(economics.get('opex_premium_eur_per_t_feed', 0.0) or 0.0))
    legacy_support = annual_feed_t * legacy_premium_per_t
    grass_bonus_rate = float(economics.get('grass_utilization_bonus_eur_per_t_feed', 0.0) or 0.0)
    if not math.isfinite(grass_bonus_rate) or not 0.0 <= grass_bonus_rate <= MAX_GRASS_UTILIZATION_BONUS_EUR_PER_T:
        raise ValueError('Grass utilization bonus must be between €0 and €50 per wet tonne processed.')
    grass_bonus_years = max(0, min(lifetime, int(economics.get('grass_utilization_bonus_years', 0) or 0)))
    grass_bonus_annual = annual_feed_t * grass_bonus_rate
    operating_support_annual = legacy_support + gas_bonus_annual + grass_bonus_annual
    annual_support_in_effect = operating_support_annual + additional_annual
    profit_during_support = operating_profit + annual_support_in_effect
    effective_gas_bonus_years = gas_bonus_years if gas_bonus_annual > 0 else 0
    effective_grass_bonus_years = grass_bonus_years if grass_bonus_annual > 0 else 0
    effective_additional_years = additional_years if additional_annual > 0 else 0
    support_undiscounted = capex_grant + legacy_support*support_years + gas_bonus_annual*effective_gas_bonus_years + grass_bonus_annual*effective_grass_bonus_years + additional_annual*effective_additional_years
    working_capital = max(0.0, float(economics.get('working_capital_eur', 0.0) or 0.0))
    residual_value = max(0.0, float(economics.get('residual_value_eur', 0.0) or 0.0))
    cashflows = [-(high_capex-capex_grant)-working_capital]
    for year in range(1, lifetime+1):
        support = (legacy_support if year<=support_years else 0.0) + (gas_bonus_annual if year<=effective_gas_bonus_years else 0.0) + (grass_bonus_annual if year<=effective_grass_bonus_years else 0.0) + (additional_annual if year<=effective_additional_years else 0.0)
        pre_tax = operating_profit + support
        cash = pre_tax - max(0.0, pre_tax)*tax_rate
        if year == lifetime:
            cash += residual_value + working_capital
        cashflows.append(cash)
    revenue_complete = totals.get('revenue_status') in (None, 'complete')
    computed_npv = sum(cash/(1.0+discount)**year for year,cash in enumerate(cashflows))
    proxy_npv = computed_npv if revenue_complete else None
    proxy_irr = _irr(cashflows) if revenue_complete else None
    proxy_payback = _payback(cashflows, 0.0) if revenue_complete else None
    capex_grant_pv = capex_grant
    support_pv = legacy_support*_annuity_factor(discount,support_years) + gas_bonus_annual*_annuity_factor(discount,effective_gas_bonus_years) + grass_bonus_annual*_annuity_factor(discount,effective_grass_bonus_years) + additional_annual*_annuity_factor(discount,effective_additional_years)
    total_support_pv = capex_grant_pv + support_pv
    tax_annual = max(0.0, operating_profit+operating_support_annual+additional_annual)*tax_rate
    grant_fraction_applied = capex_grant/high_capex if high_capex else 0.0
    annual_capital_recovery = (high_capex-capex_grant) * (1/lifetime if discount==0 else discount/(1-(1+discount)**(-lifetime)))
    optimized_profit = profit_during_support - tax_annual - annual_capital_recovery
    if capex_override not in (None, ''):
        tea['capex_lines'] = [{'cost_id':'USER-TOTAL-CAPEX','process_area':'Project total','process_step':'Total CAPEX override',
                               'equipment_or_cost_item':'User-entered total project CAPEX','direct_cost_eur':high_capex,
                               'installed_cost_eur':high_capex,'calculation_status':'user_total_capex_override'}]
    totals.update({
        'base_annual_revenue_eur':base_revenue, 'base_annual_opex_eur':original_opex,
        'annual_opex_eur':adjusted_opex, 'annual_revenue_eur':base_revenue,
        'annual_gross_profit_eur':operating_profit, 'net_operating_margin_eur_per_year':operating_profit,
        'ebitda_like_operating_cash_flow_eur_per_year':operating_profit,
        'partial_operating_margin_eur_per_year':operating_profit,
        'operating_profit_before_support_eur_per_year':operating_profit,
        'operating_profit_during_support_eur_per_year':profit_during_support,
        'annual_operating_support_eur_per_year':annual_support_in_effect,
        'optimization_savings_eur_per_year':0.0, 'optimization_revenue_uplift_eur_per_year':0.0,
        'optimized_annual_revenue_eur':base_revenue, 'optimized_annual_opex_eur':adjusted_opex,
        'high_direct_capex_eur':high_capex, 'screening_capital_basis_eur':high_capex,
        'total_capex_override_eur':high_capex if capex_override not in (None, '') else None,
        'total_direct_capex_eur':high_capex if capex_override not in (None, '') else totals.get('total_direct_capex_eur'),
        'partial_direct_capex_eur':high_capex if capex_override not in (None, '') else totals.get('partial_direct_capex_eur'),
        'total_installed_capex_eur':high_capex if capex_override not in (None, '') else totals.get('total_installed_capex_eur'),
        'screening_capital_basis_eur':high_capex,
        'screening_operating_balance_eur_per_year':operating_profit,
        'subsidy_eur':capex_grant, 'subsidy_adjusted_capex_eur':high_capex-capex_grant,
        'capex_grant_fraction_applied':grant_fraction_applied,
        'opex_premium_eur_per_year':operating_support_annual+additional_annual,
        'opex_premium_eur_per_t_feed':legacy_premium_per_t,
        'grass_utilization_bonus_eur_per_year':grass_bonus_annual,
        'grass_utilization_bonus_eur_per_t_feed':grass_bonus_rate,
        'grass_utilization_bonus_years':grass_bonus_years,
        'grass_utilization_bonus_basis':'User-defined logistics grass bonus per wet tonne processed; distinct from CAPEX grants and biomethane support; not an awarded subsidy.',
        'opex_support_years':max(support_years,effective_gas_bonus_years,effective_grass_bonus_years,effective_additional_years),
        'total_public_support_undiscounted_eur':support_undiscounted,
        'total_public_support_pv_eur':total_support_pv,
        'proxy_npv_eur':proxy_npv, 'proxy_irr':proxy_irr, 'proxy_simple_payback_years':proxy_payback,
        'proxy_npv_basis':'After-tax constant-account screening cash flows; explicit CAPEX override where provided, upfront grant, user-rated labor/utilities/logistics, product sales, and time-limited operating support; working capital recovered at end of project.',
        'tax_rate_applied':tax_rate, 'tax_eur_per_year':tax_annual,
        'optimized_after_tax_profit_eur_per_year':optimized_profit,
        'optimization_status':'user_assumption_overlay_no_process_performance_uplifts',
    })
    tea['totals']=totals
    financial=tea.get('financial_kpis') or {}
    financial.update({
        'annual_gross_profit_eur':operating_profit,
        'net_operating_margin_eur_per_year':operating_profit,
        'ebitda_like_operating_cash_flow_eur_per_year':operating_profit,
        'partial_operating_margin_eur_per_year':operating_profit,
        'operating_profit_before_support_eur_per_year':operating_profit,
        'operating_profit_during_support_eur_per_year':profit_during_support,
        'annual_operating_support_eur_per_year':annual_support_in_effect,
        'npv_eur':proxy_npv,'irr':proxy_irr,'simple_payback_years':proxy_payback,
        'financial_kpi_status':'user_assumption_screening_proxy' if revenue_complete else 'incomplete',
        'financial_kpi_basis':totals['proxy_npv_basis'],
        'financial_kpi_blockers':([] if revenue_complete else ['Product revenue is incomplete: validated or explicitly assumed prices are required before investment KPIs can be reported.']),
    })
    tea['financial_kpis']=financial
    tea['cash_flow']=[{'year':year,'cash_flow_eur':cash,'basis':'user-assumption screening proxy'} for year,cash in enumerate(cashflows)]
    tea['candidate_economics']={
        'assumptions':economics, 'optimization_savings_eur_per_year':0.0, 'revenue_uplift_eur_per_year':0.0,
        'subsidy_eur':capex_grant, 'grant_awarding_organization':economics.get('grant_awarding_organization'),
        'operating_support_awarding_organization':economics.get('operating_support_awarding_organization'),
        'grant_scenario_name':economics.get('grant_scenario_name'), 'opex_support_scenario_name':economics.get('opex_support_scenario_name'),
        'high_direct_capex_eur':high_capex, 'capex_estimate_before_override_eur':capex_estimate,
        'capex_grant_fraction_applied':grant_fraction_applied, 'opex_premium_eur_per_year':operating_support_annual+additional_annual,
        'operating_profit_before_support_eur_per_year':operating_profit,
        'operating_profit_during_support_eur_per_year':profit_during_support,
        'biomethane_bonus_eur_per_year':gas_bonus_annual,
        'grass_utilization_bonus_eur_per_year':grass_bonus_annual,
        'grass_utilization_bonus_eur_per_t_feed':grass_bonus_rate,
        'grass_utilization_bonus_years':grass_bonus_years,
        'additional_benefit_eur_per_year':additional_annual,
        'opex_support_years':max(support_years,effective_gas_bonus_years,effective_grass_bonus_years,effective_additional_years),
        'total_public_support_undiscounted_eur':support_undiscounted,'total_public_support_pv_eur':total_support_pv,
        'proxy_npv_eur':proxy_npv,'proxy_irr':proxy_irr,'proxy_simple_payback_years':proxy_payback,
        'proxy_npv_basis':totals['proxy_npv_basis'],'tax_eur_per_year':tax_annual,
        'annual_capital_recovery_after_subsidy_eur':annual_capital_recovery,
        'optimized_after_tax_profit_eur_per_year':optimized_profit,'annual_cash_flows_eur':cashflows,
        'opex_user_cost_lines':user_cost_lines,
    }
    return tea


def default_configuration():
    return {
        'simulation':{'schema_version':'1.0.0','request_id':'decision-support','project_id':'greenhub',
                      'calculation_mode':'structural','resolution_mode':'steady_state','selected_month':'July',
                      'scenarios':{'feed_preparation':'F1','protein_recovery':'PR3','anaerobic_digestion':'AD1','biogas_upgrading':'BG2','nutrient_recovery':'NR4','process_order':'A'},
                      'wet_feed_rate_kg_hr':1000,'plant_capacity_kg_hr':1000,
                      'operating_schedule':{'operating_days_per_week':7,'operating_hours_per_day':24},
                      'export_formats':['json','csv'],'strict_validation':True},
        'project_basis':{'currency':'EUR','price_year':2026,'location':'Netherlands'},
        'tea':{},'financial_assumptions':{'product_prices':{},'use_screening_price_benchmarks':False},
        'candidate_economics':{'biomethane_bonus_enabled':False,'biomethane_bonus_eur_per_m3':DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3,'biomethane_bonus_years':DEFAULT_BIOMETHANE_BONUS_YEARS,'grass_utilization_bonus_eur_per_t_feed':DEFAULT_GRASS_UTILIZATION_BONUS_EUR_PER_T,'grass_utilization_bonus_years':DEFAULT_GRASS_UTILIZATION_BONUS_YEARS,'logistics_cost_eur_per_t_km':0.0,'logistics_distance_km':0.0},
        'use_screening_process_assumptions':False,'use_screening_lca_factors':False,'lca':{},'climate_factors':{},'additional_inventory':[],
        # Optional precomputed logistics evidence; post-route only.
        'logistics_result':None}


def options():
    from Greenhub.storage_reactions import reaction_catalog
    from Greenhub.tea_finance import TEAFinancialAssumptions
    from Greenhub.product_price_benchmarks import product_price_source_references, screening_tea_product_price_ranges, screening_tea_product_prices
    from Greenhub.process_assumption_profile import screening_process_assumption_profile
    return {'defaults':default_configuration(),'biomethane_bonus_default':{'rate_eur_per_m3':DEFAULT_BIOMETHANE_BONUS_EUR_PER_M3,'duration_years':DEFAULT_BIOMETHANE_BONUS_YEARS,'basis':'Midpoint of the supplied €1.28–€2.46/m³ biomethane screening range.','enabled_by_default':False},'tea_basis':asdict(TEAProjectBasis()),
            'product_price_requirements':json.loads((Path(__file__).parents[1]/'data/tea/product_price_requirements.json').read_text())['products'],
            'financial_assumptions':asdict(TEAFinancialAssumptions()),'lca':lca_options(),
            'storage_reactions':reaction_catalog(),
            'screening_tea_product_prices':screening_tea_product_prices(),
            'screening_tea_product_price_ranges':screening_tea_product_price_ranges(),
            'product_price_source_references': {'biomethane_market': product_price_source_references()},
            'screening_price_activation': 'Set financial_assumptions.use_screening_price_benchmarks=true to opt in; optional screening_product_ids limits activated benchmarks to listed products; explicit product_prices override benchmark values.',
            'screening_process_assumptions': screening_process_assumption_profile(),
            'readiness':{'validated_simulation_ready':False,'validated_tea_ready':False,'validated_lca_ready':False},
            'feedstock_options':[{'id':'workbook_grass','label':'Existing seasonal grass workbook'},
                                 {'id':'grass_varta_default','label':'VARTA measured whole-grass profile',
                                  'status':'measured_plus_calculated_wet_basis_nutrients',
                                  'source':'Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_fiber_measurements.csv'},
                                 {'id':'explicit_composition','label':'Explicit wet component fractions (user evidence required)'}],
            'note':'Dynamic uses the existing quasi_dynamic inventory controller; the opt-in dynamic complete proxy remains a separate endpoint.'}


class DecisionSupportService:
    def __init__(self, simulations=None):
        self.simulations=simulations or SimulationService()

    def evaluate(self, configuration):
        config=deepcopy(configuration)
        allowed=set(default_configuration())
        allowed.add('candidate_economics')
        if set(config)-allowed: raise ValueError('Unknown decision support fields: '+', '.join(sorted(set(config)-allowed)))
        if not isinstance(config.get('simulation'),dict): raise ValueError('simulation request object is required.')
        use_screening_process_assumptions = bool(config.pop('use_screening_process_assumptions', False))
        use_screening_lca_factors = bool(config.pop('use_screening_lca_factors', False))
        process_assumption_profile = None
        if use_screening_process_assumptions:
            from Greenhub.process_assumption_profile import screening_process_assumption_profile, screening_storage_conditions
            process_assumption_profile = screening_process_assumption_profile()
            simulation_config = config['simulation'] = deepcopy(config['simulation'])
            if simulation_config.get('storage_conditions') is None:
                simulation_config['storage_conditions'] = screening_storage_conditions()
        project=config.get('project_basis',{})
        if set(project)-{'currency','price_year','location','screening_estimates'}: raise ValueError('Project basis uses currency, price_year, location and screening_estimates; put explicit process quantities in simulation.')
        request=SimulationRequest.from_dict(config['simulation'])
        run_id=self.simulations.create_run(request)
        result=self.simulations.execute_run(run_id)
        annual=build_annual_summary(result,request)
        hours=float(annual['period']['operating_hours']); wet=annual['feed_processed']['value']
        dry=None
        if result.throughput_series:
            states={r['time']:r.get('inlet') for r in result.process_state_series}
            values=[]
            for row in result.throughput_series:
                state=states.get(row['time']); mass=row['actual_throughput_kg']
                if not mass: values.append(0.0)
                elif state and state.get('moisture_fraction') is not None: values.append(mass*(1-state['moisture_fraction']))
                else: break
            if len(values)==len(result.throughput_series): dry=sum(values)
        else:
            stream=next((s for s in result.streams if 'feed' in s.aliases or s.stream_id=='feed'),None)
            if stream and wet is not None:
                water=stream.components.get('Water')
                dry=wet-float(water.value)*hours if water is not None and water.value is not None else None
        tea_basis={**config.get('tea',{}),**project}
        lca_basis={**config.get('lca',{}),'location':project.get('location','Netherlands'),'reference_year':project.get('price_year')}
        for basis in (tea_basis,lca_basis):
            for key,actual in (('operating_hours_per_year',hours),('annual_throughput_kg',wet)):
                if key in basis and basis[key] is not None and actual is not None and abs(basis[key]-actual)>max(1e-6,abs(actual)*1e-8):
                    raise ValueError(f'{key} conflicts with the actual process schedule; post-route analysis cannot override throughput.')
                basis[key]=actual
        lca_basis['annual_dry_feed_kg']=dry
        if result.throughput_series and not annual['period'].get('full_calendar_year'):
            tea_basis['cost_boundary_complete']=False
            lca_basis['inventory_completeness']={key:{'status':'partial','note':'Partial-year simulation; annual inventory is not established.'} for key in lca_basis.get('inventory_completeness',{})}
        finance_config = deepcopy(config.get('financial_assumptions') or {})
        use_benchmarks = bool(finance_config.pop('use_screening_price_benchmarks', False))
        screening_product_ids = finance_config.pop('screening_product_ids', None)
        if use_benchmarks:
            from Greenhub.product_price_benchmarks import screening_tea_product_prices
            benchmark_prices = screening_tea_product_prices()
            if screening_product_ids is not None:
                if not isinstance(screening_product_ids, (list, tuple)) or any(
                    not isinstance(product_id, str) for product_id in screening_product_ids
                ):
                    raise ValueError('financial_assumptions.screening_product_ids must be a list of product IDs.')
                unknown = sorted(set(screening_product_ids) - set(benchmark_prices))
                if unknown:
                    raise ValueError(f'Unknown screening product IDs: {unknown}.')
                selected = set(screening_product_ids)
                benchmark_prices = {
                    product_id: price for product_id, price in benchmark_prices.items()
                    if product_id in selected
                }
            explicit_prices = dict(finance_config.get('product_prices') or {})
            finance_config['product_prices'] = {**benchmark_prices, **explicit_prices}
            finance_config['notes'] = (
                str(finance_config.get('notes') or '')
                + ' Industrial benchmark prices activated as screening assumptions; explicit prices take precedence.'
            ).strip()
        logistics_result = config.get('logistics_result')
        tea=calculate_empirical_tea(result,project_basis=tea_basis,financial_assumptions=finance_config,logistics_result=logistics_result).to_dict()
        tea = _apply_candidate_economics(tea, config.get('candidate_economics') or {}, annual, result.units)
        config['candidate_economics'] = deepcopy(tea['candidate_economics']['assumptions'])
        lca_factors = dict(config.get('climate_factors') or {})
        if use_screening_lca_factors:
            from .lca_service import screening_lca_factors
            lca_factors = {**screening_lca_factors(), **lca_factors}
        lca=calculate_empirical_lca(result,lca_basis,factors=lca_factors,additional_inventory=config.get('additional_inventory',()),logistics_result=logistics_result).to_dict()
        seasonal_checks=all(abs(float(row.get('overall_mass_residual_kg',0)))<=max(1e-5,(wet or 0)*1e-8) for row in result.balance_residual_series)
        storage_checks=all(abs(float(row.get('storage_mass_residual_kg',0)))<=max(1e-5,(wet or 0)*1e-8) for row in result.storage_inventory_series)
        numerical_ok=result.validation.passed and seasonal_checks and storage_checks
        storage_blockers=list(dict.fromkeys(b for row in result.storage_inventory_series for stage in ('incoming_residence','carried_inventory_reactions') for b in (row.get(stage) or {}).get('blockers',[])))
        t=tea['totals']; lt=lca['totals']
        process_evidence = Counter(
            (getattr(getattr(item, 'evidence_class', None), 'value', None)
             or str(getattr(item, 'evidence_class', None) or getattr(item, 'value_status', None) or 'unspecified'))
            for item in result.resolved_parameters
        )
        factor_evidence = Counter(str(item.get('evidence_class') or item.get('source_status') or 'unspecified') for item in lca.get('factors', []))
        maturity_summary={
            'process_model': result.model_maturity,
            'process_parameter_evidence': dict(sorted(process_evidence.items())),
            'tea_status': {'capex': t.get('capex_status'), 'opex': t.get('opex_status'), 'revenue': t.get('revenue_status'), 'profit': t.get('profit_status')},
            'lca_status': {'climate_objective_eligible': lca['readiness'].get('climate_objective_eligible'), 'factor_evidence': dict(sorted(factor_evidence.items())), 'missing_inputs': len(lca.get('missing_inputs', []))},
            'interpretation': 'Counts describe evidence and completeness only; they are not a validation score or TRL estimate.',
        }
        climate_value = lt.get('climate_kg_co2e_per_year')
        if climate_value is None:
            climate_value = lt.get('partial_climate_kg_co2e_per_year')
        economics_result = tea.get('candidate_economics') or {}
        assumptions = economics_result.get('assumptions') or {}
        operating_load_t_co2e = climate_value / 1000.0 if climate_value is not None else None

        def carbon_in_stream_t_y(stream_id):
            stream = next((item for item in result.streams if item.stream_id == stream_id), None)
            if stream is None:
                return 0.0
            carbon_kg_h = 0.0
            for component_id, component_flow in stream.components.items():
                mass = getattr(component_flow, 'value', None)
                if mass is None:
                    continue
                metadata = COMPONENT_METADATA.get(component_id)
                if metadata is not None:
                    carbon_kg_h += float(mass) * metadata.carbon_mass_fraction
            return carbon_kg_h * hours / 1000.0

        fiber_carbon_t_y = carbon_in_stream_t_y('pressed_fibre_cake')
        nutrient_solids_carbon_t_y = carbon_in_stream_t_y('nutrient_rich_digestate_solids')
        soil_retention_fraction = float(assumptions.get('soil_carbon_retention_fraction', 0.10))
        furniture_retention_fraction = float(assumptions.get('furniture_carbon_retention_fraction', 1.0))
        stored_carbon_t_y = (fiber_carbon_t_y * furniture_retention_fraction
                             + nutrient_solids_carbon_t_y * soil_retention_fraction)
        net_carbon_t_c_y = (operating_load_t_co2e * (12.0 / 44.0) - stored_carbon_t_y
                            if operating_load_t_co2e is not None else None)
        carbon_assessment = {
            'fiber_carbon_t_c_per_year': fiber_carbon_t_y,
            'nutrient_rich_solids_carbon_t_c_per_year': nutrient_solids_carbon_t_y,
            'furniture_carbon_retention_fraction': furniture_retention_fraction,
            'soil_carbon_retention_fraction': soil_retention_fraction,
            'total_carbon_stored_t_c_per_year': stored_carbon_t_y,
            'operational_climate_load_t_co2e_per_year': operating_load_t_co2e,
            'net_carbon_t_c_per_year': net_carbon_t_c_y,
            'method': 'Operational climate load converted to t C (12/44) minus assumed furniture carbon stock and soil-retained nutrient-rich-solids carbon.',
            'limitations': ['Furniture conversion losses and end-of-life are excluded.',
                            '10% soil retention is a screening assumption, not measured for this product.',
                            'Protein is not credited because it may be used as feed.',
                            'Operational climate inventory covers only included gate-to-gate groups and declared emission factors.'],
        }
        objectives={
            'operating_profit':{'value':t['annual_revenue_eur']-t['annual_opex_eur'],'direction':'maximize','unit':'EUR/year','eligible':numerical_ok,'definition':'Original modeled annual sales minus partial OPEX, before support, tax and capital recovery; no assumed performance improvements.'},
            'climate':{'value':climate_value,'direction':'minimize','unit':'kg CO2e/year','eligible':numerical_ok and climate_value is not None,'definition':'Attributional plant climate estimate; partial inventory may be used for screening and must be completed before investment decisions'},
            'net_carbon':{'value':net_carbon_t_c_y,'direction':'minimize','unit':'t C/year','eligible':numerical_ok and net_carbon_t_c_y is not None,'definition':'Operational climate load converted from t CO2e to t C, less assumed carbon stored in furniture and soil-retained nutrient-rich solids; screening proxy.'},
            'npv':{'value':economics_result.get('proxy_npv_eur'),'direction':'maximize','unit':'EUR','eligible':numerical_ok and economics_result.get('proxy_npv_eur') is not None,'definition':economics_result.get('proxy_npv_basis','Proxy NPV unavailable; missing financial inputs.')},
            'subsidy_granted':{'value':economics_result.get('total_public_support_pv_eur'),'direction':'minimize','unit':'EUR present value','eligible':numerical_ok and economics_result.get('total_public_support_pv_eur') is not None,'definition':'Present value of the assumed upfront CAPEX grant plus discounted operating-support overlay; the Pareto analysis computes the overlay dynamically from candidate biomethane volume, not as a fixed €/t-feed rate. This is not an eligibility or award estimate.'},
            'installed_capex':{'value':t.get('total_installed_capex_eur'),'direction':'minimize','unit':'EUR','eligible':t.get('capex_status')=='complete_screening'},
            'route_trl':{'value':None,'direction':'maximize','unit':'TRL','eligible':False,'definition':'No evidence-backed route-level TRL aggregation exists; never inferred from component maturity'}}
        root=Path(__file__).resolve().parents[2]
        tracked=('Greenhub/storage_reactions.py','Greenhub/application/seasonal_service.py','Greenhub/application/tea_service.py','Greenhub/data/storage/grass_degradation_reactions.csv','Greenhub/data/tea/tea_cost_register.csv','Greenhub/data/lca/climate_factors.json')
        fingerprint={name:sha256((root/name).read_bytes()).hexdigest() for name in tracked if (root/name).exists()}
        report={'schema_version':'greenhub-decision-support-1.0','run_id':run_id,'configuration':config,
                'analysis_period':annual['period'],
                'scenario_ids':list(request.scenarios.scenario_ids),'model_type':request.resolution_mode.value,
                'annual':annual,'products':[asdict(p) for p in result.products],'balances':[asdict(b) for b in result.balances],
                'process_parameter_evidence':[asdict(p) for p in result.resolved_parameters],
                'state_outputs':{
                    'process_state_snapshots':list(result.process_state_snapshots),
                    'process_state_history':list(result.process_state_history),
                    'unit_state_summaries':list(result.unit_state_summaries),
                    'parameter_sensitivity':list(result.parameter_sensitivity),
                    'equation_usage':list(result.equation_usage),
                    'component_fate':list(result.component_fate),
                    'utility_consumption':list(result.utility_consumption),
                    'inventory_evolution':list(result.inventory_evolution),
                },
                'storage':list(result.storage_inventory_series),'throughput':list(result.throughput_series),
                'tea':tea,'lca':lca,'maturity_summary':maturity_summary,'objectives':objectives,
                'carbon_assessment':carbon_assessment,
                'process_assumption_profile': process_assumption_profile,
                'feasibility':{'numerical_checks_passed':numerical_ok,'route_compatible':True,'storage_blockers':storage_blockers,
                               'eligible_for_ranking':numerical_ok and not storage_blockers,'product_quality_status':'requires_product_specific_evidence'},
                'readiness':{'validated_simulation_ready':False,'scientific_validation':'not established','process_evidence':result.model_maturity},
                'provenance':{'process':result.reproducibility_metadata,'source_hashes':fingerprint},
                'warnings':list(result.warnings) + (['Screening process assumptions were activated; measured or validated values should replace them before investment decisions.'] if process_assumption_profile else []),
                'limitations':list(result.limitations),
                'artifact_name':'decision_support.json'}
        json.dumps(report,allow_nan=False)
        path=self.simulations.repository.get(run_id).run_directory/'decision_support.json'
        path.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
        return report
