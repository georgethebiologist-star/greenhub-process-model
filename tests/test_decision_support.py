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
from Greenhub.application.decision_support_service import DecisionSupportService, default_configuration
from Greenhub.application.simulation_service import SimulationService
from Greenhub.application.contracts import BiomassSchedule, SimulationRequest
from Greenhub.application.biomass_schedule import schedule_feed_rows
from Greenhub.time_grid import generate_time_grid
from Greenhub.scenario_exploration import sample_configurations, pareto_front, run_batch, sensitivity


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
