import React,{useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {Bar,BarChart,CartesianGrid,Legend,ReferenceLine,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis} from 'recharts';
import paretoSnapshot from '../data/actualParetoPreview.json';
import {apiJson} from '../data/apiClient';
import {decisionApi,type DecisionReport} from '../data/decisionSupport';
import './decisionSupport.css';
import type {FeedInputs} from './InputStudio';
import type {CalculationMode,ScenarioSelection} from '../types';

type View='hotspots'|'optimization';
type Point={sample_id:string;source_sample_id:string;x:number;y:number;pareto:boolean};
type Scenario={sample_id:string;source_sample_id:string;configuration:any;objectives:{operating_profit:number;climate_load:number};feasibility:any;products:any[];tea:any};
const euro=(v:any)=>v==null||!Number.isFinite(Number(v))?'Incomplete':new Intl.NumberFormat(undefined,{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(Number(v));
const number=(v:any,d=1)=>v==null||!Number.isFinite(Number(v))?'Incomplete':Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const compact=(v:number)=>Math.abs(v)>=1e6?`${(v/1e6).toFixed(1)}m`:Math.abs(v)>=1000?`${(v/1000).toFixed(0)}k`:String(Math.round(v));
const economics=paretoSnapshot.economics;

const routeFields:{key:keyof ScenarioSelection;label:string;values:readonly (readonly [string,string])[]}[]=[
  {key:'feed_front_end',label:'Feed preparation',values:[['F0','Measured fraction'],['F1','No PEF'],['F2','PEF baseline'],['F3','PEF sensitivity']]},
  {key:'protein_recovery',label:'Protein recovery',values:[['PR0','Bypass'],['PR1','Acid'],['PR2','Heat'],['PR3','Acid + heat']]},
  {key:'anaerobic_digestion',label:'Digestion',values:[['AD0','Off'],['AD1','Baseline'],['AD2','Protein-rich liquid'],['AD3','Alternative'],['AD4','Advanced']]},
  {key:'biogas_upgrading',label:'Biogas upgrading',values:[['BG0','Off'],['BG1','Conditioning'],['BG2','Baseline'],['BG3','Water scrubber'],['BG4','Membrane'],['BG5','Amine']]},
  {key:'nutrient_recovery',label:'Nutrient recovery',values:[['NR0','Off'],['NR1','Solid-liquid'],['NR2','Struvite'],['NR3','Ammonia'],['NR4','Integrated N/P'],['NR5','Calcium phosphate'],['NR6','Ion exchange'],['NR7','Integrated N/P/K']]},
  {key:'process_order',label:'Process order',values:[['A','Sequence A'],['B','Sequence B']]},
];

export default function AnalyticsPreview({view,scenario,setScenario,feed,setFeed,month,setMonth,mode,setMode,running,onRun}:{view:View;scenario:ScenarioSelection;setScenario:React.Dispatch<React.SetStateAction<ScenarioSelection>>;feed:FeedInputs;setFeed:React.Dispatch<React.SetStateAction<FeedInputs>>;month:string;setMonth:(month:string)=>void;mode:CalculationMode;setMode:(mode:CalculationMode)=>void;running:boolean;onRun:()=>void}) {
  const scenarioRows=paretoSnapshot.scenarios as Scenario[];
  const scenarioById=useMemo(()=>new Map(scenarioRows.map(row=>[row.sample_id,row])),[scenarioRows]);
  const points=useMemo(()=>{
    const frontIds=new Set((paretoSnapshot.front as any[]).map(p=>p.sample_id));
    const mapped=[...(paretoSnapshot.cloud as any[]),...(paretoSnapshot.front as any[])];
    const unique=new Map(mapped.map(p=>[p.sample_id,p]));
    return [...unique.values()].map(p=>({...p,pareto:frontIds.has(p.sample_id)})) as Point[];
  },[]);
  const defaultScenario=scenarioRows.find(row=>row.sample_id===(paretoSnapshot.front as any[])[0]?.sample_id)||scenarioRows[0];
  const [selected,setSelected]=useState<Scenario>(defaultScenario);
  const [report,setReport]=useState<DecisionReport|null>(null);
  const [units,setUnits]=useState<any[]>([]);
  const [utilities,setUtilities]=useState<any[]>([]);
  const [detailBusy,setDetailBusy]=useState(false);
  const [detailError,setDetailError]=useState('');
  const detailRequest=useRef(0);

  const loadScenario=useCallback(async(row:Scenario,syncInputs=true)=>{
    const requestId=++detailRequest.current;
    setSelected(row);setReport(null);setUnits([]);setUtilities([]);setDetailError('');setDetailBusy(true);
    if(syncInputs) {
      const sim=row.configuration.simulation||{},routes=sim.scenarios||{},schedule=sim.operating_schedule||{};
      setScenario(current=>({...current,feed_front_end:routes.feed_preparation??current.feed_front_end,protein_recovery:routes.protein_recovery??current.protein_recovery,anaerobic_digestion:routes.anaerobic_digestion??current.anaerobic_digestion,biogas_upgrading:routes.biogas_upgrading??current.biogas_upgrading,nutrient_recovery:routes.nutrient_recovery??current.nutrient_recovery,process_order:routes.process_order??current.process_order}));
      setFeed(current=>({...current,feedAmountKgh:Number(sim.wet_feed_rate_kg_hr??current.feedAmountKgh),operatingDaysPerWeek:Number(schedule.operating_days_per_week??current.operatingDaysPerWeek),operatingHoursPerDay:Number(schedule.operating_hours_per_day??current.operatingHoursPerDay)}));
      if(sim.selected_month)setMonth(sim.selected_month);
      if(sim.calculation_mode)setMode(sim.calculation_mode as CalculationMode);
    }
    try {
      const full=await decisionApi<DecisionReport>('evaluate',{configuration:row.configuration});
      if(requestId!==detailRequest.current)return;
      setReport(full);
      const [unitResult,utilityResult]=await Promise.all([
        apiJson<any>(`/simulations/${encodeURIComponent(full.run_id)}/units`),
        apiJson<any>(`/simulations/${encodeURIComponent(full.run_id)}/utilities`),
      ]);
      if(requestId!==detailRequest.current)return;
      setUnits(Array.isArray(unitResult)?unitResult:unitResult.units||[]);
      setUtilities(Array.isArray(utilityResult)?utilityResult:utilityResult.utilities||[]);
    } catch(error) {
      if(requestId===detailRequest.current)setDetailError(error instanceof Error?error.message:'Detailed backend scenario could not be loaded. Saved scenario data remain visible.');
    } finally {if(requestId===detailRequest.current)setDetailBusy(false);}
  },[setScenario,setFeed,setMonth,setMode]);

  useEffect(()=>{if(view==='hotspots'&&selected&&!report&&!detailBusy)void loadScenario(selected,false);},[view,selected?.sample_id,report,detailBusy,loadScenario]);

  const selectedObjectives=selected.objectives;
  const tea=report?.tea||selected.tea;
  const opex=(tea?.opex_lines||[]).map((line:any)=>({name:[line.process_step||line.step,line.equipment_or_cost_item||line.item].filter(Boolean).join(' · ')||line.process_area||line.area||'Reported cost',value:Number(line.annual_cost_eur??line.annual_opex_eur??line.amount)})).filter((r:any)=>Number.isFinite(r.value)&&r.value>0).sort((a:any,b:any)=>b.value-a.value).slice(0,8);
  const capex=(tea?.capex_lines||[]).map((line:any)=>({name:[line.process_step||line.step,line.equipment_or_cost_item||line.item].filter(Boolean).join(' · ')||line.process_area||line.area||'Reported equipment',value:Number(line.installed_cost_eur??line.direct_capex_eur??line.direct_cost_eur??line.amount)})).filter((r:any)=>Number.isFinite(r.value)&&r.value>0).sort((a:any,b:any)=>b.value-a.value).slice(0,8);
  const operatingHours=Number(report?.annual?.period?.operating_hours);
  const electricity=utilities.filter((u:any)=>String(u.kind).toLowerCase()==='electricity').map((u:any)=>{
    const demand=Number(u.demand?.value??u.demand);
    const demandUnit=String(u.demand?.unit||'kW');
    const isPower=/^kw$/i.test(demandUnit);
    const unit=units.find((item:any)=>item.unit_id===u.unit_id);
    return {unit_id:u.unit_id,name:unit?.display_name||u.unit_id,value:isPower&&operatingHours>0?demand*operatingHours:demand,unit:isPower&&operatingHours>0?'kWh/year':demandUnit};
  }).filter((r:any)=>Number.isFinite(r.value)&&r.value>0).sort((a:any,b:any)=>b.value-a.value).slice(0,10);
  const inventory=report?.lca?.inventory||[];
  const climateBurdens=inventory.filter((r:any)=>Number.isFinite(r.climate_kg_co2e)&&r.climate_kg_co2e>0).map((r:any)=>({name:r.flow_id,value:r.climate_kg_co2e})).sort((a:any,b:any)=>b.value-a.value).slice(0,8);
  const climateCredits=inventory.filter((r:any)=>Number.isFinite(r.climate_kg_co2e)&&r.climate_kg_co2e<0).map((r:any)=>({name:r.flow_id,value:Math.abs(r.climate_kg_co2e)})).sort((a:any,b:any)=>b.value-a.value).slice(0,8);
  const electricityLoad=inventory.filter((r:any)=>String(r.group||r.flow_id).toLowerCase().includes('electric')&&Number.isFinite(r.climate_kg_co2e)&&r.climate_kg_co2e>0).reduce((sum:number,r:any)=>sum+r.climate_kg_co2e,0);
  const totalElectricity=electricity.reduce((sum:number,r:any)=>sum+r.value,0);
  const allocatedUnitClimate=electricityLoad>0&&totalElectricity>0?electricity.map((r:any)=>({...r,value:electricityLoad*r.value/totalElectricity})).sort((a:any,b:any)=>b.value-a.value).slice(0,10):[];
  const frontier=points.filter(p=>p.pareto),ordinary=points.filter(p=>!p.pareto);
  const handlePoint=(value:any)=>{const id=value?.payload?.sample_id||value?.sample_id;const row=scenarioById.get(id);if(row)void loadScenario(row,true);};

  return <section className="panel analytics-preview" aria-label={view==='optimization'?'BioSTEAM Pareto optimization':'BioSTEAM scenario hotspots'}>
    <div className="analytics-preview-top"><span className="ds-badge">BIOSTEAM · {paretoSnapshot.completed_count.toLocaleString()} SCENARIOS · PARTIAL LCA</span><span className="analytics-preview-meta">Subsidy {number(economics.subsidy_rate*100,0)}% · eligible CAPEX {number(economics.eligible_capex_fraction*100,0)}% · tax {number(economics.tax_rate*100,1)}%</span></div>
    <section className="analytics-preview-config" aria-label="Model configuration">
      <div className="analytics-preview-config-head"><h2>Model configuration</h2><button className="run-button" onClick={onRun} disabled={running}>{running?'Running model…':'Run model'}</button></div>
      <div className="analytics-preview-controls">
        <label>Wet feed rate (kg/h)<input type="number" min="1" value={feed.feedAmountKgh} onChange={e=>setFeed(current=>({...current,feedAmountKgh:Number(e.target.value)}))}/></label>
        <label>Operating days/week<input type="number" min="1" max="7" value={feed.operatingDaysPerWeek} onChange={e=>setFeed(current=>({...current,operatingDaysPerWeek:Number(e.target.value)}))}/></label>
        <label>Operating hours/day<input type="number" min="1" max="24" value={feed.operatingHoursPerDay} onChange={e=>setFeed(current=>({...current,operatingHoursPerDay:Number(e.target.value)}))}/></label>
        <label>Reference month<select value={month} onChange={e=>setMonth(e.target.value)}>{['January','February','March','April','May','June','July','August','September','October','November','December'].map(m=><option key={m}>{m}</option>)}</select></label>
        {routeFields.map(group=><label key={group.key}>{group.label}<select value={scenario[group.key]} onChange={e=>setScenario(current=>({...current,[group.key]:e.target.value}))}>{group.values.map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label>)}
      </div>
    </section>

    {view==='optimization'?<>
      <div className="analytics-preview-axis-title">Attributional climate load · kg CO₂e/year · lower is better · credits excluded</div>
      <div className="analytics-preview-chart" style={{width:'100%',height:570,minHeight:440,minWidth:0}} role="img" aria-label="BioSTEAM Pareto chart: after-tax profit versus annual attributional climate load">
        <ResponsiveContainer width="100%" height="100%" minWidth={320} minHeight={440}><ScatterChart margin={{top:12,right:28,bottom:18,left:24}}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--line)"/>
          <XAxis type="number" dataKey="x" name="After-tax profit" tickFormatter={compact} tick={{fontSize:11}} domain={['auto','auto']}/>
          <YAxis type="number" dataKey="y" name="Annual climate load" tickFormatter={compact} tick={{fontSize:11}} domain={['auto','auto']}/>
          <Tooltip formatter={(value:any,name:any)=>[name==='After-tax profit'?`${euro(Number(value))}/year`:`${number(value,0)} kg CO₂e/year`,name]} labelFormatter={(_,payload:any[])=>payload?.[0]?.payload?.source_sample_id||payload?.[0]?.payload?.sample_id}/>
          <Legend verticalAlign="top" height={30}/><ReferenceLine x={0} stroke="#819188"/>
          <Scatter name="Backend candidates" data={ordinary} fill="#5f8bb5" fillOpacity={0.48} onClick={handlePoint} isAnimationActive={false}/>
          <Scatter name="Pareto front · max profit / min load" data={frontier} fill="#bd7837" onClick={handlePoint} isAnimationActive={false}/>
        </ScatterChart></ResponsiveContainer>
      </div>
      <div className="analytics-preview-x-title">After-tax profit · EUR/year · higher is better</div>
    </>:<HotspotCharts opex={opex} capex={capex} electricity={electricity} climateBurdens={climateBurdens} climateCredits={climateCredits} allocatedUnitClimate={allocatedUnitClimate} loading={detailBusy}/>}

    <div className="analytics-preview-footer">{view==='optimization'?`${points.length} points shown · ${frontier.length} true nondominated points from the full batch`:detailBusy?'Loading detailed unit, TEA and LCA data…':'Selected scenario hotspots'}</div>
    <label className="analytics-preview-select">Scenario details<select value={selected.sample_id} onChange={e=>{const row=scenarioById.get(e.target.value);if(row)void loadScenario(row,true);}}>{points.map(point=><option key={point.sample_id} value={point.sample_id}>{point.source_sample_id||point.sample_id}{point.pareto?' · Pareto front':''}</option>)}</select></label>
    <details className="analytics-scenario-details" open>
      <summary>{selected.source_sample_id||selected.sample_id} · {detailBusy?'loading detail':report?'detailed process result':'saved BioSTEAM result'}</summary>
      {detailError&&<p className="analytics-detail-error">Detailed process data unavailable; saved scenario results are shown.</p>}
      <ScenarioDetails scenario={selected} report={report}/>
    </details>
    {view==='optimization'&&<HotspotCharts opex={opex} capex={capex} electricity={electricity} climateBurdens={climateBurdens} climateCredits={climateCredits} allocatedUnitClimate={allocatedUnitClimate} loading={detailBusy} compactView/>}
  </section>;
}

function ScenarioDetails({scenario:s,report}:{scenario:Scenario;report:DecisionReport|null}) {
  const sim=s.configuration.simulation||{},routes=sim.scenarios||{},totals=report?.tea?.totals||s.tea.totals||{},economics=s.configuration.candidate_economics||{},products=report?.products||s.products;
  const climate=report?.objectives?.climate?.value??s.objectives.climate_load;
  return <>
    <div className="analytics-detail-kpis">
      <Kpi label="After-tax profit" value={euro(s.objectives.operating_profit)} unit="EUR/year · subsidy-adjusted"/>
      <Kpi label="Climate load" value={number(climate,0)} unit="kg CO₂e/year · attributional burden"/>
      <Kpi label="Subsidy" value={euro(totals.subsidy_eur)} unit="applied to eligible CAPEX"/>
      <Kpi label="Optimization savings" value={euro(totals.optimization_savings_eur_per_year)} unit="EUR/year"/>
      <Kpi label="Annual revenue" value={euro(totals.optimized_annual_revenue_eur??totals.annual_revenue_eur)} unit="EUR/year"/>
      <Kpi label="Annual OPEX" value={euro(totals.optimized_annual_opex_eur??totals.annual_opex_eur)} unit="EUR/year"/>
    </div>
    <div className="analytics-detail-grid">
      <section><h3>Configuration</h3><dl>
        <Fact label="Feed rate" value={`${number(sim.wet_feed_rate_kg_hr)} kg/h`}/><Fact label="Capacity" value={`${number(sim.plant_capacity_kg_hr)} kg/h`}/><Fact label="Schedule" value={`${sim.operating_schedule?.operating_days_per_week} d/week · ${sim.operating_schedule?.operating_hours_per_day} h/day`}/><Fact label="Month / model" value={`${sim.selected_month||'—'} · ${sim.resolution_mode||'—'}`}/><Fact label="Project basis" value={`${s.configuration.project_basis?.location||'—'} · ${s.configuration.project_basis?.currency||'EUR'} ${s.configuration.project_basis?.price_year||''}`}/><Fact label="Process assumptions" value={s.configuration.use_screening_process_assumptions?'Screening assumptions enabled':'Explicit configuration'}/><Fact label="Storage" value={sim.storage_conditions?`${sim.storage_conditions.storage_days??0} days · ${sim.storage_conditions.aerobic_fraction??0} aerobic`:(s.configuration.use_screening_process_assumptions?'Screening storage profile':'Not enabled')}/><Fact label="Price basis" value={s.configuration.financial_assumptions?.use_screening_price_benchmarks?'Registered screening benchmarks':'Explicit prices'}/>
        {routeFields.map(r=><Fact key={r.key} label={r.label} value={routes[r.key]||'—'}/>)}<Fact label="Process order" value={routes.process_order||'—'}/>
      </dl></section>
      <section><h3>Optimization assumptions</h3><dl>
        <Fact label="Labour reduction" value={`${number((economics.labour_reduction||0)*100,1)}%`}/><Fact label="Logistics reduction" value={`${number((economics.logistics_reduction||0)*100,1)}%`}/><Fact label="Energy reduction" value={`${number((economics.energy_reduction||0)*100,1)}%`}/><Fact label="Protein yield uplift" value={`${number((economics.protein_yield_uplift||0)*100,1)}%`}/><Fact label="Nutrient recovery uplift" value={`${number((economics.nutrient_recovery_uplift||0)*100,1)}%`}/><Fact label="Subsidy" value={`${number((economics.subsidy_rate||0)*100,0)}% · ${euro(economics.subsidy_cap_eur)} cap · ${number((economics.eligible_capex_fraction||0)*100,0)}% eligible CAPEX`}/>
      </dl></section>
      <section><h3>TEA and products</h3><dl>
        <Fact label="Direct CAPEX" value={euro(totals.partial_direct_capex_eur??totals.total_direct_capex_eur)}/><Fact label="CAPEX completeness" value={totals.capex_status||'partial'}/><Fact label="TEA completeness" value={`OPEX ${totals.opex_status||'partial'} · revenue ${totals.revenue_status||'reported'} · profit ${totals.profit_status||'reported'}`}/><Fact label="LCA readiness" value={report?.lca?.readiness?.climate_objective_eligible?'Climate objective eligible':'Partial climate inventory'}/>
        {products.map((p:any)=><Fact key={p.product_id} label={p.product_id} value={`${number(p.mass_flow?.value,2)} ${p.mass_flow?.unit||'kg/h'}`}/>)}
        <Fact label="LCA objective" value={paretoSnapshot.climate_objective}/>
        {(report?.lca?.missing_inputs?.length||0)>0&&<Fact label="LCA missing inputs" value={`${report?.lca?.missing_inputs?.length} inputs`}/>}
      </dl></section>
    </div>
  </>;
}

function HotspotCharts({opex,capex,electricity,climateBurdens,climateCredits,allocatedUnitClimate,loading,compactView=false}:{opex:any[];capex:any[];electricity:any[];climateBurdens:any[];climateCredits:any[];allocatedUnitClimate:any[];loading:boolean;compactView?:boolean}) {
  const costRows=opex;
  const capexRows=capex;
  const Chart=({title,rows,color,unit}:{title:string;rows:any[];color:string;unit:string})=><section className="analytics-hotspot-card"><h3>{title}</h3>{rows.length?<div className="analytics-hotspot-plot" style={{width:'100%',height:230,minHeight:185,minWidth:0}}><ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={185}><BarChart data={rows} layout="vertical" margin={{top:4,right:24,bottom:4,left:8}}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact} tick={{fontSize:10}}/><YAxis type="category" dataKey="name" width={166} tick={{fontSize:10}} tickFormatter={(value:any)=>String(value).length>26?`${String(value).slice(0,25)}…`:String(value)}/><Tooltip formatter={(v:any)=>[`${number(v,1)} ${unit}`,title]}/><Bar dataKey="value" name={title} fill={color} radius={[0,4,4,0]}/></BarChart></ResponsiveContainer></div>:<div className="analytics-hotspot-empty">{loading?'Loading…':'Not reported for this scenario'}</div>}</section>;
  return <div className={`analytics-hotspot-grid${compactView?' compact':''}`}>
    <Chart title="Annual cost by process step · EUR/year" rows={costRows} color="#527d5e" unit="EUR/year"/>
    <Chart title="Direct CAPEX by equipment · EUR" rows={capexRows} color="#bd7837" unit="EUR"/>
    <Chart title={`Annual electricity by unit · ${electricity[0]?.unit||'kWh/year'}`} rows={electricity} color="#5f8bb5" unit={electricity[0]?.unit||'kWh/year'}/>
    <Chart title="Climate load by inventory burden · kg CO₂e/year" rows={climateBurdens} color="#bd7837" unit="kg CO₂e/year"/>
    <Chart title="Allocated electricity climate by unit · kg CO₂e/year" rows={allocatedUnitClimate} color="#527d5e" unit="kg CO₂e/year"/>
    <Chart title="Substitution credits · separate · kg CO₂e/year" rows={climateCredits} color="#729ad2" unit="kg CO₂e/year"/>
  </div>;
}

function Kpi({label,value,unit}:{label:string;value:string;unit:string}){return <article><span>{label}</span><strong>{value}</strong><small>{unit}</small></article>;}
function Fact({label,value}:{label:string;value:string}){return <div><dt>{label}</dt><dd>{value}</dd></div>;}
