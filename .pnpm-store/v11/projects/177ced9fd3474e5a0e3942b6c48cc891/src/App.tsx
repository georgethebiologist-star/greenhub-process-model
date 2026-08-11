import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  CircleDot,
  FileDown,
  Gauge,
  GitCompare,
  Layers3,
  Play,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Wrench,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { DEFAULT_PARAMETERS, runSimulation } from './data/greenhubData';
import { buildPythonRequest, fetchRunResources, runPythonSimulation } from './data/apiClient';
import { normalizeResult } from './data/normalizeResult';
import { ReportCenter, ResultsWorkbench } from './components/ResultsWorkbench';
import { InputStudio, type FeedInputs } from './components/InputStudio';
import type { CalculationMode, ParameterDefinition, ScenarioSelection, SimulationResult } from './types';

type RuntimeSource = 'python' | 'fallback';
type TabId = 'overview' | 'configure' | 'results' | 'reports' | 'advanced';
type SavedRun = { label: string; result: SimulationResult; scenario: ScenarioSelection; savedAt: string };
type Artifact = { name: string; type: string; description: string; url?: string; available: boolean; warning?: string };

const defaults: ScenarioSelection = {
  feed_front_end: 'F2', protein_recovery: 'PR3', anaerobic_digestion: 'AD1',
  biogas_upgrading: 'BG2', nutrient_recovery: 'NR4', process_order: 'A',
};
const qualityHelp = {
  A: 'Measured or verified', B: 'Strong literature basis', C: 'Engineering estimate',
  D: 'Uncertain or quarantined', E: 'Structural placeholder',
};
const areaLabels: Record<string, string> = {
  front_end: 'Feed and front-end', feedstock_and_characterization: 'Feed characterization',
  feed_preparation_and_primary_separation: 'Feed preparation', protein_recovery: 'Protein recovery',
  anaerobic_digestion: 'Anaerobic digestion', biogas_upgrading: 'Biogas upgrading',
  biogas_conditioning_and_upgrading: 'Biogas upgrading', nutrient_recovery: 'Nutrient recovery',
  digestate_treatment_and_nutrient_recovery: 'Nutrient recovery',
  shared_utilities_and_supporting_operations: 'Utilities',
};
const modeLabels: Record<CalculationMode, string> = {
  structural: 'Structural model', literature_default: 'Literature defaults', calibrated: 'Calibrated data',
};
const scenarioGroups = [
  { key: 'feed_front_end' as const, title: 'Feed preparation', affects: 'Liquid yield, solids split and electricity', options: [['F0','Measured liquid fraction','active'],['F1','Roadside grass without PEF','active'],['F2','PEF baseline','active'],['F3','PEF sensitivity-ready','active']] },
  { key: 'protein_recovery' as const, title: 'Protein recovery', affects: 'Protein yield and downstream COD', options: [['PR0','Bypass protein recovery','active'],['PR1','Acid precipitation','active'],['PR2','Heat coagulation','active'],['PR3','Combined acid and heat','active'],['PR4','Lactic fermentation','planned'],['PR5','CO₂-assisted precipitation','planned'],['PR6','Ultrafiltration','planned']] },
  { key: 'anaerobic_digestion' as const, title: 'Anaerobic digestion', affects: 'Biogas production and digestate', options: [['AD0','No digestion','active'],['AD1','Baseline digestion','active'],['AD2','Protein-rich liquid route','active'],['AD3','Alternative AD configuration','active'],['AD4','Advanced digestion route','active'],['AD5','Reserved digestion route','planned']] },
  { key: 'biogas_upgrading' as const, title: 'Biogas upgrading', affects: 'Biomethane recovery and utilities', options: [['BG0','No upgrading','active'],['BG1','Conditioning only','active'],['BG2','Baseline upgrading','active'],['BG3','Water scrubbing','active'],['BG4','Membrane separation','active'],['BG5','Amine absorption','active'],['BG6','Reserved upgrading route','planned']] },
  { key: 'nutrient_recovery' as const, title: 'Nutrient recovery', affects: 'P/N/K products and energy demand', options: [['NR0','No targeted recovery','active'],['NR1','Solid-liquid separation','active'],['NR2','Struvite recovery','active'],['NR3','Ammonia capture','active'],['NR4','Integrated P and N recovery','active'],['NR5','Calcium-phosphate recovery','active'],['NR6','Ion-exchange ammonia recovery','active'],['NR7','Integrated P/N/K recovery','active']] },
];

