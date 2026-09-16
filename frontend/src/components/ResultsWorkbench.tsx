import React, { useMemo, useState } from 'react';
import { Activity, AlertTriangle, BarChart3, CheckCircle2, FileDown, GitBranch, Package, Scale, Table2, Zap } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { AnnualSummary, PlotCatalogItem, SimulationResult } from '../types';
import type { ResultSourceState } from '../types';
import { EmpiricalEngineeringReport, type EmpiricalComparisonRun } from './EngineeringReport';

type GraphLike = { nodes?: any[]; edges?: any[]; run_id?: string } | null;
type Artifact = { name: string; type: string; description: string; url?: string; available: boolean; warning?: string };
type ViewId = 'story'|'annual'|'pathway'|'diagnostics'|'engineering'|'technical';
const chartColors = ['#408f4d','#729ad2','#d1a520','#d277a3'];
const areaLabels: Record<string,string> = {
  feedstock_and_characterization: 'Feed characterization', feed_preparation_and_primary_separation: 'Feed preparation',
  protein_recovery: 'Protein recovery', anaerobic_digestion: 'Anaerobic digestion',
  biogas_conditioning_and_upgrading: 'Biogas upgrading', biogas_upgrading: 'Biogas upgrading',
  digestate_treatment_and_nutrient_recovery: 'Nutrient recovery', nutrient_recovery: 'Nutrient recovery',
  shared_utilities_and_supporting_operations: 'Utilities', integrated_system: 'Whole system', unassigned: 'Other units',
};

export function ResultsWorkbench({ result, graph, runtime, sourceState, savedRuns, onSaveRun }: {
  result: SimulationResult; graph: GraphLike; runtime: string; artifacts?: Artifact[]; sourceState?:ResultSourceState; savedRuns?:EmpiricalComparisonRun[]; onSaveRun?:(label:string,result:SimulationResult)=>void;
}) {
  const [view, setView] = useState<ViewId>('story');
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const annual = (result as SimulationResult & { annual?: AnnualSummary | null }).annual ?? null;
  const nodes = graph?.nodes ?? result.units.map(unit => ({ unit_id:unit.id,display_name:unit.name,process_area:unit.area,active:unit.status==='active',technology:unit.type,key_kpis:{power_kw:unit.power_kw},warning_count:unit.status_reason?1:0 }));
  const edges = graph?.edges ?? [];
  const grouped = useMemo(() => nodes.reduce<Record<string,any[]>>((acc,node) => { (acc[node.process_area || 'unassigned'] ||= []).push(node); return acc; },{}),[nodes]);
  const tabs: [ViewId,string,any][] = [
    ['story','Key findings',Activity],['annual','Annual plan',BarChart3],['pathway','Process pathway',GitBranch],
    ['diagnostics','Balance and quality',Scale],['engineering','Engineering report',FileDown],['technical','Detailed data',Table2],
  ];

  return <section className="results-workbench panel">
    <div className="panel-title result-heading"><span className="title-icon"><BarChart3 size={17}/></span><div><h3>Simulation results</h3><p>{runtime} · run completed {new Date(result.timestamp).toLocaleString()}</p></div><span className={`status ${result.validation.status}`}>{result.validation.status === 'pass' ? 'checks passed' : `${result.validation.status} — review`}</span></div>
    <div className="result-tabs">{tabs.map(([id,label,Icon]) => <button className={view===id?'active':''} onClick={() => setView(id)} key={id}><Icon size={14}/>{label}</button>)}</div>
    {view==='story' && <StoryView result={result} annual={annual}/>}
    {view==='annual' && <AnnualView result={result} annual={annual}/>}
    {view==='pathway' && <PathwayView result={result} annual={annual} nodes={nodes} grouped={grouped} selected={selectedNode} onSelect={setSelectedNode}/>}
    {view==='diagnostics' && <Diagnostics result={result}/>}
    {view==='engineering' && <EmpiricalEngineeringReport result={result} status={sourceState || {status:'preview_baseline',label:runtime,detail:'Result source was not supplied.',is_live:false}} savedRuns={savedRuns} onSave={onSaveRun}/>}
    {view==='technical' && <TechnicalView result={result}/>}
  </section>;
}

