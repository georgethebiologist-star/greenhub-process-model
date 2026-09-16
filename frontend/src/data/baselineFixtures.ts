import { runSimulation } from './greenhubData';
import type { AnnualSummary, ResultSourceState, SimulationResult } from '../types';
import type { DynamicOptions, DynamicReport, DynamicScenario, Evidence } from './dynamicComplete';

export const BASELINE_FIXTURE_VERSION = 'greenhub-baseline-2026-09-16';

export const PREVIEW_BASELINE_STATUS: ResultSourceState = {
  status: 'preview_baseline',
  label: 'Preview baseline',
  detail: 'Bundled known-good baseline. This is not a live Python calculation.',
  is_live: false,
  fixture_version: BASELINE_FIXTURE_VERSION,
};

type ScheduleRow = {
  time_label: string; operating_hours: number; available_biomass_tonnes: number;
  processed_biomass_tonnes: number; unused_biomass_tonnes: number;
  utilization_fraction: number; basis_feed_kg_per_hr: number;
};

const scheduleRows: ScheduleRow[] = [
  ['2026-01',0,0,0,0,0,0], ['2026-02',0,0,0,0,0,0], ['2026-03',0,0,0,0,0,0],
  ['2026-04',384,731.494063,731.494063,0,1,1904.932456],
  ['2026-05',744,2801.318648,2801.318648,0,1,3765.213237],
  ['2026-06',720,4900.092193,4900.092193,0,1,6805.683601],
  ['2026-07',744,6779.326588,6779.326588,0,1,9111.998103],
  ['2026-08',744,6712.008052,6712.008052,0,1,9021.516199],
  ['2026-09',720,4756.846082,4756.846082,0,1,6606.730670],
  ['2026-10',744,2666.651329,2666.651329,0,1,3584.208776],
  ['2026-11',360,652.263044,652.263044,0,1,1811.841788], ['2026-12',0,0,0,0,0,0],
].map(([time_label, operating_hours, available_biomass_tonnes, processed_biomass_tonnes, unused_biomass_tonnes, utilization_fraction, basis_feed_kg_per_hr]) => ({
  time_label: String(time_label), operating_hours: Number(operating_hours), available_biomass_tonnes: Number(available_biomass_tonnes),
  processed_biomass_tonnes: Number(processed_biomass_tonnes), unused_biomass_tonnes: Number(unused_biomass_tonnes),
  utilization_fraction: Number(utilization_fraction), basis_feed_kg_per_hr: Number(basis_feed_kg_per_hr),
}));

const dynamicScenario: DynamicScenario = {
  annual_available_biomass_tonnes: 30000, annual_processed_biomass_tonnes: 30000,
  collection_refinery_fraction: 1, feed_basis: 'tonnes_per_year', feed_kg_per_hr: 1000,
  season_start: '2026-04-15', season_end: '2026-11-15', peak_date: '2026-07-31', spread_days: 55,
  full_year: false, active_months: [1,2,3,4,5,6,7,8,9,10,11,12], annualize: false,
  protein_method: 'isoelectric', protein_recovery_fraction: null, drying_method: 'spray_drying_proxy',
  target_product_moisture: 0.15, gas_route: 'water_scrubbing',
  resource_recovery_methods: ['digestate_separation','ammonia_recovery','phosphorus_recovery','potassium_water_concentration','ion_exchange'],
  allow_assumptions: true, show_strict_mode_blockers: true, include_press_cake_in_ad: false,
};

