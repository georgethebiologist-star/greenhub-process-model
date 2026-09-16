import React, { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { fetchDynamicOptions, runDynamicScenario, type DynamicOptions, type DynamicReport, type DynamicScenario, type Evidence } from '../data/dynamicComplete';
import './dynamicComplete.css';

const label = (value: string) => value.replaceAll('_', ' ');
const number = (value: number | null | undefined) => value == null ? 'Unavailable' : value.toLocaleString(undefined, {maximumFractionDigits: 1});
const colors = ['#408f4d', '#729ad2', '#cc7252', '#8569a9', '#bb9419', '#307e86'];
const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
type Series = {key: string; title: string};

function Chart({title, unit, data, series, bars = false, xKey = 'month'}: {title: string; unit: string; data: object[]; series: Series[]; bars?: boolean; xKey?: string}) {
  const Plot = bars ? BarChart : LineChart;
  return <section className="panel proxy-chart"><h3>{title}</h3><p>{unit}</p><div role="img" aria-label={`${title}, ${unit}`} className="proxy-chart-canvas">
    <ResponsiveContainer width="100%" height="100%"><Plot data={data} layout={bars ? 'vertical' : 'horizontal'} margin={{top: 12, right: 16, bottom: 12, left: 12}}>
      <CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey={bars ? undefined : xKey} type={bars ? 'number' : 'category'} tick={{fontSize: 11}}/><YAxis dataKey={bars ? xKey : undefined} type={bars ? 'category' : 'number'} width={bars ? 150 : 65} tick={{fontSize: 11}} tickFormatter={v => bars ? String(v) : number(v)}/>
      <Tooltip formatter={(v: number, name: string) => [number(v), name]}/><Legend wrapperStyle={{fontSize: 12}}/>{bars ? <ReferenceLine x={0} stroke="#587174"/> : <ReferenceLine y={0} stroke="#587174"/>}
      {series.map((s, i) => bars ? <Bar key={s.key} dataKey={s.key} name={s.title} fill={colors[i % colors.length]}/> : <Line key={s.key} type="linear" dataKey={s.key} name={s.title} stroke={colors[i % colors.length]} strokeWidth={2.5} dot={{r: 3}} connectNulls={false} isAnimationActive={false}/>)}
    </Plot></ResponsiveContainer>
  </div><details><summary>View chart data</summary><div className="proxy-table-scroll"><table><thead><tr><th>Period / category</th>{series.map(s => <th key={s.key}>{s.title}</th>)}</tr></thead><tbody>{data.map((row: any, i) => <tr key={i}><td>{row[xKey]}</td>{series.map(s => <td key={s.key}>{number(row[s.key])}</td>)}</tr>)}</tbody></table></div></details></section>;
}

function EvidenceTable({records}: {records: Evidence[]}) {
  return <div className="proxy-table-scroll"><table><thead><tr><th>policy_id / name</th><th>Value / unit</th><th>source_status / certainty_class</th><th>source_file / source_id</th><th>Warning</th></tr></thead><tbody>{records.map((r, i) => <tr key={i}>
    <td><code>{r.policy_id}</code><br/>{r.name}<small>{r.time_labels?.join(', ')}{r.usage === 'closure_registry' ? ' · registry; not selected unit evidence' : ''}</small></td>
    <td>{typeof r.value === 'object' ? <details><summary>Policy values</summary><pre>{JSON.stringify(r.value, null, 2)}</pre></details> : String(r.value)}<br/>{r.unit}</td>
    <td><strong>{r.source_status}</strong><br/>{r.certainty_class}</td><td>{r.source_file || 'No source file'}<br/>{r.source_id}</td><td>{r.warning}{r.provenance != null && <details><summary>Full provenance</summary><pre>{JSON.stringify(r.provenance, null, 2)}</pre></details>}</td>
  </tr>)}</tbody></table></div>;
}

export default function DynamicCompleteDashboard() {
  const [options, setOptions] = useState<DynamicOptions | null>(null);
  const [scenario, setScenario] = useState<DynamicScenario | null>(null);
  const [factors, setFactors] = useState<Record<string, number>>({});
  const [report, setReport] = useState<DynamicReport | null>(null);
  const [running, setRunning] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  async function load() {
    setError('');
    try { const data = await fetchDynamicOptions(); setOptions(data); setScenario(data.defaults); }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not load proxy options.'); }
  }
  useEffect(() => { void load(); }, []);
  function update<K extends keyof DynamicScenario>(key: K, value: DynamicScenario[K]) {
    setScenario(current => current && ({...current, [key]: value})); setDirty(true);
  }
  async function run() {
    if (!scenario) return;
    setRunning(true); setError('');
    try { setReport(await runDynamicScenario(scenario, factors)); setDirty(false); }
    catch (e) { setError(e instanceof Error ? e.message : 'Proxy scenario failed.'); }
    finally { setRunning(false); }
  }
  const annual = (key: string, unit: string) => report?.annual_summary[key]?.[unit];
  const chartRows = report?.monthly.map(row => ({month: months[Number(row.time_label.slice(5)) - 1], ...Object.fromEntries(Object.entries(row.metrics).map(([key, values]) => [key, Object.entries(values).find(([unit]) => unit.endsWith('_per_month'))?.[1]]))})) || [];
  const schedule = report?.biomass_schedule;
  const economic = report?.analysis.economic, environment = report?.analysis.environmental;
  return <div className="page-stack proxy-dashboard">
    <section className="overview-head"><div><span className="eyebrow">Opt-in scenario exploration</span><h1>Grass to products</h1><p>Start with 30,000 tonnes of fresh grass per year. Follow the seasonal supply through protein, gas, fertilizer candidates and water recovery.</p></div></section>
    <section className="proxy-validity" role="status"><strong>Proxy-complete model · Not validated simulation</strong><span>{scenario?.allow_assumptions === false ? 'Strict mode' : 'Assumptions enabled'} · validated_simulation_ready = false</span><p>Literature transfers, legacy ratios and engineering closures remain visible. Press cake leaves the system; it never enters AD.</p></section>
    {error && <div className="proxy-error" role="alert">{error} {!options && <button className="secondary" onClick={load}>Retry connection</button>}</div>}
    {!options || !scenario ? <p>{error ? 'Connect the Python API to load the scenario controls.' : 'Loading scenario options…'}</p> : <>
      <section className="panel proxy-controls"><h2>Scenario controls</h2><p>Availability stays fixed when processing is reduced. A monthly capacity ceiling creates a plateau; the remainder is unused.</p>
        <fieldset disabled={running}><div className="proxy-input-grid">
          <label>Annual processed biomass (t/year)<input type="number" min="0" step="100" value={scenario.annual_processed_biomass_tonnes} onChange={e => update('annual_processed_biomass_tonnes', +e.target.value)}/></label>
          <label>Collection / refinery fraction: {number(scenario.collection_refinery_fraction * 100)}%<input type="range" min="0" max="100" value={scenario.collection_refinery_fraction * 100} onChange={e => update('collection_refinery_fraction', +e.target.value / 100)}/></label>
          <label>Feed input basis<select value={scenario.feed_basis} onChange={e => update('feed_basis', e.target.value as DynamicScenario['feed_basis'])}><option value="tonnes_per_year">Annual target (t/year)</option><option value="kg_per_hr">Hourly capacity (kg/h)</option></select></label>
          {scenario.feed_basis === 'kg_per_hr' && <label>Processing capacity (kg/h)<input type="number" min="0" value={scenario.feed_kg_per_hr} onChange={e => update('feed_kg_per_hr', +e.target.value)}/></label>}
          <label>Protein method<select value={scenario.protein_method} onChange={e => update('protein_method', e.target.value)}>{options.protein_methods.map(m => <option key={m} value={m}>{label(m)}{m === 'heat' ? ' (explicit proxy closure)' : ''}</option>)}</select></label>
          {['heat','generic'].includes(scenario.protein_method) && <label>Explicit protein recovery fraction<input type="number" min="0" max="1" step="0.01" required value={scenario.protein_recovery_fraction ?? ''} onChange={e => update('protein_recovery_fraction', e.target.value === '' ? null : +e.target.value)}/></label>}
          <label>Drying method<select value={scenario.drying_method} onChange={e => update('drying_method', e.target.value)}>{options.drying_methods.map(m => <option key={m} value={m}>{label(m)}</option>)}</select></label>
          <label>Target product moisture (%)<input type="number" min="0" max="99" step="1" value={scenario.target_product_moisture * 100} onChange={e => update('target_product_moisture', +e.target.value / 100)}/></label>
          <label>Gas route<select value={scenario.gas_route} onChange={e => update('gas_route', e.target.value)}>{options.gas_routes.map(m => <option key={m} value={m}>{m === 'chp_utilities' ? 'CHP' : label(m)}</option>)}</select></label>
        </div>
        <details><summary>Supply season and active months</summary><div className="proxy-input-grid">
          <label>Available biomass at 100% (t/year)<input type="number" min="0" value={scenario.annual_available_biomass_tonnes} onChange={e => update('annual_available_biomass_tonnes', +e.target.value)}/></label>
          <label>Season start<input type="date" value={scenario.season_start} disabled={scenario.full_year} onChange={e => update('season_start', e.target.value)}/></label>
          <label>Season end<input type="date" value={scenario.season_end} disabled={scenario.full_year} onChange={e => update('season_end', e.target.value)}/></label>
          <label>Peak date<input type="date" value={scenario.peak_date} onChange={e => update('peak_date', e.target.value)}/></label>
          <label>Spread (days)<input type="number" min="1" max="366" value={scenario.spread_days} onChange={e => update('spread_days', +e.target.value)}/></label>
        </div><div className="proxy-checks"><label><input type="checkbox" checked={scenario.full_year} onChange={e => update('full_year', e.target.checked)}/>Full-year supply curve</label>{months.map((m, i) => <label key={m}><input type="checkbox" checked={scenario.active_months.includes(i + 1)} onChange={e => update('active_months', e.target.checked ? [...scenario.active_months, i + 1].sort((a,b) => a-b) : scenario.active_months.filter(n => n !== i + 1))}/>{m}</label>)}</div></details>
        <h3>Resource recovery</h3><div className="proxy-checks">{options.resource_recovery_methods.map(m => <label key={m}><input type="checkbox" checked={scenario.resource_recovery_methods.includes(m)} onChange={e => update('resource_recovery_methods', e.target.checked ? [...scenario.resource_recovery_methods, m] : scenario.resource_recovery_methods.filter(n => n !== m))}/>{label(m)}</label>)}</div>
        <div className="proxy-checks"><label><input type="checkbox" checked={scenario.allow_assumptions} onChange={e => update('allow_assumptions', e.target.checked)}/>Allow proxy assumptions</label><label><input type="checkbox" checked={scenario.show_strict_mode_blockers} onChange={e => update('show_strict_mode_blockers', e.target.checked)}/>Show strict mode blockers</label><label><input type="checkbox" checked={scenario.annualize} onChange={e => update('annualize', e.target.checked)}/>Show full-year extrapolation</label></div>
        <details><summary>Economic and environmental scenario factors (all unvalidated)</summary><div className="proxy-input-grid">{Object.entries(options.analysis_factors).map(([key, factor]) => <label key={key}>{label(key)} ({factor.unit})<input type="number" min="0" step="any" value={factors[key] ?? factor.value} onChange={e => {setFactors(current => ({...current, [key]: +e.target.value})); setDirty(true);}}/><small>{key in factors ? 'User input; no source attached' : factor.source_status}</small></label>)}</div></details>
        <div className="proxy-actions"><button className="run-button" onClick={run}>{running ? 'Calculating proxy scenario…' : 'Run proxy scenario'}</button><button className="secondary" onClick={() => {setScenario(options.defaults); setFactors({}); setReport(null); setDirty(false); setError('');}}>Reset to baseline</button></div>
        </fieldset>
      </section>
      {dirty && report && <div className="proxy-error" role="status">Controls have changed. Results below belong to the previous scenario; run again to update.</div>}
      {running && <p role="status">Running the isolated BioSTEAM proxy chain and checking stream parity…</p>}
      {!report && <section className="panel"><h2>Process story</h2><p>Feed → press cake (external) + juice → protein product + residual → AD → gas route → fertilizer candidates + recovered water.</p><p>Run the proxy scenario to calculate monthly masses, energy and preliminary analysis. No empirical run is replaced.</p></section>}
      {report && schedule && <>
        <div className="proxy-result-context"><strong>Displayed scenario:</strong> {label(report.scenario.protein_method)} · {label(report.scenario.drying_method)} · {label(report.scenario.gas_route)} · {report.scenario.allow_assumptions ? 'Assumptions enabled' : 'Strict mode'} · {report.readiness.status}</div>
        <section className="kpi-grid proxy-kpis">{[
          ['Feed processed', 'feed_processed', 'tonnes_per_year', 't/year'], ['Dried protein product', 'dried_protein_product', 'tonnes_per_year', 't/year'],
          ['Biomethane', 'biomethane', 'm3_per_year', 'm³/year'], ['Electricity demand', 'electricity_demand', 'MWh_per_year', 'MWh/year'],
          ['Heat demand', 'heat_demand', 'GJ_per_year', 'GJ/year'], ['Ammonium candidate', 'ammonium_product', 'tonnes_per_year', 't/year'],
          ['Struvite candidate', 'struvite_candidate', 'tonnes_per_year', 't/year'], ['Recovered water', 'recovered_water', 'tonnes_per_year', 't/year'],
        ].map(([title, key, unit, display]) => <div className="kpi" key={key}><span>{title}</span><strong>{number(annual(key, unit))}</strong><small>{display} · scheduled total</small></div>)}</section>
        <section className="panel"><h2>Process flow summary</h2><p>Scheduled tonnes/year at each stage. Digestate and juice are intermediate streams, not additional final products.</p><div className="proxy-process">{[
          ['Fresh grass', `${number(annual('feed_processed','tonnes_per_year'))} t`], ['Press', `${number(annual('press_cake','tonnes_per_year'))} t external cake + ${number(annual('juice','tonnes_per_year'))} t juice`],
          ['Protein + residual', `${number(annual('dried_protein_product','tonnes_per_year'))} t product (${number(annual('recovered_protein','tonnes_per_year'))} t protein); ${number(annual('ad_feed','tonnes_per_year'))} t to AD`],
          ['AD + gas route', `${number(annual('raw_biogas','m3_per_year'))} m³ raw gas → ${number(annual('biomethane','m3_per_year'))} m³ biomethane; ${number(annual('digestate','tonnes_per_year'))} t digestate`],
          ['Recovery', `${number(annual('ammonium_product','tonnes_per_year'))} t ammonium; ${number(annual('struvite_candidate','tonnes_per_year'))} t struvite; ${number(annual('potassium_concentrate','tonnes_per_year'))} t K concentrate; ${number(annual('recovered_water','tonnes_per_year'))} t water; ${number(annual('final_residual_liquor','tonnes_per_year'))} t residual liquor`],
        ].map(([title, detail], i) => <div key={title}><small>{i + 1} →</small><strong>{title}</strong><p>{detail}</p></div>)}</div></section>
        <section className="panel"><h2>Supply utilization</h2><div className="proxy-utilization"><span>Available: <strong>{number(schedule.annual_available_tonnes)} t/year</strong></span><span>Processed: <strong>{number(schedule.annual_processed_tonnes)} t/year</strong></span><span>Utilization: <strong>{number(schedule.utilization_fraction * 100)}%</strong></span><span>Peak month: <strong>{number(schedule.peak_month_processed_tonnes)} t</strong></span></div>{schedule.unmet_target_tonnes > 0.01 && <p role="alert">Unmet processing target: {number(schedule.unmet_target_tonnes)} tonnes. Review active months and hourly capacity.</p>}</section>
        <Chart title="Biomass Supply Schedule" unit="tonnes/month" data={schedule.monthly.map(r => ({...r, month: months[+r.time_label.slice(5) - 1]}))} series={[{key:'available_biomass_tonnes',title:'Available'},{key:'processed_biomass_tonnes',title:'Processed'},{key:'unused_biomass_tonnes',title:'Unused / uncollected'}]}/>
        <div className="proxy-chart-grid">
          <Chart title="Feed and bulk streams" unit="tonnes/month; press cake remains external" data={chartRows} series={[{key:'feed_processed',title:'Processed feed'},{key:'press_cake',title:'External press cake'},{key:'digestate',title:'Digestate'}]}/>
          <Chart title="Protein and fertilizer candidates" unit="tonnes/month; separated from feed scale" data={chartRows} series={[{key:'dried_protein_product',title:'Dried protein'},{key:'ammonium_product',title:'Ammonium'},{key:'struvite_candidate',title:'Struvite'},{key:'potassium_concentrate',title:'K concentrate'}]}/>
          <Chart title="Biomethane output" unit="m³/month (normal-volume proxy)" data={chartRows} series={[{key:'biomethane',title:'Biomethane'}]}/>
          <Chart title="Recovered water" unit="tonnes/month; proxy quality remains unvalidated" data={chartRows} series={[{key:'recovered_water',title:'Recovered water'}]}/>
          <Chart title="Electricity demand and CHP output" unit="MWh/month; incomplete utility coverage" data={chartRows} series={[{key:'drying_electricity',title:'Drying'},{key:'gas_upgrading_electricity',title:'Gas upgrading'},{key:'chp_electricity_output',title:'CHP output'}]}/>
          <Chart title="Heat demand and CHP output" unit="GJ/month; gross demand, no heat integration" data={chartRows} series={[{key:'ad_heat',title:'AD heat'},{key:'drying_heat',title:'Drying heat'},{key:'gas_heat',title:'Gas route heat'},{key:'chp_heat_output',title:'CHP output'}]}/>
        </div>
        {report.annualized_estimate && <details className="panel"><summary>Full-year extrapolation (not biomass-constrained)</summary><p>Mean operating rates extrapolated to every calendar hour. These are separate from the scheduled annual cards.</p><dl>{['feed_processed','dried_protein_product','biomethane','electricity_demand','heat_demand'].map(key => <React.Fragment key={key}><dt>{label(key)}</dt><dd>{Object.entries(report.annualized_estimate![key]).map(([unit, value]) => `${number(value)} ${unit}`).join(', ')}</dd></React.Fragment>)}</dl></details>}
        <section className="panel"><h2>Assumption traceability</h2><p>{report.assumptions_count} unique process evidence records · {report.warnings_count} warning occurrences · {report.blockers_count} blocker occurrences</p><div className="proxy-utilization"><span>Direct dataset: <strong>{report.assumption_counts.direct_dataset || 0}</strong></span><span>Legacy proxy: <strong>{report.assumption_counts.greenhub_legacy_proxy_result || 0}</strong></span><span>Engineering assumptions: <strong>{report.assumption_counts.engineering_assumption || 0}</strong></span></div><p>Key output drivers (qualitative; not a sensitivity ranking): {report.top_assumptions.join(', ')}</p>
          <details><summary>Expand process evidence and assumptions</summary><EvidenceTable records={report.assumptions}/></details>
          <details><summary>Warnings ({Object.keys(report.warning_counts).length} distinct)</summary><ul>{Object.keys(report.warning_counts).map(w => <li key={w}>{w}</li>)}</ul></details>
          {report.blockers_count > 0 && <p role="alert">This scenario is blocked. Downstream production and analysis totals are withheld.</p>}
          {scenario.show_strict_mode_blockers && <details open={report.blockers_count > 0}><summary>Strict mode blockers</summary>{report.blockers_count ? <ul>{Object.keys(report.blocker_counts).map(b => <li key={b}>{b}</li>)}</ul> : <p>No blockers in the current assumption-enabled run. Disable assumptions and run again to inspect strict-mode blockers.</p>}</details>}
        </section>
        <section className="panel"><h2>Economic and environmental proxy</h2><p>proxy_analysis_ready = {String(report.analysis.proxy_analysis_ready)} · Not validated TEA / LCA. Every factor below is an illustrative placeholder or user input.</p>{economic && environment && <><div className="proxy-utilization"><span>Operating margin: <strong>€{number(economic.net_operating_margin_eur_per_year)}/year</strong></span><span>Included cost: <strong>€{number(economic.cost_eur_per_tonne_feed)}/t feed</strong></span><span>Net emissions: <strong>{number(environment.net_kg_co2e_per_year / 1000)} t CO₂e/year</strong></span></div><p>Cost: €{number(economic.cost_eur_per_kg_dried_protein)}/kg dried product; €{number(economic.cost_eur_per_m3_biomethane)}/m³ biomethane. Emissions: {number(environment.kg_co2e_per_tonne_feed)} kg CO₂e/t feed; {number(environment.kg_co2e_per_kg_dried_protein)} kg CO₂e/kg dried product.</p><p>{economic.allocation_note}</p></>}
          <details open><summary>Analysis limitations</summary><ul>{report.analysis.warnings.map(w => <li key={w}>{w}</li>)}</ul></details><details><summary>Economic / environmental factor provenance</summary><EvidenceTable records={report.analysis.assumptions}/></details></section>
        {economic && environment && <div className="proxy-chart-grid"><Chart title="Annual revenue and included costs" unit="EUR/year; cost bars are negative" bars data={[...Object.entries(economic.revenue_eur_per_year).map(([key,v]) => ({month:label(key), revenue:v, cost:0})),...Object.entries(economic.costs_eur_per_year).map(([key,v]) => ({month:label(key), revenue:0, cost:-v}))]} series={[{key:'revenue',title:'Revenue / credit'},{key:'cost',title:'Included cost'}]}/><Chart title="Emissions proxy contributions" unit="tonnes CO₂e/year; negative = avoided emissions" bars data={Object.entries(environment.contributions_kg_co2e_per_year).map(([key,v]) => ({month:label(key), emissions:v / 1000}))} series={[{key:'emissions',title:'CO₂e proxy'}]}/></div>}
      </>}
    </>}
  </div>;
}
