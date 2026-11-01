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


def _apply_candidate_economics(tea: dict, economics: dict) -> dict:
    """Apply transparent candidate-level screening overlays after the real run."""
    totals = tea.get('totals') or {}
    base_revenue = float(totals.get('annual_revenue_eur') or 0.0)
    base_opex = float(totals.get('annual_opex_eur') or 0.0)
    base_capex = float(totals.get('screening_capital_basis_eur') or totals.get('partial_direct_capex_eur') or 0.0)
    labor = max(0.0, min(0.30, float(economics.get('labour_reduction', 0.0))))
    logistics = max(0.0, min(0.25, float(economics.get('logistics_reduction', 0.0))))
    energy = max(0.0, min(0.25, float(economics.get('energy_reduction', 0.0))))
    yield_uplift = max(0.0, min(0.20, float(economics.get('protein_yield_uplift', 0.0))))
    recovery_uplift = max(0.0, min(0.15, float(economics.get('nutrient_recovery_uplift', 0.0))))
    subsidy_rate = max(0.0, min(0.20, float(economics.get('subsidy_rate', 0.20))))
    subsidy_cap = max(0.0, float(economics.get('subsidy_cap_eur', 250000.0)))
    tax_rate = max(0.0, min(1.0, float(economics.get('tax_rate', 0.258))))
    eligible_fraction = max(0.0, min(1.0, float(economics.get('eligible_capex_fraction', 0.35))))
    savings = base_opex * (0.35 * labor + 0.20 * logistics + 0.45 * energy)
    revenue_uplift = base_revenue * (0.65 * yield_uplift + 0.35 * recovery_uplift)
    optimized_revenue = base_revenue + revenue_uplift
    optimized_opex = max(0.0, base_opex - savings)
    subsidy = min(subsidy_cap, base_capex * eligible_fraction * subsidy_rate)
    subsidy_capex = max(0.0, base_capex - subsidy)
    operating_profit = optimized_revenue - optimized_opex
    after_tax_operating_profit = operating_profit - max(0.0, operating_profit) * tax_rate
    lifetime = int(economics.get('project_lifetime_years', 20) or 20)
    discount = float(economics.get('discount_rate', 0.08) or 0.08)
    recovery = 1 / lifetime if discount == 0 else discount / (1 - (1 + discount) ** (-lifetime))
    annual_capital_recovery = subsidy_capex * recovery
    optimized_profit = after_tax_operating_profit - annual_capital_recovery
    totals.update({
        'base_annual_revenue_eur': base_revenue,
        'base_annual_opex_eur': base_opex,
        'optimization_savings_eur_per_year': savings,
        'optimization_revenue_uplift_eur_per_year': revenue_uplift,
        'optimized_annual_revenue_eur': optimized_revenue,
        'optimized_annual_opex_eur': optimized_opex,
        'subsidy_eur': subsidy,
        'subsidy_adjusted_capex_eur': subsidy_capex,
        'tax_rate_applied': tax_rate,
        'tax_eur_per_year': max(0.0, operating_profit) * tax_rate,
        'optimized_after_tax_profit_eur_per_year': optimized_profit,
        'optimization_status': 'candidate_screening_overlay',
    })
    tea['totals'] = totals
    tea['candidate_economics'] = {
        'assumptions': economics,
        'optimization_savings_eur_per_year': savings,
        'revenue_uplift_eur_per_year': revenue_uplift,
        'subsidy_eur': subsidy,
        'tax_eur_per_year': max(0.0, operating_profit) * tax_rate,
        'annual_capital_recovery_after_subsidy_eur': annual_capital_recovery,
        'optimized_after_tax_profit_eur_per_year': optimized_profit,
    }
    return tea


def default_configuration():
    return {
        'simulation':{'schema_version':'1.0.0','request_id':'decision-support','project_id':'greenhub',
                      'calculation_mode':'structural','resolution_mode':'steady_state','selected_month':'July',
                      'scenarios':{'feed_preparation':'F2','protein_recovery':'PR3','anaerobic_digestion':'AD1','biogas_upgrading':'BG2','nutrient_recovery':'NR4','process_order':'A'},
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
    from Greenhub.product_price_benchmarks import screening_tea_product_prices
    from Greenhub.process_assumption_profile import screening_process_assumption_profile
    return {'defaults':default_configuration(),'tea_basis':asdict(TEAProjectBasis()),
            'product_price_requirements':json.loads((Path(__file__).parents[1]/'data/tea/product_price_requirements.json').read_text())['products'],
            'financial_assumptions':asdict(TEAFinancialAssumptions()),'lca':lca_options(),
            'storage_reactions':reaction_catalog(),
            'screening_tea_product_prices':screening_tea_product_prices(),
            'screening_price_activation': 'Set financial_assumptions.use_screening_price_benchmarks=true to opt in; explicit product_prices override benchmark values.',
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
        if set(project)-{'currency','price_year','location'}: raise ValueError('Project basis uses currency, price_year and location; put explicit process quantities in simulation.')
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
        if use_benchmarks:
            from Greenhub.product_price_benchmarks import screening_tea_product_prices
            benchmark_prices = screening_tea_product_prices()
            explicit_prices = dict(finance_config.get('product_prices') or {})
            finance_config['product_prices'] = {**benchmark_prices, **explicit_prices}
            finance_config['notes'] = (
                str(finance_config.get('notes') or '')
                + ' Industrial benchmark prices activated as screening assumptions; explicit prices take precedence.'
            ).strip()
        logistics_result = config.get('logistics_result')
        tea=calculate_empirical_tea(result,project_basis=tea_basis,financial_assumptions=finance_config,logistics_result=logistics_result).to_dict()
        tea = _apply_candidate_economics(tea, config.get('candidate_economics') or {})
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
        objectives={
            'operating_profit':{'value':t.get('optimized_after_tax_profit_eur_per_year', t.get('net_operating_margin_eur_per_year')),'direction':'maximize','unit':'EUR/year','eligible':numerical_ok and t.get('optimized_after_tax_profit_eur_per_year', t.get('net_operating_margin_eur_per_year')) is not None,'definition':'Candidate-adjusted annual profit after tax, optimization savings and subsidy-adjusted annual capital recovery'},
            'climate':{'value':climate_value,'direction':'minimize','unit':'kg CO2e/year','eligible':numerical_ok and climate_value is not None,'definition':'Attributional plant climate estimate; partial inventory may be used for screening and must be completed before investment decisions'},
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
