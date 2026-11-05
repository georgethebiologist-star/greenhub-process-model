import React, { useMemo, useState } from 'react';
import { Activity, AlertTriangle, BarChart3, CheckCircle2, FileDown, GitBranch, Package, Scale, Table2, Zap } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, LineChart, ResponsiveContainer, Sankey, Tooltip, XAxis, YAxis } from 'recharts';
import type { AnnualSummary, PlotCatalogItem, SimulationResult } from '../types';
import type { ResultSourceState } from '../types';
import { EmpiricalEngineeringReport, type EmpiricalComparisonRun } from './EngineeringReport';
import BaselineTimeSeries from './BaselineTimeSeries';

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

export function ResultsWorkbench({ result, graph, runtime, sourceState, savedRuns, onSaveRun, analysis, limitations = [], initialView = 'story' }: {
  result: SimulationResult; graph: GraphLike; runtime: string; artifacts?: Artifact[]; analysis?:any; limitations?:string[]; sourceState?:ResultSourceState; savedRuns?:EmpiricalComparisonRun[]; onSaveRun?:(label:string,result:SimulationResult)=>void; initialView?:ViewId;
}) {
  const annual = (result as SimulationResult & { annual?: AnnualSummary | null }).annual ?? null;
  const feedStream=result.streams.find(stream=>/roadside_grass|whole.?feed|raw.?feed|feedstock/i.test(`${stream.id} ${stream.name}`));
  const juiceStream=result.streams.find(stream=>/raw_liquid_fraction|juice_fraction/i.test(`${stream.id} ${stream.name}`));
  const juiceFlowRatio=feedStream&&feedStream.mass_flow_kgh>0&&juiceStream?juiceStream.mass_flow_kgh/feedStream.mass_flow_kgh:0;
  const nodes = graph?.nodes ?? result.units.map(unit => ({ unit_id:unit.id,display_name:unit.name,process_area:unit.area,active:unit.status==='active',technology:unit.type,key_kpis:{power_kw:unit.power_kw},warning_count:unit.status_reason?1:0 }));
  const edges = graph?.edges ?? [];
  const grouped = useMemo(() => nodes.reduce<Record<string,any[]>>((acc,node) => { (acc[node.process_area || 'unassigned'] ||= []).push(node); return acc; },{}),[nodes]);
  return <div className="results-workbench">
    <StoryView result={result} annual={annual} analysis={analysis} limitations={limitations} nodes={nodes} grouped={grouped} juiceFlowRatio={juiceFlowRatio}/>
  </div>;
}

export function ReportCenter({ result, artifacts = [], runtime, exportContext }: {
  result: SimulationResult; artifacts?: Artifact[]; runtime: string; exportContext?: Record<string, unknown>;
}) {
  const decisionAnalysis = exportContext?.post_route_decision_analysis;
  return <section className="reports-workbench panel">
    <div className="panel-title result-heading"><span className="title-icon"><FileDown size={17}/></span><div><h3>Run exports</h3><p>{runtime} · completed {new Date(result.timestamp).toLocaleString()}</p></div><span className={`status ${result.validation.status}`}>{result.validation.status === 'pass' ? 'checks passed' : `${result.validation.status} — review`}</span></div>
    <div className="export-actions"><button className="secondary" onClick={()=>downloadFile(JSON.stringify({exported_at:new Date().toISOString(),runtime,configuration:exportContext??null,result},null,2),'application/json',`greenhub-${safeFilePart(result.run_id)}-run.json`)}><FileDown size={14}/>Download reproducibility bundle (JSON)</button><button className="secondary" onClick={()=>downloadFile(summaryCsv(result,decisionAnalysis),'text/csv;charset=utf-8',`greenhub-${safeFilePart(result.run_id)}-summary.csv`)}><FileDown size={14}/>Download KPI summary (CSV)</button></div>
    <ReportsView artifacts={artifacts} result={result}/>
  </section>;
}

