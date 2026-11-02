import React,{useEffect,useMemo,useState} from 'react';
import {CartesianGrid,Legend,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis,Cell} from 'recharts';
import {API_BASE,apiJson} from '../data/apiClient';
import './decisionSupport.css';

const fmt=(v:any,d=1)=>v==null||!Number.isFinite(Number(v))?'—':Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const money=(v:any)=>v==null||!Number.isFinite(Number(v))?'—':new Intl.NumberFormat(undefined,{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(Number(v));
const names={protein_enabled:'Protein recovery enabled',protein_bypass:'Protein recovery bypassed'};
const objectiveTitles={net_carbon_vs_npv:'Net carbon vs NPV',subsidy_vs_npv:'Public support vs NPV',net_carbon_npv_subsidy:'Carbon, NPV and support'};
const colors={ink:'#0c3338',rose:'#d277a3',green:'#408f4d',blue:'#729ad2',yellow:'#d1a520'};
type Payload=any;
type FigurePayload={count:number;figures:Array<{figure_id:number;figure_name:string;description:string;scenario:string;units:string;category:string;image_url:string}>};
const blend=(a:string,b:string,t:number)=>{const hex=(s:string)=>s.match(/[a-f0-9]{2}/gi)!.map(x=>parseInt(x,16));const x=hex(a),y=hex(b);return `rgb(${x.map((v,i)=>Math.round(v+(y[i]-v)*t)).join(',')})`;};

export default function ParetoScreening(){
  const [data,setData]=useState<Payload|null>(null),[group,setGroup]=useState('protein_enabled'),[objective,setObjective]=useState('net_carbon_vs_npv'),[support,setSupport]=useState('all'),[busy,setBusy]=useState(true),[error,setError]=useState('');
  const [figureData,setFigureData]=useState<FigurePayload|null>(null),[figureCategory,setFigureCategory]=useState('all');
  useEffect(()=>{apiJson<Payload>('/decision-support/pareto/latest').then(setData).catch(e=>setError(e instanceof Error?e.message:String(e))).finally(()=>setBusy(false));},[]);
  useEffect(()=>{apiJson<FigurePayload>('/decision-support/pareto/latest/figure-index').then(setFigureData).catch(()=>setFigureData(null));},[]);
  const result=data?.groups_payload?.[group];
  const front=useMemo(()=>{
    if(!result)return null;
    if(objective==='net_carbon_vs_npv'&&support!=='all')return result.fronts?.by_support_case?.[support];
    return result.fronts?.[objective];
  },[result,objective,support]);
  const points=front?.points||[];
  const selected=useMemo(()=>{
    const key=objective==='subsidy_vs_npv'?'subsidy_vs_npv':'net_carbon_vs_npv';
    const prefix=objective==='net_carbon_vs_npv'&&support!=='all'?`${key}_${support}`:key;
    return result?.selected_candidates?.[prefix]||[];
  },[result,objective,support]);
  const plotted=useMemo(()=>{
    const byId=new Map(points.map((p:any)=>[p.sample_id,p]));
    for(const row of selected){const base:any=byId.get(row.sample_id)||{sample_id:row.sample_id,support_case:row.support_case};byId.set(row.sample_id,{...base,net_carbon:row.values?.net_carbon,npv:row.values?.npv,subsidy_granted:row.values?.subsidy_granted,rank:row.rank});}
    return [...byId.values()];
  },[points,selected]);
  const xKey=objective==='subsidy_vs_npv'?'subsidy_granted':'net_carbon';
  const xUnit=xKey==='net_carbon'?'t C/year':'€ present value';
  const chartData=plotted.filter((p:any)=>Number.isFinite(Number(p[xKey]))&&Number.isFinite(Number(p.npv)));
  const figureCategories=[...new Set(figureData?.figures.map(f=>f.category)||[])];
  const visibleFigures=figureData?.figures.filter(f=>figureCategory==='all'||f.category===figureCategory)||[];
  const candidateLabel=(row:any)=>{
    const s=row.configuration?.simulation?.scenarios||{};const protein=s.protein_recovery!=='PR0';const biogas=s.biogas_upgrading!=='BG0';const n=['NR3','NR4','NR6','NR7'].includes(s.nutrient_recovery);const p=['NR2','NR4','NR5','NR7'].includes(s.nutrient_recovery);const k=s.nutrient_recovery==='NR7';
    return `${protein?'✓':'X'}-${biogas?'✓':'X'}-${n?'✓':'X'}-${p?'✓':'X'}-${k?'✓':'X'} · ${s.protein_recovery||'—'}/${s.biogas_upgrading||'—'}/${s.nutrient_recovery||'—'}`;
  };
  if(busy)return <section className="panel ds-pareto"><h2>RVO Pareto analysis</h2><p>Loading the latest BioSTEAM optimization.</p></section>;
  return <section className="panel ds-pareto" aria-label="RVO Pareto analysis">
    <div className="pareto-backend-heading"><div><span className="ds-badge">BIoSTEAM · NO PEF</span><h2>Technology trade-offs</h2><p>Paired process designs are evaluated under user-defined Dutch support what-if cases. The sample-bounded fronts optimize net stored carbon, screening NPV and assumed public support.</p></div></div>
    <div className="pareto-report-links"><a href={`${API_BASE}/decision-support/pareto/latest/report`} target="_blank" rel="noreferrer">Download current report PDF</a><span>Full current-run report with candidate tables and PNG atlas</span></div>
    {error&&<p role="alert" className="ds-warning">{error}</p>}
    {data&&<>
      <div className="ds-controls pareto-controls"><label>Protein route<select value={group} onChange={e=>setGroup(e.target.value)}><option value="protein_enabled">Protein recovery enabled</option><option value="protein_bypass">Protein recovery bypassed</option></select></label><label>Optimization view<select value={objective} onChange={e=>setObjective(e.target.value)}><option value="net_carbon_vs_npv">Net carbon vs NPV</option><option value="subsidy_vs_npv">Public support vs NPV</option><option value="net_carbon_npv_subsidy">Carbon, NPV and support</option></select></label><label>Support case<select value={support} onChange={e=>setSupport(e.target.value)} disabled={objective!=='net_carbon_vs_npv'}><option value="all">All paired cases</option>{Object.entries(data.support_scenarios||{}).map(([id,s]:any)=><option key={id} value={id}>{s.name}</option>)}</select></label></div>
      <div className="ds-cards pareto-backend-kpis"><article><span>Sampled designs</span><strong>{fmt(result?.requested_designs,0)}</strong><small>per protein group</small></article><article><span>Evaluated</span><strong>{fmt(result?.evaluated_count,0)}</strong><small>{fmt(result?.rejected_count,0)} rejected with reason retained</small></article><article><span>Front size</span><strong>{fmt(points.length,0)}</strong><small>nondominated points</small></article><article><span>Updated</span><strong>{String(data.created_at_utc||'—').slice(0,10)}</strong><small>Seed {data.seed}</small></article></div>
      {objective==='net_carbon_npv_subsidy'?<div className="pareto-3d-figure"><h3>Three-objective frontier</h3><img src={`${API_BASE}/decision-support/pareto/latest/figures/${group}`} alt={`Three-dimensional Pareto frontier for ${names[group as keyof typeof names]}`} /><p>Static 3D view of net carbon, NPV and assumed support PV. The chart below is the carbon–NPV projection; exact third-objective values remain in the candidate table.</p></div>:null}
      <div className="pareto-objective-heading"><div><h3>{(objectiveTitles as any)[objective]}</h3><p>{objective==='subsidy_vs_npv'?'Lower present value of assumed grant and operating premium is preferred; higher NPV is preferred.':'Lower net carbon is preferred; higher pre-tax screening NPV is preferred.'} Rose marks rank 0 (highest NPV); green marks rank 10 (lower-carbon endpoint among selected candidates). In the carbon–NPV chart, rank labels are selected from the three-objective front and projected into two dimensions.</p></div></div>
      <div className="ds-pareto-chart pareto-backend-chart"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:18,right:26,bottom:28,left:22}}><CartesianGrid strokeDasharray="3 3" stroke="#d8ded8"/><XAxis type="number" dataKey={xKey} name={xKey==='net_carbon'?'Net carbon':'Public support'} unit={xKey==='net_carbon'?' t C/year':' €'} label={{value:`${xKey==='net_carbon'?'Net carbon':'Public support'} (${xUnit}) · minimize`,position:'insideBottom',offset:-18,fill:colors.ink}}/><YAxis type="number" dataKey="npv" name="NPV" unit=" €" label={{value:'NPV (€) · maximize',angle:-90,position:'insideLeft',fill:colors.ink}}/><Tooltip formatter={(value:any,key:any)=>[key==='npv'?money(value):`${fmt(value,2)} ${xUnit}`,key==='npv'?'NPV':key==='net_carbon'?'Net carbon':'Public support']}/><Legend/><Scatter name="Other front points" data={chartData.filter((p:any)=>p.rank==null)} fill={colors.blue} fillOpacity={.7}>{objective==='net_carbon_npv_subsidy'&&chartData.filter((p:any)=>p.rank==null).map((p:any,i:number)=><Cell key={i} fill={blend(colors.blue,colors.rose,(Number(p.subsidy_granted)-Math.min(...chartData.map((q:any)=>Number(q.subsidy_granted))))/(Math.max(...chartData.map((q:any)=>Number(q.subsidy_granted)))-Math.min(...chartData.map((q:any)=>Number(q.subsidy_granted)))||1))}/>)}</Scatter><Scatter name="Selected rank 0–10" data={chartData.filter((p:any)=>p.rank!=null)} shape="circle" fill={colors.yellow} fillOpacity={.92} label={{dataKey:'rank',position:'top',fill:colors.ink,fontSize:12}}>{chartData.filter((p:any)=>p.rank!=null).map((p:any,i:number)=><Cell key={i} fill={p.rank===0?colors.rose:p.rank===10?colors.green:blend(colors.rose,colors.green,Number(p.rank)/10)}/>)}</Scatter></ScatterChart></ResponsiveContainer></div>
      <div className="ds-table"><table><thead><tr><th>Rank</th><th>Switches P–B–N–P–K</th><th>Case</th><th>Net carbon (t C/year)</th><th>NPV (€)</th><th>Support PV (€)</th><th>Feed (t/year)</th></tr></thead><tbody>{selected.map((row:any)=><tr key={row.sample_id}><td>{row.rank}</td><td>{candidateLabel(row)}</td><td>{row.scenario_label}</td><td>{fmt(row.values?.net_carbon,2)}</td><td>{money(row.values?.npv)}</td><td>{money(row.values?.subsidy_granted)}</td><td>{fmt(row.configuration?.simulation?.wet_feed_rate_kg_hr*8760/1000,0)}</td></tr>)}</tbody></table></div>
      <details className="pareto-limitations"><summary>Assumptions and scope</summary><ul>{(data.limitations||[]).map((v:string,i:number)=><li key={i}>{v}</li>)}</ul><p>DEI+ and SDE++ labels identify the user-supplied hypothetical screening cases and RVO as the named awarding authority; these values are not verified programme rates or eligibility determinations.</p></details>
      <details className="pareto-figure-library"><summary>Current figure library · {figureData?.count??'…'} PNGs</summary>
        <div className="pareto-gallery-controls"><label>Figure group<select value={figureCategory} onChange={e=>setFigureCategory(e.target.value)}><option value="all">All groups</option>{figureCategories.map(category=><option key={category} value={category}>{category.replace(/^\d+_/,'').replaceAll('_',' ')}</option>)}</select></label><small>Figures use the unchanged GreenHub PNG exports; source, scenario and units are listed per image.</small></div>
        <div className="pareto-figure-grid">{visibleFigures.map(figure=><a className="pareto-figure-card" key={figure.figure_id} href={`${API_BASE}${figure.image_url}`} target="_blank" rel="noreferrer"><img loading="lazy" src={`${API_BASE}${figure.image_url}`} alt={figure.description}/><strong>{figure.figure_name.replaceAll('_',' ')}</strong><span>{figure.scenario}</span><small>{figure.units}</small></a>)}</div>
      </details>
    </>}
  </section>;
}