export function ReportCenter({ result, artifacts = [], runtime }: {
  result: SimulationResult; artifacts?: Artifact[]; runtime: string;
}) {
  return <section className="reports-workbench panel">
    <div className="panel-title result-heading"><span className="title-icon"><FileDown size={17}/></span><div><h3>Run exports</h3><p>{runtime} · completed {new Date(result.timestamp).toLocaleString()}</p></div><span className={`status ${result.validation.status}`}>{result.validation.status === 'pass' ? 'checks passed' : `${result.validation.status} — review`}</span></div>
    <ReportsView artifacts={artifacts} result={result}/>
  </section>;
}

function StoryView({result,annual}:{result:SimulationResult;annual:AnnualSummary|null}) {
  const products = productRows(result,annual);
  const utilities = utilityRows(result,annual);
  const active = result.units.filter(unit=>unit.status==='active').length;
  const warnings = result.validation.issues.length;
  return <div className="story-stack">
    <section className="decision-kpis">
      <Outcome label="Feed processed" value={annual ? formatMass(annual.feed_processed.value) : `${result.balances.mass_in_kgh.toFixed(1)} kg/h`} tone="green"/>
      <Outcome label="Protein product" value={annual ? formatMass(annual.products.dry_protein_product?.value || 0) : `${result.metrics.protein_recovered_kgh.toFixed(1)} kg/h`} tone="green"/>
      <Outcome label="Biomethane" value={annual ? formatMass(annual.products.biomethane?.value || 0) : `${result.metrics.biomethane_flow_m3h.toFixed(1)} kg/h`} tone="blue"/>
      <Outcome label="Mass closure" value={`${(annual?.balance.overall_closure_pct ?? result.balances.mass_closure_pct).toFixed(3)}%`} tone={result.validation.status==='pass'?'green':'rose'}/>
    </section>
    {annual && <div className="method-note"><CheckCircle2 size={15}/><div><strong>{annual.method_label}</strong><span>{annual.basis}</span></div></div>}
    <section className="story-grid">
      <article className="story-chart"><div className="story-title"><Package/><div><h4>Recovered products</h4><p>Where useful material leaves the process.</p></div></div><SimpleBar data={products} unit={annual?'t/year':'kg/h'}/></article>
      <article className="story-chart"><div className="story-title"><Zap/><div><h4>Utility demand</h4><p>Period energy is separated from instantaneous power.</p></div></div>{annual?<div className="utility-summary"><div><span>Electricity</span><strong>{formatEnergy(annual.utilities.electricity?.value||0)}</strong></div><div><span>Heating</span><strong>{formatHeat(annual.display_utilities?.heating?.value||0)}</strong></div><div><span>Cooling</span><strong>{formatHeat(annual.display_utilities?.cooling?.value||0)}</strong></div></div>:<SimpleBar data={utilities} unit="kW instantaneous"/>}</article>
    </section>
    <section className="process-readout">
      <div><span>Process activity</span><strong>{active} active units</strong><small>{result.units.length-active} bypassed or inactive</small></div>
      <div><span>Quality checks</span><strong>{warnings ? `${warnings} items to review` : 'No blocking issues'}</strong><small>{result.validation.status === 'pass' ? 'Balance checks passed' : 'Use results with the listed cautions'}</small></div>
      <div><span>Decision signal</span><strong>{result.validation.status === 'pass' ? 'Ready for comparison' : 'Review before comparing'}</strong><small>Warnings and assumptions remain visible in this run.</small></div>
    </section>
  </div>;
}