const factorDefaults: Record<string, {value:number; unit:string; source_status:string}> = {
  protein_price:{value:2,unit:'EUR/kg dried product',source_status:'engineering_assumption'}, biomethane_price:{value:.8,unit:'EUR/m3 product gas',source_status:'engineering_assumption'},
  fertilizer_price:{value:.1,unit:'EUR/kg candidate product',source_status:'engineering_assumption'}, press_cake_credit:{value:.03,unit:'EUR/kg external press cake',source_status:'engineering_assumption'},
  electricity_price:{value:.18,unit:'EUR/kWh',source_status:'engineering_assumption'}, heat_price:{value:16,unit:'EUR/GJ',source_status:'engineering_assumption'},
  reagent_cost:{value:0,unit:'EUR/tonne feed',source_status:'engineering_assumption'}, other_utility_cost:{value:0,unit:'EUR/tonne feed',source_status:'engineering_assumption'},
  natural_gas_displacement:{value:2,unit:'kg CO2e/m3 recovered CH4',source_status:'engineering_assumption'}, electricity_emissions:{value:.4,unit:'kg CO2e/kWh',source_status:'engineering_assumption'},
  heat_emissions:{value:56,unit:'kg CO2e/GJ',source_status:'engineering_assumption'}, fertilizer_displacement:{value:.5,unit:'kg CO2e/kg candidate product',source_status:'engineering_assumption'},
  methane_gwp:{value:28,unit:'kg CO2e/kg CH4',source_status:'engineering_assumption'}, unrecovered_methane_emitted_fraction:{value:1,unit:'fraction',source_status:'engineering_assumption'},
};

export const DYNAMIC_BASELINE_OPTIONS: DynamicOptions = {
  defaults: dynamicScenario, protein_methods:['isoelectric','lactic_acid','membrane','heat','generic'],
  drying_methods:['mass_only','spray_drying_proxy','freeze_drying_proxy'],
  gas_routes:['none','common_conditioning','membrane','psa','water_scrubbing','mea','chp_utilities'],
  resource_recovery_methods:['digestate_separation','ammonia_recovery','phosphorus_recovery','potassium_water_concentration','ion_exchange'],
  analysis_factors: factorDefaults,
};

const dynamicAnnual: Record<string, Record<string, number>> = {
  feed_processed:{tonnes_per_year:30000,kg_per_hr:5813.953488}, press_cake:{tonnes_per_year:13125,kg_per_hr:2543.604651}, juice:{tonnes_per_year:13723.41,kg_per_hr:2659.575581},
  ad_feed:{tonnes_per_year:13296.673281,kg_per_hr:2576.874667}, dried_protein_product:{tonnes_per_year:109.947461,kg_per_hr:21.307647}, recovered_protein:{tonnes_per_year:58.478604,kg_per_hr:11.333063},
  digestate:{tonnes_per_year:12036.233324,kg_per_hr:2332.603357}, ammonium_product:{tonnes_per_year:175.412573,kg_per_hr:33.994685}, struvite_candidate:{tonnes_per_year:135.983114,kg_per_hr:26.353317},
  potassium_concentrate:{tonnes_per_year:1808.838534,kg_per_hr:350.550104}, recovered_water:{tonnes_per_year:4791.838929,kg_per_hr:928.650955}, nutrient_rich_solids:{tonnes_per_year:1568.186987,kg_per_hr:303.912207},
  ion_exchange_product:{tonnes_per_year:19.147805,kg_per_hr:3.710815}, final_residual_liquor:{tonnes_per_year:3793.871096,kg_per_hr:735.246337}, methane_slip:{tonnes_per_year:6.890612,kg_per_hr:1.33539},
  raw_biogas:{m3_per_year:1435432.235938,m3_per_hr:278.184542}, methane:{m3_per_year:1250261.477502,m3_per_hr:242.298736}, biomethane:{m3_per_year:1393971.308006,m3_per_hr:270.149478}, biomethane_methane:{m3_per_year:1240634.464125,m3_per_hr:240.433036},
  electricity_demand:{MWh_per_year:420.73077,kWh_per_hr:81.536971}, drying_electricity:{MWh_per_year:47.518389,kWh_per_hr:9.20899}, gas_upgrading_electricity:{MWh_per_year:373.212381,kWh_per_hr:72.327981}, resource_electricity:{MWh_per_year:0,kWh_per_hr:0}, chp_electricity_output:{MWh_per_year:0,kWh_per_hr:0},
  heat_demand:{GJ_per_year:1512.104109,MJ_per_hr:293.043432}, ad_heat:{GJ_per_year:289.893243,MJ_per_hr:56.180861}, drying_heat:{GJ_per_year:1222.210866,MJ_per_hr:236.862571}, gas_heat:{GJ_per_year:0,MJ_per_hr:0}, resource_heat:{GJ_per_year:0,MJ_per_hr:0}, chp_heat_output:{GJ_per_year:0,MJ_per_hr:0},
};

