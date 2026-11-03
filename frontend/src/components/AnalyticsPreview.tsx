import React,{useEffect,useMemo,useState} from 'react';
import {Bar,BarChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import {apiJson} from '../data/apiClient';
import './decisionSupport.css';

type ParetoData={groups_payload?:Record<string,any>;support_scenarios?:Record<string,{name:string}>};
const money=(v:any)=>v==null||!Number.isFinite(Number(v))?'Incomplete':new Intl.NumberFormat(undefined,{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(Number(v));
const number=(v:any,d=1)=>v==null||!Number.isFinite(Number(v))?'Incomplete':Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const compact=(v:number)=>Math.abs(v)>=1e6?`${(v/1e6).toFixed(1)}m`:Math.abs(v)>=1000?`${(v/1000).toFixed(0)}k`:String(Math.round(v));
const routes=[
  {key:'feed_preparation',label:'Feed preparation'}, {key:'protein_recovery',label:'Protein recovery'},
  {key:'anaerobic_digestion',label:'Anaerobic digestion'}, {key:'biogas_upgrading',label:'Biogas upgrading'},
  {key:'nutrient_recovery',label:'Nutrient recovery'}, {key:'process_order',label:'Process order'},
];
const isN=(r:string)=>['NR3','NR4','NR6','NR7'].includes(r),isP=(r:string)=>['NR2','NR4','NR5','NR7'].includes(r),isK=(r:string)=>r==='NR7';
function candidateName(row:any){const s=row?.configuration?.simulation?.scenarios||{},n=s.nutrient_recovery||'';return `${s.protein_recovery==='PR0'?'X':'✓'}-${s.biogas_upgrading==='BG0'?'X':'✓'}-${isN(n)?'✓':'X'}-${isP(n)?'✓':'X'}-${isK(n)?'✓':'X'} · ${row?.scenario_label||row?.sample_id||'Candidate'}`;}

export default function AnalyticsPreview(){
  const [data,setData]=useState<ParetoData|null>(null),[group,setGroup]=useState('protein_enabled'),[sampleId,setSampleId]=useState('');
  const [report,setReport]=useState<any>(null),[units,setUnits]=useState<any[]>([]),[utilities,setUtilities]=useState<any[]>([]),[loading,setLoading]=useState(true),[detailLoading,setDetailLoading]=useState(false),[error,setError]=useState('');
  const candidates=useMemo(()=>data?.groups_payload?.[group]?.selected_candidates?.net_carbon_vs_npv||[],[data,group]);
  const selected=candidates.find((r:any)=>r.sample_id===sampleId)||candidates[0];
  useEffect(()=>{apiJson<ParetoData>('/decision-support/pareto/latest').then((v)=>{setData(v);const first=v.groups_payload?.protein_enabled?.selected_candidates?.net_carbon_vs_npv?.[0];setSampleId(first?.sample_id||'');}).catch((e)=>setError(e instanceof Error?e.message:String(e))).finally(()=>setLoading(false));},[]);
  useEffect(()=>{if(!candidates.length){setSampleId('');return;}if(!candidates.some((r:any)=>r.sample_id===sampleId))setSampleId(candidates[0].sample_id);},[candidates,sampleId]);
  useEffect(()=>{
    let active=true;setReport(null);setUnits([]);setUtilities([]);if(!selected?.run_id)return;
    setDetailLoading(true);setError('');
    apiJson<any>(`/decision-support/runs/${encodeURIComponent(selected.run_id)}`).then(async(full)=>{
      const [unitPayload,utilityPayload]=await Promise.all([
        apiJson<any>(`/simulations/${encodeURIComponent(selected.run_id)}/units`),
        apiJson<any>(`/simulations/${encodeURIComponent(selected.run_id)}/utilities`),
      ]);
      if(!active)return;setReport(full);setUnits(Array.isArray(unitPayload)?unitPayload:unitPayload.units||[]);setUtilities(Array.isArray(utilityPayload)?utilityPayload:utilityPayload.utilities||[]);
    }).catch((e)=>{if(active)setError(e instanceof Error?e.message:String(e));}).finally(()=>{if(active)setDetailLoading(false);});
    return()=>{active=false;};
  },[selected?.run_id]);
  const tea=report?.tea||{};
  const opex=(tea.opex_lines||[]).map((x:any)=>({name:[x.process_step||x.step,x.equipment_or_cost_item||x.item].filter(Boolean).join(' · ')||x.process_area||x.area||'Reported cost',value:Number(x.annual_cost_eur??x.annual_opex_eur??x.amount)})).filter((x:any)=>Number.isFinite(x.value)&&x.value>0).sort((a:any,b:any)=>b.value-a.value).slice(0,8);
  const capex=(tea.capex_lines||[]).map((x:any)=>({name:[x.process_step||x.step,x.equipment_or_cost_item||x.item].filter(Boolean).join(' · ')||x.process_area||x.area||'Reported equipment',value:Number(x.installed_cost_eur??x.direct_capex_eur??x.direct_cost_eur??x.amount)})).filter((x:any)=>Number.isFinite(x.value)&&x.value>0).sort((a:any,b:any)=>b.value-a.value).slice(0,8);
  const operatingHours=Number(report?.annual?.period?.operating_hours);
  const energy=(kind:string)=>utilities.filter((u:any)=>String(u.kind).toLowerCase()===kind).map((u:any)=>{
    const demand=Number(u.demand?.value??u.demand),unit=String(u.demand?.unit||'kW'),power=/^kw$/i.test(unit),equipment=units.find((x:any)=>x.unit_id===u.unit_id);
    return {name:equipment?.display_name||u.unit_id,value:power&&operatingHours>0?demand*operatingHours:demand,unit:power&&operatingHours>0?'kWh/year':unit};
  }).filter((x:any)=>Number.isFinite(x.value)&&x.value>0).sort((a:any,b:any)=>b.value-a.value).slice(0,10);
  const electricity=energy('electricity'),heat=utilities.filter((u:any)=>/heat|thermal|steam/i.test(String(u.kind))).map((u:any)=>{const demand=Number(u.demand?.value??u.demand),unit=String(u.demand?.unit||'kW'),power=/^kw$/i.test(unit),equipment=units.find((x:any)=>x.unit_id===u.unit_id);return{name:equipment?.display_name||u.unit_id,value:power&&operatingHours>0?demand*operatingHours:demand,unit:power&&operatingHours>0?'kWh/year':unit};}).filter((x:any)=>Number.isFinite(x.value)&&x.value>0).sort((a:any,b:any)=>b.value-a.value).slice(0,10);
  const climate=(report?.lca?.inventory||[]).filter((x:any)=>Number.isFinite(x.climate_kg_co2e)&&x.climate_kg_co2e>0).map((x:any)=>({name:x.flow_id,value:x.climate_kg_co2e})).sort((a:any,b:any)=>b.value-a.value).slice(0,8);
  if(loading)return <section className="panel analytics-preview"><h2>Process hotspots</h2><p>Loading selected BioSTEAM candidates…</p></section>;
  if(!selected)return <section className="panel analytics-preview"><h2>Process hotspots</h2><p role="alert">{error||'No selected candidates are available in the current Pareto analysis.'}</p></section>;
  const scenario=selected.configuration?.simulation?.scenarios||{},kpi=selected.values||{};
  return <section className="panel analytics-preview" aria-label="Current RVO Pareto candidate hotspots">
    <div className="analytics-preview-top"><span className="ds-badge">CURRENT BIOSTEAM · NO PEF</span><span className="analytics-preview-meta">Hotspots use the stored model run for the selected Pareto candidate.</span></div>
    <div className="ds-controls pareto-controls"><label>Protein group<select value={group} onChange={e=>setGroup(e.target.value)}><option value="protein_enabled">Protein enabled</option><option value="protein_bypass">Protein bypassed</option></select></label><label>Selected candidate<select value={selected.sample_id} onChange={e=>setSampleId(e.target.value)}>{candidates.map((r:any)=><option key={r.sample_id} value={r.sample_id}>Rank {r.rank} · {r.scenario_label}</option>)}</select></label></div>
    <h2 className="analytics-preview-title">{candidateName(selected)}</h2>
    <div className="ds-cards pareto-backend-kpis"><article><span>NPV</span><strong>{money(kpi.npv)}</strong><small>€ · screening case</small></article><article><span>Net carbon</span><strong>{number(kpi.net_carbon,1)}</strong><small>t C/year · lower is better</small></article><article><span>Operating profit</span><strong>{money(kpi.operating_profit)}</strong><small>€/year · screening case</small></article><article><span>Public support PV</span><strong>{money(kpi.subsidy_granted)}</strong><small>€ · assumed support</small></article></div>
    <p className="analytics-preview-meta">Routes: {scenario.protein_recovery} · {scenario.biogas_upgrading} · {scenario.nutrient_recovery} · {scenario.process_order} · {selected.scenario_label}</p>
    {error&&<p role="alert" className="analytics-detail-error">{error}</p>}
    <div className="analytics-hotspot-grid">
      <Chart title="Annual OPEX by process step" rows={opex} color="#408f4d" unit="€/year" loading={detailLoading}/>
      <Chart title="Direct CAPEX by equipment" rows={capex} color="#d1a520" unit="€" loading={detailLoading}/>
      <Chart title="Electricity by unit" rows={electricity} color="#729ad2" unit={electricity[0]?.unit||'kWh/year'} loading={detailLoading}/>
      <Chart title="Heat by unit" rows={heat} color="#d277a3" unit={heat[0]?.unit||'kWh/year'} loading={detailLoading}/>
      <Chart title="Operational climate burdens" rows={climate} color="#0c3338" unit="kg CO₂-eq/year" loading={detailLoading}/>
    </div>
    <details className="pareto-limitations"><summary>Candidate scope and assumptions</summary><p>{selected.scenario_label}; support awarding organization: {selected.configuration?.candidate_economics?.grant_awarding_organization||'not specified'}. Support is a user-defined screening assumption. The displayed cost, energy and climate hotspot breakdown comes from the paired stored BioSTEAM process run. Net-carbon storage assumptions and NPV boundaries are described in the Pareto methodology.</p><p>Route switches, in Protein–Biogas–N–P–K order: {candidateName(selected).split(' · ')[0]}.</p></details>
  </section>;
}

function Chart({title,rows,color,unit,loading}:{title:string;rows:any[];color:string;unit:string;loading:boolean}){return <section className="analytics-hotspot-card"><h3>{title} · {unit}</h3>{rows.length?<div className="analytics-hotspot-plot"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout="vertical" margin={{top:4,right:24,bottom:4,left:8}}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact}/><YAxis type="category" dataKey="name" width={166} tickFormatter={(v:any)=>String(v).length>26?`${String(v).slice(0,25)}…`:String(v)}/><Tooltip formatter={(v:any)=>[`${number(v,1)} ${unit}`,title]}/><Bar dataKey="value" name={title} fill={color} radius={[0,4,4,0]}/></BarChart></ResponsiveContainer></div>:<div className="analytics-hotspot-empty">{loading?'Loading…':'No reported values for this candidate'}</div>}</section>;}