export default function App() {
  const [tab, setTab] = useState<TabId>('overview');
  const [mode, setMode] = useState<CalculationMode>('structural');
  const [month, setMonth] = useState('July');
  const [scenario, setScenario] = useState<ScenarioSelection>(defaults);
  const [parameters, setParameters] = useState<ParameterDefinition[]>(DEFAULT_PARAMETERS);
  const [feed, setFeed] = useState<FeedInputs>({ feedAmountKgh: 500, operatingDaysPerWeek: 7, operatingHoursPerDay: 24, moisturePct: 78, liquidFractionPct: 62, proteinPct: 18, nitrogenPct: 1.1, phosphorusPct: 0.12 });
  const fallbackPreview = useMemo(() => runSimulation({ calculation_mode: mode, selected_month: month, scenarios: scenario }), []);
  const [result, setResult] = useState<SimulationResult>(fallbackPreview);
  const [runtime, setRuntime] = useState<RuntimeSource>('fallback');
  const [runtimeNote, setRuntimeNote] = useState('Preview data — run the Python model to replace it.');
  const [graph, setGraph] = useState<any | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [limitations, setLimitations] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [savedRuns, setSavedRuns] = useState<SavedRun[]>(() => {
    try { return JSON.parse(localStorage.getItem('greenhub.savedRuns') || '[]'); } catch { return []; }
  });
  const [parameterView, setParameterView] = useState<'basic'|'advanced'>('basic');

  useEffect(() => { localStorage.setItem('greenhub.savedRuns', JSON.stringify(savedRuns)); }, [savedRuns]);

  async function executeRun(saveAs?: string) {
    setRunning(true);
    setRuntimeNote('Submitting configuration to the Python backend…');
    try {
      const raw = await runPythonSimulation(buildPythonRequest(mode, month, scenario, feed));
      const envelope = normalizeResult(raw, result);
      const resources = await fetchRunResources(envelope.result.run_id, raw.plots || []);
      const next = {
        ...envelope.result,
        selected_month: month,
        plots: resources.plots.length ? resources.plots : envelope.result.plots,
        annual: resources.annual,
      };
      setResult(next);
      setGraph(resources.graph || raw.graph || null);
      setArtifacts(resources.artifacts);
      setLimitations(envelope.limitations);
      setRuntime('python');
      setRuntimeNote(resources.plots.length ? 'Python run complete — graph, plots and exports loaded.' : 'Python run complete — some optional resources were unavailable.');
      if (saveAs) saveSnapshot(saveAs, next);
      setTab('results');
    } catch (error) {
      const next = runSimulation({
        calculation_mode: mode,
        selected_month: month,
        scenarios: scenario,
        design_overrides: parameters.map(item => ({ parameter_id: item.parameter_id, value: item.current_value })),
      });
      setResult(next);
      setGraph(null);
      setArtifacts([]);
      setLimitations(['The scientific service is unavailable. Preview values are shown so the interface remains usable, but they are not an authoritative run.']);
      setRuntime('fallback');
      setRuntimeNote(error instanceof Error ? `Fallback active: ${error.message}` : 'Fallback adapter active.');
      if (saveAs) saveSnapshot(saveAs, next);
      setTab('results');
    } finally { setRunning(false); }
  }

  function saveSnapshot(label: string, source = result) {
    const snapshot = { label, result: source, scenario: source.scenarios || scenario, savedAt: new Date().toISOString() };
    setSavedRuns(previous => [...previous.filter(item => item.label !== label), snapshot]);
  }

  const activeUnits = result.units.filter(unit => unit.status === 'active').length;
  const changedParameters = parameters.filter(item => item.current_value !== item.default_value);
  const visibleParameters = parameters.filter(item => parameterView === 'advanced' ? item.category === 'advanced' : item.category === 'basic');
  const tabs: [TabId, string, LucideIcon][] = [
    ['overview', 'Overview', Gauge], ['configure', 'Configure', Settings2], ['results', 'Results', BarChart3],
    ['reports', 'Reports', FileDown], ['advanced', 'Advanced', Wrench],
  ];

  return <div className="app-shell">
    <header className="topbar">
      <button className="brand" onClick={() => setTab('overview')} aria-label="Open GreenHub overview">
        <img className="brand-icon" src="/assets/spaak/Spaak%20logo%20icoon%20(1).png" alt=""/>
        <img className="brand-wordmark" src="/assets/spaak/logo-text.svg" alt="Spaak"/>
        <span className="product-name"><strong>GreenHub</strong><small>Process model</small></span>
      </button>
      <div className="top-actions">
        <span className={`model-status ${runtime}`}><CircleDot size={12}/>{runtime === 'python' ? 'Model online' : 'Preview mode'}</span>
        <button className="run-button" onClick={() => executeRun()} disabled={running}><Play size={15}/>{running ? 'Calculating…' : 'Run annual plan'}</button>
      </div>
    </header>
    <div className={`runtime-banner ${runtime}`} role="status">
      <span>{runtime === 'python' ? 'Scientific results connected' : 'Preview values shown'}</span>
      <p>{runtimeNote}</p>
    </div>
    <nav className="primary-nav" aria-label="Application sections">
      {tabs.map(([id,label,Icon]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}><Icon size={16}/>{label}</button>)}
    </nav>
    <main className="workspace">
      {running && <section className="run-progress" role="status" aria-live="polite"><span className="progress-spinner"/><div><strong>Calculating the annual GreenHub plan</strong><p>Processing monthly feed availability, unit performance, products, utilities and balance checks.</p></div></section>}
      {tab === 'overview' && <Overview result={result} activeUnits={activeUnits} runtime={runtime} limitations={limitations} onConfigure={() => setTab('configure')} onResults={() => setTab('results')}/>} 
      {tab === 'configure' && <div className="page-stack">
        <PageIntro eyebrow="Configure" title="Set the process pathway" text="Choose the process route, review the inputs that affect the model, then calculate the annual plan."/>
        <section className="scenario-grid">{scenarioGroups.map(group => <ScenarioCard key={group.key} group={group} value={String(scenario[group.key])} onChange={value => setScenario(current => ({ ...current, [group.key]: value }))}/>)}</section>
        <section className="panel order-panel"><div><span className="eyebrow">Process sequence</span><h3>Nutrient-recovery order</h3><p>Controls the downstream separation sequence where supported.</p></div><select value={scenario.process_order} onChange={event => setScenario(current => ({...current, process_order: event.target.value as any}))}><option value="A">Separation → phosphorus → nitrogen → potassium</option><option value="B">Separation → nitrogen → phosphorus → potassium</option><option value="C">Phosphorus before separation</option><option value="D">Separation only</option></select></section>
        <InputStudio feed={feed} setFeed={setFeed} scenario={scenario} onRun={() => executeRun()}/>
        <ConfigurationReview scenario={scenario} feed={feed} mode={mode} changed={changedParameters.length} onRun={() => executeRun()} running={running}/>
      </div>}
      {tab === 'results' && <div className="page-stack"><PageIntro eyebrow="Results" title="Understand the process outcome" text="Review annual performance first, then follow the pathway and inspect balance quality or detailed model data."/><ResultsWorkbench result={result} graph={graph} artifacts={artifacts} runtime={runtime === 'python' ? 'Scientific model' : 'Preview data'}/>{limitations.length > 0 && <LimitationsPanel items={limitations}/>}</div>}
      {tab === 'reports' && <div className="page-stack"><PageIntro eyebrow="Reports" title="Download and share the run" text="Exports include the run context needed to trace the pathway, assumptions and validation status."/><ReportCenter result={result} artifacts={artifacts} runtime={runtime === 'python' ? 'Scientific model' : 'Preview data'}/></div>}
      {tab === 'advanced' && <div className="page-stack">
        <PageIntro eyebrow="Advanced" title="Evidence, assumptions and technical detail" text="Review model basis, data quality and saved scenario comparisons. Planning-only values are clearly marked and are not applied to scientific runs."/>
        <section className="advanced-grid">
          <div className="panel evidence-panel"><PanelTitle icon={<SlidersHorizontal/>} title="Model basis" text="These settings control which evidence layer and reference period the model uses."/><label><span>Evidence basis</span><select value={mode} onChange={event => setMode(event.target.value as CalculationMode)}><option value="structural">Structural model</option><option value="literature_default">Literature defaults</option><option value="calibrated">Calibrated data</option></select></label><label><span>Reference month</span><select value={month} onChange={event => setMonth(event.target.value)}>{['January','February','March','April','May','June','July','August','September','October','November','December'].map(item => <option key={item}>{item}</option>)}</select></label></div>
          <AdvancedRunDetails result={result} limitations={limitations}/>
        </section>
        <div className="parameter-toolbar"><button className={parameterView === 'basic' ? 'active' : ''} onClick={() => setParameterView('basic')}>Core assumptions</button><button className={parameterView === 'advanced' ? 'active' : ''} onClick={() => setParameterView('advanced')}>Detailed assumptions</button><span>{visibleParameters.length} items</span></div>
        <section className="parameter-layout"><div className="panel parameter-list">{visibleParameters.map(parameter => <ParameterRow key={parameter.parameter_id} parameter={parameter} onChange={value => setParameters(current => current.map(item => item.parameter_id === parameter.parameter_id ? {...item,current_value:value} : item))}/>)}</div><aside className="panel quality-panel"><ShieldCheck size={20}/><h3>Evidence quality</h3>{Object.entries(qualityHelp).map(([key,text]) => <div className="quality-line" key={key}><span className={`quality q-${key}`}>{key}</span><span>{text}</span></div>)}<p>Detailed provenance remains available in the generated run reports.</p></aside></section>
        <Comparison runs={savedRuns} current={result} onSave={saveSnapshot} onClear={() => setSavedRuns([])}/>
      </div>}
    </main>
    <footer><span>Spaak Circular Solutions · GreenHub process model</span><span>{runtime === 'python' ? 'Scientific results connected' : 'Preview mode'}</span></footer>
  </div>;
}

