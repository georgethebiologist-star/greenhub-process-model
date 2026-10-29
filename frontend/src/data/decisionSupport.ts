import { API_BASE, apiJson } from './apiClient';
export type Configuration = Record<string, any>;
export interface DecisionReport {
  run_id: string; configuration: Configuration; scenario_ids: string[]; model_type: string;
  annual: any; products: any[]; balances: any[]; storage: any[]; throughput: any[];
  state_outputs?: {
    process_state_snapshots?: any[]; process_state_history?: any[]; unit_state_summaries?: any[];
    parameter_sensitivity?: any[]; equation_usage?: any[]; component_fate?: any[];
    utility_consumption?: any[]; inventory_evolution?: any[];
  };
  tea: any; lca: any; objectives: Record<string, {value: number|null; eligible:boolean; unit:string; direction:string}>;
  maturity_summary?: any;
  feasibility: any; readiness: any; warnings: string[]; limitations: string[];
}
export interface Sample {sample_id:string; status:string; error?:string; configuration:Configuration; outputs?:DecisionReport}
export interface Batch {mode:string; seed:number; evaluated_count:number; samples:Sample[]; pareto_fronts:any[]; warning:string}
export async function decisionApi<T>(path:string, body?:unknown):Promise<T> {
  return apiJson<T>(`/decision-support/${path}`,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
}
export function buildDecisionConfiguration(base:Configuration, controls:Record<string,any>):Configuration {
  const config=structuredClone(base); const sim=config.simulation;
  config.use_screening_lca_factors=controls.screeningLca===true;
  sim.resolution_mode=controls.model; sim.wet_feed_rate_kg_hr=controls.feedRate; sim.plant_capacity_kg_hr=controls.capacity;
  sim.operating_schedule={operating_days_per_week:controls.days,operating_hours_per_day:controls.hours,target_throughput_kg_hr:controls.feedRate};
  if(controls.model==='quasi_dynamic') {
    sim.start_date=`${controls.start.slice(0,4)}-01-01`; sim.end_date=`${controls.end.slice(0,4)}-12-31`; sim.time_step=controls.timeStep;
    sim.biomass_schedule={annual_available_biomass_tonnes:controls.available,annual_processed_biomass_tonnes:controls.target,
      collection_refinery_fraction:controls.collection,season_start:controls.start,season_end:controls.end,peak_date:controls.peak,spread_days:55};
  } else {for(const key of ['start_date','end_date','time_step','biomass_schedule']) delete sim[key];}
  sim.storage_conditions=controls.storageEnabled?{model:'grass_reactions',storage_days:controls.storageDays,aerobic_fraction:controls.aerobic,allow_assumptions:true,moisture_activity:controls.activity,temperature_c:controls.temperature}:null;
  sim.feed_composition=controls.customFeed?JSON.parse(controls.composition):{};
  return config;
}
export function exportDecision(value:unknown,name:string) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));
  const link=document.createElement('a'); link.href=url;link.download=name;link.click();URL.revokeObjectURL(url);
}