function downloadFile(content:string,type:string,filename:string) { const url=URL.createObjectURL(new Blob([content],{type}));const link=document.createElement('a');link.href=url;link.download=filename;document.body.appendChild(link);link.click();link.remove();window.setTimeout(()=>URL.revokeObjectURL(url),1000); }
function safeFilePart(value:string) { return String(value||'run').replace(/[^a-zA-Z0-9_-]/g,'_'); }
function summaryCsv(result:SimulationResult, decisionAnalysis?:unknown) {
  const annual=result.annual;
  const rows:[string,string,string][]=[['Metric','Value','Unit'],['Run ID',result.run_id,''],['Timestamp',result.timestamp,''],['Validation',result.validation.status,'']];
  if(annual){
    rows.push(['Feed processed',String(annual.feed_processed.value),'kg/year']);
    rows.push([result.scenarios.protein_recovery==='PR7'?'Biostimulant wet retentate':'Dry protein product',String(annual.products[result.scenarios.protein_recovery==='PR7'?'biostimulant_product':'dry_protein_product']?.value??''),'kg/year']);
    rows.push(['Biomethane product volume',String(annual.volumetric_products?.biomethane?.value??''),'m³/year at modelled stream conditions']);
    rows.push(['Biomethane mass',String(annual.products.biomethane?.value??''),'kg/year']);
    rows.push(['Electricity',String(annual.utilities.electricity?.value??''),'kWh/year']);
    rows.push(['Overall mass closure',String(annual.balance.overall_closure_pct),'%']);
  } else {
    rows.push(['Feed mass in',String(result.balances.mass_in_kgh),'kg/h']);
    rows.push(['Protein recovered',String(result.metrics.protein_recovered_kgh),'kg/h']);
    rows.push(['Biomethane flow',String(result.metrics.biomethane_flow_m3h),'m3/h']);
    rows.push(['Overall mass closure',String(result.balances.mass_closure_pct),'%']);
  }
  if(decisionAnalysis&&typeof decisionAnalysis==='object') {
    const analysis=decisionAnalysis as {tea?:{totals?:Record<string,unknown>;financial_kpis?:Record<string,unknown>;candidate_economics?:Record<string,unknown>};lca?:{totals?:Record<string,unknown>};carbon_assessment?:Record<string,unknown>};
    const tea=analysis.tea?.totals||{}, finance=analysis.tea?.financial_kpis||{}, candidate=analysis.tea?.candidate_economics||{}, lca=analysis.lca?.totals||{};
    const add=(label:string,value:unknown,unit:string)=>{if(value!==null&&value!==undefined&&Number.isFinite(Number(value)))rows.push([label,String(value),unit]);};
    add('Sales revenue',tea.annual_revenue_eur,'EUR/year');
    add('OPEX',tea.annual_opex_eur,'EUR/year');
    add('Operating profit before support',tea.partial_operating_margin_eur_per_year??tea.net_operating_margin_eur_per_year,'EUR/year');
    add('Profit during operating support',tea.operating_profit_during_support_eur_per_year,'EUR/year');
    add('CAPEX basis',tea.high_direct_capex_eur??tea.partial_direct_capex_eur,'EUR');
    add('CAPEX grant fraction',candidate.capex_grant_fraction_applied,'fraction');
    add('CAPEX grant',candidate.subsidy_eur??tea.subsidy_eur,'EUR upfront');
    add('Annual operating support',candidate.opex_premium_eur_per_year??tea.opex_premium_eur_per_year,'EUR/year');
    add('Total public support present value',candidate.total_public_support_pv_eur??tea.total_public_support_pv_eur,'EUR');
    add('NPV',finance.npv_eur??tea.proxy_npv_eur,'EUR');
    const irr=finance.irr??tea.proxy_irr;
    add('IRR',irr===null||irr===undefined?null:Number(irr)*100,'%');
    add('Simple payback',finance.simple_payback_years??tea.proxy_simple_payback_years,'years');
    add('Operational climate load',lca.climate_kg_co2e_per_year??lca.partial_climate_kg_co2e_per_year,'kg CO2e/year');
    add('Net carbon',analysis.carbon_assessment?.net_carbon_t_c_per_year,'t C/year');
  }
  return rows.map(row=>row.map(value=>`"${value.replace(/"/g,'""')}"`).join(',')).join('\r\n');
}

