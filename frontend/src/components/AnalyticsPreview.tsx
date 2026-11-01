import React,{useMemo,useState} from 'react';
import {Bar,BarChart,CartesianGrid,Legend,ReferenceLine,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis} from 'recharts';
import {defaultRanges,defaultSettings,generateScreeningBatch,type Point} from '../data/paretoScreening';

type View='hotspots'|'optimization';
const euro=(v:number)=>new Intl.NumberFormat(undefined,{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(v);
const number=(v:number,d=0)=>Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const routeText=(p:Point)=>`${p.routes.pef?'PEF':'No PEF'} · ${p.routes.protein} · ${p.routes.digestion} · ${p.routes.gas} · ${p.routes.fertilizer}`;
const colors=['#377d55','#5484bf','#c99a39','#b66e6b','#8f72aa','#48a5a1'];

function pareto(points:Point[],y:'offset'|'capital') {
  const candidates=points.filter(p=>p.feasible);
  return candidates.filter(p=>!candidates.some(q=>q.id!==p.id&&q.profit>=p.profit&&(y==='offset'?q.offset>=p.offset:q.capital<=p.capital)&&(q.profit>p.profit||(y==='offset'?q.offset>p.offset:q.capital<p.capital))));
}

export default function AnalyticsPreview({view}:{view:View}) {
  const batch=useMemo(()=>generateScreeningBatch(42,defaultRanges,defaultSettings),[]);
  const profitClimate=useMemo(()=>pareto(batch.points,'offset'),[batch]);
  const profitCapex=useMemo(()=>pareto(batch.points,'capital'),[batch]);
  const [selectedId,setSelectedId]=useState(()=>profitClimate[0]?.id||batch.points[0]?.id||'');
  const selected=batch.points.find(p=>p.id===selectedId)||batch.points[0];
  if(view==='hotspots')return <HotspotsPreview points={batch.points} selected={selected} onSelect={setSelectedId}/>;
  return <OptimizationPreview points={batch.points} frontClimate={profitClimate} frontCapex={profitCapex} selected={selected} selectedId={selectedId} onSelect={setSelectedId} seed={batch.seed}/>;
}

function PreviewHeader({eyebrow,title,description}:{eyebrow:string;title:string;description:string}) {
  return <div className="analytics-preview-head"><div><span className="ds-badge">OFFLINE PREVIEW · NOT LIVE</span><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{description}</p></div><div className="preview-only-note"><strong>Illustrative screening model</strong><span>These charts do not respond to Configure inputs and do not call the process backend.</span></div></div>;
}

function HotspotsPreview({points,selected,onSelect}:{points:Point[];selected:Point;onSelect:(id:string)=>void}) {
  const a=selected.assumptions;
  const protein=selected.routes.protein!=='Bypass',ad=selected.routes.digestion!=='Bypass';
  const gas=ad&&selected.routes.gas!=='No product · flare';
  const fertilizer=ad&&selected.routes.fertilizer!=='Bypass';
  const reagent=selected.magnesiumReagentKg*a.magnesiumPrice;
  const labour=selected.people*1500*a.labourRate;
  const logistics=selected.feedTonnes*a.logisticsRate;
  const electricity=selected.electricityKwh*a.electricityPrice;
  const heat=selected.heatKwh*a.heatPrice;
  const maintenance=.02*selected.capital;
  const consumables=selected.feedTonnes*a.consumablesCost*((protein?1:0)+(gas?.25:0)+(fertilizer?1:0));
  const costs=[{name:'Labour',value:labour},{name:'Logistics',value:logistics},{name:'Electricity',value:electricity},{name:'Heat',value:heat},{name:'Consumables',value:consumables},{name:'Mg reagent',value:reagent},{name:'Maintenance',value:maintenance}].filter(x=>x.value>0).sort((x,y)=>y.value-x.value);
  const mgBurden=selected.magnesiumReagentKg*a.magnesiumFootprint;
  const electricBurden=selected.electricityKwh*a.gridFactor;
  const heatBurden=selected.heatKwh*a.heatFactor;
  const transportBurden=selected.feedTonnes*a.transportFactor;
  const methaneBurden=Math.max(0,selected.burden-mgBurden-electricBurden-heatBurden-transportBurden);
  const climate=[{name:'Electricity',burden:electricBurden,credit:0},{name:'Heat',burden:heatBurden,credit:0},{name:'Transport',burden:transportBurden,credit:0},{name:'Mg reagent',burden:mgBurden,credit:0},{name:'Methane / residual',burden:methaneBurden,credit:0},{name:'Fossil gas displacement',burden:0,credit:selected.credit}];
  const feasible=points.filter(p=>p.feasible).length;
  return <section className="panel analytics-preview" aria-label="Offline hotspots chart preview">
    <PreviewHeader eyebrow="Explore · Hotspots" title="Cost and climate contribution preview" description="A scenario-level preview of the current screening equations. Choose another sample to inspect how proxy cost and climate contributors move across routes and scale."/>
    <div className="ds-warning"><strong>Preview basis:</strong> 2,000 deterministic local screening scenarios (seed 42). Cost and climate contributors are calculated from explicit screening assumptions—not backend TEA/LCA outputs or measured plant data.</div>
    <div className="ds-cards preview-kpis"><PreviewKpi label="Preview scenarios" value={number(points.length)} note="Fixed seed · local equations"/><PreviewKpi label="Screening-feasible" value={number(feasible)} note="Not technically validated"/><PreviewKpi label="Selected feed" value={`${number(selected.feedTonnes)} t/year`} note={`${number(selected.flowKgH)} kg/h`}/><PreviewKpi label="Selected net climate offset" value={`${number(selected.offset,1)} t CO₂e/year`} note="Credit minus included proxy burdens"/></div>
    <label className="preview-scenario-select">Preview scenario<select value={selected.id} onChange={e=>onSelect(e.target.value)}>{points.map(p=><option key={p.id} value={p.id}>{p.id} · {p.feasible?'screening-feasible':'excluded'} · {euro(p.profit)}/year</option>)}</select><small>Selection changes these preview charts only; it does not run the process model.</small></label>
    <div className="preview-hotspot-grid"><section className="preview-chart-card"><h3>Annual operating-cost hotspots</h3><p>Selected scenario · screening EUR/year by modeled cost contribution.</p><ResponsiveContainer width="100%" height={330}><BarChart data={costs} layout="vertical" margin={{left:12,right:22}}><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" tickFormatter={v=>number(v/1000,0)+'k'} unit=" EUR/year"/><YAxis type="category" dataKey="name" width={112}/><Tooltip formatter={(v:any)=>euro(Number(v))}/><Bar dataKey="value" name="Screening OPEX" fill={colors[0]} radius={[0,5,5,0]}/></BarChart></ResponsiveContainer></section><section className="preview-chart-card"><h3>Climate burden and displacement hotspots</h3><p>Selected scenario · included burden estimates and potential gas-displacement credit, kg CO₂e/year.</p><ResponsiveContainer width="100%" height={330}><BarChart data={climate} margin={{left:4,right:15}}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name" angle={-20} textAnchor="end" height={70} interval={0}/><YAxis tickFormatter={v=>number(v/1000,0)+'k'}/><Tooltip formatter={(v:any)=>`${number(Number(v),0)} kg CO₂e/year`}/><Legend/><Bar dataKey="burden" name="Burden proxy" fill={colors[3]}/><Bar dataKey="credit" name="Potential displacement credit" fill={colors[1]}/></BarChart></ResponsiveContainer></section></div>
    <PreviewScenario point={selected}/>
  </section>;
}

function OptimizationPreview({points,frontClimate,frontCapex,selected,selectedId,onSelect,seed}:{points:Point[];frontClimate:Point[];frontCapex:Point[];selected:Point;selectedId:string;onSelect:(id:string)=>void;seed:number}) {
  const plotted=points.filter(p=>p.feasible);
  const climateData=plotted.map(p=>({...p,pareto:frontClimate.some(f=>f.id===p.id)}));
  const capexData=plotted.map(p=>({...p,pareto:frontCapex.some(f=>f.id===p.id)}));
  const pick=(v:any)=>{const id=v?.payload?.id;if(id)onSelect(id);};
  return <section className="panel analytics-preview" aria-label="Offline optimization graph preview">
    <PreviewHeader eyebrow="Explore · Optimization" title="Scenario trade-off preview" description="Two preview frontiers compare the same locally generated process-screening scenarios. Select a point to see its route, feed rate, proxy TEA and climate assumptions."/>
    <div className="ds-warning"><strong>Not a BioSTEAM or backend run.</strong> These are seeded, local screening estimates. “Pareto” means nondominated within this sampled preview only; it is not a validated or globally optimal design.</div>
    <div className="ds-cards preview-kpis"><PreviewKpi label="Sampled designs" value={number(points.length)} note={`Seed ${seed} · reproducible`} /><PreviewKpi label="Plotted" value={number(plotted.length)} note="Pass local topology/scale checks"/><PreviewKpi label="Profit vs climate front" value={number(frontClimate.length)} note="Maximize profit and net offset"/><PreviewKpi label="Profit vs CAPEX front" value={number(frontCapex.length)} note="Maximize profit · minimize CAPEX"/></div>
    <div className="preview-pareto-grid"><PreviewScatter title="Annualized profit vs net climate offset" subtitle="Upper-right improves both proxy objectives · EUR/year vs t CO₂e/year" data={climateData} yKey="offset" yName="Net offset proxy" yUnit=" t CO₂e/year" xName="Annualized profit proxy" color={colors[1]} frontColor={colors[2]} onPick={pick}/><PreviewScatter title="Annualized profit vs screening CAPEX" subtitle="Upper-left reduces CAPEX while increasing proxy profit · EUR/year" data={capexData} yKey="capital" yName="Screening CAPEX" yUnit=" EUR" xName="Annualized profit proxy" color={colors[1]} frontColor={colors[2]} onPick={pick}/></div>
    <label className="preview-scenario-select">Inspect preview scenario<select value={selectedId} onChange={e=>onSelect(e.target.value)}>{points.map(p=><option key={p.id} value={p.id}>{p.id} · {p.feasible?'screening-feasible':'excluded'} · {euro(p.profit)}/year</option>)}</select><small>Click either graph or choose a scenario. The selected configuration is descriptive preview data only.</small></label>
    <PreviewScenario point={selected}/>
  </section>;
}

function PreviewScatter({title,subtitle,data,yKey,yName,yUnit,xName,color,frontColor,onPick}:{title:string;subtitle:string;data:Point[];yKey:'offset'|'capital';yName:string;yUnit:string;xName:string;color:string;frontColor:string;onPick:(value:any)=>void}) {
  const front=data.filter(p=>p.pareto);const ordinary=data.filter(p=>!p.pareto);
  return <section className="preview-chart-card"><h3>{title}</h3><p>{subtitle}</p><div className="preview-scatter"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:12,right:18,bottom:25,left:5}}><CartesianGrid strokeDasharray="3 3"/><XAxis type="number" dataKey="profit" name={xName} tickFormatter={v=>number(v/1000,0)+'k'} unit=" EUR/year"/><YAxis type="number" dataKey={yKey} name={yName} tickFormatter={v=>number(v/1000,0)+'k'} unit={yUnit}/><Tooltip content={<PreviewTooltip/>} cursor={{strokeDasharray:'3 3'}}/><Legend verticalAlign="top"/><ReferenceLine x={0} stroke="#80958a"/><Scatter name="Screening samples" data={ordinary} fill={color} fillOpacity={.4} onClick={onPick} isAnimationActive={false}/><Scatter name="Sampled Pareto preview" data={front} fill={frontColor} onClick={onPick} isAnimationActive={false}/></ScatterChart></ResponsiveContainer></div></section>;
}

