import React,{useEffect,useMemo,useState} from 'react';
import {CartesianGrid,Legend,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis} from 'recharts';
import {apiJson} from '../data/apiClient';
import './decisionSupport.css';

const palette={ink:'#0c3338',rose:'#d277a3',green:'#408f4d',blue:'#729ad2',muted:'#71817a',grid:'#d8ded8'};
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
function pareto(rows:Candidate[],x:(row:Candidate)=>number){
  return rows.filter(a=>!rows.some(b=>b!==a&&x(b)<=x(a)&&Number(b.values.npv)>=Number(a.values.npv)&&(x(b)<x(a)||Number(b.values.npv)>Number(a.values.npv))));
}
function TooltipContent({active,payload}:any){
  const row=payload?.[0]?.payload;
  if(!active||!row)return null;
  return <div className="ds-point-tooltip"><strong>{row.scenario_label||row.sample_id}</strong><p>{productName(row)}</p><div className="pareto-tooltip-values"><span>NPV</span><b>{money(row.values?.npv)}</b><span>Public support PV</span><b>{money(row.values?.subsidy_granted)}</b><span>Modeled climate load</span><b>{fmt(Number(row.values?.climate)/1000,1)} t CO₂-eq/year</b></div></div>;
}

export default function ParetoScreening({onApplyCandidate,applying=false}:Props){
  const [data,setData]=useState<any>(null),[busy,setBusy]=useState(true),[error,setError]=useState(''),[offlinePreview,setOfflinePreview]=useState(false);
  const [filters,setFilters]=useState<Record<string,boolean>>({protein:true,biogas:true,nitrogen:true,phosphorus:true,potassium:true});
  const [grassBonusFilter,setGrassBonusFilter]=useState('all');
  const [grantFilter,setGrantFilter]=useState('all');
  const [selected,setSelected]=useState<Candidate|null>(null);
  useEffect(()=>{let active=true;apiJson<any>('/decision-support/pareto/latest').then(value=>{if(active)setData(value);}).catch(async error=>{try{const response=await fetch('/data/greenhub-pareto-latest.json');if(!response.ok)throw error;const snapshot=await response.json();if(active){setData(snapshot);setOfflinePreview(true);}}catch(fallbackError){if(active)setError(fallbackError instanceof Error?fallbackError.message:String(fallbackError));}}).finally(()=>{if(active)setBusy(false);});return()=>{active=false;};},[]);
  const candidates=useMemo(()=>{
    const byId=new Map<string,Candidate>();
    for(const group of ['protein_enabled','protein_bypass']){
      const selections=data?.groups_payload?.[group]?.selected_candidates||{};
      for(const key of ['subsidy_vs_npv','net_carbon_vs_npv','grass_bonus_sensitivity'])for(const row of selections[key]||[])byId.set(row.sample_id,row);
      const grantCases=grantFilter==='all'?['C0','C30','C45','C60']:[grantFilter];
      const bonusRates=grassBonusFilter==='all'?[0,10,20,30,40,50]:[Number(grassBonusFilter)];
      if(grantFilter!=='all'||grassBonusFilter!=='all')for(const grant of grantCases)for(const rate of bonusRates){
        const key=`net_carbon_vs_npv_${grant}-GB${rate}`;
        for(const row of selections[key]||[])byId.set(row.sample_id,row);
      }
    }
    return [...byId.values()].filter(row=>productFilters.every(([key])=>filters[key]||!hasProduct(row,key))).filter(row=>grassBonusFilter==='all'||Number(row.configuration?.candidate_economics?.grass_utilization_bonus_eur_per_t_feed)===Number(grassBonusFilter)).filter(row=>grantFilter==='all'||(row.grant_case||row.configuration?.candidate_economics?.grant_scenario_id)===grantFilter).filter(row=>Number.isFinite(Number(row.values?.npv))&&Number.isFinite(Number(row.values?.subsidy_granted))&&Number.isFinite(Number(row.values?.climate)));
  },[data,filters,grassBonusFilter,grantFilter]);
  const supportFront=useMemo(()=>pareto(candidates,row=>Number(row.values.subsidy_granted)),[candidates]);
  const emissionFront=useMemo(()=>pareto(candidates,row=>Number(row.values.climate)),[candidates]);
  const selectedLive=selected?candidates.find(row=>row.sample_id===selected.sample_id)||selected:null;
  const makeChart=(rows:Candidate[],front:Candidate[],xKey:'subsidy_granted'|'climate')=>{
    const fronts=new Set(front.map(row=>row.sample_id));
    const points=rows.map(row=>({...row,support:Number(row.values.subsidy_granted),climate_tonnes:Number(row.values.climate)/1000,npv:Number(row.values.npv)}));
    const selectedId=selectedLive?.sample_id;
    const ordinary=points.filter(row=>!fronts.has(row.sample_id)&&row.sample_id!==selectedId);
    const optimal=points.filter(row=>fronts.has(row.sample_id)&&row.sample_id!==selectedId);
    const selectedPoint=points.filter(row=>row.sample_id===selectedId);
    return <ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:12,right:22,bottom:48,left:34}} onClick={(event:any)=>{const row=event?.activePayload?.[0]?.payload;if(row)setSelected(row);}}>
      <CartesianGrid strokeDasharray="3 3" stroke={palette.grid}/>
      <XAxis type="number" dataKey={xKey==='climate'?'climate_tonnes':'support'} name={xKey==='climate'?'Climate load':'Public support'} tickFormatter={(v:number)=>fmt(v)} tickMargin={8} label={{value:xKey==='climate'?'Climate load (t CO₂-eq/year)':'Public support PV (€)',position:'insideBottom',offset:-31,fill:palette.ink,fontSize:11}}/>
      <YAxis type="number" dataKey="npv" name="NPV" width={100} tickFormatter={(v:number)=>fmt(v)} tickMargin={8} label={{value:'NPV (€)',angle:-90,position:'insideLeft',offset:8,fill:palette.ink,fontSize:11}}/>
      <Tooltip content={<TooltipContent/>}/><Legend verticalAlign="top" height={32}/>
      <Scatter name="Scenarios" data={ordinary} fill={palette.blue} fillOpacity={.5} onClick={(row:any)=>setSelected(row)} r={4}/>
      <Scatter name="Optimal candidates" data={optimal} fill={palette.green} onClick={(row:any)=>setSelected(row)} r={5}/>
      <Scatter name="Selected candidate" data={selectedPoint} fill={palette.rose} onClick={(row:any)=>setSelected(row)} r={7}/>
    </ScatterChart></ResponsiveContainer>;
  };
  const route=selectedLive?routeOf(selectedLive):{};
  const labels=[route.protein_recovery,route.biogas_upgrading,route.nutrient_recovery].filter(Boolean).join(' · ');
  const selectedTea=selectedLive?.tea_totals||{};
  const selectedFinance=selectedLive?.candidate_economics||{};
  const selectedLca=selectedLive?.lca_totals||{};
  if(busy)return <section className="panel ds-pareto optimization-page"><h2>Optimization</h2><p>Loading the latest BioSTEAM Pareto scenarios…</p></section>;
  return <section className="panel ds-pareto optimization-page" aria-label="Optimization">
    <header className="optimization-heading"><div><h2>Optimization</h2><p>Filter products and support assumptions to compare more scenarios. Productless routes are excluded. NPV is maximized; support and modeled climate load are minimized.</p></div></header>
    {error&&<p role="alert" className="ds-warning">{error}</p>}
    {!error&&data&&<>
      <fieldset className="optimization-product-filters"><legend>Include technologies</legend>{productFilters.map(([key,label])=><label key={key}><input type="checkbox" checked={filters[key]} onChange={event=>{setFilters(value=>({...value,[key]:event.target.checked}));setSelected(null);}}/>{label}</label>)}</fieldset>
      <div className="optimization-scenario-filters"><label className="optimization-grass-filter">CAPEX grant<select value={grantFilter} onChange={event=>{setGrantFilter(event.target.value);setSelected(null);}}><option value="all">All levels</option><option value="C0">0%</option><option value="C30">30%</option><option value="C45">45%</option><option value="C60">60%</option></select></label><label className="optimization-grass-filter">Grass logistics bonus<select value={grassBonusFilter} onChange={event=>{setGrassBonusFilter(event.target.value);setSelected(null);}}><option value="all">All rates</option>{[0,10,20,30,40,50].map(rate=><option value={rate} key={rate}>€{rate}/wet t</option>)}</select></label><label className="optimization-grass-filter">Scenario<select value={selectedLive?.sample_id||''} onChange={event=>setSelected(candidates.find(row=>row.sample_id===event.target.value)||null)}><option value="">Choose a plotted scenario</option>{candidates.map(row=><option key={row.sample_id} value={row.sample_id}>{row.sample_id} · {money(row.values?.npv)} NPV</option>)}</select></label></div>
      <div className="optimization-filter-summary">{candidates.length} selectable scenarios · {supportFront.length} support-front points in view · {emissionFront.length} climate-front points in view</div>
      <section className="optimization-chart-panel"><div className="optimization-chart-title"><h3>NPV vs public support</h3></div><div className="optimization-chart">{makeChart(candidates,supportFront,'subsidy_granted')}</div></section>
      <section className="optimization-chart-panel"><div className="optimization-chart-title"><h3>NPV vs climate load</h3></div><div className="optimization-chart">{makeChart(candidates,emissionFront,'climate')}</div></section>
      {selectedLive&&<section className="optimization-candidate" aria-live="polite"><div className="optimization-candidate-info"><span className="ds-badge">SELECTED SCENARIO</span><h3>{selectedLive.scenario_label||selectedLive.sample_id}</h3><p>{labels||'Technology route unavailable'} · {productName(selectedLive)}</p><dl><div><dt>NPV</dt><dd>{money(selectedLive.values?.npv)}</dd></div><div><dt>Revenue / year</dt><dd>{money(selectedTea.annual_revenue_eur)}</dd></div><div><dt>OPEX / year</dt><dd>{money(selectedTea.annual_opex_eur)}</dd></div><div><dt>Operating profit / year</dt><dd>{money(selectedTea.annual_gross_profit_eur)}</dd></div><div><dt>Direct CAPEX</dt><dd>{money(selectedTea.high_direct_capex_eur)}</dd></div><div><dt>IRR</dt><dd>{selectedFinance.proxy_irr==null?'—':`${fmt(Number(selectedFinance.proxy_irr)*100,1)}%`}</dd></div><div><dt>Simple payback</dt><dd>{selectedFinance.proxy_simple_payback_years==null?'—':`${fmt(selectedFinance.proxy_simple_payback_years,1)} years`}</dd></div><div><dt>Public support PV</dt><dd>{money(selectedLive.values?.subsidy_granted)}</dd></div><div><dt>Grass bonus</dt><dd>{fmt(selectedFinance.grass_utilization_bonus_eur_per_t_feed)} €/wet t</dd></div><div><dt>Modeled climate load</dt><dd>{fmt(Number(selectedLive.values?.climate)/1000,1)} t CO₂-eq/year</dd></div><div><dt>Climate intensity</dt><dd>{fmt(selectedLca.kg_co2e_per_tonne_wet_feed,1)} kg CO₂-eq/t wet feed</dd></div><div><dt>Feed rate</dt><dd>{fmt(Number(selectedLive.configuration?.simulation?.wet_feed_rate_kg_hr)*8760/1000,0)} t/year</dd></div></dl>{selectedLive.selection_basis&&<small>{selectedLive.selection_basis}</small>}<small>TEA and LCA retain screening/proxy status and their stated boundaries.</small></div><button type="button" className="run-button optimization-submit" disabled={applying||offlinePreview} onClick={()=>onApplyCandidate(selectedLive)}>{applying?'Running candidate…':'Run this scenario in Results'}</button></section>}
      {!selectedLive&&<p className="optimization-select-hint">Select a point in either graph to review its technology route and KPIs.</p>}
      <details className="pareto-limitations"><summary>Optimization basis</summary><p>Candidate cases use the latest BioSTEAM optimization dataset ({data.created_at_utc?String(data.created_at_utc).slice(0,10):'date unavailable'}). Public support is the present value of hypothetical CAPEX grants and user-defined biomethane and grass-use bonuses; no award is implied. Climate load includes modeled process emissions and life-cycle utility factors. Other upstream materials, feedstock, equipment manufacture, logistics and downstream fate remain outside the boundary.</p></details>
    </>}
  </section>;
}