function AnnualView({result,annual}:{result:SimulationResult;annual:AnnualSummary|null}) {
  if (!annual) return <Empty title="Annual results are not available" text="Run the Python model to calculate a full-year operating plan."/>;
  const charts = annual.chart_data;
  const schedule = annual.biomass_schedule;
  const nutrient = (annual.products.phosphorus_product?.value||0)+(annual.products.ammonium_product?.value||0)+(annual.products.potassium_concentrate?.value||0);
  return <div className="annual-stack">
    <section className="decision-kpis annual-kpis"><Outcome label="Annual feed" value={formatMass(annual.feed_processed.value)} tone="green"/><Outcome label="Protein" value={formatMass(annual.products.dry_protein_product?.value||0)} tone="green"/><Outcome label="Biomethane" value={formatMass(annual.products.biomethane?.value||0)} tone="blue"/><Outcome label="Nutrient products" value={formatMass(nutrient)} tone="yellow"/><Outcome label="Electricity" value={formatEnergy(annual.utilities.electricity?.value||0)} tone="rose"/></section>
    <section className="annual-basis"><div><span>Calculation basis</span><strong>{annual.method_label}</strong><p>{annual.basis}</p></div><dl><div><dt>Operating hours</dt><dd>{annual.period.operating_hours.toLocaleString(undefined,{maximumFractionDigits:0})} h/year</dd></div><div><dt>Schedule</dt><dd>{annual.period.schedule_source}</dd></div><div><dt>Balance result</dt><dd>{annual.balance.passed?'Passed':'Review required'}</dd></div></dl></section>
    {charts?.schedule?.length ? <>
      <section className="schedule-facts"><div><span>Available</span><strong>{schedule.annual_available_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Processed</span><strong>{schedule.annual_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Unused</span><strong>{schedule.annual_unused_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Utilization</span><strong>{(schedule.utilization_fraction*100).toFixed(1)}%</strong></div><div><span>Peak month</span><strong>{schedule.peak_month_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t</strong></div></section>
      <TrendChart title="Biomass schedule" note="Availability remains fixed; processed biomass follows the refinery cap." unit="tonnes/month" data={charts.schedule} series={[['available_biomass_tonnes','Available'],['processed_biomass_tonnes','Processed'],['unused_biomass_tonnes','Unused']]}/>
      <div className="annual-chart-grid">
        <TrendChart title="Feed and bulk streams" note="Large streams use their own mass scale." unit="tonnes/month" data={charts.bulk_streams} series={[['feed_processed_tonnes','Feed'],['press_cake_tonnes','Press cake'],['digestate_tonnes','Digestate']]}/>
        <TrendChart title="Protein and fertilizer products" note="Small products are separated from feed so they remain visible." unit="tonnes/month" data={charts.small_products} series={[['protein_tonnes','Protein'],['phosphorus_product_tonnes','P product'],['ammonium_product_tonnes','Ammonium'],['potassium_concentrate_tonnes','K concentrate']]}/>
        <TrendChart title="Biomethane route" note="Monthly gas volume at the modelled product-stream state." unit="m³/month" data={charts.biomethane} series={[["biomethane_m3","Biomethane"]]}/>
        <TrendChart title="Electricity" note="Integrated energy, not instantaneous power." unit="MWh/month" data={charts.energy} series={[["electricity_MWh","Electricity demand"]]}/>
        <TrendChart title="Heating and cooling" note="Thermal energy is reported separately from electricity." unit="GJ/month" data={charts.energy} series={[["heating_GJ","Heating"],["cooling_GJ","Cooling"]]}/>
        <TrendChart title="Mass-balance closure" note="Monthly empirical balance check." unit="%" data={charts.mass_balance} series={[["closure_percent","Mass closure"]]}/>
        <TrendChart title="Monthly supply utilization" note="Processed share of available biomass in each month." unit="%" data={charts.schedule} series={[["utilization_percent","Utilization"]]}/>
      </div>
    </> : <Empty title="No monthly series for this run" text="These totals were annualized from one steady-state result; a seasonal trend was not invented."/>}
  </div>;
}

function Diagnostics({result}:{result:SimulationResult}) {
  const rows=[['Overall mass',result.balances.mass_in_kgh,result.balances.mass_out_kgh,result.balances.mass_closure_pct],...Object.entries(result.balances.elemental).map(([name,value])=>[humanize(name),value.in,value.out,value.closure])];
  return <div className="diagnostic-stack"><section className={`balance-banner ${result.validation.status}`}><Scale/><div><span>Overall mass closure</span><strong>{result.balances.mass_closure_pct.toFixed(5)}%</strong><p>{result.validation.status==='pass'?'The run meets the configured balance tolerance.':'Review residuals and validation notes before using this run.'}</p></div></section><DataTable headers={['Balance','In','Out','Closure']} rows={rows.map(([name,input,output,closure])=>[String(name),`${Number(input).toFixed(3)} kg/h`,`${Number(output).toFixed(3)} kg/h`,`${Number(closure).toFixed(4)}%`])}/>{result.validation.issues.length?<div className="issue-list">{result.validation.issues.map((issue,index)=><div key={index}><AlertTriangle size={14}/><span>{issue.message}</span></div>)}</div>:<div className="quality-ok"><CheckCircle2/><span>No blocking validation issues were returned for this run.</span></div>}</div>;
}

function TechnicalView({result}:{result:SimulationResult}) { const utility=(value:number)=>Math.abs(value)>1e-9?`${value.toFixed(1)} kW`:'Not modelled'; return <div className="technical-stack"><details open><summary>Process streams <span>{result.streams.length}</span></summary><DataTable headers={['Stream','From → to','Mass','Dry solids','COD','N','P']} rows={result.streams.map(stream => [humanize(stream.name||stream.id),`${humanize(stream.origin)} → ${humanize(stream.destination)}`,`${stream.mass_flow_kgh.toFixed(1)} kg/h`,stream.dry_solids_pct?`${stream.dry_solids_pct.toFixed(1)}%`:'—',stream.cod_kgh?stream.cod_kgh.toFixed(1):'—',stream.nitrogen_kgh?stream.nitrogen_kgh.toFixed(2):'—',stream.phosphorus_kgh?stream.phosphorus_kgh.toFixed(2):'—'])}/></details><details><summary>Unit operations <span>{result.units.length}</span></summary><DataTable headers={['Unit','Area','Status','Instantaneous power','Instantaneous duty']} rows={result.units.map(unit => [unit.name,areaLabels[unit.area]||humanize(unit.area),humanize(unit.status),utility(unit.power_kw),utility(unit.duty_kw)])}/></details><details><summary>Additional model charts <span>{result.plots.length}</span></summary><AnalyticsView plots={result.plots}/></details></div>; }

function AnalyticsView({plots}:{plots:PlotCatalogItem[]}) { return plots.length ? <div className="chart-grid">{plots.map(plot => <ChartCard key={plot.id} plot={plot}/>)}</div> : <Empty title="No additional charts" text="The model did not return optional chart datasets for this configuration."/>; }
function ChartCard({plot}:{plot:PlotCatalogItem}) { const rows=plot.data||[]; const first=rows[0]||{}; const keys=Object.keys(first); const labelKey=keys.find(key => typeof first[key]==='string')||keys[0]; const numericKeys=keys.filter(key => key!==labelKey&&typeof first[key]==='number').slice(0,4); if(!rows.length||!numericKeys.length)return <div className="chart-card unavailable"><span className="eyebrow">{humanize(plot.category)}</span><h4>{plot.title}</h4><Empty title="Dataset unavailable" text="This chart is not produced by the selected pathway."/></div>; const data=rows.map(row=>({...row,label:String(row[labelKey]??'')})); return <div className="chart-card"><span className="eyebrow">{humanize(plot.category)}</span><h4>{plot.title}</h4><p>{plot.description}</p><ResponsiveContainer width="100%" height={220}><BarChart data={data}><CartesianGrid stroke="#d4cec7" vertical={false}/><XAxis dataKey="label" stroke="#587174" fontSize={8}/><YAxis stroke="#587174" fontSize={8}/><Tooltip contentStyle={tooltipStyle}/>{numericKeys.map((key,index)=><Bar key={key} name={humanize(key)} dataKey={key} fill={chartColors[index]} radius={[3,3,0,0]}/>)}</BarChart></ResponsiveContainer></div>; }

function ReportsView({artifacts,result}:{artifacts:Artifact[];result:SimulationResult}) { const items=artifacts.length?artifacts:[{name:'Run exports',type:'Report',description:'No downloadable files were returned for this run.',available:false,warning:'Run the Python model to generate reports.'}]; const preferred=['Annual Summary','Summary','Products Csv','Utilities Csv','Validation Csv','Run Manifest','Simulation Result']; const featured=preferred.flatMap(name=>items.filter(item=>item.name===name)); return <div className="reports-stack"><div className="report-context"><div><span>Scenario</span><strong>{result.scenarios.feed_front_end} · {result.scenarios.protein_recovery} · {result.scenarios.anaerobic_digestion} · {result.scenarios.biogas_upgrading} · {result.scenarios.nutrient_recovery}</strong></div><div><span>Completed</span><strong>{new Date(result.timestamp).toLocaleString()}</strong></div><div><span>Run reference</span><strong>{result.run_id.slice(0,12)}</strong></div></div><div><span className="eyebrow">Recommended downloads</span><ArtifactRows items={featured.length?featured:items}/></div>{artifacts.length>featured.length&&<details className="all-exports"><summary>All generated files <span>{artifacts.length}</span></summary><ArtifactRows items={artifacts}/></details>}</div>; }
function ArtifactRows({items}:{items:Artifact[]}) { return <div className="artifact-list">{items.map((artifact,index)=><div className="artifact-card" key={`${artifact.name}-${index}`}><div><span className="eyebrow">{artifact.type}</span><h4>{artifact.name}</h4><p>{artifact.description}</p>{artifact.warning&&<small className="artifact-warning"><AlertTriangle size={12}/>{artifact.warning}</small>}</div>{artifact.available&&artifact.url?<a className="secondary" href={artifact.url} download><FileDown size={14}/>Download</a>:<span className="status disabled">unavailable</span>}</div>)}</div>; }

function PathwayView({result,annual,nodes,grouped,selected,onSelect}:{result:SimulationResult;annual:AnnualSummary|null;nodes:any[];grouped:Record<string,any[]>;selected:any;onSelect:(value:any)=>void}) {
  const fallbackStages = [
    ['feed','Feed',['feedstock_and_characterization','front_end']],['pretreatment','Pre-treatment / press',['feed_preparation_and_primary_separation']],
    ['protein','Protein recovery',['protein_recovery']],['ad','Anaerobic digestion',['anaerobic_digestion']],
    ['gas','Gas upgrading / CHP',['biogas_conditioning_and_upgrading','biogas_upgrading']],['nutrients','Nutrient recovery / products',['digestate_treatment_and_nutrient_recovery','nutrient_recovery']],
  ].map(([stage_id,label,areas]:any[])=>{const stageNodes=(areas as string[]).flatMap(area=>grouped[area]||[]);return{stage_id,label,active_unit_names:stageNodes.filter(node=>node.active!==false).map(node=>node.display_name),unit_count:stageNodes.length,products_kg_hr:{},power_kw:stageNodes.reduce((sum,node)=>sum+Math.max(Number(node.key_kpis?.power_kw||0),0),0)||null,heat_duty_kw:null,limitations:stageNodes.filter(node=>node.warning_count).map(node=>`${node.display_name}: review model notes`),data_quality:'empirical structural model'};});
  const stages = annual?.process_pathway?.length ? annual.process_pathway : fallbackStages;
  const active = selected || stages[0];
  const productEntries=Object.entries(active.products_kg_hr||{}).filter(([,value])=>Number(value)>0);
  return <div className="pathway-infographic"><div className="pathway-strip" role="list" aria-label="Empirical process pathway">{stages.map((stage,index)=><React.Fragment key={stage.stage_id}><button role="listitem" className={`pathway-stage ${active.stage_id===stage.stage_id?'selected':''}`} aria-expanded={active.stage_id===stage.stage_id} onClick={()=>onSelect(stage)} onFocus={()=>onSelect(stage)}><span>{String(index+1).padStart(2,'0')}</span><strong>{stage.label}</strong><small>{stage.unit_count} active/modelled units</small>{productEntries.length>0&&active.stage_id===stage.stage_id?<em>{productEntries.length} product outputs</em>:null}</button>{index<stages.length-1&&<b aria-hidden="true">→</b>}</React.Fragment>)}</div><section className="pathway-detail" aria-live="polite"><div><span className="eyebrow">Selected stage</span><h4>{active.label}</h4><p>{active.active_unit_names.length?active.active_unit_names.join(' · '):'No active units in this stage.'}</p></div><dl><div><dt>Products / intermediates</dt><dd>{productEntries.length?productEntries.map(([name,value])=>`${humanize(name)} ${Number(value).toFixed(2)} kg/h`).join(' · '):'No product stream reported'}</dd></div><div><dt>Utilities</dt><dd>{active.power_kw?`${active.power_kw.toFixed(1)} kW instantaneous power`:active.heat_duty_kw?`${active.heat_duty_kw.toFixed(1)} kW instantaneous heat duty`:'Not modelled or zero demand'}</dd></div><div><dt>Data quality</dt><dd>{active.data_quality||'Not reported'}</dd></div><div><dt>Assumptions / limitations</dt><dd>{active.limitations?.length?active.limitations.slice(0,3).join(' · '):'No stage-specific limitation returned'}</dd></div></dl></section><p className="pathway-note">Stage cards summarize the active empirical route. Select or focus a stage for unit names, products, utilities and limitations.</p></div>;
}

function TrendChart({title,note,unit,data,series}:{title:string;note:string;unit:string;data:Array<Record<string,number|string>>;series:Array<[string,string]>}) { return <section className="trend-card"><div className="story-title"><BarChart3/><div><h4>{title}</h4><p>{note}</p></div></div><span className="chart-unit">{unit}</span><ResponsiveContainer width="100%" height={260}><LineChart data={data}><CartesianGrid stroke="#d4cec7" vertical={false}/><XAxis dataKey={data[0]?.period!==undefined?'period':'time_label'} stroke="#587174" fontSize={10}/><YAxis stroke="#587174" fontSize={9}/><Tooltip contentStyle={tooltipStyle}/><Legend/>{series.map(([key,label],index)=><Line key={key} type="monotone" dataKey={key} name={label} stroke={chartColors[index%chartColors.length]} strokeWidth={2.3} dot={false} connectNulls={false}/>)}</LineChart></ResponsiveContainer></section>; }

function Outcome({label,value,tone}:{label:string;value:string;tone:string}) { return <div className="outcome"><span>{label}</span><strong className={tone}>{value}</strong></div>; }
function SimpleBar({data,unit}:{data:Array<{name:string;value:number}>;unit:string}) { return <ResponsiveContainer width="100%" height={240}><BarChart data={data} layout="vertical" margin={{left:12,right:22}}><CartesianGrid stroke="#d4cec7" horizontal={false}/><XAxis type="number" stroke="#587174" fontSize={9} unit={` ${unit}`}/><YAxis type="category" dataKey="name" width={115} stroke="#587174" fontSize={9}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="value" radius={[0,4,4,0]}>{data.map((item,index)=><Cell key={item.name} fill={chartColors[index%chartColors.length]}/>)}</Bar></BarChart></ResponsiveContainer>; }
function DataTable({headers,rows}:{headers:string[];rows:string[][]}) { return <div className="data-table-wrap"><table className="data-table"><thead><tr>{headers.map(header=><th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={index}>{row.map((cell,column)=><td key={column}>{cell}</td>)}</tr>)}</tbody></table>{!rows.length&&<div className="empty-state">No data returned for this run.</div>}</div>; }
function Empty({title,text}:{title:string;text:string}) { return <div className="empty-state"><BarChart3 size={22}/><strong>{title}</strong><span>{text}</span></div>; }
function productRows(result:SimulationResult,annual:AnnualSummary|null) { const values = annual ? [['Protein',annual.products.dry_protein_product?.value||0],['Biomethane',annual.products.biomethane?.value||0],['Phosphorus',annual.products.phosphorus_product?.value||0],['Ammonium',annual.products.ammonium_product?.value||0],['Potassium',annual.products.potassium_concentrate?.value||0]] : [['Protein',result.metrics.protein_recovered_kgh],['Biomethane',result.metrics.biomethane_flow_m3h],['Phosphorus',result.metrics.struvite_yield_kgh],['Ammonium',result.metrics.ammonia_sulfate_kgh],['Potassium',result.metrics.potassium_concentrate_kgh]]; return values.map(([name,value])=>({name:String(name),value:Number(value)/(annual?1000:1)})); }
function utilityRows(result:SimulationResult,annual:AnnualSummary|null) { return annual ? [['Electricity',annual.utilities.electricity?.value||0],['Heating',annual.utilities.heating?.value||0],['Cooling',annual.utilities.cooling?.value||0]].map(([name,value])=>({name:String(name),value:Number(value)/1000})) : [{name:'Electricity',value:Math.abs(result.metrics.total_power_kw)},{name:'Heating',value:Math.abs(result.metrics.total_heat_kw)}]; }
function formatMass(value:number) { return `${(value/1000).toLocaleString(undefined,{maximumFractionDigits:1})} t/year`; }
function formatEnergy(value:number) { return `${(value/1000).toLocaleString(undefined,{maximumFractionDigits:1})} MWh/year`; }
function formatHeat(value:number) { return `${value.toLocaleString(undefined,{maximumFractionDigits:1})} GJ/year`; }
function humanize(value:string) { return String(value||'').replace(/[._-]+/g,' ').replace(/\b\w/g,letter=>letter.toUpperCase()); }
const tooltipStyle = {background:'#fffdf9',border:'1px solid #c9c2ba',borderRadius:8,fontSize:10,color:'#0c3338'};