function Overview({ result, activeUnits, runtime, limitations, onConfigure, onResults }: any) {
  const metrics = result.metrics;
  const annual = result.annual;
  const outcomes = annual ? [
    ['Feed processed', annual.feed_processed.value / 1000, 't/year', 'green'],
    ['Protein product', (annual.products.dry_protein_product?.value || 0) / 1000, 't/year', 'green'],
    ['Biomethane', (annual.products.biomethane?.value || 0) / 1000, 't/year', 'blue'],
    ['Electricity', (annual.utilities.electricity?.value || 0) / 1000, 'MWh/year', 'rose'],
    ['Mass closure', annual.balance.overall_closure_pct, '%', annual.balance.passed ? 'green' : 'rose'],
  ] : [
    ['Feed rate', result.balances.mass_in_kgh, 'kg/h', 'green'],
    ['Protein product', metrics.protein_recovered_kgh, 'kg/h', 'green'],
    ['Biomethane', metrics.biomethane_flow_m3h, 'm³/h', 'blue'],
    ['Net power', metrics.net_power_kw, 'kW', 'rose'],
    ['Mass closure', result.balances.mass_closure_pct, '%', 'green'],
  ];
  return <div className="page-stack">
    <section className="overview-head">
      <div><span className="eyebrow">GreenHub process model</span><h1>Annual process plan</h1><p>Configure a route, run the scientific model and review products, utilities and balance quality in one place.</p></div>
      <div className="overview-actions"><button className="run-button" onClick={onConfigure}><Settings2 size={16}/>Configure pathway</button><button className="secondary" onClick={onResults}><Activity size={16}/>View results</button></div>
    </section>
    <section className="kpi-grid">{outcomes.map(([label,value,unit,color]: any[]) => <div className="kpi" key={String(label)}><span>{label}</span><strong className={String(color)}>{Number(value).toLocaleString(undefined,{maximumFractionDigits:1})}</strong><small>{unit}</small></div>)}</section>
    <section className="overview-grid">
      <div className="panel"><PanelTitle icon={<Layers3/>} title="Current process pathway" text={`${activeUnits} active units across ${Object.keys(result.process_areas).length} process areas.`}/><div className="process-strip">{Object.values(result.process_areas).map((area:any,index:number) => <React.Fragment key={area.id}><div className="process-node"><span>{String(index+1).padStart(2,'0')}</span><strong>{areaLabels[area.id] || area.name}</strong><small>{area.units.length} units · {area.limitations.length ? 'review notes' : 'active'}</small></div>{index < Object.keys(result.process_areas).length-1 && <b>→</b>}</React.Fragment>)}</div></div>
      <div className="panel"><PanelTitle icon={runtime === 'python' ? <CheckCircle2/> : <AlertTriangle/>} title={runtime === 'python' ? 'Model connected' : 'Preview mode'} text={runtime === 'python' ? 'Results originate from the Python scientific service.' : 'Run the model before using values for decisions.'}/><div className="trust-list"><span><i className="status-dot active"/>Active simulated</span><span><i className="status-dot planned"/>Planned or data-gated</span><span><i className="status-dot warning"/>Provisional assumption</span></div>{limitations.slice(0,2).map((item:string,index:number) => <p className="compact-warning" key={index}>{item}</p>)}</div>
    </section>
  </div>;
}

