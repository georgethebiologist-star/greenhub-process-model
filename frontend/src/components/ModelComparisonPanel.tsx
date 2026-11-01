import React from 'react';
import type {SimulationResult} from '../types';

type Props={dynamic:SimulationResult;empirical:SimulationResult|null;live:boolean;busy:boolean;onRun:()=>void;error:string};
const n=(value:number|undefined|null)=>value==null||!Number.isFinite(value)?'Not reported':value.toLocaleString(undefined,{maximumFractionDigits:2});
const metrics=[
  ['Feed processed','feed'],['Dry protein product','protein'],['Biomethane product','methane'],['Electricity demand','electricity'],['Mass closure','closure'],
] as const;
function value(result:SimulationResult,key:typeof metrics[number][1]):number|null {
  const a=result.annual;if(!a)return null;
  if(key==='feed')return a.feed_processed?.value??null;
  if(key==='protein')return a.products?.dry_protein_product?.value??null;
  if(key==='methane')return a.products?.biomethane?.value??null;
  if(key==='electricity')return a.utilities?.electricity?.value??null;
  return a.balance?.overall_closure_pct??null;
}
function unit(key:typeof metrics[number][1]) {return key==='closure'?'%':key==='electricity'?'kWh / reported period':'kg / reported period';}

export default function ModelComparisonPanel({dynamic,empirical,live,busy,onRun,error}:Props) {
  return <section className="model-comparison panel"><div className="overview-head"><div><span className="eyebrow">Model comparison</span><h2>Quasi-dynamic vs empirical steady-state</h2><p>Same selected feed and route. Quasi-dynamic totals integrate the configured monthly schedule; steady-state totals annualize the selected reference month. Differences are model-basis comparisons, not experimental validation.</p></div><button className="run-button" onClick={onRun} disabled={!live||busy}>{busy?'Calculating comparison…':'Run empirical comparison'}</button></div>
    {!live&&<p className="ds-warning">Run the live quasi-dynamic simulation before comparing. A preview baseline is not used as a comparison result.</p>}{error&&<p role="alert" className="ds-warning">{error}</p>}
    <div className="comparison-grid"><article><span>Primary</span><h3>Quasi-dynamic</h3><p>{dynamic.annual?.method_label||'Waiting for live annual report'}</p></article><article><span>Secondary benchmark</span><h3>Empirical steady-state</h3><p>{empirical?.annual?.method_label||'Run the same selected route at the reference month'}</p></article></div>
    <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Indicator</th><th>Quasi-dynamic</th><th>Empirical</th><th>Relative deviation</th></tr></thead><tbody>{metrics.map(([label,key])=>{const a=value(dynamic,key),b=empirical?value(empirical,key):null;const deviation=a!=null&&b!=null&&a!==0?100*(b-a)/a:null;return <tr key={key}><th>{label}<small>{unit(key)}</small></th><td>{n(a)}</td><td>{n(b)}</td><td>{deviation==null?'—':`${deviation>0?'+':''}${deviation.toLocaleString(undefined,{maximumFractionDigits:1})}%`}</td></tr>;})}</tbody></table></div>
    {empirical?.annual&&<details><summary>Comparison conditions and balance details</summary><p>Quasi-dynamic basis: {dynamic.annual?.basis||'unavailable'}</p><p>Empirical basis: {empirical.annual.basis}</p><p className="comparison-caveat">Storage reactions are only included when enabled in the quasi-dynamic configuration; the steady-state comparison does not currently apply those storage conditions. If storage is enabled, this comparison is therefore not storage-matched.</p><pre>{JSON.stringify({dynamic:{scenario:dynamic.scenarios,validation:dynamic.validation,period:dynamic.annual?.period,balance:dynamic.annual?.balance},empirical:{scenario:empirical.scenarios,validation:empirical.validation,period:empirical.annual.period,balance:empirical.annual.balance}},null,2)}</pre></details>}
  </section>;
}