const processEvidence: Evidence[] = [
  evidence('RAW_0001-RAW_0016','Raw press partition policy','direct PRG fresh-mass, water, DM and crude-protein partitions','direct_dataset','direct_grass_source','greenhub_direct_raw_press_component_partitioning.csv','RAW_0001','Source closure is retained; unrecovered press mass is explicit.'),
  evidence('CEN_0011/CEN_0013','First centrifuge debris capture','0.319961 wet sediment; 0.0827 sediment DM','literature_proxy','legume_proxy','greenhub_centrifuge_debris_suspended_protein_capture.csv','CEN_0011','Alfalfa green juice is a proxy for GreenHub brown juice.'),
  evidence('REC-001','Isoelectric protein recovery',0.34,'literature_proxy','N_to_protein_proxy','recovery.csv','REC-001','Precipitated nitrogen is used as a proxy for soluble-protein recovery.'),
  evidence('PCEN_0003','Wet protein cake moisture',0.781,'direct_dataset','direct_grass_source','greenhub_second_centrifuge_protein_capture.csv','PCEN_0003','Direct PRG evidence applies to the pH 3.5 isoelectric-like route.'),
  evidence('BMP_DFOS_VS','Residual methane potential',0.52028,'literature_proxy','supernatant_like_proxy','ad_bmp_observations.csv','BMP_DFOS_VS','de-FOS grass whey BMP applies only to the supernatant-like residual fraction.'),
  evidence('WATER-SCRUBBING-PROXY','Gas upgrading route','water scrubbing','greenhub_legacy_proxy_result','proxy_route','phase6_selected_metrics.csv','BG-WS','Technology performance is not validated at GreenHub composition or scale.'),
  evidence('ASSUMP-NUT-003','Digestate nutrient speciation','retained N/P/K proxy','engineering_assumption','proxy_closure','dynamic_complete_proxy.py','ASSUMP-NUT-003','Fertilizer candidates are not quality-certified products.'),
  evidence('SCENARIO-MOISTURE-015','Dried product moisture target',0.15,'user_input','scenario_input_baseline','','target_product_moisture','Scenario input, not measured drying performance.'),
];

const analysisEvidence = Object.entries(factorDefaults).map(([name, item]) => evidence(`ANALYSIS-${name.toUpperCase()}`,name,item.value,'engineering_assumption','unvalidated illustrative scenario factor','',`analysis_factors.${name}`,'Illustrative placeholder; not a market quote or validated LCA factor.',item.unit));

function evidence(policy_id:string,name:string,value:unknown,source_status:string,certainty_class:string,source_file:string,source_id:string,warning:string,unit='policy value'): Evidence {
  return {policy_id,name,value,unit,source_status,certainty_class,source_file,source_id,warning};
}

