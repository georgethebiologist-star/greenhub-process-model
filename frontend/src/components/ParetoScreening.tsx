import React,{useEffect,useMemo,useState} from 'react';
import {CartesianGrid,Legend,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis,Cell} from 'recharts';
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
  return <div className="ds-point-tooltip"><strong>{row.scenario_label||row.sample_id}</strong><p>{productName(row)}</p><div className="pareto-tooltip-values"><span>NPV</span><b>{money(row.values?.npv)}</b><span>Public support PV</span><b>{money(row.values?.subsidy_granted)}</b><span>Operational emissions</span><b>{fmt(Number(row.values?.climate)/1000,1)} t CO₂-eq/year</b></div></div>;
}

export default function ParetoScreening({onApplyCandidate,applying=false}:Props){
  const [data,setData]=useState<any>(null),[busy,setBusy]=useState(true),[error,setError]=useState('');
  const [filters,setFilters]=useState<Record<string,boolean>>({protein:true,biogas:true,nitrogen:true,phosphorus:true,potassium:true});
  const [selected,setSelected]=useState<Candidate|null>(null);
  useEffect(()=>{apiJson<any>('/decision-support/pareto/latest').then(setData).catch(e=>setError(e instanceof Error?e.message:String(e))).finally(()=>setBusy(false));},[]);
  const candidates=useMemo(()=>{
    const byId=new Map<string,Candidate>();
    for(const group of ['protein_enabled','protein_bypass']){
      const selections=data?.groups_payload?.[group]?.selected_candidates||{};
      for(const key of ['subsidy_vs_npv','net_carbon_vs_npv'])for(const row of selections[key]||[])byId.set(row.sample_id,row);
    }
    return [...byId.values()].filter(row=>productFilters.every(([key])=>filters[key]||!hasProduct(row,key))).filter(row=>Number.isFinite(Number(row.values?.npv))&&Number.isFinite(Number(row.values?.subsidy_granted))&&Number.isFinite(Number(row.values?.climate)));
  },[data,filters]);
  const supportFront=useMemo(()=>pareto(candidates,row=>Number(row.values.subsidy_granted)),[candidates]);
  const emissionFront=useMemo(()=>pareto(candidates,row=>Number(row.values.climate)),[candidates]);
  const selectedLive=selected?candidates.find(row=>row.sample_id===selected.sample_id)||selected:null;
  const makeChart=(rows:Candidate[],front:Candidate[],xKey:'subsidy_granted'|'climate')=>{
    const fronts=new Set(front.map(row=>row.sample_id));
    return <ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:18,right:24,bottom:34,left:28}} onClick={(event:any)=>{const row=event?.activePayload?.[0]?.payload;if(row)setSelected(row);}}>
      <CartesianGrid strokeDasharray="3 3" stroke={palette.grid}/>
      <XAxis type="number" dataKey={xKey==='climate'?'climate_tonnes':'support'} name={xKey==='climate'?'Emissions':'Public support'} tickFormatter={(v:number)=>fmt(v)} label={{value:xKey==='climate'?'Operational emissions (t CO₂-eq/year) · minimize':'Public support PV (€) · minimize',position:'insideBottom',offset:-22,fill:palette.ink,fontSize:12}}/>
      <YAxis type="number" dataKey="npv" name="NPV" tickFormatter={(v:number)=>fmt(v)} label={{value:'NPV (€) · maximize',angle:-90,position:'insideLeft',fill:palette.ink,fontSize:12}}/>
      <Tooltip content={<TooltipContent/>}/><Legend verticalAlign="top" height={30}/>
      <Scatter name="Candidate scenarios" data={rows.map(row=>({...row,support:Number(row.values.subsidy_granted),climate_tonnes:Number(row.values.climate)/1000,npv:Number(row.values.npv)}))} fill={palette.blue} fillOpacity={.45} onClick={(row:any)=>setSelected(row)}>
        {rows.map(row=><Cell key={row.sample_id} fill={selectedLive?.sample_id===row.sample_id?palette.rose:fronts.has(row.sample_id)?palette.green:palette.blue} fillOpacity={selectedLive?.sample_id===row.sample_id?1:fronts.has(row.sample_id)?.95:.38} r={selectedLive?.sample_id===row.sample_id?8:fronts.has(row.sample_id)?6:4}/>) }
      </Scatter>
    </ScatterChart></ResponsiveContainer>;
  };
  const route=selectedLive?routeOf(selectedLive):{};
  const labels=[route.protein_recovery,route.biogas_upgrading,route.nutrient_recovery].filter(Boolean).join(' · ');
  if(busy)return <section className="panel ds-pareto optimization-page"><h2>Optimization</h2><p>Loading the latest BioSTEAM Pareto scenarios…</p></section>;
  return <section className="panel ds-pareto optimization-page" aria-label="Optimization">
    <header className="optimization-heading"><div><span className="ds-badge">BIOSTEAM · NO PEF</span><h2>Optimization</h2><p>Filter process products to compare the resulting candidate set and Pareto front. NPV is maximized; support and operational emissions are minimized.</p></div></header>
    {error&&<p role="alert" className="ds-warning">{error}</p>}
    {!error&&data&&<>
      <fieldset className="optimization-product-filters"><legend>Include technologies</legend>{productFilters.map(([key,label])=><label key={key}><input type="checkbox" checked={filters[key]} onChange={event=>{setFilters(value=>({...value,[key]:event.target.checked}));setSelected(null);}}/>{label}</label>)}</fieldset>
      <div className="optimization-filter-summary">{candidates.length} candidate scenarios · {supportFront.length} support front points · {emissionFront.length} emissions front points</div>
      <section className="optimization-chart-panel"><div className="optimization-chart-title"><h3>NPV vs public support</h3><span>Green points mark the current Pareto front</span></div><div className="optimization-chart">{makeChart(candidates,supportFront,'subsidy_granted')}</div></section>
      <section className="optimization-chart-panel"><div className="optimization-chart-title"><h3>NPV vs emissions</h3><span>Attributional operational climate load · Green points mark the current Pareto front</span></div><div className="optimization-chart">{makeChart(candidates,emissionFront,'climate')}</div></section>
      {selectedLive&&<section className="optimization-candidate" aria-live="polite"><div className="optimization-candidate-info"><span className="ds-badge">SELECTED SCENARIO</span><h3>{selectedLive.scenario_label||selectedLive.sample_id}</h3><p>{labels||'Technology route unavailable'} · {productName(selectedLive)}</p><dl><div><dt>NPV</dt><dd>{money(selectedLive.values?.npv)}</dd></div><div><dt>Public support PV</dt><dd>{money(selectedLive.values?.subsidy_granted)}</dd></div><div><dt>Operational emissions</dt><dd>{fmt(Number(selectedLive.values?.climate)/1000,1)} t CO₂-eq/year</dd></div><div><dt>Feed rate</dt><dd>{fmt(Number(selectedLive.configuration?.simulation?.wet_feed_rate_kg_hr)*8760/1000,0)} t/year</dd></div></dl></div><button type="button" className="run-button optimization-submit" disabled={applying} onClick={()=>onApplyCandidate(selectedLive)}>{applying?'Running candidate…':'Run this scenario in Results'}</button></section>}
      {!selectedLive&&<p className="optimization-select-hint">Select a point in either graph to review its technology route and KPIs.</p>}
      <details className="pareto-limitations"><summary>Optimization basis</summary><p>Candidate cases use the latest BioSTEAM optimization dataset ({data.created_at_utc?String(data.created_at_utc).slice(0,10):'date unavailable'}). Public support is the present value of the modeled upfront CAPEX grant and biomethane operating premium. Emissions are the factory gate-to-gate operational climate load; upstream feedstock, equipment manufacture, logistics and downstream fate are outside that boundary.</p></details>
    </>}
  </section>;
}
