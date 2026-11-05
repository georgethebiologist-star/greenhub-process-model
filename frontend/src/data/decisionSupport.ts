import { apiJson } from './apiClient';
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
  carbon_assessment?: any;
  maturity_summary?: any;
  feasibility: any; readiness: any; warnings: string[]; limitations: string[];
}
export interface Sample {sample_id:string; status:string; error?:string; configuration:Configuration; outputs?:DecisionReport}
export interface Batch {mode:string; seed:number; evaluated_count:number; samples:Sample[]; pareto_fronts:any[]; warning:string}
export function candidateSupportDurations(economics:Record<string,any>, current:{grassUtilizationBonusYears:number;biomethaneBonusYears:number}) {
  return {
    grassUtilizationBonusYears:Number(economics.grass_utilization_bonus_years??current.grassUtilizationBonusYears),
    biomethaneBonusYears:Number(economics.biomethane_bonus_years??economics.opex_support_years??current.biomethaneBonusYears),
  };
}
export function candidateEconomicSettings(economics:Record<string,any>, current:Record<string,any>) {
  const legacyBiomethaneRate=economics.opex_premium_eur_per_nm3_biomethane;
  return {
    totalCapexOverride:economics.total_capex_override_eur??'',
    projectLifetimeYears:Number(economics.project_lifetime_years??current.projectLifetimeYears),
    discountRate:Number(economics.discount_rate??current.discountRate),
    taxRate:Number(economics.tax_rate??current.taxRate),
    capexGrantFraction:Number(economics.capex_grant_fraction??0),
    grassUtilizationBonusEurPerT:Number(economics.grass_utilization_bonus_eur_per_t_feed??0),
    ...candidateSupportDurations(economics,current as {grassUtilizationBonusYears:number;biomethaneBonusYears:number}),
    biomethaneBonusEnabled:economics.biomethane_bonus_enabled==null
      ? Number(legacyBiomethaneRate??0)>0 : Boolean(economics.biomethane_bonus_enabled),
    biomethaneBonusEurM3:Number(economics.biomethane_bonus_eur_per_m3??legacyBiomethaneRate??current.biomethaneBonusEurM3),
    additionalBenefitEurYear:Number(economics.additional_benefit_eur_per_year??0),
    additionalBenefitYears:Number(economics.additional_benefit_years??0),
  };
}
export async function decisionApi<T>(path:string, body?:unknown, method:'GET'|'POST'='POST'):Promise<T> {
  if(method==='GET'||path.replace(/^\/+/, '').split('/')[0]==='options')return apiJson<T>(`/decision-support/${path}`,{method:'GET'});
  return apiJson<T>(`/decision-support/${path}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body??{})});
}
export function buildDecisionConfiguration(base:Configuration, controls:Record<string,any>):Configuration {
  const config=structuredClone(base); const sim=config.simulation;
  config.use_screening_lca_factors=controls.screeningLca===true;
  config.tea={...config.tea,staffing_people:controls.people??5,paid_hours_per_person:1500,screening_estimates:controls.screeningTea!==false};
  config.financial_assumptions={...config.financial_assumptions,use_screening_price_benchmarks:controls.screeningTea!==false};
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