function StoryView({result,annual,analysis,limitations,nodes,grouped,juiceFlowRatio}:{result:SimulationResult;annual:AnnualSummary|null;analysis:any;limitations:string[];nodes:any[];grouped:Record<string,any[]>;juiceFlowRatio:number}) {
  const [selectedStage,setSelectedStage]=useState<any|null>(null);
  const products = productRows(result,annual);
  const utilities = utilityRows(result,annual);
  const pr7Metrics=result.process_areas.protein_recovery.metrics||{};
  const tea=analysis?.tea?.totals||{}, finance=analysis?.tea?.financial_kpis||{}, candidate=analysis?.tea?.candidate_economics||{};
  const lca=analysis?.lca?.totals||{}, carbon=analysis?.carbon_assessment||{};
  const cashFlow=(analysis?.tea?.cash_flow||[]) as Array<{year:number;cash_flow_eur:number}>;
  const life=Math.min(20,Math.max(0,...cashFlow.map(row=>Number(row.year)||0)));
  const annualSales=Number(tea.annual_revenue_eur)||0;
  const annualSupport=Number(candidate.opex_premium_eur_per_year)||Number(tea.opex_premium_eur_per_year)||0;
  const supportYears=Number(candidate.opex_support_years)||Number(tea.opex_support_years)||0;
  const capitalGrant=Number(candidate.subsidy_eur)||Number(tea.subsidy_eur)||0;
  const cashFlowByYear=new Map(cashFlow.map(row=>[Number(row.year),Number(row.cash_flow_eur)]));
  let cumulativeCashFlow=0;
  const financeSeries=Array.from({length:life+1},(_,year)=>{
    const yearlyCashFlow=cashFlowByYear.get(year);
    if(yearlyCashFlow!==undefined&&Number.isFinite(yearlyCashFlow))cumulativeCashFlow+=yearlyCashFlow;
    return {year:year===0?'Year 0':`Year ${year}`,cumulativeCashFlow:yearlyCashFlow===undefined?null:cumulativeCashFlow,sales:year?annualSales:0,subsidies:year===0?capitalGrant:(year<=supportYears?annualSupport:0)};
  });
  const emissions=Number(carbon.operational_climate_load_t_co2e_per_year ?? (Number(lca.climate_kg_co2e_per_year||lca.partial_climate_kg_co2e_per_year)/1000));
  const stored=Number(carbon.total_carbon_stored_t_c_per_year);
  const netCarbon=carbon.net_carbon_t_c_per_year;
  return <div className="story-stack">
    <section className="panel result-section"><div className="story-title"><GitBranch/><div><h4>Process pathway</h4><p>Select a stage to inspect unit operations, flows, conversions and energy demand.</p></div></div><PathwayView result={result} annual={annual} nodes={nodes} grouped={grouped} selected={selectedStage} onSelect={setSelectedStage} startAtPretreatment/></section>
    <section className="panel result-section"><div className="story-title"><Activity/><div><h4>Process KPIs</h4><p>Annual feed throughput and recovered products.</p></div></div><section className="decision-kpis annual-kpis"><Outcome label="Feed processed" value={annual ? formatMass(annual.feed_processed.value) : `${result.balances.mass_in_kgh.toFixed(1)} kg/h`} tone="green"/>{products.map((product,index)=><Outcome key={product.name} label={product.name} value={`${product.value.toLocaleString(undefined,{maximumFractionDigits:1})} ${product.unit}`} tone={index%2?'blue':'green'}/>)}</section></section>
    <section className="panel result-section"><div className="story-title"><GitBranch/><div><h4>Grass fractionation</h4></div></div><MassFlowSankey result={result} annual={annual}/></section>
    <section className="panel result-section"><div className="story-title"><Package/><div><h4>Recovered products</h4><p>Bar lengths use reported amounts; hover to see each product’s unit.</p></div></div><SimpleBar data={products} unit={annual?'t/year':'kg/h'} mixedUnits={Boolean(annual)}/></section>
    {annual&&<section className="panel result-section"><div className="story-title"><BarChart3/><div><h4>Annual planning</h4><p>Seasonal feed, residual streams, products and utilities.</p></div></div><BaselineTimeSeries annual={annual} nutrientRecovery={result.scenarios.nutrient_recovery} juiceFlowRatio={juiceFlowRatio} embedded/></section>}
    <section className="panel result-section"><div className="story-title"><Zap/><div><h4>Utility demand</h4><p>Period energy is separated from instantaneous power.</p></div></div>{annual?<div className="utility-summary"><div><span>Electricity</span><strong>{formatEnergy(annual.utilities.electricity?.value||0)}</strong></div><div><span>Heating</span><strong>{formatHeat(annual.display_utilities?.heating?.value||0)}</strong></div><div><span>Cooling</span><strong>{formatHeat(annual.display_utilities?.cooling?.value||0)}</strong></div></div>:<SimpleBar data={utilities} unit="kW instantaneous"/>}</section>
    <section className="panel result-section"><div className="story-title"><BarChart3/><div><h4>Financial performance</h4><p>Screening TEA values returned for this run.</p></div></div>{analysis?.tea?<><div className="decision-kpis annual-kpis"><Outcome label="CAPEX" value={money(Number(tea.high_direct_capex_eur??tea.partial_direct_capex_eur))} tone="yellow"/><Outcome label="OPEX" value={money(Number(tea.annual_opex_eur))+'/year'} tone="yellow"/><Outcome label="Revenue" value={money(annualSales)+'/year'} tone="green"/><Outcome label="Profit" value={money(Number(tea.operating_profit_during_support_eur_per_year??tea.partial_operating_margin_eur_per_year))+'/year'} tone="rose"/><Outcome label="NPV" value={money(Number(finance.npv_eur??tea.proxy_npv_eur))} tone="blue"/><Outcome label="IRR" value={finance.irr==null?'Not defined':`${(Number(finance.irr)*100).toFixed(1)}%`} tone="blue"/><Outcome label="CAPEX grant" value={money(capitalGrant)} tone="yellow"/><Outcome label="Operating support" value={money(annualSupport)+'/year'} tone="yellow"/></div>{financeSeries.length>1&&<div className="finance-projection"><h5>20-year cash flow and revenue</h5><ResponsiveContainer width="100%" height={280}><ComposedChart data={financeSeries} margin={{top:10,right:18,bottom:8,left:8}}><CartesianGrid stroke="#d4cec7" vertical={false}/><XAxis dataKey="year" tick={{fontSize:9}} interval={1}/><YAxis tick={{fontSize:9}} tickFormatter={compactMoney}/><Tooltip contentStyle={tooltipStyle} formatter={(value:number,name:string)=>[money(value),name]}/><Legend/><Bar dataKey="sales" name="Product sales" stackId="revenue" fill={chartColors[0]}/><Bar dataKey="subsidies" name="Subsidies" stackId="revenue" fill={chartColors[2]}/><Line dataKey="cumulativeCashFlow" name="Cumulative cash flow" stroke={chartColors[3]} strokeWidth={2.4} dot={false} connectNulls={false}/></ComposedChart></ResponsiveContainer></div>}</>:<Empty title="Financial results unavailable" text="Run the post-route TEA analysis to populate costs, revenue, cash flow, NPV and IRR."/>}</section>
    <section className="panel result-section"><div className="story-title"><Activity/><div><h4>Environmental performance</h4><p>Attributional operational burdens and carbon storage.</p></div></div>{analysis?.carbon_assessment||analysis?.lca?<><div className="decision-kpis annual-kpis"><Outcome label="Carbon emitted" value={Number.isFinite(emissions)?`${emissions.toLocaleString(undefined,{maximumFractionDigits:1})} t CO₂-eq/year`:'Not reported'} tone="rose"/><Outcome label="Carbon stored" value={Number.isFinite(stored)?`${stored.toLocaleString(undefined,{maximumFractionDigits:1})} t C/year`:'Not reported'} tone="green"/><Outcome label="Net carbon" value={netCarbon==null?'Not reported':`${Number(netCarbon).toLocaleString(undefined,{maximumFractionDigits:1})} t C/year`} tone="blue"/></div><EnvironmentalCharts carbon={carbon}/></>:<Empty title="Environmental results unavailable" text="Run the LCA assessment to populate operational emissions and carbon storage."/>}</section>
    <details className="result-disclosure"><summary>Process streams <span>{result.streams.length}</span></summary><DataTable headers={['Stream','From → to','Mass','Dry solids','COD','N','P']} rows={result.streams.map(stream=>[humanize(stream.name||stream.id),`${humanize(stream.origin)} → ${humanize(stream.destination)}`,`${stream.mass_flow_kgh.toFixed(1)} kg/h`,stream.dry_solids_pct?`${stream.dry_solids_pct.toFixed(1)}%`:'—',stream.cod_kgh?stream.cod_kgh.toFixed(1):'—',stream.nitrogen_kgh?stream.nitrogen_kgh.toFixed(2):'—',stream.phosphorus_kgh?stream.phosphorus_kgh.toFixed(2):'—'])}/></details>
    <details className="result-disclosure"><summary>Unit operations <span>{result.units.length}</span></summary><DataTable headers={['Unit','Area','Status','Power','Heat duty']} rows={result.units.map(unit=>[unit.name,areaLabels[unit.area]||humanize(unit.area),humanize(unit.status),`${unit.power_kw.toFixed(1)} kW`,`${unit.duty_kw.toFixed(1)} kW`])}/></details>
    <details className="result-disclosure"><summary>Additional charts <span>{result.plots.length}</span></summary><AnalyticsView plots={result.plots}/>{result.scenarios.protein_recovery==='PR7'&&<><div className="method-note"><Activity size={15}/><div><strong>Membrane flux · {String(pr7Metrics.biostimulant_flux_method||'not reported').replaceAll('_',' ')}</strong><span>{Number(pr7Metrics.biostimulant_membrane_flux_L_m2_h||0).toLocaleString(undefined,{maximumFractionDigits:2})} L/(m²·h) · {Number(pr7Metrics.biostimulant_membrane_area_m2||0).toLocaleString(undefined,{maximumFractionDigits:1})} m² area · VCF target {Number(pr7Metrics.biostimulant_target_concentration_factor||0).toLocaleString(undefined,{maximumFractionDigits:2})} · simulated {pr7Metrics.biostimulant_actual_volume_concentration_factor==null?'n/a':Number(pr7Metrics.biostimulant_actual_volume_concentration_factor).toLocaleString(undefined,{maximumFractionDigits:2})}{pr7Metrics.biostimulant_feed_to_reference_concentration_ratio!==null&&pr7Metrics.biostimulant_feed_to_reference_concentration_ratio!==undefined?` · Cf/C0 ${Number(pr7Metrics.biostimulant_feed_to_reference_concentration_ratio).toPrecision(3)}`:''}</span><small>{String(pr7Metrics.biostimulant_flux_evidence||'')}</small></div></div>{pr7Metrics.biostimulant_hormone_feed_basis==='user_supplied_clarified_juice_benchmark_screening'&&<div className="method-note"><Activity size={15}/><div><strong>Hormone feed · benchmark screening input</strong><span>{Number(pr7Metrics.biostimulant_hormone_benchmark_feed_kg_hr||0).toPrecision(3)} kg/h analyte-equivalent supplement · {String(pr7Metrics.biostimulant_hormone_benchmark_source||'source not reported')}</span><small>Separate trace feed, based on supplied clarified-juice benchmark concentrations; not a GreenHub measurement.</small></div></div>}<PR7HormoneCapture result={result} annual={annual}/></>}</details>
    <details className="result-disclosure"><summary>Quality control</summary><div className="quality-control-content"><div className={`balance-banner ${result.validation.status}`}><Scale/><div><span>Mass closure</span><strong>{(annual?.balance.overall_closure_pct??result.balances.mass_closure_pct).toFixed(4)}%</strong><p>{result.validation.status==='pass'?'Model balance checks passed.':'Review the returned balance and validation notes.'}</p></div></div><DataTable headers={['Balance','In','Out','Closure']} rows={[["Total mass",`${result.balances.mass_in_kgh.toFixed(2)} kg/h`,`${result.balances.mass_out_kgh.toFixed(2)} kg/h`,`${result.balances.mass_closure_pct.toFixed(3)}%`],...Object.entries(result.balances.elemental).map(([name,value])=>[humanize(name),`${value.in.toFixed(3)} kg/h`,`${value.out.toFixed(3)} kg/h`,`${value.closure.toFixed(3)}%`])]}/>{result.validation.issues.length>0&&<section className="issue-list">{result.validation.issues.map((issue,index)=><div key={index}><AlertTriangle size={14}/><span>{issue.message}</span></div>)}</section>}<ul>{[...limitations,...(analysis?.warnings||[]),...(analysis?.limitations||[]),...(annual?.warnings||[])].filter(Boolean).map((item,index)=><li key={index}>{item}</li>)}</ul></div></details>
    
  </div>;
}

