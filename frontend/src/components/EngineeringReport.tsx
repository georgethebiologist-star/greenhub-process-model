import React, { useEffect, useMemo, useState } from 'react';
import { Download, GitCompare, Save, ShieldAlert } from 'lucide-react';
import { DYNAMIC_BASELINE_REPORT, EMPIRICAL_BASELINE_RESULT } from '../data/baselineFixtures';
import type { DynamicReport } from '../data/dynamicComplete';
import type { AnnualSummary, ResultSourceState, ScenarioSelection, SimulationResult } from '../types';

export type EmpiricalComparisonRun = {label:string; result:SimulationResult; scenario:ScenarioSelection; savedAt:string};
type Metric = {key:string; label:string; value:number; unit:string};
type ExportBundle = {json:unknown; monthly:Array<Record<string,unknown>>; annual:Array<Record<string,unknown>>; assumptions:Array<Record<string,unknown>>; markdown:string};

export function EmpiricalEngineeringReport({result,status,savedRuns=[],onSave}:{result:SimulationResult;status:ResultSourceState;savedRuns?:EmpiricalComparisonRun[];onSave?:(label:string,result:SimulationResult)=>void}) {
  const annual = result.annual ?? null;
  const current = empiricalMetrics(result);
  const baseline = empiricalMetrics(EMPIRICAL_BASELINE_RESULT);
  const comparison = [{label:'Bundled baseline',metrics:baseline},{label:status.is_live?'Current live run':'Displayed preview',metrics:current},...savedRuns.slice(-3).map(run=>({label:run.label,metrics:empiricalMetrics(run.result)}))];
  const bundle = useMemo(()=>empiricalExports(result,status),[result,status]);
  const maturity = result.parameters.reduce<Record<string,number>>((acc,item)=>{acc[item.quality_class]=(acc[item.quality_class]||0)+1;return acc;},{});
  return <div className="engineering-report">
    <ReportHeader title="Empirical engineering report" status={status} bundle={bundle}/>
    {onSave&&<div className="comparison-actions"><button className="secondary" onClick={()=>onSave(`Scenario ${savedRuns.length+1}`,result)}><Save size={14}/>Save displayed scenario</button></div>}
    <section className="engineering-kpis">{current.map(metric=><MetricCard key={metric.key} metric={metric}/>)}</section>
    <section className="engineering-grid">
      <article><span>Design basis</span><strong>{annual?.method_label || 'Hourly empirical snapshot'}</strong><p>{annual?.basis || 'Annual reporting bundle is unavailable.'}</p></article>
      <article><span>Biomass schedule</span><strong>{number(annual?.biomass_schedule.annual_processed_tonnes)} t/year</strong><p>{number(annual?.biomass_schedule.peak_month_processed_tonnes)} t peak month · {number(annual?.biomass_schedule.annual_unused_tonnes)} t unused</p></article>
      <article><span>Active route</span><strong>{Object.values(result.scenarios).filter(value=>typeof value==='string').slice(0,5).join(' → ')}</strong><p>{result.units.filter(unit=>unit.status==='active').length} active units; empirical and dynamic calculations remain independent.</p></article>
      <article><span>Validation / maturity</span><strong>{result.validation.status} · {result.balances.mass_closure_pct.toFixed(3)}% closure</strong><p>{Object.entries(maturity).map(([key,value])=>`Class ${key}: ${value}`).join(' · ')}</p></article>
      <article><span>Unmodelled utilities</span><strong>{result.units.filter(unit=>Math.abs(unit.power_kw)+Math.abs(unit.duty_kw)<1e-9).length} units</strong><p>Zero utility entries are presented as “Not modelled”, not as proven zero demand.</p></article>
      <article><span>Top warnings</span><strong>{result.validation.issues.length + (annual?.warnings.length || 0)} notes</strong><p>{[...result.validation.issues.map(item=>item.message),...(annual?.warnings||[])].slice(0,2).join(' ')}</p></article>
    </section>
    <ComparisonTable rows={comparison} baseline={baseline}/>
  </div>;
}

