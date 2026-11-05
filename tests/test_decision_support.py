"""Scientific, accounting and frontend-visible decision support contracts."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import math
from pathlib import Path
import pytest

from Greenhub.storage import apply_storage_conditions
from Greenhub.storage_reactions import reaction_catalog, simulate_reactions
from Greenhub.lca_inventory import LCAProjectBasis, load_climate_factors
from Greenhub.application.lca_service import calculate_lca_inventory
from Greenhub.application.decision_support_service import DecisionSupportService, default_configuration, _apply_candidate_economics
from Greenhub.application.simulation_service import SimulationService
from Greenhub.application.contracts import BiomassSchedule, SimulationRequest
from Greenhub.application.biomass_schedule import schedule_feed_rows
from Greenhub.time_grid import generate_time_grid
from Greenhub.scenario_exploration import sample_configurations, pareto_front, run_batch, sensitivity


def test_economic_overrides_reconcile_costs_support_and_ui_financial_kpis():
    tea={
        'totals':{'annual_revenue_eur':1_000_000,'annual_opex_eur':300_000,'partial_direct_capex_eur':800_000},
        'opex_lines':[
            {'cost_id':'TEA-029','annual_cost_eur':100_000},
            {'cost_id':'TEA-036','annual_cost_eur':50_000},
            {'cost_id':'TEA-038','annual_cost_eur':30_000},
            {'cost_id':'TEA-032','annual_cost_eur':10_000},
            {'cost_id':'TEA-033','annual_cost_eur':1_000},
            {'cost_id':'TEA-OTHER','annual_cost_eur':109_000},
        ],
        'capex_lines':[{'cost_id':'base','direct_cost_eur':800_000}],
        'financial_kpis':{},
    }
    annual={
        'feed_processed':{'value':1_000_000,'unit':'kg/year'},
        'utilities':{
            'electricity':{'value':100_000,'unit':'kWh/year'},
            'heating':{'value':50_000,'unit':'kWh/year'},
            'cooling':{'value':10_000,'unit':'kWh/year'},
        },
    }
    economics={
        'total_capex_override_eur':1_000_000,'capex_grant_fraction':0.30,
        'staffing_people':4,'paid_hours_per_person':1_000,'labor_cost_eur_per_person_hour':50,
        'electricity_cost_eur_per_mwh':200,'heat_cost_eur_per_mwh':80,'cooling_cost_eur_per_mwh':10,
        'logistics_cost_eur_per_t_km':0.1,'logistics_distance_km':20,
        'project_lifetime_years':20,'discount_rate':0.08,'tax_rate':0.25,
        'additional_benefit_eur_per_year':10_000,'additional_benefit_years':5,
        'biomethane_bonus_enabled':True,'annual_biomethane_m3':1_000,
        'biomethane_bonus_eur_per_m3':1.87,'biomethane_bonus_years':3,
    }
    source_tea=deepcopy(tea)
    report=_apply_candidate_economics(tea,economics,annual)
    assert report['totals']['high_direct_capex_eur']==1_000_000
    assert report['totals']['annual_opex_eur']==pytest.approx(335_100)
    assert report['totals']['partial_operating_margin_eur_per_year']==pytest.approx(664_900)
    assert report['candidate_economics']['subsidy_eur']==pytest.approx(300_000)
    assert report['candidate_economics']['proxy_npv_eur'] is not None
    assert report['financial_kpis']['npv_eur']==report['candidate_economics']['proxy_npv_eur']
    assert report['financial_kpis']['irr']==report['candidate_economics']['proxy_irr']
    assert report['candidate_economics']['biomethane_bonus_eur_per_year']==pytest.approx(1_870)
    assert report['totals']['operating_profit_during_support_eur_per_year']==pytest.approx(676_770)
    assert next(row for row in report['opex_lines'] if row['cost_id']=='USER-LOGISTICS')['annual_cost_eur']==pytest.approx(2_000)

    no_support={**economics,'capex_grant_fraction':0,'additional_benefit_eur_per_year':0,'additional_benefit_years':0,'biomethane_bonus_enabled':False}
    baseline=_apply_candidate_economics(deepcopy(source_tea),no_support,annual)
    grant=report['candidate_economics']['subsidy_eur']
    support_annuity=(1-(1+economics['discount_rate'])**(-economics['additional_benefit_years']))/economics['discount_rate']
    gas_annuity=(1-(1+economics['discount_rate'])**(-economics['biomethane_bonus_years']))/economics['discount_rate']
    expected_npv_delta=(grant+economics['additional_benefit_eur_per_year']*(1-economics['tax_rate'])*support_annuity
                        +economics['annual_biomethane_m3']*economics['biomethane_bonus_eur_per_m3']*(1-economics['tax_rate'])*gas_annuity)
    assert report['cash_flow'][0]['cash_flow_eur']-baseline['cash_flow'][0]['cash_flow_eur']==pytest.approx(grant)
    assert report['candidate_economics']['proxy_npv_eur']-baseline['candidate_economics']['proxy_npv_eur']==pytest.approx(expected_npv_delta)
    assert report['totals']['partial_operating_margin_eur_per_year']==baseline['totals']['partial_operating_margin_eur_per_year']
    assert report['totals']['operating_profit_during_support_eur_per_year']>baseline['totals']['operating_profit_during_support_eur_per_year']


def test_logistics_cost_override_requires_both_rate_and_distance():
    with pytest.raises(ValueError,match='both a €/t·km rate and a haul distance'):
        _apply_candidate_economics(
            {'totals':{'annual_revenue_eur':0,'annual_opex_eur':0,'partial_direct_capex_eur':1},'opex_lines':[]},
            {'logistics_cost_eur_per_t_km':0.1,'logistics_distance_km':None},
            {'feed_processed':{'value':1000}},
        )


def test_logistics_costs_default_to_zero_and_replace_legacy_lines():
    tea = {
        'totals': {'annual_revenue_eur': 0, 'annual_opex_eur': 16_000, 'partial_direct_capex_eur': 1},
        'opex_lines': [
            {'cost_id': 'TEA-032', 'annual_cost_eur': 10_000},
            {'cost_id': 'TEA-033', 'annual_cost_eur': 6_000},
        ],
        'capex_lines': [], 'financial_kpis': {},
    }
    report = _apply_candidate_economics(tea, {}, {'feed_processed': {'value': 1_000_000}})
    assert report['totals']['annual_opex_eur'] == pytest.approx(5 * 1500 * 47.9)
    assert all(line['annual_cost_eur'] == 0 for line in report['opex_lines'] if line['cost_id'] in {'TEA-032', 'TEA-033', 'USER-LOGISTICS'})


def test_biomethane_bonus_requires_a_reported_annual_volume():
    with pytest.raises(ValueError,match='requires the simulated annual biomethane volume'):
        _apply_candidate_economics(
            {'totals':{'annual_revenue_eur':0,'annual_opex_eur':0,'partial_direct_capex_eur':1},'opex_lines':[]},
            {'biomethane_bonus_enabled':True},
            {'feed_processed':{'value':1000}},
        )


def test_storage_package_is_source_gated_and_stoichiometric():
    rows=reaction_catalog()
    assert len(rows)==23
    assert not next(r for r in rows if r['reaction_id']=='R14')['mapping_ready']
    assert all(r['source_url'] and r['policy_id'] and r['uncertainty'] for r in rows)
    masses={'Glucose':180.156,'Water':1000}
    config={'storage_days':2,'aerobic_fraction':1,'reaction_ids':['R08'],'allow_assumptions':True,'max_step_days':0.02}
    report=simulate_reactions(masses,config)
    assert report['mass_balance_residual_kg']==pytest.approx(0,abs=1e-8)
    assert report['retained_component_masses_kg']['Glucose']==pytest.approx(180.156*math.exp(-0.2),rel=1e-9)
    assert report['external_oxygen_kg']>0
    assert report['emissions_kg']['CarbonDioxide']>0
    assert report['leaching_kg'] is None
    assert report['validated_simulation_ready'] is False
    with pytest.raises(ValueError,match='allow_assumptions'):
        simulate_reactions(masses,{**config,'allow_assumptions':False})


def test_reaction_network_competition_and_timestep_convergence():
    masses={'Cellulose':100,'Glucose':10,'Water':500}
    config={'storage_days':5,'aerobic_fraction':0.5,'allow_assumptions':True,'reaction_ids':['R01','R02','R08','R09'],'max_step_days':0.02}
    a=simulate_reactions(masses,config); b=simulate_reactions(masses,{**config,'max_step_days':0.01})
    assert a['mass_balance_residual_kg']==pytest.approx(0,abs=1e-8)
    assert all(v>=0 for v in a['retained_component_masses_kg'].values())
    assert a['retained_component_masses_kg']['LacticAcid']==pytest.approx(b['retained_component_masses_kg']['LacticAcid'],rel=0.005)


def test_component_loss_is_export_not_invented_emissions():
    report=apply_storage_conditions({'Water':100,'Cellulose':10},{'storage_days':2,'aerobic_fraction':1,'component_rates':{'Cellulose':{'aerobic':{'value':0.1,'source_status':'engineering_assumption'}}}})
    assert report['total_exported_kg']>0
    assert report['emissions_kg'] is None
    assert report['blockers'] # Water has no rate: unchanged conditionally, not zero kinetics.


def test_daily_supply_integrates_monthly_cap_and_real_dates():
    config=BiomassSchedule(annual_processed_biomass_tonnes=20000)
    daily=schedule_feed_rows(config,generate_time_grid('2026-01-01','2026-12-31','daily'))
    monthly=schedule_feed_rows(config)
    for month in monthly:
        assert sum(r['collected_biomass_kg'] for r in daily if r['time'].startswith(month['time']))==pytest.approx(month['collected_biomass_kg'])
    assert sum(r['available_wet_biomass_kg'] for r in daily)==pytest.approx(30e6)
    assert sum(r['collected_biomass_kg'] for r in daily)==pytest.approx(20e6)


def test_processing_delay_shifts_processing_but_preserves_availability_and_request_value():
    config=BiomassSchedule()
    grid=generate_time_grid('2026-01-01','2026-12-31','monthly')
    immediate=schedule_feed_rows(config,grid,processing_delay_days=0)
    delayed=schedule_feed_rows(config,grid,processing_delay_days=60)
    immediate_by_month={row['time']:row for row in immediate}
    delayed_by_month={row['time']:row for row in delayed}
    assert sum(row['available_wet_biomass_kg'] for row in delayed)==pytest.approx(30e6)
    assert sum(row['collected_biomass_kg'] for row in delayed)==pytest.approx(30e6)
    for month,row in immediate_by_month.items():
        assert delayed_by_month[month]['available_wet_biomass_kg']==pytest.approx(row['available_wet_biomass_kg'])
    assert next(row['time'] for row in immediate if row['collected_biomass_kg']>0)== '2026-04'
    assert next(row['time'] for row in delayed if row['collected_biomass_kg']>0)== '2026-06'
    request=SimulationRequest.from_dict({
        'schema_version':'1.0.0','request_id':'storage-delay-test','project_id':'greenhub',
        'biomass_schedule':{'processing_delay_days':60},
    })
    assert request.biomass_schedule.processing_delay_days==60


def test_daily_processing_series_exposes_fourteen_day_storage_delay():
    from Greenhub.time_grid import generate_time_grid
    config=BiomassSchedule(
        annual_available_biomass_tonnes=30000,
        annual_processed_biomass_tonnes=30000,
        season_start='2026-04-15',season_end='2026-11-15',
        peak_date='2026-07-31',spread_days=55,
    )
    grid=generate_time_grid('2026-01-01','2026-12-31','daily')
    rows=schedule_feed_rows(config,grid,processing_delay_days=14)
    first_available=next(row['time'] for row in rows if row['available_wet_biomass_kg']>0)
    first_processing=next(row['time'] for row in rows if row['collected_biomass_kg']>0)
    assert first_available=='2026-04-15'
    assert first_processing=='2026-04-29'
    assert sum(row['available_wet_biomass_kg'] for row in rows)==pytest.approx(30e6)
    assert sum(row['collected_biomass_kg'] for row in rows)==pytest.approx(30e6)


def test_weekly_processing_series_shows_storage_shift_without_daily_run_cost():
    config=BiomassSchedule(
        annual_available_biomass_tonnes=30000,
        annual_processed_biomass_tonnes=30000,
        season_start='2026-04-15',season_end='2026-11-15',
        peak_date='2026-07-31',spread_days=55,
    )
    grid=generate_time_grid('2026-01-01','2026-12-31','weekly')
    rows=schedule_feed_rows(config,grid,processing_delay_days=14)
    first_available=next(row['time'] for row in rows if row['available_wet_biomass_kg']>0)
    first_processing=next(row['time'] for row in rows if row['collected_biomass_kg']>0)
    assert first_available=='2026-04-15'
    assert first_processing=='2026-04-29'
    assert len(rows)<60
    assert sum(row['available_wet_biomass_kg'] for row in rows)==pytest.approx(30e6)
    assert sum(row['collected_biomass_kg'] for row in rows)==pytest.approx(30e6)


@pytest.mark.parametrize('values,total', [
    ({'Water':0.855,'Cellulose':0.045},0.90),
    ({'Water':0.99,'Cellulose':0.11},1.10),
])
def test_feed_composition_near_100_percent_is_normalized(values,total):
    request=SimulationRequest.from_dict({
        'schema_version':'1.0.0','request_id':'feed-composition-test','project_id':'greenhub',
        'feed_composition':values,
    })
    assert sum(request.feed_composition.values())==pytest.approx(1.0)
    assert request.feed_composition['Water']==pytest.approx(values['Water']/total)
    assert request.feed_composition['Cellulose']==pytest.approx(values['Cellulose']/total)


@pytest.mark.parametrize('total_percent', [90.0, 110.0])
def test_complete_canonical_profile_normalizes_at_90_and_110_percent(total_percent):
    profile_path=Path(__file__).parents[1]/'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json'
    profile=json.loads(profile_path.read_text(encoding='utf-8'))['compounds']
    composition={key:row['wet_mass_fraction'] for key,row in profile.items()}
    composition['Water']+=(total_percent/100.0)-1.0
    request=SimulationRequest.from_dict({
        'schema_version':'1.0.0','request_id':f'complete-feed-boundary-{total_percent:g}','project_id':'greenhub',
        'feed_composition':composition,
    })
    assert set(request.feed_composition)==set(profile)
    assert sum(request.feed_composition.values())==pytest.approx(1.0)
    assert request.feed_composition['Water']==pytest.approx(composition['Water']/(total_percent/100.0))


@pytest.mark.parametrize('values,total', [
    ({'Water':0.845,'Cellulose':0.045},0.89),
    ({'Water':1.0,'Cellulose':0.11},1.11),
])
def test_feed_composition_outside_normalization_window_is_rejected(values,total):
    with pytest.raises(ValueError,match='between 0.90 and 1.10'):
        SimulationRequest.from_dict({
            'schema_version':'1.0.0','request_id':'feed-composition-test','project_id':'greenhub',
            'feed_composition':values,
        })


@pytest.mark.parametrize('value', [True, '0.5', float('nan'), float('inf'), -0.1])
def test_feed_composition_rejects_non_numeric_boolean_or_invalid_values(value):
    with pytest.raises(ValueError, match='feed_composition values'):
        SimulationRequest.from_dict({
            'schema_version':'1.0.0','request_id':'feed-composition-invalid-test','project_id':'greenhub',
            'feed_composition':{'Water':value},
        })


def test_feed_composition_rejects_noncanonical_compound_ids():
    with pytest.raises(ValueError, match='unknown compounds'):
        SimulationRequest.from_dict({
            'schema_version':'1.0.0','request_id':'feed-composition-unknown-test','project_id':'greenhub',
            'feed_composition':{'Water':0.9,'UnrecognizedCompound':0.1},
        })


def test_feed_composition_defaults_match_backend_wet_mass_basis():
    from Greenhub.application.contracts.requests import (
        FEED_COMPOSITION_MAX_TOTAL,
        FEED_COMPOSITION_MIN_TOTAL,
        FEED_COMPOSITION_NORMALIZED_TOTAL,
    )
    profile_path=Path(__file__).parents[1]/'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json'
    profile_document=json.loads(profile_path.read_text(encoding='utf-8'))
    profile=profile_document['compounds']
    limits=profile_document['composition_limits']
    assert FEED_COMPOSITION_MIN_TOTAL==pytest.approx(limits['minimum_total_fraction'])
    assert FEED_COMPOSITION_MAX_TOTAL==pytest.approx(limits['maximum_total_fraction'])
    assert FEED_COMPOSITION_NORMALIZED_TOTAL==pytest.approx(limits['normalized_total_fraction'])
    displayed_percent={key:row['wet_mass_fraction']*100 for key,row in profile.items()}
    entered_total=sum(displayed_percent.values())
    assert entered_total==pytest.approx(100.0)
    normalized={key:value/entered_total for key,value in displayed_percent.items()}
    request=SimulationRequest.from_dict({
        'schema_version':'1.0.0','request_id':'feed-default-profile-test','project_id':'greenhub',
        'feed_composition':normalized,
    })
    assert request.feed_composition==pytest.approx({key:row['wet_mass_fraction'] for key,row in profile.items()})
    assert all(row['model_baseline_percent']==pytest.approx(row['wet_mass_fraction']*100) for row in profile.values())


def test_omitted_and_empty_feed_composition_use_the_canonical_reset_profile():
    profile_path=Path(__file__).parents[1]/'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json'
    profile=json.loads(profile_path.read_text(encoding='utf-8'))['compounds']
    expected={key:row['wet_mass_fraction'] for key,row in profile.items()}
    for payload_value in ('omitted', {}):
        payload={
            'schema_version':'1.0.0','request_id':f'feed-default-{payload_value!s}','project_id':'greenhub',
        }
        if payload_value != 'omitted':
            payload['feed_composition']=payload_value
        request=SimulationRequest.from_dict(payload)
        assert request.feed_composition==pytest.approx(expected)


def test_weekly_chart_adapter_keeps_real_model_throughput_and_products():
    from types import SimpleNamespace
    from Greenhub.application.annual_service import _interval_chart_rows
    result=SimpleNamespace(
        throughput_series=({'time':'2026-04-29','actual_throughput_kg':1250.0},),
        product_series=({'time':'2026-04-29','products_kg':{'dry_protein_product':5.0},
                         'intermediate_streams_kg':{'pressed_fibre_cake':600.0},
                         'volumetric_products_m3':{'biomethane':1.5}},),
        utility_series=({'time':'2026-04-29','electricity_kwh':8.0,'heating_kwh':9.0,'cooling_kwh':10.0},),
        balance_residual_series=({'time':'2026-04-29','overall_mass_residual_kg':0.0},),
    )
    row=_interval_chart_rows(result)[0]
    assert row['feed_processed_kg']==1250.0
    assert row['products_kg']['dry_protein_product']==5.0
    assert row['intermediate_streams_kg']['pressed_fibre_cake']==600.0
    assert row['volumetric_products_m3']['biomethane']==1.5
    assert row['utilities_kwh']['electricity_kwh']==8.0


def scoped_basis():
    excluded={g:'Outside explicit gas-only unit-test boundary.' for g in ('electricity','heat','materials','transport','storage_emissions','waste','feedstock_production','equipment')}
    return LCAProjectBasis(included_groups=('process_emissions',),exclusions=excluded,boundary='Gas-only characterization fixture',annual_throughput_kg=1000,annual_dry_feed_kg=200,inventory_completeness={'process_emissions':{'status':'complete','note':'Single synthetic methane emission inventory.'}})


def test_climate_inventory_not_zero_or_double_counted():
    flow={'flow_id':'methane','group':'process_emissions','quantity':2,'unit':'kg','factor_id':'biogenic_methane','accounting_key':'methane_air','source_id':'synthetic_test'}
    report=calculate_lca_inventory([flow],scoped_basis()).to_dict()
    assert report['totals']['climate_kg_co2e_per_year']==54
    assert report['totals']['kg_co2e_per_tonne_dry_feed']==270
    assert report['readiness']['validated_lca_ready'] is False
    partial=calculate_lca_inventory([{**flow,'factor_id':'missing'}],scoped_basis()).to_dict()
    assert partial['totals']['climate_kg_co2e_per_year'] is None
    with pytest.raises(ValueError,match='Duplicate'): calculate_lca_inventory([flow,flow],scoped_basis())
    with pytest.raises(ValueError,match='metadata'): load_climate_factors({'electricity':0.4})


def test_seeded_sampling_correlations_and_pareto_missing_objectives():
    specs=[{'path':'x','low':0,'high':1,'correlation_group':'linked'},{'path':'y','low':0,'high':2,'correlation_group':'linked'}]
    a=sample_configurations({},specs,8,17); assert a==sample_configurations({},specs,8,17)
    assert sorted(int(r['x']*8) for r in a)==list(range(8))
    assert all(r['y']==2*r['x'] for r in a)
    assert a!=sample_configurations({},specs,8,17,'uncertainty')
    def sample(i,profit,impact,eligible=True):
        return {'sample_id':i,'outputs':{'feasibility':{'eligible_for_ranking':True},'objectives':{'profit':{'value':profit,'eligible':eligible,'direction':'maximize'},'climate':{'value':impact,'eligible':True,'direction':'minimize'}}}}
    front=pareto_front([sample('loss',-5,1),sample('best',5,2),sample('dominated',1,3),sample('missing',None,0,False)],'profit','climate')
    assert {p['sample_id'] for p in front['points']}=={'loss','best'}
    assert front['excluded'][0]['sample_id']=='missing'
    assert front['objective_metadata']['x']['direction']=='maximize'
    assert front['objective_metadata']['y']['direction']=='minimize'


def test_scenario_reports_include_feasibility_counts_and_sensitivity_deltas():
    def evaluator(config):
        value = config["x"]
        return {
            "feasibility": {"eligible_for_ranking": value >= 0},
            "objectives": {
                "operating_profit": {"value": value * 10, "eligible": True, "direction": "maximize"},
            },
        }

    batch = run_batch(evaluator, {"x": 0}, [{"path": "x", "low": -1, "high": 1}], count=4, seed=3)
    assert batch["feasibility_summary"]["evaluated_count"] == 4
    assert batch["feasibility_summary"]["technically_feasible_count"] == 2
    report = sensitivity(evaluator, {"x": 1}, [{"path": "x", "values": [2]}])
    assert report["variations"][0]["objective_deltas"]["operating_profit"] == 10


@pytest.fixture(scope='module')
def integrated(tmp_path_factory):
    service=DecisionSupportService(SimulationService(run_root=tmp_path_factory.mktemp('decision_runs')))
    config=default_configuration()
    config['simulation']['operating_schedule']['operating_dates']=[f'2026-07-{day:02d}' for day in range(1,32)]
    static=service.evaluate(config)
    profile={'profile_id':'steady_july','resolution':'monthly','points':[{'period':'2026-07','available_wet_biomass_kg':744000}]}
    service.simulations.feed_profiles.register_mapping(profile)
    dynamic=deepcopy(config)
    dynamic['simulation'].update(resolution_mode='quasi_dynamic',start_date='2026-07-01',end_date='2026-07-31',time_step='monthly',feed_supply_profile_id='steady_july')
    return service,config,static,service.evaluate(dynamic)


def test_steady_and_dynamic_equivalence_and_readiness(integrated):
    service,config,static,dynamic=integrated
    assert static['scenario_ids']==dynamic['scenario_ids']
    assert set(static['state_outputs']) == {
        'process_state_snapshots', 'process_state_history', 'unit_state_summaries',
        'parameter_sensitivity', 'equation_usage', 'component_fate',
        'utility_consumption', 'inventory_evolution',
    }
    assert static['state_outputs']['process_state_snapshots']
    assert dynamic['state_outputs']['process_state_history']
    assert static['maturity_summary']['process_model']
    assert static['maturity_summary']['process_parameter_evidence']
    assert 'tea_status' in static['maturity_summary']
    assert 'lca_status' in static['maturity_summary']
    assert static['annual']['feed_processed']['value']==pytest.approx(744000)
    assert dynamic['annual']['feed_processed']['value']==pytest.approx(744000)
    for key,value in static['annual']['products'].items():
        assert dynamic['annual']['products'][key]['value']==pytest.approx(value['value'],rel=1e-8,abs=1e-7)
    assert static['readiness']['validated_simulation_ready'] is False
    assert static['tea']['totals']['partial_direct_capex_eur']>=0
    assert static['tea']['financial_kpis']['npv_eur'] is None
    assert static['lca']['totals']['climate_kg_co2e_per_year'] is None
    assert 'C:\\' not in json.dumps(static,allow_nan=False)


def test_postroute_does_not_mutate_process_and_api_contract(integrated,tmp_path):
    from api.app import create_app
    from test_api_v1 import invoke
    service,config,report,dynamic=integrated
    result=service.simulations.repository.get(report['run_id']).result
    before=result.to_dict()
    from Greenhub.application.tea_service import calculate_empirical_tea
    calculate_empirical_tea(result,project_basis={'operating_hours_per_year':744})
    assert before==result.to_dict()
    app=create_app(tmp_path)
    status,options=invoke(app,'GET','/api/v1/decision-support/options')
    assert status==200 and len(options['storage_reactions'])==23
    status,error=invoke(app,'POST','/api/v1/decision-support/evaluate',{'configuration':{'simulation':{'bad':True}}})
    assert status==422 and error['error']['message']


def test_decision_support_forwards_optional_logistics_evidence(integrated):
    service, config, _static, _dynamic = integrated
    configured = deepcopy(config)
    configured['logistics_result'] = {
        'transport_cost_currency': 1234.5,
        'emissions_kg_co2': 456.0,
        'limitations': [],
    }
    report = service.evaluate(configured)
    logistics_lines = [line for line in report['tea']['opex_lines'] if line.get('cost_type') == 'logistics']
    assert logistics_lines
    assert any(line['calculation_status'] == 'calculated_from_logistics_result' for line in logistics_lines)
    transport = [row for row in report['lca']['inventory'] if row['flow_id'] == 'feedstock_transport']
    assert len(transport) == 1
    assert transport[0]['quantity'] == pytest.approx(456.0)


def test_baseline_process_has_not_changed():
    from Greenhub.integration import create_integrated_greenhub_system
    old=json.loads(Path('Greenhub/results/decision_support_baseline_before.json').read_text())
    model=create_integrated_greenhub_system(scenario_id='NR4',biogas_upgrading_scenario_id='BG2',anaerobic_digestion_scenario_id='AD1',protein_recovery_scenario_id='PR3',feed_preparation_scenario_id='F2',selected_month='July').simulate()
    for name,mass in old['streams_kg_hr'].items():
        assert float(model.streams[name].F_mass)==pytest.approx(mass,rel=1e-10,abs=1e-9)