function PR7HormoneCapture({result,annual}:{result:SimulationResult;annual:AnnualSummary|null}) {
  const feed=result.streams.find(stream=>stream.id==='clarified_protein_rich_liquid');
  const product=result.streams.find(stream=>stream.id==='biostimulant_product');
  const permeate=result.streams.find(stream=>stream.id==='biostimulant_permeate');
  const pr7Assumptions=result.units.find(unit=>unit.id==='PR7_M101')?.warnings?.filter(warning=>warning.includes('solid-phase'))||[];
  const groups=[
    ['IAA',['Indole3AceticAcid','ProteinBoundIAA']],
    ['Zeatin',['Zeatin','PeptideBoundZeatin']],
    ['Zeatin riboside',['ZeatinRiboside','BoundZeatinRiboside']],
  ] as const;
  const hasPools=Boolean(feed?.components_kg_hr&&groups.some(([,ids])=>ids.some(id=>id in (feed.components_kg_hr||{}))));
  if(!hasPools)return <section className="panel">{pr7Assumptions.length>0&&<div className="method-note"><Activity size={15}/><div><strong>Solid-pool screening assumption</strong><span>Unclassified model solids are assigned complete membrane retention. Validate particulate capture and fouling using the clarified-juice feed.</span></div></div>}<Empty title="No non-zero hormone pools in this run" text="The sparse stream export contains no non-zero IAA, zeatin or zeatin-riboside feed mass. This is a model-input result, not a measurement of real grass juice."/></section>;
  const multiplier=annual?annual.period.operating_hours*1e6:1e6;
  const unit=annual?'mg/year':'mg/h';
  const rows=groups.map(([label,ids])=>{
    const input=ids.reduce((sum,id)=>sum+(feed?.components_kg_hr?.[id]||0),0);
    const captured=ids.reduce((sum,id)=>sum+(product?.components_kg_hr?.[id]||0),0);
    const passed=ids.reduce((sum,id)=>sum+(permeate?.components_kg_hr?.[id]||0),0);
    return {label,feed:input*multiplier,retentate:captured*multiplier,permeate:passed*multiplier,capture:input>0?captured/input:null,balanceError:input-captured-passed};
  });
  const anyDeclared=rows.some(row=>row.feed>0);
  return <section className="panel"><div className="story-title"><Package/><div><h4>Hormone recovery</h4><p>Modelled analyte payload entering the membrane and leaving in retentate or permeate.</p></div></div>{pr7Assumptions.length>0&&<div className="method-note"><Activity size={15}/><div><strong>Solid-pool screening assumption</strong><span>Unclassified model solids are assigned complete membrane retention. Validate particulate capture and fouling using the clarified-juice feed.</span></div></div>}
    {anyDeclared?<><div className="ds-chart"><ResponsiveContainer width="100%" height={260}><BarChart data={rows} margin={{top:12,right:16,bottom:4,left:8}}><CartesianGrid stroke="#d4cec7" vertical={false}/><XAxis dataKey="label" stroke="#587174" fontSize={10}/><YAxis stroke="#587174" fontSize={9} unit={` ${unit}`}/><Tooltip contentStyle={tooltipStyle} formatter={(value:number,name:string)=>[`${Number(value).toLocaleString(undefined,{maximumFractionDigits:2})} ${unit}`,name]}/><Legend/><Bar dataKey="feed" name="Feed" fill={chartColors[1]} radius={[3,3,0,0]}/><Bar dataKey="retentate" name="Retentate" fill={chartColors[0]} radius={[3,3,0,0]}/><Bar dataKey="permeate" name="Permeate" fill={chartColors[2]} radius={[3,3,0,0]}/></BarChart></ResponsiveContainer></div><div className="process-readout">{rows.map(row=><div key={row.label}><span>{row.label} capture</span><strong>{row.capture==null?'Not defined':`${(row.capture*100).toFixed(1)}%`}</strong><small>{row.capture==null?'No analyte declared in feed':`Retentate / feed · balance error ${row.balanceError.toExponential(2)} kg/h`}</small></div>)}</div></>:<p className="method-note"><strong>No hormone analyte mass was declared in this run’s feed composition.</strong> Screening benchmarks are not inserted into the plant mass balance; this result is not a measurement of hormone absence in grass juice.</p>}
  </section>;
}