function ScenarioCard({ group, value, onChange }: any) {
  const selected = group.options.find((item:any[]) => item[0] === value) || group.options[0];
  return <section className="panel scenario-card"><div className="scenario-heading"><div><span className="eyebrow">{group.title}</span><h3>{selected[1]}</h3></div><span className={`status ${selected[2]}`}>{selected[2]}</span></div><select value={value} onChange={event => onChange(event.target.value)}>{group.options.map((item:any[]) => <option value={item[0]} key={item[0]}>{item[1]}{item[2] === 'planned' ? ' (planned)' : ''}</option>)}</select><p>{group.affects}</p><small>{selected[2] === 'planned' ? 'Data gate incomplete; strict validation will reject this option.' : 'Available in the current scientific model.'}</small></section>;
}

function ConfigurationReview({ scenario, feed, mode, onRun, running }: any) {
  const hours = Math.min(8760, 365 / 7 * feed.operatingDaysPerWeek * feed.operatingHoursPerDay);
  const route = scenarioGroups.map(group => group.options.find(item => item[0] === scenario[group.key])?.[1]).filter(Boolean).join(' · ');
  return <section className="review-panel"><div><span className="eyebrow">Ready to run</span><h3>Annual configuration reviewed</h3><p>{route}</p></div><div className="review-facts"><span><b>{feed.feedAmountKgh.toLocaleString()} kg/h</b>target throughput</span><span><b>{hours.toLocaleString(undefined,{maximumFractionDigits:0})} hours</b>annual schedule</span><span><b>{modeLabels[mode as CalculationMode]}</b>evidence basis</span><span><b>Monthly</b>seasonal calculation</span></div><button className="run-button" onClick={onRun} disabled={running}><Play size={15}/>{running ? 'Calculating…' : 'Run annual plan'}</button></section>;
}