function monthlyMetric(annualKey:string, row:ScheduleRow): Record<string,number|null> {
  const annual = dynamicAnnual[annualKey] || {};
  const fraction = row.processed_biomass_tonnes / 30000;
  if ('tonnes_per_year' in annual) {
    const tonnes = annual.tonnes_per_year * fraction;
    return {kg_per_hr: row.operating_hours ? tonnes * 1000 / row.operating_hours : 0, tonnes_per_month: tonnes};
  }
  if ('m3_per_year' in annual) {
    const volume = annual.m3_per_year * fraction;
    return {m3_per_hr: row.operating_hours ? volume / row.operating_hours : 0, m3_per_month: volume};
  }
  if ('MWh_per_year' in annual) {
    const energy = annual.MWh_per_year * fraction;
    return {kWh_per_hr: row.operating_hours ? energy * 1000 / row.operating_hours : 0, MWh_per_month: energy};
  }
  const energy = (annual.GJ_per_year || 0) * fraction;
  return {MJ_per_hr: row.operating_hours ? energy * 1000 / row.operating_hours : 0, GJ_per_month: energy};
}

const dynamicMonthly: DynamicReport['monthly'] = scheduleRows.map(row => ({
  ...row, calendar_hours: new Date(2026, Number(row.time_label.slice(5)), 0).getDate() * 24,
  metrics: Object.fromEntries(Object.keys(dynamicAnnual).map(key => [key, monthlyMetric(key,row)])),
}));

export const DYNAMIC_BASELINE_REPORT: DynamicReport = {
  scenario: dynamicScenario, monthly: dynamicMonthly, annual_summary: dynamicAnnual, annualized_estimate:null,
  biomass_schedule:{monthly:scheduleRows,annual_available_tonnes:30000,annual_processed_tonnes:30000,annual_unused_tonnes:0,utilization_fraction:1,peak_month_processed_tonnes:6779.326588,unmet_target_tonnes:0},
  assumptions:processEvidence, assumption_counts:{user_input:8,engineering_assumption:56,greenhub_legacy_proxy_result:7,direct_dataset:53,literature_proxy:25}, assumptions_count:149,
  top_assumptions:['SCHEDULE-CAP-001','engineering_proxy_closure_v1','BMP_DFOS_VS','ASSUMP-NUT-003','ASSUMP-NUT-004','REPORT-UTILITIES-001'],
  warning_counts:{'complete proxy closure is not measured GreenHub performance':8,'legacy result ratios are internal model references, not experimental truth':8,'validated_simulation_ready remains false':8,'press cake excluded from AD':8,'Gross utility totals exclude unmodelled demands.':1}, warnings_count:251,
  blocker_counts:{},blockers_count:0,readiness:{status:'Proxy-complete preview baseline',validated_simulation_ready:false,can_drive_complete_biosteam_proxy:true,assumptions_enabled:true},
  analysis:{proxy_analysis_ready:true,assumptions:analysisEvidence,warnings:['Preliminary operating proxy only: excludes CAPEX, labour, maintenance, logistics, financing and taxes.','Not a validated TEA or LCA.'],
    economic:{revenue_eur_per_year:{protein_product:219894.921,biomethane:1115177.046,fertilizer_candidates:212023.422,external_press_cake:393750},costs_eur_per_year:{electricity:75731.539,heat:24193.666,reagents:0,other_utilities:0},total_revenue_eur_per_year:1940845.39,total_cost_eur_per_year:99925.204,net_operating_margin_eur_per_year:1840920.185,cost_eur_per_tonne_feed:3.33084,cost_eur_per_kg_dried_protein:.908845,cost_eur_per_m3_biomethane:.071684,allocation_note:'Each intensity divides the same gross included cost by one output; no coproduct allocation.'},
    environmental:{contributions_kg_co2e_per_year:{avoided_natural_gas:-2481268.928,electricity:168292.308,heat:84677.83,fertilizer_displacement:-1060117.11,methane_slip:192937.134},net_kg_co2e_per_year:-3095478.767,kg_co2e_per_tonne_feed:-103.182626,kg_co2e_per_kg_dried_protein:-28.154163}},
};

const empiricalBase = runSimulation({calculation_mode:'structural',selected_month:'July',scenarios:{feed_front_end:'F2',protein_recovery:'PR3',anaerobic_digestion:'AD1',biogas_upgrading:'BG2',nutrient_recovery:'NR4',process_order:'A'}});