function AnnualView({result,annual}:{result:SimulationResult;annual:AnnualSummary|null}) {
  if (!annual) return <Empty title="Annual results are not available" text="Run the Python model to calculate a full-year operating plan."/>;
  const charts = annual.chart_data;
  const schedule = annual.biomass_schedule;
  const nutrient = (annual.named_products?.struvite_product?.value||annual.products.phosphorus_product?.value||0)+(annual.products.ammonium_product?.value||0)+(annual.products.potassium_concentrate?.value||0);
  return <div className="annual-stack">
    <section className="decision-kpis annual-kpis"><Outcome label="Annual feed" value={formatMass(annual.feed_processed.value)} tone="green"/><Outcome label={result.scenarios.protein_recovery==='PR7'?'Biostimulant retentate':'Protein'} value={formatMass(annual.products[result.scenarios.protein_recovery==='PR7'?'biostimulant_product':'dry_protein_product']?.value||0)} tone="green"/><Outcome label="Biomethane" value={`${(annual.volumetric_products?.biomethane?.value||0).toLocaleString(undefined,{maximumFractionDigits:1})} m³/year`} tone="blue"/><Outcome label="Nutrient products" value={formatMass(nutrient)} tone="yellow"/><Outcome label="Electricity" value={formatEnergy(annual.utilities.electricity?.value||0)} tone="rose"/></section>
    <section className="annual-basis"><div><span>Calculation basis</span><strong>{annual.method_label}</strong><p>{annual.basis}</p></div><dl><div><dt>Operating hours</dt><dd>{annual.period.operating_hours.toLocaleString(undefined,{maximumFractionDigits:0})} h/year</dd></div><div><dt>Schedule</dt><dd>{annual.period.schedule_source}</dd></div><div><dt>Balance result</dt><dd>{annual.balance.passed?'Passed':'Review required'}</dd></div></dl></section>
    {charts?.schedule?.length ? <>
      <section className="schedule-facts"><div><span>Available</span><strong>{schedule.annual_available_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Processed</span><strong>{schedule.annual_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Unused</span><strong>{schedule.annual_unused_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Utilization</span><strong>{(schedule.utilization_fraction*100).toFixed(1)}%</strong></div><div><span>Peak month</span><strong>{schedule.peak_month_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t</strong></div></section>
      <TrendChart title="Biomass schedule" note="Availability remains fixed; processed biomass follows the refinery cap." unit="tonnes/month" data={charts.schedule} series={[['available_biomass_tonnes','Available'],['processed_biomass_tonnes','Processed'],['unused_biomass_tonnes','Unused']]}/>
      <div className="annual-chart-grid">
        <TrendChart title="Feed and bulk streams" note="Large streams use their own mass scale." unit="tonnes/month" data={charts.bulk_streams} series={[['feed_processed_tonnes','Feed'],['press_cake_tonnes','Press cake'],['digestate_tonnes','Digestate']]}/>
        <TrendChart title="Protein and fertilizer products" note="Small products are separated from feed so they remain visible." unit="tonnes/month" data={charts.small_products} series={[['protein_tonnes','Protein'],['phosphorus_product_tonnes','Struvite'],['ammonium_product_tonnes','Ammonium sulfate'],['potassium_concentrate_tonnes','K concentrate']]}/>
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

function PathwayView({result,annual,nodes,grouped,selected,onSelect,startAtPretreatment=false}:{result:SimulationResult;annual:AnnualSummary|null;nodes:any[];grouped:Record<string,any[]>;selected:any;onSelect:(value:any)=>void;startAtPretreatment?:boolean}) {
  const fallbackStages = [
    ['feed','Feed',['feedstock_and_characterization','front_end']],['pretreatment','Pre-treatment / press',['feed_preparation_and_primary_separation']],
    ['protein','Protein recovery',['protein_recovery']],['ad','Anaerobic digestion',['anaerobic_digestion']],
    ['gas','Gas upgrading / CHP',['biogas_conditioning_and_upgrading','biogas_upgrading']],['nutrients','Nutrient recovery / products',['digestate_treatment_and_nutrient_recovery','nutrient_recovery']],
  ].map(([stage_id,label,areas]:any[])=>{const stageNodes=(areas as string[]).flatMap(area=>grouped[area]||[]);return{stage_id,label,active_unit_names:stageNodes.filter(node=>node.active!==false).map(node=>node.display_name),unit_count:stageNodes.length,products_kg_hr:{},power_kw:stageNodes.reduce((sum,node)=>sum+Math.max(Number(node.key_kpis?.power_kw||0),0),0)||null,heat_duty_kw:null,limitations:stageNodes.filter(node=>node.warning_count).map(node=>`${node.display_name}: review model notes`),data_quality:'empirical structural model'};});
  const allStages = annual?.process_pathway?.length ? annual.process_pathway : fallbackStages;
  const stages = startAtPretreatment ? allStages.filter(stage=>!['feed','feedstock','characterization','feed_characterization'].includes(stage.stage_id)) : allStages;
  const active = selected || stages[0];
  const productEntries=Object.entries(active.products_kg_hr||{}).filter(([,value])=>Number(value)>0);
  const stageUnits=result.units.filter(unit=>active.active_unit_names.includes(unit.name));
  return <div className="pathway-infographic"><div className="pathway-strip" role="list" aria-label="Empirical process pathway">{stages.map((stage,index)=><React.Fragment key={stage.stage_id}><button role="listitem" className={`pathway-stage ${active.stage_id===stage.stage_id?'selected':''}`} aria-expanded={active.stage_id===stage.stage_id} onClick={() => onSelect(stage)}><span>{String(index+1).padStart(2,'0')}</span><strong>{stage.label}</strong><small>{stage.unit_count} active/modelled units</small>{productEntries.length>0&&active.stage_id===stage.stage_id?<em>{productEntries.length} product outputs</em>:null}</button>{index<stages.length-1&&<b aria-hidden="true">→</b>}</React.Fragment>)}</div><section className="pathway-detail" aria-live="polite"><div><span className="eyebrow">Selected stage</span><h4>{active.label}</h4><p>{active.active_unit_names.length?active.active_unit_names.join(' · '):'No active units in this stage.'}</p></div><dl><div><dt>Products</dt><dd>{productEntries.length?productEntries.map(([name,value])=>`${humanize(name)} ${Number(value).toFixed(2)} kg/h`).join(' · '):'No product stream reported'}</dd></div><div><dt>Stage energy</dt><dd>{active.power_kw?`${active.power_kw.toFixed(1)} kW electricity`: 'Electricity not reported'}{active.heat_duty_kw?` · ${active.heat_duty_kw.toFixed(1)} kW heat duty`:''}</dd></div></dl>{stageUnits.length>0&&<div className="stage-unit-list"><h5>Unit operations</h5>{stageUnits.map(unit=>{const flows=result.streams.filter(stream=>[unit.id,unit.name].some(key=>stream.origin.toLowerCase().includes(key.toLowerCase())||stream.destination.toLowerCase().includes(key.toLowerCase())));const incoming=flows.filter(stream=>[unit.id,unit.name].some(key=>stream.destination.toLowerCase().includes(key.toLowerCase()))).reduce((sum,stream)=>sum+stream.mass_flow_kgh,0);const outgoing=flows.filter(stream=>[unit.id,unit.name].some(key=>stream.origin.toLowerCase().includes(key.toLowerCase()))).reduce((sum,stream)=>sum+stream.mass_flow_kgh,0);return <div className="stage-unit-row" key={unit.id}><strong>{unit.name}</strong><span>{unit.status}</span><small>{incoming?`In ${incoming.toFixed(1)} kg/h`:''}{incoming&&outgoing?' · ':''}{outgoing?`Out ${outgoing.toFixed(1)} kg/h`:''}{!incoming&&!outgoing?'Flow not exposed':''}</small><small>{unit.power_kw.toFixed(1)} kW power · {unit.duty_kw.toFixed(1)} kW duty</small></div>})}</div>}<p className="pathway-note">Stage cards show model-reported totals. Per-unit material flows are displayed when stream endpoints identify the unit.</p></section></div>;
}

function MassFlowSankey({result,annual}:{result:SimulationResult;annual:AnnualSummary|null}) {
  const streams=result.streams;
  const streamMass=(pattern:RegExp)=>Number(streams.find(stream=>pattern.test(`${stream.id} ${stream.name} ${stream.origin} ${stream.destination}`))?.mass_flow_kgh)||0;
  const annualMass=(key:string)=>Number(annual?.products?.[key]?.value)||0;
  const integratedBulk=(key:string)=>((annual?.chart_data?.bulk_streams||[]) as Array<Record<string,any>>).reduce((sum,row)=>sum+Number(row[key]||0),0)*1000;
  const feed=Number(annual?.feed_processed?.value)||Number(result.balances.mass_in_kgh)||0;
  const cake=integratedBulk('press_cake_tonnes')||streamMass(/pressed_fibre_cake|fibre_cake/i)*(annual?.period?.operating_hours||1);
  const basis=feed>0?feed:1000;
  const toFU=(kg:number)=>Math.max(0,kg/basis);
  const fiberFraction=toFU(cake), juiceFraction=Math.max(0,1-fiberFraction);
  const outputs=[
    ['Protein',annualMass('dry_protein_product')||streamMass(/dry_protein_product/i)*(annual?.period?.operating_hours||1)],
    ['Biomethane',annualMass('biomethane')||streamMass(/water_scrubber_biomethane|biomethane_product/i)*(annual?.period?.operating_hours||1)],
    ['Ammonium',annualMass('ammonium_product')||streamMass(/ammonium_salt_product/i)*(annual?.period?.operating_hours||1)],
    ['Struvite',annualMass('phosphorus_product')||streamMass(/struvite_product/i)*(annual?.period?.operating_hours||1)],
    ['Potassium',annualMass('potassium_concentrate')||streamMass(/potassium_concentrate/i)*(annual?.period?.operating_hours||1)],
    ['Nutrient solids',annualMass('nutrient_rich_solids')||streamMass(/nutrient_rich_digestate_solids/i)*(annual?.period?.operating_hours||1)],
  ].map(([name,mass])=>({name:String(name),value:toFU(Number(mass))})).filter(item=>item.value>1e-8);
  const recovered=outputs.reduce((sum,item)=>sum+item.value,0);
  const residual=Math.max(0,juiceFraction-recovered);
  const liquidDischarge=residual;
  const nodes=[{name:'Grass'}, {name:'Fiber'}, {name:'Juice'}, ...outputs.map(item=>({name:item.name})), ...(liquidDischarge>1e-8?[{name:'Liquid discharge'}]:[])];
  const ix=(name:string)=>nodes.findIndex(node=>node.name===name);
  const links=[
    {source:ix('Grass'),target:ix('Fiber'),value:fiberFraction,name:'Press cake'},
    {source:ix('Grass'),target:ix('Juice'),value:juiceFraction,name:'Juice'},
    ...outputs.map(item=>({source:ix('Juice'),target:ix(item.name),value:item.value,name:item.name})),
    ...(residual>1e-8?[{source:ix('Juice'),target:ix('Liquid discharge'),value:residual,name:'Residual liquid'}]:[]),
  ].filter(link=>link.source>=0&&link.target>=0&&link.value>0);
  const data={nodes,links};
  return links.length?<div className="mass-sankey"><ResponsiveContainer width="100%" height={350}><Sankey data={data} node={<PercentSankeyNode/>} nodePadding={27} nodeWidth={12} linkCurvature={0.5} iterations={32} margin={{top:8,right:150,bottom:8,left:76}}><Tooltip contentStyle={tooltipStyle} formatter={(value:number,name:string)=>[`${(Number(value)*100).toLocaleString(undefined,{maximumFractionDigits:2})}% of grass feed`,name]}/></Sankey></ResponsiveContainer></div>:<Empty title="Mass flow data unavailable" text="No positive feed and product mass flows were returned for this simulation."/>;
}

function PercentSankeyNode(props:any) {
  const {x,y,width,height,payload,value}=props;
  if(!Number.isFinite(x)||!Number.isFinite(y)||!Number.isFinite(height))return null;
  const left=x<90, labelX=left?x-7:x+width+7, anchor=left?'end':'start';
  const labelOffset=payload?.name==='Juice'?8:0;
  const labelY=y+height/2+labelOffset;
  const percent=Number(value)*100;
  const percentLabel=Math.abs(percent-100)<1e-6?'100%':`${percent.toFixed(2)}%`;
  return <g><rect x={x} y={y} width={width} height={Math.max(height,1)} fill={left?'#408f4d':payload?.name==='Fiber'?'#d1a520':payload?.name==='Juice'?'#729ad2':'#b77436'} stroke="none"/><text x={labelX} y={labelY-2} textAnchor={anchor} fill="#0c3338" fontSize={11} paintOrder="stroke" stroke="#fffdf9" strokeWidth={3}>{payload?.name||''}</text>{Number.isFinite(Number(value))&&<text x={labelX} y={labelY+12} textAnchor={anchor} fill="#587174" fontSize={10} paintOrder="stroke" stroke="#fffdf9" strokeWidth={3}>{percentLabel}</text>}</g>;
}

function EnvironmentalCharts({carbon}:{carbon:any}) {
  const grossCarbon=Number(carbon.operational_climate_load_t_co2e_per_year)*(12/44);
  const carbonRows=[['Gross emissions',grossCarbon],['Stored carbon',Number(carbon.total_carbon_stored_t_c_per_year)],['Net carbon',Number(carbon.net_carbon_t_c_per_year)]]
    .filter(([,value])=>Number.isFinite(value)).map(([name,value])=>({name:String(name),value:Number(value)}));
  return <div className="environment-chart-grid">{carbonRows.length>0&&<article className="baseline-series-plot"><h3>Carbon balance <span>t C/year</span></h3><ResponsiveContainer width="100%" height={245}><BarChart data={carbonRows} layout="vertical" margin={{top:8,right:24,bottom:8,left:14}}><CartesianGrid stroke="#ded8d0" horizontal={false}/><XAxis type="number" tick={{fontSize:10}}/><YAxis type="category" dataKey="name" width={120} tick={{fontSize:10}}/><Tooltip contentStyle={tooltipStyle} formatter={(value:number)=>[`${Number(value).toLocaleString(undefined,{maximumFractionDigits:2})} t C/year`,'Carbon']}/><Bar dataKey="value" name="Carbon" radius={[0,4,4,0]}>{carbonRows.map((item,index)=><Cell key={item.name} fill={item.name==='Stored carbon'?chartColors[0]:item.name==='Net carbon'?chartColors[3]:chartColors[2]}/>)}</Bar></BarChart></ResponsiveContainer></article>}</div>;
}

function TrendChart({title,note,unit,data,series}:{title:string;note:string;unit:string;data:Array<Record<string,number|string>>;series:Array<[string,string]>}) { return <section className="trend-card"><div className="story-title"><BarChart3/><div><h4>{title}</h4><p>{note}</p></div></div><span className="chart-unit">{unit}</span><ResponsiveContainer width="100%" height={260}><LineChart data={data}><CartesianGrid stroke="#d4cec7" vertical={false}/><XAxis dataKey={data[0]?.period!==undefined?'period':'time_label'} stroke="#587174" fontSize={10}/><YAxis stroke="#587174" fontSize={9}/><Tooltip contentStyle={tooltipStyle}/><Legend/>{series.map(([key,label],index)=><Line key={key} type="monotone" dataKey={key} name={label} stroke={chartColors[index%chartColors.length]} strokeWidth={2.3} dot={false} connectNulls={false}/>)}</LineChart></ResponsiveContainer></section>; }

function Outcome({label,value,tone}:{label:string;value:string;tone:string}) { return <div className="outcome"><span>{label}</span><strong className={tone}>{value}</strong></div>; }
function SimpleBar({data,unit,mixedUnits=false}:{data:Array<{name:string;value:number;unit?:string}>;unit:string;mixedUnits?:boolean}) { return <ResponsiveContainer width="100%" height={240}><BarChart data={data} layout="vertical" margin={{left:12,right:22}}><CartesianGrid stroke="#d4cec7" horizontal={false}/><XAxis type="number" stroke="#587174" fontSize={9} unit={mixedUnits?'':` ${unit}`}/><YAxis type="category" dataKey="name" width={115} stroke="#587174" fontSize={9}/><Tooltip content={mixedUnits?<ProductTooltip/>:undefined} contentStyle={tooltipStyle}/><Bar dataKey="value" radius={[0,4,4,0]}>{data.map((item,index)=><Cell key={item.name} fill={chartColors[index%chartColors.length]}/>)}</Bar></BarChart></ResponsiveContainer>; }
function ProductTooltip({active,payload}:{active?:boolean;payload?:Array<{payload:{name:string;value:number;unit?:string}}>} ) { const item=payload?.[0]?.payload; if(!active||!item)return null; return <div style={tooltipStyle}><strong>{item.name}</strong><div>{item.value.toLocaleString(undefined,{maximumFractionDigits:1})} {item.unit||'t/year'}</div></div>; }
function DataTable({headers,rows}:{headers:string[];rows:string[][]}) { return <div className="data-table-wrap"><table className="data-table"><thead><tr>{headers.map(header=><th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={index}>{row.map((cell,column)=><td key={column}>{cell}</td>)}</tr>)}</tbody></table>{!rows.length&&<div className="empty-state">No data returned for this run.</div>}</div>; }
function Empty({title,text}:{title:string;text:string}) { return <div className="empty-state"><BarChart3 size={22}/><strong>{title}</strong><span>{text}</span></div>; }
function productRows(result:SimulationResult,annual:AnnualSummary|null) { const isPR7=result.scenarios.protein_recovery==='PR7'; const values:Array<{name:string;value:number;unit:string}> = annual ? [[isPR7?'Biostimulant retentate':'Protein',annual.products[isPR7?'biostimulant_product':'dry_protein_product']?.value||0,'t/year'],['Struvite',annual.named_products?.struvite_product?.value||annual.products.phosphorus_product?.value||0,'t/year'],['Ammonium sulfate',annual.products.ammonium_product?.value||0,'t/year'],['Potassium',annual.products.potassium_concentrate?.value||0,'t/year']].map(([name,value,unit])=>({name:String(name),value:Number(value)/1000,unit:String(unit)})) : [[isPR7?'Biostimulant retentate':'Protein',isPR7?Number(result.process_areas.protein_recovery.metrics?.biostimulant_product_flow_kg_hr||0):result.metrics.protein_recovered_kgh,'kg/h'],['Struvite',result.metrics.struvite_yield_kgh,'kg/h'],['Ammonium sulfate',result.metrics.ammonia_sulfate_kgh,'kg/h'],['Potassium',result.metrics.potassium_concentrate_kgh,'kg/h']].map(([name,value,unit])=>({name:String(name),value:Number(value),unit:String(unit)})); if(annual){const gas=annual.volumetric_products?.biomethane?.value;if(gas!=null)values.push({name:'Biomethane',value:Number(gas),unit:(annual.volumetric_products?.biomethane?.unit||'m³/year').replace('m3/','m³/')});} return values.filter(item=>Number.isFinite(item.value)&&item.value>0); }
function utilityRows(result:SimulationResult,annual:AnnualSummary|null) { return annual ? [['Electricity',annual.utilities.electricity?.value||0],['Heating',annual.utilities.heating?.value||0],['Cooling',annual.utilities.cooling?.value||0]].map(([name,value])=>({name:String(name),value:Number(value)/1000})) : [{name:'Electricity',value:Math.abs(result.metrics.total_power_kw)},{name:'Heating',value:Math.abs(result.metrics.total_heat_kw)}]; }
function formatMass(value:number) { return `${(value/1000).toLocaleString(undefined,{maximumFractionDigits:1})} t/year`; }
function formatEnergy(value:number) { return `${(value/1000).toLocaleString(undefined,{maximumFractionDigits:1})} MWh/year`; }
function formatHeat(value:number) { return `${value.toLocaleString(undefined,{maximumFractionDigits:1})} GJ/year`; }
function money(value:number) { return Number.isFinite(value)?`€${value.toLocaleString(undefined,{maximumFractionDigits:0})}`:'Not reported'; }
function compactMoney(value:number) { const amount=Number(value)||0;return Math.abs(amount)>=1e6?`€${(amount/1e6).toFixed(1)}m`:Math.abs(amount)>=1e3?`€${(amount/1e3).toFixed(0)}k`:`€${amount.toFixed(0)}`; }
function humanize(value:string) { return String(value||'').replace(/[._-]+/g,' ').replace(/\b\w/g,letter=>letter.toUpperCase()); }
const tooltipStyle = {background:'#fffdf9',border:'1px solid #c9c2ba',borderRadius:8,fontSize:10,color:'#0c3338'};
