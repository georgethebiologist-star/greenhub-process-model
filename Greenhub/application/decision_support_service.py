"""Compose existing process services with read-only post-route analyses."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from collections import Counter
from pathlib import Path

from .contracts import SimulationRequest
from .simulation_service import SimulationService
from .annual_service import build_annual_summary
from .tea_service import calculate_empirical_tea, TEAProjectBasis
from .lca_service import calculate_empirical_lca, lca_options
from Greenhub.component_metadata import COMPONENT_METADATA


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
    """Apply public support to original process economics, without performance uplifts."""
    # Old saved configurations may still contain improvement knobs. Ignore them
    # rather than allowing historical requests to alter modeled costs or sales.
    economics = {key: value for key, value in economics.items() if key not in {
        'labour_reduction', 'logistics_reduction', 'energy_reduction',
        'protein_yield_uplift', 'nutrient_recovery_uplift',
        'subsidy_rate', 'subsidy_cap_eur', 'eligible_capex_fraction',
    }}
    totals = tea.get('totals') or {}
    base_revenue = float(totals.get('annual_revenue_eur') or 0.0)
    base_opex = float(totals.get('annual_opex_eur') or 0.0)
    base_capex = float(totals.get('screening_capital_basis_eur') or totals.get('partial_direct_capex_eur') or 0.0)
    # Public support is never presumed. Pareto cases must carry an explicit
    # grant fraction plus its grant scenario metadata.
    tax_rate = max(0.0, min(1.0, float(economics.get('tax_rate', 0.258))))
    optimized_revenue = base_revenue
    optimized_opex = base_opex
    lifetime = int(economics.get('project_lifetime_years', 20) or 20)
    discount = float(economics.get('discount_rate', 0.08))
    high_capex = _high_direct_capex_basis(tea, units) or totals.get('high_direct_capex_eur') or base_capex
    grant_fraction = economics.get('capex_grant_fraction')
    if grant_fraction is not None:
        grant_fraction = max(0.0, min(0.60, float(grant_fraction)))
        subsidy = high_capex * grant_fraction
        subsidy_capex = max(0.0, high_capex - subsidy)
    else:
        subsidy = 0.0
        subsidy_capex = high_capex
    operating_profit = optimized_revenue - optimized_opex
    after_tax_operating_profit = operating_profit - max(0.0, operating_profit) * tax_rate
    recovery = 1 / lifetime if discount == 0 else discount / (1 - (1 + discount) ** (-lifetime))
    annual_capital_recovery = subsidy_capex * recovery
    optimized_profit = after_tax_operating_profit - annual_capital_recovery
    annual_feed_t = max(0.0, float(((annual or {}).get('feed_processed') or {}).get('value') or 0.0) / 1000.0)
    opex_premium_per_t = max(0.0, float(economics.get('opex_premium_eur_per_t_feed', 0.0) or 0.0))
    support_years = max(0, min(lifetime, int(economics.get('opex_support_years', 15) or 0)))
    annual_opex_premium = annual_feed_t * opex_premium_per_t
    base_cash = optimized_revenue - optimized_opex
    grant_fraction_for_proxy = subsidy / high_capex if high_capex > 0 else 0.0
    annual_cashflows = [-(high_capex - subsidy)]
    annual_cashflows.extend(base_cash + annual_opex_premium for _ in range(support_years))
    annual_cashflows.extend(base_cash for _ in range(max(0, lifetime - support_years)))
    proxy_npv = sum(cash / (1.0 + discount) ** year for year, cash in enumerate(annual_cashflows))
    support_pv = annual_opex_premium * _annuity_factor(discount, support_years)
    subsidy_pv = subsidy + support_pv
    totals.update({
        'base_annual_revenue_eur': base_revenue,
        'base_annual_opex_eur': base_opex,
        'optimization_savings_eur_per_year': 0.0,
        'optimization_revenue_uplift_eur_per_year': 0.0,
        'optimized_annual_revenue_eur': optimized_revenue,
        'optimized_annual_opex_eur': optimized_opex,
        'subsidy_eur': subsidy,
        'subsidy_adjusted_capex_eur': subsidy_capex,
        'high_direct_capex_eur': high_capex,
        'capex_grant_fraction_applied': grant_fraction_for_proxy,
        'opex_premium_eur_per_year': annual_opex_premium,
        'opex_premium_eur_per_t_feed': opex_premium_per_t,
        'opex_support_years': support_years,
        'total_public_support_pv_eur': subsidy_pv,
        'proxy_npv_eur': proxy_npv,
        'proxy_npv_basis': 'Pre-tax constant-account screening cash flow; high direct uninstalled CAPEX less upfront grant; annual partial operating margin; OPEX premium only during stated support years.',
        'tax_rate_applied': tax_rate,
        'tax_eur_per_year': max(0.0, operating_profit) * tax_rate,
        'optimized_after_tax_profit_eur_per_year': optimized_profit,
        'optimization_status': 'support_only_no_performance_uplifts',
    })
    tea['totals'] = totals
    tea['candidate_economics'] = {
        'assumptions': economics,
        'optimization_savings_eur_per_year': 0.0,
        'revenue_uplift_eur_per_year': 0.0,
        'subsidy_eur': subsidy,
        'grant_awarding_organization': economics.get('grant_awarding_organization'),
        'operating_support_awarding_organization': economics.get('operating_support_awarding_organization'),
        'grant_scenario_name': economics.get('grant_scenario_name'),
        'opex_support_scenario_name': economics.get('opex_support_scenario_name'),
        'high_direct_capex_eur': high_capex,
        'capex_grant_fraction_applied': grant_fraction_for_proxy,
        'opex_premium_eur_per_year': annual_opex_premium,
        'opex_support_years': support_years,
        'total_public_support_pv_eur': subsidy_pv,
        'proxy_npv_eur': proxy_npv,
        'proxy_npv_basis': 'Pre-tax constant-account screening cash flow; high direct uninstalled CAPEX less upfront grant; annual partial operating margin; OPEX premium only during stated support years.',
        'tax_eur_per_year': max(0.0, operating_profit) * tax_rate,
        'annual_capital_recovery_after_subsidy_eur': annual_capital_recovery,
        'optimized_after_tax_profit_eur_per_year': optimized_profit,
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
        'tea':{},'financial_assumptions':{'product_prices':{},'use_screening_price_benchmarks':False},'use_screening_process_assumptions':False,'use_screening_lca_factors':False,'lca':{},'climate_factors':{},'additional_inventory':[],
        # Optional precomputed logistics evidence; post-route only.
        'logistics_result':None}


def options():
    from Greenhub.storage_reactions import reaction_catalog
    from Greenhub.tea_finance import TEAFinancialAssumptions
    from Greenhub.product_price_benchmarks import screening_tea_product_price_ranges, screening_tea_product_prices
    from Greenhub.process_assumption_profile import screening_process_assumption_profile
    return {'defaults':default_configuration(),'tea_basis':asdict(TEAProjectBasis()),
            'product_price_requirements':json.loads((Path(__file__).parents[1]/'data/tea/product_price_requirements.json').read_text())['products'],
            'financial_assumptions':asdict(TEAFinancialAssumptions()),'lca':lca_options(),
            'storage_reactions':reaction_catalog(),
            'screening_tea_product_prices':screening_tea_product_prices(),
            'screening_tea_product_price_ranges':screening_tea_product_price_ranges(),
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