function buildEmpiricalAnnual(): AnnualSummary {
  const productRatios: Record<string,number> = {dry_protein_product:.0363293,biomethane:.0334568,phosphorus_product:.01978,ammonium_product:.040257,nutrient_rich_solids:.05,potassium_concentrate:0};
  const monthly = scheduleRows.map(row => {
    const feed = row.processed_biomass_tonnes * 1000;
    return {period:row.time_label,feed_processed_kg:feed,products_kg:Object.fromEntries(Object.entries(productRatios).map(([key,ratio])=>[key,feed*ratio])),intermediate_streams_kg:{pressed_fibre_cake:feed*.395,digestate:feed*.65},volumetric_products_m3:{biomethane:feed*.046468},utilities_kwh:{electricity_kwh:feed*.033248,heating_kwh:feed*.053354,cooling_kwh:feed*.003},mass_residual_kg:feed*.0008};
  });
  const products = Object.fromEntries(Object.entries(productRatios).map(([key,ratio])=>[key,{value:30000000*ratio,unit:'kg/year'}]));
  const schedule = {monthly:scheduleRows.map(row=>({...row,planned_processed_biomass_tonnes:row.processed_biomass_tonnes,actual_processed_biomass_tonnes:row.processed_biomass_tonnes,utilization_percent:row.utilization_fraction*100,operating_hours:row.operating_hours})),annual_available_tonnes:30000,annual_processed_tonnes:30000,annual_unused_tonnes:0,utilization_fraction:1,peak_month_processed_tonnes:6779.326588,peak_throughput_kg_per_hr:9111.998103,policy_id:'shared_normal_distribution_cap_v1',warning:'Saved baseline schedule; not recalculated from current controls.'};
  const chart_data = {
    schedule:schedule.monthly, bulk_streams:monthly.map(r=>({period:r.period,feed_processed_tonnes:r.feed_processed_kg/1000,press_cake_tonnes:r.intermediate_streams_kg.pressed_fibre_cake/1000,digestate_tonnes:r.intermediate_streams_kg.digestate/1000})),
    small_products:monthly.map(r=>({period:r.period,protein_tonnes:r.products_kg.dry_protein_product/1000,phosphorus_product_tonnes:r.products_kg.phosphorus_product/1000,ammonium_product_tonnes:r.products_kg.ammonium_product/1000,potassium_concentrate_tonnes:0,nutrient_rich_solids_tonnes:r.products_kg.nutrient_rich_solids/1000})),
    biomethane:monthly.map(r=>({period:r.period,biomethane_m3:r.volumetric_products_m3.biomethane})), energy:monthly.map(r=>({period:r.period,electricity_MWh:r.utilities_kwh.electricity_kwh/1000,heating_GJ:r.utilities_kwh.heating_kwh*.0036,cooling_GJ:r.utilities_kwh.cooling_kwh*.0036})),
    mass_balance:monthly.map(r=>({period:r.period,closure_percent:r.feed_processed_kg?99.92:100,residual_kg:r.mass_residual_kg})), annual_product_mix:Object.entries(products).filter(([,v])=>v.value>0).map(([product,v])=>({product,tonnes_per_year:v.value/1000})), groups:{large_mass:['feed_processed_tonnes','press_cake_tonnes','digestate_tonnes'],small_products:['protein_tonnes','phosphorus_product_tonnes','ammonium_product_tonnes','potassium_concentrate_tonnes','nutrient_rich_solids_tonnes']},
  };
  return {method:'quasi_dynamic_integration',method_label:'Saved monthly baseline integration',basis:'Bundled baseline generated from the known-good empirical July route and the shared 30,000 t/year schedule. It is not recalculated from current controls.',period:{start_date:'2026-01-01',end_date:'2026-12-31',operating_hours:5160,schedule_source:'Bundled shared seasonal schedule'},feed_processed:{value:30000000,unit:'kg/year'},products,utilities:{electricity:{value:997440,unit:'kWh/year'},heating:{value:1600620,unit:'kWh/year'},cooling:{value:90000,unit:'kWh/year'}},balance:{overall_closure_pct:99.92,process_mass_residual_kg:24000,storage_mass_residual_kg:0,element_residuals_kg:{carbon:0,nitrogen:0,phosphorus:0,potassium:0,sulfur:0},passed:true},monthly,biomass_schedule:schedule,chart_data,display_utilities:{electricity:{value:997.44,unit:'MWh/year'},heating:{value:5762.232,unit:'GJ/year'},cooling:{value:324,unit:'GJ/year'}},process_pathway:[
    {stage_id:'feed',label:'Feed',active_unit_names:['Feed macerator and homogenizer'],unit_count:1,products_kg_hr:{},power_kw:18,heat_duty_kw:12.5,limitations:['Feed composition remains provisional.'],data_quality:'empirical / measured inputs'},
    {stage_id:'pretreatment',label:'Pre-treatment / press',active_unit_names:['Primary dewatering screw press'],unit_count:1,products_kg_hr:{press_cake:2616},power_kw:15,heat_duty_kw:4.2,limitations:['Mechanical split is empirical.'],data_quality:'empirical correlation'},
    {stage_id:'protein',label:'Protein recovery',active_unit_names:['Isoelectric precipitation vessel','Protein decanter centrifuge'],unit_count:2,products_kg_hr:{dry_protein_product:240.5},power_kw:29.5,heat_duty_kw:53,limitations:['Product purity and acid demand need project validation.'],data_quality:'literature defaults'},
    {stage_id:'ad',label:'Anaerobic digestion',active_unit_names:['CSTR digester'],unit_count:1,products_kg_hr:{},power_kw:35,heat_duty_kw:180,limitations:['Kinetics remain empirical.'],data_quality:'empirical model'},
    {stage_id:'gas',label:'Gas upgrading / CHP',active_unit_names:['Biogas compressor','Gas upgrading module'],unit_count:2,products_kg_hr:{biomethane:221.484},power_kw:59.6,heat_duty_kw:17,limitations:['Gas route is a selected empirical configuration.'],data_quality:'literature / vendor proxy'},
    {stage_id:'nutrients',label:'Nutrient recovery / products',active_unit_names:['Digestate centrifuge','Struvite crystallizer','Ammonia stripping and absorption'],unit_count:4,products_kg_hr:{phosphorus_product:130.944,ammonium_product:266.5},power_kw:63,heat_duty_kw:86.5,limitations:['Fertilizer quality and regulatory status are not modelled.'],data_quality:'engineering estimates'},
  ],reporting_status:{model:'empirical_preview_fixture',schedule_policy:'shared_normal_distribution_cap_v1',validated_simulation_ready:false,note:`${BASELINE_FIXTURE_VERSION}; backend-independent preview only.`},warnings:['Backend-independent saved baseline. Current controls have not recalculated these values.','Use a live Python result for engineering decisions.']};
}

export const EMPIRICAL_BASELINE_RESULT: SimulationResult = {
  ...empiricalBase, run_id:'preview-baseline-empirical-2026', timestamp:'2026-09-16T00:00:00.000Z', annual:buildEmpiricalAnnual(),
  validation:{...empiricalBase.validation,status:'warning',issues:[...empiricalBase.validation.issues,{severity:'warning',message:'Bundled preview baseline; backend was not used for this result.'}]},
};

export function cloneEmpiricalBaseline(): SimulationResult { return structuredClone(EMPIRICAL_BASELINE_RESULT); }
export function cloneDynamicBaseline(): DynamicReport { return structuredClone(DYNAMIC_BASELINE_REPORT); }
