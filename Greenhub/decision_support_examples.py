"""Run reproducible examples: python -m Greenhub.decision_support_examples."""
from copy import deepcopy
import argparse
import json
from pathlib import Path

from .application.decision_support_service import DecisionSupportService, default_configuration
from .application.simulation_service import SimulationService
from .scenario_exploration import run_batch, sensitivity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='Greenhub/results/decision_support')
    parser.add_argument('--count',type=int,default=8)
    args=parser.parse_args(); root=Path(args.output); root.mkdir(parents=True,exist_ok=True)
    service=DecisionSupportService(SimulationService(run_root=root/'runs'))
    def save(name,value): (root/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
    static=default_configuration(); save('static',service.evaluate(static))
    dynamic=deepcopy(static)
    dynamic['simulation'].update(resolution_mode='quasi_dynamic',start_date='2026-01-01',end_date='2026-12-31',time_step='monthly',wet_feed_rate_kg_hr=10000,plant_capacity_kg_hr=10000,
        biomass_schedule={'annual_available_biomass_tonnes':30000,'annual_processed_biomass_tonnes':30000,'season_start':'2026-04-15','season_end':'2026-11-15','peak_date':'2026-07-31'})
    dynamic['simulation']['operating_schedule']['target_throughput_kg_hr']=10000
    save('dynamic',service.evaluate(dynamic))
    storage=deepcopy(static)
    storage['simulation']['storage_conditions']={'model':'grass_reactions','storage_days':2,'aerobic_fraction':0.5,'allow_assumptions':True,'moisture_activity':1,'temperature_c':20}
    save('storage',service.evaluate(storage))
    designs=[{'path':'simulation.wet_feed_rate_kg_hr','low':500,'high':1500},
             {'path':'simulation.plant_capacity_kg_hr','low':800,'high':1600},
             {'path':'simulation.operating_schedule.operating_hours_per_day','low':8,'high':24},
             {'path':'simulation.scenarios.protein_recovery','distribution':'categorical','choices':['PR1','PR3']},
             {'path':'simulation.scenarios.biogas_upgrading','distribution':'categorical','choices':['BG2','BG3']},
             {'path':'simulation.storage_conditions.storage_days','low':0,'high':7},
             {'path':'simulation.storage_conditions.aerobic_fraction','low':0,'high':1}]
    batch=run_batch(service.evaluate,storage,designs,args.count,42,'design',180); save('design_batch',batch)
    # Uncertainty is explicitly a hypothetical assay uncertainty, not design search.
    uncertainty=[{'path':'simulation.wet_feed_rate_kg_hr','distribution':'triangular','low':950,'mode':1000,'high':1050,
                  'basis':'Hypothetical +/-5% flow-meter uncertainty; illustrative, not measured.'}]
    save('uncertainty',run_batch(service.evaluate,static,uncertainty,min(args.count,8),43,'uncertainty',120))
    save('sensitivity',sensitivity(service.evaluate,static,[{'path':'simulation.wet_feed_rate_kg_hr','values':[500,1500]}]))
    summary={'static':'static.json','dynamic':'dynamic.json','storage':'storage.json','design':'design_batch.json','uncertainty':'uncertainty.json','sensitivity':'sensitivity.json',
             'note':'Illustrative process scenarios. Economic/environmental objectives remain excluded when evidence is incomplete; no fabricated profit/climate Pareto front.'}
    save('manifest',summary); print(json.dumps(summary))


if __name__=='__main__': main()