function PreviewTooltip({active,payload}:any){const p=payload?.[0]?.payload as Point|undefined;return active&&p?<div className="ds-point-tooltip"><strong>{p.id}{p.pareto?' · sampled front':''}</strong><p>{routeText(p)}</p><dl className="ds-point-kpis"><dt>Proxy profit</dt><dd>{euro(p.profit)}/year</dd><dt>Net climate offset</dt><dd>{number(p.offset,1)} t CO₂e/year</dd><dt>Feed rate</dt><dd>{number(p.flowKgH,1)} kg/h</dd></dl></div>:null;}

function PreviewScenario({point:p}:{point:Point}) {
  return <section className="ds-selected-point preview-scenario"><div className="preview-detail-head"><div><span className="eyebrow">Selected local preview point</span><h3>{p.id}{p.pareto?' · proxy Pareto sample':''}</h3><p>{routeText(p)} · {p.feasible?'passes preview constraints':'excluded from plotted frontier'}</p></div><span className="ds-badge">STATIC ASSUMPTION-BASED</span></div><div className="ds-cards preview-detail-kpis"><PreviewKpi label="Feed basis" value={`${number(p.feedTonnes)} t/year`} note={`${number(p.flowKgH,1)} kg/h`} /><PreviewKpi label="Proxy revenue" value={`${euro(p.revenue)}/year`} note="Marketability not validated"/><PreviewKpi label="Proxy OPEX" value={`${euro(p.opex)}/year`} note="Included screening lines"/><PreviewKpi label="Operating profit" value={`${euro(p.operatingProfit)}/year`} note="Before annual capital recovery"/><PreviewKpi label="Capital recovery" value={`${euro(p.capitalCharge)}/year`} note={`${euro(p.capital)} screening CAPEX`}/><PreviewKpi label="Annualized proxy profit" value={`${euro(p.profit)}/year`} note="Revenue − OPEX − capital recovery"/><PreviewKpi label="Climate burden / credit" value={`${number(p.burden/1000,1)} / ${number(p.credit/1000,1)} t`} note="Proxy kg CO₂e contributions / 1,000"/><PreviewKpi label="Subsidy overlay" value="Not applied" note="Requires the backend decision-analysis calculation"/></div><details><summary>Preview configuration and assumptions</summary><div className="pareto-configuration-grid"><ConfigFact label="PEF" value={p.routes.pef?'On':'Off'}/><ConfigFact label="Protein route" value={p.routes.protein}/><ConfigFact label="Digestion" value={p.routes.digestion}/><ConfigFact label="Gas route" value={p.routes.gas}/><ConfigFact label="Nutrient route" value={p.routes.fertilizer}/><ConfigFact label="Biomass fraction" value={`${number(p.fraction*100,1)}%`}/><ConfigFact label="People assumption" value={`${p.people} people · 1,500 paid h/person/year`}/><ConfigFact label="Evidence caveat" value={p.feasible?'Assumption-based screening; not technical validation':p.reasons.join(' ')}/></div><details><summary>All sampled parameter assumptions</summary><pre>{JSON.stringify(p.assumptions,null,2)}</pre></details></details></section>;
}
function PreviewKpi({label,value,note}:{label:string;value:string;note:string}){return <article><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;}
function ConfigFact({label,value}:{label:string;value:string}){return <div><span>{label}</span><strong>{value}</strong></div>;}