function ParameterRow({ parameter }: { parameter: ParameterDefinition; onChange:(value:number|string|boolean)=>void }) {
  return <div className="parameter-row"><div><strong>{parameter.name}</strong><small>{areaLabels[parameter.process_area]}</small><p>{parameter.description}</p></div><span className={`quality q-${parameter.quality_class}`} title={(qualityHelp as any)[parameter.quality_class]}>{parameter.quality_class}</span><label><input type="number" value={Number(parameter.current_value)} disabled aria-label={`${parameter.name} planning reference`}/><em>{parameter.unit}</em></label><span className="parameter-state">Planning reference · not applied to runs</span></div>;
}

function AdvancedRunDetails({ result, limitations }: { result: SimulationResult; limitations: string[] }) {
  return <section className="panel advanced-run"><PanelTitle icon={<ShieldCheck/>} title="Technical run status" text="Identifiers and validation detail are kept here for traceability."/><dl><div><dt>Run reference</dt><dd className="mono">{result.run_id}</dd></div><div><dt>Scenario codes</dt><dd className="mono">{result.scenarios.feed_front_end} · {result.scenarios.protein_recovery} · {result.scenarios.anaerobic_digestion} · {result.scenarios.biogas_upgrading} · {result.scenarios.nutrient_recovery}</dd></div><div><dt>Residual error</dt><dd>{result.validation.residual_error_kgh.toFixed(4)} kg/h</dd></div><div><dt>Model notes</dt><dd>{limitations.length}</dd></div></dl></section>;
}