export function DynamicEngineeringReport({report,status}:{report:DynamicReport;status:ResultSourceState}) {
  const [saved,setSaved]=useState<Array<{label:string;report:DynamicReport;savedAt:string}>>(()=>readSavedDynamic());
  useEffect(()=>localStorage.setItem('greenhub.dynamicSavedRuns',JSON.stringify(saved)),[saved]);
  const current=dynamicMetrics(report), baseline=dynamicMetrics(DYNAMIC_BASELINE_REPORT);
  const rows=[{label:'Bundled baseline',metrics:baseline},{label:status.is_live?'Current live scenario':'Displayed preview',metrics:current},...saved.slice(-3).map(item=>({label:item.label,metrics:dynamicMetrics(item.report)}))];
  const bundle=useMemo(()=>dynamicExports(report,status),[report,status]);
  return <section className="panel engineering-report">
    <ReportHeader title="Dynamic proxy engineering report" status={status} bundle={bundle}/>
    <div className="comparison-actions"><button className="secondary" onClick={()=>setSaved(items=>[...items,{label:`Scenario ${items.length+1}`,report,savedAt:new Date().toISOString()}])}><Save size={14}/>Save displayed scenario</button>{saved.length>0&&<button className="text-button" onClick={()=>setSaved([])}>Clear saved</button>}</div>
    <section className="engineering-kpis">{current.slice(0,8).map(metric=><MetricCard key={metric.key} metric={metric}/>)}</section>
    <section className="engineering-grid"><article><span>Design basis</span><strong>Complete proxy chain</strong><p>30,000 t/year saved baseline · {report.scenario.protein_method} · {report.scenario.gas_route}</p></article><article><span>Model boundary</span><strong>Press cake external</strong><p>Only cell debris and final supernatant enter the in-project AD candidate.</p></article><article><span>Assumption maturity</span><strong>{report.assumptions_count} evidence records</strong><p>{Object.entries(report.assumption_counts).map(([key,value])=>`${key}: ${value}`).join(' · ')}</p></article><article><span>Validation status</span><strong>Not validated</strong><p>{report.warnings_count} warning occurrences · {report.blockers_count} blockers</p></article></section>
    <ComparisonTable rows={rows} baseline={baseline}/>
  </section>;
}

function ReportHeader({title,status,bundle}:{title:string;status:ResultSourceState;bundle:ExportBundle}) { return <div className="engineering-head"><div><span className="eyebrow">Decision record</span><h3>{title}</h3><p><ShieldAlert size={13}/>{status.label}: {status.detail}</p></div><div className="export-actions"><button onClick={()=>download('scenario.json',JSON.stringify(bundle.json,null,2),'application/json')}><Download size={13}/>Scenario JSON</button><button onClick={()=>download('monthly.csv',csv(bundle.monthly),'text/csv')}><Download size={13}/>Monthly CSV</button><button onClick={()=>download('annual-summary.csv',csv(bundle.annual),'text/csv')}><Download size={13}/>Annual CSV</button><button onClick={()=>download('assumptions.csv',csv(bundle.assumptions),'text/csv')}><Download size={13}/>Assumptions CSV</button><button onClick={()=>download('engineering-report.md',bundle.markdown,'text/markdown')}><Download size={13}/>Report Markdown</button></div></div>; }
function MetricCard({metric}:{metric:Metric}) { return <div><span>{metric.label}</span><strong>{number(metric.value)}</strong><small>{metric.unit}</small></div>; }

function ComparisonTable({rows,baseline}:{rows:Array<{label:string;metrics:Metric[]}>;baseline:Metric[]}) { return <section className="engineering-comparison"><div><GitCompare/><h4>Scenario comparison</h4><p>Delta bars compare each displayed or saved case with the bundled baseline.</p></div><div className="proxy-table-scroll"><table><thead><tr><th>Case</th>{baseline.map(metric=><th key={metric.key}>{metric.label}<small>{metric.unit}</small></th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={`${row.label}-${index}`}><td><strong>{row.label}</strong></td>{baseline.map(base=>{const value=row.metrics.find(item=>item.key===base.key)?.value||0;const delta=value-base.value;const pct=base.value?Math.max(-100,Math.min(100,delta/base.value*100)):0;return <td key={base.key}>{number(value)}<small className={delta>0?'delta-up':delta<0?'delta-down':''}>{index===0?'reference':`${delta>=0?'+':''}${number(delta)}`}</small><i className="delta-bar"><b style={{width:`${Math.abs(pct)}%`}}/></i></td>})}</tr>)}</tbody></table></div></section>; }

