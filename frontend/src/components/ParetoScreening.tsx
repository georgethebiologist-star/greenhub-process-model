import React,{useEffect,useMemo,useState} from 'react';
import {Bar,CartesianGrid,ComposedChart,Legend,Line,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis} from 'recharts';
import {apiJson} from '../data/apiClient';
import {displayQualityClass} from '../data/qualityClass';
import './decisionSupport.css';

const palette={ink:'#0c3338',rose:'#d277a3',green:'#408f4d',blue:'#729ad2',amber:'#d1a520',muted:'#71817a',grid:'#d8ded8'};
const fmt=(v:any,d=0)=>v==null||!Number.isFinite(Number(v))?'—':Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const money=(v:any)=>v==null||!Number.isFinite(Number(v))?'—':new Intl.NumberFormat(undefined,{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(Number(v));
const productFilters=[['protein','Protein'],['biogas','Biomethane'],['nitrogen','Ammonium'],['phosphorus','Struvite'],['potassium','Potassium']] as const;
type Candidate=any;
type Props={onApplyCandidate:(candidate:Candidate)=>void; applying?:boolean};

function routeOf(row:Candidate){return row?.configuration?.simulation?.scenarios||{};}
function hasProduct(row:Candidate,key:string){
  const s=routeOf(row),nr=s.nutrient_recovery;
  if(key==='protein')return Boolean(s.protein_recovery&&s.protein_recovery!=='PR0');
  if(key==='biogas')return ['BG2','BG3','BG4','BG5','BG6'].includes(s.biogas_upgrading);
  if(key==='nitrogen')return ['NR3','NR4','NR6','NR7'].includes(nr);
  if(key==='phosphorus')return ['NR2','NR4','NR5','NR7'].includes(nr);
  return nr==='NR7';
}
function productName(row:Candidate){
  const present=productFilters.filter(([key])=>hasProduct(row,key)).map(([,label])=>label);
  return present.length?present.join(' · '):'No recovery products';
}
export function pareto(rows:Candidate[],x:(row:Candidate)=>number){
  return rows.filter(a=>!rows.some(b=>b!==a&&x(b)<=x(a)&&Number(b.values.npv)>=Number(a.values.npv)&&(x(b)<x(a)||Number(b.values.npv)>Number(a.values.npv))));
}
export function collectParetoGroupCandidates(groupData:any):Candidate[]{
  const byId=new Map<string,Candidate>();
  const add=(row:Candidate)=>{
    if(!row?.sample_id)return;
    const previous=byId.get(row.sample_id);
    byId.set(row.sample_id,previous?{
      ...previous,...row,
      seasonal_feed_profile:row.seasonal_feed_profile?.length?row.seasonal_feed_profile:previous.seasonal_feed_profile,
      seasonal_availability_profile:row.seasonal_availability_profile??previous.seasonal_availability_profile,
    }:row);
  };
  for(const row of groupData?.scenario_catalog||[])add(row);
  for(const rows of Object.values(groupData?.selected_candidates||{}))if(Array.isArray(rows))for(const row of rows as Candidate[])add(row);
  return [...byId.values()];
}
export const PARETO_PLOT_LIMIT=200;
function evenlySample<T>(rows:T[],limit:number):T[]{
  if(rows.length<=limit)return rows;
  if(limit<=0)return [];
  if(limit===1)return [rows[Math.floor((rows.length-1)/2)]];
  return Array.from({length:limit},(_,index)=>rows[Math.round(index*(rows.length-1)/(limit-1))]);
}
export function plotCandidates(rows:Candidate[],front:Candidate[],selectedId?:string,xKey:'subsidy_granted'|'climate'='subsidy_granted'):Candidate[]{
  const selected=selectedId?rows.find(row=>row.sample_id===selectedId):undefined;
  const objective=(row:Candidate)=>Number(row.values?.[xKey]);
  const orderedFront=[...front].sort((a,b)=>objective(a)-objective(b)||Number(a.values?.npv)-Number(b.values?.npv)||a.sample_id.localeCompare(b.sample_id));
  const frontBudget=Math.min(orderedFront.length,selected?PARETO_PLOT_LIMIT-1:PARETO_PLOT_LIMIT);
  const chosen=new Map(evenlySample(orderedFront,frontBudget).map(row=>[row.sample_id,row]));
  if(selected)chosen.set(selected.sample_id,selected);
  const remaining=PARETO_PLOT_LIMIT-chosen.size;
  if(remaining>0){
    const otherRows=rows.filter(row=>!chosen.has(row.sample_id)).sort((a,b)=>objective(a)-objective(b)||Number(a.values?.npv)-Number(b.values?.npv)||a.sample_id.localeCompare(b.sample_id));
    for(const row of evenlySample(otherRows,remaining))chosen.set(row.sample_id,row);
  }
  return [...chosen.values()];
}
function TooltipContent({active,payload}:any){
  const row=payload?.[0]?.payload;
  if(!active||!row)return null;
  return <div className="ds-point-tooltip"><strong>{row.scenario_label||row.sample_id}</strong><p>{productName(row)}</p><div className="pareto-tooltip-values"><span>Proxy NPV incl. hypothetical support</span><b>{money(row.values?.npv)}</b><span>Proxy NPV without public support</span><b>{money(row.candidate_economics?.proxy_npv_without_public_support_eur)}</b><span>Proxy NPV without support or grass bonus</span><b>{money(row.candidate_economics?.proxy_npv_without_public_support_or_grass_bonus_eur)}</b><span>Sales − OPEX before bonuses</span><b>{money(row.tea_totals?.operating_profit_before_support_eur_per_year)}/year</b><span>Operating profit incl. grass bonus</span><b>{money(row.tea_totals?.operating_profit_including_grass_bonus_excluding_public_support_eur_per_year)}/year</b><span>Public support PV</span><b>{money(row.values?.subsidy_granted)}</b><span>Modeled climate load</span><b>{fmt(Number(row.values?.climate)/1000,1)} t CO₂-eq/year</b></div></div>;
}

export default function ParetoScreening({onApplyCandidate,applying=false}:Props){
  const [data,setData]=useState<any>(null),[busy,setBusy]=useState(true),[error,setError]=useState('');
  const [filters,setFilters]=useState<Record<string,boolean>>({protein:true,biogas:true,nitrogen:true,phosphorus:true,potassium:true});
  const [grassBonusFilter,setGrassBonusFilter]=useState('all');
  const [grantFilter,setGrantFilter]=useState('all');
  const [selected,setSelected]=useState<Candidate|null>(null);
  useEffect(()=>{let active=true;apiJson<any>('/decision-support/pareto/latest').then(value=>{if(active)setData(value);}).catch(async error=>{try{const response=await fetch('/data/greenhub-pareto-positive-200-2026.json');if(!response.ok)throw error;const snapshot=await response.json();if(active){setData(snapshot);}}catch(fallbackError){if(active)setError(fallbackError instanceof Error?fallbackError.message:String(fallbackError));}}).finally(()=>{if(active)setBusy(false);});return()=>{active=false;};},[]);
  const candidates=useMemo(()=>{
    const byId=new Map<string,Candidate>();
    for(const group of ['protein_enabled','protein_bypass']){
      const groupData=data?.groups_payload?.[group]||{};
      for(const row of collectParetoGroupCandidates(groupData))byId.set(row.sample_id,row);
    }
    return [...byId.values()].filter(row=>productFilters.every(([key])=>filters[key]||!hasProduct(row,key))).filter(row=>grassBonusFilter==='all'||Number(row.configuration?.candidate_economics?.grass_utilization_bonus_eur_per_t_feed)===Number(grassBonusFilter)).filter(row=>grantFilter==='all'||(row.grant_case||row.configuration?.candidate_economics?.grant_scenario_id)===grantFilter).filter(row=>Number.isFinite(Number(row.values?.npv))&&Number.isFinite(Number(row.values?.subsidy_granted))&&Number.isFinite(Number(row.values?.climate)));
  },[data,filters,grassBonusFilter,grantFilter]);
  const supportFront=useMemo(()=>pareto(candidates,row=>Number(row.values.subsidy_granted)),[candidates]);
  const emissionFront=useMemo(()=>pareto(candidates,row=>Number(row.values.climate)),[candidates]);
  const selectedLive=selected?candidates.find(row=>row.sample_id===selected.sample_id)||selected:null;
  const makeChart=(rows:Candidate[],front:Candidate[],xKey:'subsidy_granted'|'climate')=>{
    const fronts=new Set(front.map(row=>row.sample_id));
    const points=plotCandidates(rows,front,selectedLive?.sample_id,xKey).map(row=>({...row,support:Number(row.values.subsidy_granted),climate_tonnes:Number(row.values.climate)/1000,npv:Number(row.values.npv)}));
    const selectedId=selectedLive?.sample_id;
    const ordinary=points.filter(row=>!fronts.has(row.sample_id)&&row.sample_id!==selectedId);
    const optimal=points.filter(row=>fronts.has(row.sample_id)&&row.sample_id!==selectedId);
    const selectedPoint=points.filter(row=>row.sample_id===selectedId);
    return <ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:12,right:22,bottom:48,left:34}} onClick={(event:any)=>{const row=event?.activePayload?.[0]?.payload;if(row)setSelected(row);}}>
      <CartesianGrid strokeDasharray="3 3" stroke={palette.grid}/>
      <XAxis type="number" dataKey={xKey==='climate'?'climate_tonnes':'support'} name={xKey==='climate'?'Climate load':'Public support'} tickFormatter={(v:number)=>fmt(v)} tickMargin={8} label={{value:xKey==='climate'?'Climate load (t CO₂-eq/year)':'Public support PV (€)',position:'insideBottom',offset:-31,fill:palette.ink,fontSize:11}}/>
      <YAxis type="number" dataKey="npv" name="Proxy NPV" width={100} tickFormatter={(v:number)=>fmt(v)} tickMargin={8} label={{value:'Proxy NPV incl. hypothetical support (€)',angle:-90,position:'insideLeft',offset:8,fill:palette.ink,fontSize:11}}/>
      <Tooltip content={<TooltipContent/>}/><Legend verticalAlign="top" height={32}/>
      <Scatter name="Scenarios" data={ordinary} fill={palette.blue} fillOpacity={.5} onClick={(row:any)=>setSelected(row)} r={4}/>
      <Scatter name="Pareto-front scenarios" data={optimal} fill={palette.green} onClick={(row:any)=>setSelected(row)} r={5}/>
      <Scatter name="Selected candidate" data={selectedPoint} fill={palette.rose} onClick={(row:any)=>setSelected(row)} r={7}/>
    </ScatterChart></ResponsiveContainer>;
  };
  const route=selectedLive?routeOf(selectedLive):{};
  const labels=[route.protein_recovery,route.biogas_upgrading,route.nutrient_recovery].filter(Boolean).join(' · ');
  const selectedTea=selectedLive?.tea_totals||{};
  const selectedFinance=selectedLive?.candidate_economics||{};
  const selectedLca=selectedLive?.lca_totals||{};
  const selectedSimulation=selectedLive?.configuration?.simulation||{};
  const selectedBiomass=selectedSimulation.biomass_schedule||{};
  const selectedProfile=selectedLive?.seasonal_availability_profile||{};
  const selectedFeedProfile=selectedLive?.seasonal_feed_profile||[];
  const seasonalTotal=(field:string)=>selectedFeedProfile.reduce((total:number,row:Candidate)=>total+(Number(row?.[field])||0),0);
  const selectedAvailability=displayQualityClass(selectedBiomass.availability_evidence_class);
  const selectedHarvestWindowQuality=displayQualityClass(selectedProfile.quality_class||'B');
  const selectedWithinWindowQuality=displayQualityClass(selectedProfile.within_window_profile_quality_class||'E');
  if(busy)return <section className="panel ds-pareto optimization-page"><h2>Optimization</h2><p>Loading the latest BioSTEAM Pareto scenarios…</p></section>;
  return <section className="panel ds-pareto optimization-page" aria-label="Optimization">
    <header className="optimization-heading"><div><h2>Optimization</h2><p>Explore positive-NPV screening scenarios above 14,000 wet tonnes processed per year. The 30,000 t/year supply is project context; higher-supply cases are hypothetical regional imports. Proxy NPV includes hypothetical support.</p></div></header>
    {error&&<p role="alert" className="ds-warning">{error}</p>}
    {!error&&data&&<>
      <fieldset className="optimization-product-filters"><legend>Include technologies</legend>{productFilters.map(([key,label])=><label key={key}><input type="checkbox" checked={filters[key]} onChange={event=>{setFilters(value=>({...value,[key]:event.target.checked}));setSelected(null);}}/>{label}</label>)}</fieldset>
      <div className="optimization-scenario-filters"><label className="optimization-grass-filter">CAPEX grant<select value={grantFilter} onChange={event=>{setGrantFilter(event.target.value);setSelected(null);}}><option value="all">All levels</option><option value="C0">0%</option><option value="C30">30%</option><option value="C45">45%</option><option value="C60">60%</option></select></label><label className="optimization-grass-filter">Grass logistics bonus<select value={grassBonusFilter} onChange={event=>{setGrassBonusFilter(event.target.value);setSelected(null);}}><option value="all">All rates</option>{[0,10,20,30,40,50].map(rate=><option value={rate} key={rate}>€{rate}/wet t</option>)}</select></label><label className="optimization-grass-filter">Scenario<select value={selectedLive?.sample_id||''} onChange={event=>setSelected(candidates.find(row=>row.sample_id===event.target.value)||null)}><option value="">Choose a plotted scenario</option>{candidates.map(row=><option key={row.sample_id} value={row.sample_id}>{row.sample_id} · {money(row.values?.npv)} NPV incl. support</option>)}</select></label></div>
      <div className="optimization-filter-summary">{data.trial_composition?.process_designs_screened??'—'} physical designs screened · {candidates.length} selectable positive-NPV scenarios · {candidates.filter(row=>Number(row.actual_feed_processed_tonnes)>=18000&&Number(row.actual_feed_processed_tonnes)<=25000).length} at 18–25k t/year · {candidates.filter(row=>row.supply_cohort==='hypothetical_import').length} hypothetical imports · up to {PARETO_PLOT_LIMIT} plotted per graph</div>
      <section className="optimization-chart-panel"><div className="optimization-chart-title"><h3>NPV incl. support vs public support</h3></div><div className="optimization-chart">{makeChart(candidates,supportFront,'subsidy_granted')}</div></section>
      <section className="optimization-chart-panel"><div className="optimization-chart-title"><h3>NPV incl. support vs climate load</h3></div><div className="optimization-chart">{makeChart(candidates,emissionFront,'climate')}</div></section>
      {selectedLive&&selectedFeedProfile.length>0&&<section className="optimization-chart-panel optimization-season-chart"><div className="optimization-chart-title"><h3>Seasonal biomass · {selectedProfile.label||selectedLive.sample_id}</h3></div><div className="optimization-chart"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={selectedFeedProfile} margin={{top:8,right:12,bottom:18,left:8}}><CartesianGrid strokeDasharray="3 3" stroke={palette.grid}/><XAxis dataKey="time_label" tickFormatter={(value:string)=>String(value).slice(5)} tick={{fill:palette.ink,fontSize:10}}/><YAxis width={58} tick={{fill:palette.ink,fontSize:10}} tickFormatter={(value:number)=>fmt(value)} label={{value:'Wet tonnes',angle:-90,position:'insideLeft',fill:palette.ink,fontSize:10}}/><Tooltip contentStyle={{borderColor:palette.grid}} formatter={(value:number,name:string)=>[`${fmt(value,1)} t`,name]}/><Legend verticalAlign="top" height={34}/><Bar dataKey="available_biomass_tonnes" name="Available at harvest" fill={palette.blue} radius={[3,3,0,0]}/><Bar dataKey="collected_at_harvest_tonnes" name="Collected" fill={palette.muted} radius={[3,3,0,0]}/><Bar dataKey="collected_for_processing_tonnes" name="Released after storage" fill="#d1a520" radius={[3,3,0,0]}/><Bar dataKey="processed_biomass_tonnes" name="Actually processed" fill={palette.green} radius={[3,3,0,0]}/><Line dataKey="ending_inventory_tonnes" name="Storage inventory" stroke={palette.rose} strokeWidth={2} dot={false} connectNulls/><Line dataKey="collection_delay_inventory_remaining_tonnes" name="Harvest-to-processing inventory" stroke="#5069a8" strokeWidth={2} dot={false} connectNulls/></ComposedChart></ResponsiveContainer></div></section>}
      {selectedLive&&<section className="optimization-candidate" aria-live="polite"><div className="optimization-candidate-info"><span className="ds-badge">{selectedLive.supply_cohort==='hypothetical_import'?'HYPOTHETICAL REGIONAL IMPORT':'PROJECT CONTEXT SUPPLY'}</span><h3>{selectedLive.scenario_label||selectedLive.sample_id}</h3><p>{labels||'Technology route unavailable'} · {productName(selectedLive)}</p><dl><div><dt>Proxy NPV incl. hypothetical support</dt><dd>{money(selectedLive.values?.npv)}</dd></div><div><dt>Proxy NPV without public support</dt><dd>{money(selectedLive.candidate_economics?.proxy_npv_without_public_support_eur)}</dd></div><div><dt>Product sales / year</dt><dd>{money(selectedTea.annual_revenue_eur)}</dd></div><div><dt>OPEX / year</dt><dd>{money(selectedTea.annual_opex_eur)}</dd></div><div><dt>Operating profit incl. grass bonus / year</dt><dd>{money(selectedTea.operating_profit_including_grass_bonus_excluding_public_support_eur_per_year)}</dd></div><div><dt>Direct CAPEX</dt><dd>{money(selectedTea.high_direct_capex_eur)}</dd></div><div><dt>IRR</dt><dd>{selectedFinance.proxy_irr==null?'—':`${fmt(Number(selectedFinance.proxy_irr)*100,1)}%`}</dd></div><div><dt>Simple payback</dt><dd>{selectedFinance.proxy_simple_payback_years==null?'—':`${fmt(selectedFinance.proxy_simple_payback_years,1)} years`}</dd></div><div><dt>Public support PV</dt><dd>{money(selectedLive.values?.subsidy_granted)}</dd></div><div><dt>Grass logistics bonus</dt><dd>{fmt(selectedFinance.grass_utilization_bonus_eur_per_t_feed)} €/wet t</dd></div><div><dt>Modeled climate load</dt><dd>{fmt(Number(selectedLive.values?.climate)/1000,1)} t CO₂-eq/year</dd></div><div><dt>Climate intensity</dt><dd>{fmt(selectedLca.kg_co2e_per_tonne_wet_feed,1)} kg CO₂-eq/t wet feed</dd></div><div><dt>Fresh water use</dt><dd>{selectedLive.fresh_water_m3_year==null?'—':`${fmt(selectedLive.fresh_water_m3_year,1)} m³/year`}</dd></div><div><dt>Fresh water OPEX</dt><dd>{money(selectedLive.fresh_water_opex_eur_year)}/year</dd></div><div><dt>Requested seasonal feed</dt><dd>{fmt(selectedLive.requested_feed_target_tonnes??selectedBiomass.annual_processed_biomass_tonnes,0)} t/year</dd></div><div><dt>Actually processed</dt><dd>{fmt(selectedLive.actual_feed_processed_tonnes,0)} t/year</dd></div><div><dt>Unmet feed target</dt><dd>{fmt(selectedLive.unmet_feed_target_tonnes,1)} t/year</dd></div><div><dt>Seasonal availability</dt><dd>{fmt(selectedBiomass.annual_available_biomass_tonnes,0)} t/year</dd></div><div><dt>Collected at harvest</dt><dd>{fmt(seasonalTotal('collected_at_harvest_tonnes'),0)} t/year</dd></div><div><dt>Uncollected</dt><dd>{fmt(seasonalTotal('uncollected_biomass_tonnes'),0)} t/year</dd></div><div><dt>Harvest regime</dt><dd>{selectedProfile.label||selectedBiomass.harvest_regime_label||'Not recorded'}</dd></div><div><dt>Collection window</dt><dd>{selectedBiomass.season_start||'—'} to {selectedBiomass.season_end||'—'}</dd></div><div><dt>Operating months</dt><dd>{(selectedBiomass.active_months||[]).map((month:number)=>new Date(2026,month-1).toLocaleString('en',{month:'short'})).join(', ')||'—'}</dd></div><div><dt>Plant rate</dt><dd>{fmt(selectedSimulation.operating_schedule?.target_throughput_kg_hr,0)} kg/hour</dd></div></dl>{selectedLive.selection_basis&&<small>{selectedLive.selection_basis}</small>}<small>TEA and LCA retain screening/proxy status and their stated boundaries.</small></div><button type="button" className="run-button optimization-submit" disabled={applying} onClick={()=>onApplyCandidate(selectedLive)}>{applying?'Running candidate…':'Run this scenario in Results'}</button></section>}
      {selectedLive&&<small className="optimization-assumption-note" title={selectedBiomass.availability_note||'Site-specific harvest data are unavailable.'}>Supply amount · class {selectedAvailability}; harvest windows · class {selectedHarvestWindowQuality}; within-window distribution · class {selectedWithinWindowQuality}.</small>}
      {!selectedLive&&<p className="optimization-select-hint">Select a point in either graph to review its technology route and KPIs.</p>}
      <details className="pareto-limitations"><summary>Optimization basis</summary><p>Candidate cases use the latest BioSTEAM optimization dataset ({data.created_at_utc?String(data.created_at_utc).slice(0,10):'date unavailable'}). Public support is the present value of hypothetical CAPEX grants and biomethane/other public operating support; the separately reported grass logistics bonus is operating income. No award is implied. Climate load includes modeled process emissions and life-cycle utility factors. Other upstream materials, feedstock, equipment manufacture, logistics and downstream fate remain outside the boundary.</p></details>
    </>}
  </section>;
}