function Comparison({ runs, current, onSave, onClear }: any) {
  const rows = runs.length ? runs : [];
  return <section className="comparison-section"><div className="section-heading"><div><span className="eyebrow">Scenario comparison</span><h2>Saved decision cases</h2><p>Snapshots stay in this browser and can be compared before selecting a preferred pathway.</p></div><div className="comparison-actions"><button className="secondary" onClick={() => onSave('Baseline',current)}>Save baseline</button><button className="secondary" onClick={() => onSave(`Candidate ${runs.length+1}`,current)}>Save candidate</button>{rows.length > 0 && <button className="text-button" onClick={onClear}>Clear</button>}</div></div>{rows.length ? <div className="comparison-grid">{rows.map((run:any) => <article className="panel comparison-card" key={run.label}><span className="eyebrow">{run.label}</span><h3>{scenarioGroups.map(group => group.options.find(item => item[0] === run.scenario[group.key])?.[1]).filter(Boolean).slice(0,3).join(' · ')}</h3><small>{new Date(run.savedAt).toLocaleString()}</small><dl><div><dt>Protein</dt><dd>{run.result.metrics.protein_recovered_kgh.toFixed(1)} kg/h</dd></div><div><dt>Biomethane</dt><dd>{run.result.metrics.biomethane_flow_m3h.toFixed(1)} m³/h</dd></div><div><dt>Net power</dt><dd>{run.result.metrics.net_power_kw.toFixed(1)} kW</dd></div><div><dt>Validation</dt><dd>{run.result.validation.status}</dd></div></dl></article>)}</div> : <div className="empty-panel"><GitCompare size={28}/><h3>No saved comparisons yet</h3><p>Run a configuration, then save it as a baseline or candidate.</p></div>}</section>;
}

function LimitationsPanel({items}:{items:string[]}) {
  const visible = items.slice(0,4); const remaining = items.slice(4);
  return <section className="panel limitation-panel"><AlertTriangle size={18}/><div><h3>Assumptions and limitations</h3>{visible.map((item,index)=><p key={index}>{item}</p>)}{remaining.length>0&&<details><summary>Review {remaining.length} additional model notes</summary><div className="limitation-list">{remaining.map((item,index)=><p key={index}>{item}</p>)}</div></details>}</div></section>;
}
function PageIntro({ eyebrow,title,text }: any) { return <header className="page-intro"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{text}</p></header>; }
function PanelTitle({ icon,title,text }: any) { return <div className="panel-title"><span className="title-icon">{icon}</span><div><h3>{title}</h3><p>{text}</p></div></div>; }