function empiricalMetrics(result:SimulationResult):Metric[] {
  const annual=result.annual;
  const feed=(annual?.feed_processed.value||0)/1000;
  const pressCake=(annual?.monthly||[]).reduce((sum,row)=>sum+(row.intermediate_streams_kg.pressed_fibre_cake||0),0)/1000;
  const biomethane=(annual?.monthly||[]).reduce((sum,row)=>sum+(row.volumetric_products_m3.biomethane||0),0);
  const electricity=(annual?.utilities.electricity.value||0)/1000;
  const heat=(annual?.utilities.heating.value||0)*.0036;
  return [{key:'feed',label:'Feed processed',value:feed,unit:'t/year'},{key:'protein',label:'Dried protein',value:(annual?.products.dry_protein_product?.value||0)/1000,unit:'t/year'},{key:'biomethane',label:'Biomethane',value:biomethane,unit:'m³/year'},{key:'press_cake',label:'Press cake',value:pressCake,unit:'t/year'},{key:'electricity',label:'Electricity',value:electricity,unit:'MWh/year'},{key:'heat',label:'Heat',value:heat,unit:'GJ/year'},{key:'closure',label:'Mass closure',value:annual?.balance.overall_closure_pct??result.balances.mass_closure_pct,unit:'%'},{key:'limitations',label:'Limitations',value:result.validation.issues.length+(annual?.warnings.length||0),unit:'count'},{key:'protein_intensity',label:'Protein intensity',value:feed?(annual?.products.dry_protein_product?.value||0)/feed:0,unit:'kg/t feed'},{key:'utilization',label:'Capacity utilization',value:(annual?.biomass_schedule.utilization_fraction||0)*100,unit:'%'}];
}
function dynamicMetrics(report:DynamicReport):Metric[] { const get=(key:string,unit:string)=>report.annual_summary[key]?.[unit]||0;const feed=get('feed_processed','tonnes_per_year');return [{key:'protein',label:'Dried protein',value:get('dried_protein_product','tonnes_per_year'),unit:'t/year'},{key:'biomethane',label:'Biomethane',value:get('biomethane','m3_per_year'),unit:'m³/year'},{key:'ammonium',label:'Ammonium',value:get('ammonium_product','tonnes_per_year'),unit:'t/year'},{key:'struvite',label:'Struvite',value:get('struvite_candidate','tonnes_per_year'),unit:'t/year'},{key:'potassium',label:'K concentrate',value:get('potassium_concentrate','tonnes_per_year'),unit:'t/year'},{key:'water',label:'Recovered water',value:get('recovered_water','tonnes_per_year'),unit:'t/year'},{key:'electricity',label:'Electricity',value:get('electricity_demand','MWh_per_year'),unit:'MWh/year'},{key:'heat',label:'Heat',value:get('heat_demand','GJ_per_year'),unit:'GJ/year'},{key:'margin',label:'Margin proxy',value:report.analysis.economic?.net_operating_margin_eur_per_year||0,unit:'EUR/year'},{key:'co2e',label:'CO₂e proxy',value:(report.analysis.environmental?.net_kg_co2e_per_year||0)/1000,unit:'t CO₂e/year'},{key:'assumptions',label:'Assumptions',value:report.assumptions_count,unit:'count'},{key:'protein_intensity',label:'Protein intensity',value:feed?get('dried_protein_product','tonnes_per_year')*1000/feed:0,unit:'kg/t feed'},{key:'biomethane_intensity',label:'Biomethane intensity',value:feed?get('biomethane','m3_per_year')/feed:0,unit:'m³/t feed'},{key:'electricity_intensity',label:'Electricity intensity',value:feed?get('electricity_demand','MWh_per_year')/feed:0,unit:'MWh/t feed'}]; }

function empiricalExports(result:SimulationResult,status:ResultSourceState):ExportBundle { const annual=result.annual;const assumptions=result.parameters.map(item=>({parameter_id:item.parameter_id,value:item.current_value,unit:item.unit,quality_class:item.quality_class,notes:item.notes||''}));const annualRows=empiricalMetrics(result).map(item=>({metric:item.label,value:item.value,unit:item.unit}));return {json:{source_status:status,result},monthly:(annual?.monthly||[]).map(row=>({period:row.period,feed_processed_kg:row.feed_processed_kg,...row.products_kg,...row.volumetric_products_m3,...row.utilities_kwh,mass_residual_kg:row.mass_residual_kg})),annual:annualRows,assumptions,markdown:markdownReport('Empirical GreenHub engineering report',status,annualRows,assumptions)}; }
function dynamicExports(report:DynamicReport,status:ResultSourceState):ExportBundle { const annualRows=dynamicMetrics(report).map(item=>({metric:item.label,value:item.value,unit:item.unit}));const monthly=report.monthly.map(row=>({time_label:row.time_label,operating_hours:row.operating_hours,...Object.fromEntries(Object.entries(row.metrics).map(([key,value])=>[key,Object.values(value).at(-1)]))}));return {json:{source_status:status,report},monthly,annual:annualRows,assumptions:report.assumptions as unknown as Array<Record<string,unknown>>,markdown:markdownReport('Dynamic proxy engineering report',status,annualRows,report.assumptions as unknown as Array<Record<string,unknown>>)}; }
function markdownReport(title:string,status:ResultSourceState,metrics:Array<Record<string,unknown>>,assumptions:Array<Record<string,unknown>>) { return `# ${title}\n\n**Result source:** ${status.label}\n\n${status.detail}\n\n## Annual summary\n\n${metrics.map(row=>`- ${row.metric}: ${row.value} ${row.unit}`).join('\n')}\n\n## Evidence and assumptions\n\n${assumptions.slice(0,20).map(row=>`- ${row.policy_id||row.parameter_id||'record'}: ${row.warning||row.notes||'See scenario JSON.'}`).join('\n')}\n\nThis report is not a substitute for the live model provenance package.\n`; }
function csv(rows:Array<Record<string,unknown>>) { if(!rows.length)return '';const keys=[...new Set(rows.flatMap(row=>Object.keys(row)))];const cell=(value:unknown)=>`"${String(value??'').replaceAll('"','""')}"`;return [keys.map(cell).join(','),...rows.map(row=>keys.map(key=>cell(typeof row[key]==='object'?JSON.stringify(row[key]):row[key])).join(','))].join('\n'); }
function download(name:string,content:string,type:string) { const url=URL.createObjectURL(new Blob([content],{type}));const anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();URL.revokeObjectURL(url); }
function number(value:number|undefined) { return Number(value||0).toLocaleString(undefined,{maximumFractionDigits:2}); }
function readSavedDynamic() { try{return JSON.parse(localStorage.getItem('greenhub.dynamicSavedRuns')||'[]')}catch{return []} }
