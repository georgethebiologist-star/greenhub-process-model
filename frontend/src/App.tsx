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
import DynamicCompleteDashboard from './components/DynamicCompleteDashboard';
import type { CalculationMode, EmpiricalBiomassSchedule, ParameterDefinition, ScenarioSelection, SimulationResult } from './types';

type RuntimeSource = 'python' | 'fallback';
type TabId = 'overview' | 'configure' | 'results' | 'reports' | 'advanced' | 'dynamic-proxy';
type SavedRun = { label: string; result: SimulationResult; scenario: ScenarioSelection; savedAt: string };
type Artifact = { name: string; type: string; description: string; url?: string; available: boolean; warning?: string };

const defaults: ScenarioSelection = {
  feed_front_end: 'F2', protein_recovery: 'PR3', anaerobic_digestion: 'AD1',
  biogas_upgrading: 'BG2', nutrient_recovery: 'NR4', process_order: 'A',
};
const scheduleDefaults: EmpiricalBiomassSchedule = {
  annual_available_biomass_tonnes: 30000,
  annual_processed_biomass_tonnes: 30000,
  collection_refinery_fraction: 1,
  feed_basis: 'tonnes_per_year',
  feed_kg_per_hr: 1000,
  season_start: '2026-04-15',
  season_end: '2026-11-15',
  peak_date: '2026-07-31',
  spread_days: 55,
  active_months: Array.from({length: 12}, (_, index) => index + 1),
};
const monthLabels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
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
  const [biomassSchedule, setBiomassSchedule] = useState<EmpiricalBiomassSchedule>(scheduleDefaults);
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
      const raw = await runPythonSimulation(buildPythonRequest(mode, month, scenario, feed, biomassSchedule));
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
    ['dynamic-proxy', 'Dynamic proxy', Activity],
  ];

  return <div className="app-shell">
    <header className="topbar">
      <button className="brand" onClick={() => setTab('overview')} aria-label="Open GreenHub overview">
        <img className="brand-icon" src="/assets/spaak/Spaak%20logo%20icoon%20(1).png" alt=""/>
        <img className="brand-wordmark" src="/assets/spaak/logo-text.svg" alt="Spaak"/>
        <span className="product-name"><strong>GreenHub</strong><small>Process model</small></span>
      </button>
      <div className="top-actions">
        <span className={`model-status ${runtime}`}><CircleDot size={12}/>{tab === 'dynamic-proxy' ? 'Unvalidated proxy' : runtime === 'python' ? 'Model online' : 'Preview mode'}</span>
        {tab !== 'dynamic-proxy' && <button className="run-button" onClick={() => executeRun()} disabled={running}><Play size={15}/>{running ? 'Calculating…' : 'Run annual plan'}</button>}
      </div>
    </header>
    {tab !== 'dynamic-proxy' && <div className={`runtime-banner ${runtime}`} role="status">
      <span>{runtime === 'python' ? 'Scientific results connected' : 'Preview values shown'}</span>
      <p>{runtimeNote}</p>
    </div>}
    <nav className="primary-nav" aria-label="Application sections">
      {tabs.map(([id,label,Icon]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}><Icon size={16}/>{label}</button>)}
    </nav>
    <main className="workspace">
      {tab === 'dynamic-proxy' && <DynamicCompleteDashboard/>}
      {tab === 'overview' && <section className="panel proxy-entry"><strong>Explore the complete dynamic proxy</strong><p>30,000 t/year fresh grass · seasonal supply · monthly products · energy and assumption traceability.</p><button className="secondary" onClick={() => setTab('dynamic-proxy')}>Open opt-in proxy dashboard</button></section>}
      {running && <section className="run-progress" role="status" aria-live="polite"><span className="progress-spinner"/><div><strong>Calculating the annual GreenHub plan</strong><p>Processing monthly feed availability, unit performance, products, utilities and balance checks.</p></div></section>}
      {tab === 'overview' && <Overview result={result} activeUnits={activeUnits} runtime={runtime} limitations={limitations} onConfigure={() => setTab('configure')} onResults={() => setTab('results')}/>} 
      {tab === 'configure' && <div className="page-stack">
        <PageIntro eyebrow="Configure" title="Set the process pathway" text="Choose the process route, review the inputs that affect the model, then calculate the annual plan."/>
        <SectionHeading title="Feed schedule" text="Define annual availability and refinery intake. Supply keeps its seasonal shape; lower processing targets create a monthly plateau and explicit unused biomass."/>
        <FeedScheduleControls value={biomassSchedule} onChange={setBiomassSchedule}/>
        <SectionHeading title="Process route" text="Choose one empirical route in each process area. These selections remain independent from the dynamic proxy pathway."/>
        <section className="scenario-grid">{scenarioGroups.map(group => <ScenarioCard key={group.key} group={group} value={String(scenario[group.key])} onChange={value => setScenario(current => ({ ...current, [group.key]: value }))}/>)}</section>
        <section className="panel order-panel"><div><span className="eyebrow">Process sequence</span><h3>Nutrient-recovery order</h3><p>Controls the downstream separation sequence where supported.</p></div><select value={scenario.process_order} onChange={event => setScenario(current => ({...current, process_order: event.target.value as any}))}><option value="A">Separation → phosphorus → nitrogen → potassium</option><option value="B">Separation → nitrogen → phosphorus → potassium</option><option value="C">Phosphorus before separation</option><option value="D">Separation only</option></select></section>
        <InputStudio feed={feed} setFeed={setFeed} scenario={scenario} onRun={() => executeRun()}/>
        <SectionHeading title="Evidence / model mode" text="The evidence basis changes parameter resolution. The reference month remains visible because empirical composition is month-specific."/>
        <section className="panel configure-evidence"><label><span>Evidence basis</span><select value={mode} onChange={event => setMode(event.target.value as CalculationMode)}><option value="structural">Structural model</option><option value="literature_default">Literature defaults</option><option value="calibrated">Calibrated data</option></select><small>Controls which eligible evidence layer supplies empirical parameters.</small></label><label><span>Reference composition month</span><select value={month} onChange={event => setMonth(event.target.value)}>{['January','February','March','April','May','June','July','August','September','October','November','December'].map(item => <option key={item}>{item}</option>)}</select><small>Used where a route requires one representative monthly composition.</small></label><div><span>Model status</span><strong>Empirical scientific pathway</strong><small>Dynamic proxy assumptions are not imported into this run.</small></div></section>
        <section className="panel advanced-link"><div><span className="eyebrow">Advanced parameters</span><h3>{changedParameters.length ? `${changedParameters.length} reviewed values differ from defaults` : 'Review evidence and technical parameters'}</h3><p>Detailed assumptions remain separate from the primary operating-scale controls.</p></div><button className="secondary" onClick={() => setTab('advanced')}>Open advanced parameters</button></section>
        <ConfigurationReview scenario={scenario} schedule={biomassSchedule} mode={mode} onRun={() => executeRun()} running={running}/>
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
    <footer><span>Spaak Circular Solutions · GreenHub process model</span><span>{tab === 'dynamic-proxy' ? 'Opt-in proxy · not validated' : runtime === 'python' ? 'Scientific results connected' : 'Preview mode'}</span></footer>
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
    {annual?.biomass_schedule&&<section className="panel"><PanelTitle icon={<Gauge/>} title="Annual biomass schedule" text="The empirical plan uses the same seasonal availability and monthly cap policy as the dynamic dashboard, without sharing process calculations."/><div className="schedule-facts"><div><span>Available</span><strong>{annual.biomass_schedule.annual_available_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Processed</span><strong>{annual.biomass_schedule.annual_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Unused</span><strong>{annual.biomass_schedule.annual_unused_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Utilization</span><strong>{(annual.biomass_schedule.utilization_fraction*100).toFixed(1)}%</strong></div><div><span>Peak month</span><strong>{annual.biomass_schedule.peak_month_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t</strong></div></div></section>}
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

function FeedScheduleControls({value,onChange}:{value:EmpiricalBiomassSchedule;onChange:React.Dispatch<React.SetStateAction<EmpiricalBiomassSchedule>>}) {
  const update = <K extends keyof EmpiricalBiomassSchedule>(key:K, next:EmpiricalBiomassSchedule[K]) => onChange(current => ({...current,[key]:next}));
  return <section className="panel empirical-schedule"><div className="schedule-primary">
    <label>Annual available biomass <span><input type="number" min="0" step="100" value={value.annual_available_biomass_tonnes} onChange={event=>update('annual_available_biomass_tonnes',+event.target.value)}/><em>t/year</em></span><small>Fresh biomass available before collection and refinery limits.</small></label>
    <label>Annual processed target <span><input type="number" min="0" step="100" value={value.annual_processed_biomass_tonnes} onChange={event=>update('annual_processed_biomass_tonnes',+event.target.value)}/><em>t/year</em></span><small>Lower targets cap monthly intake rather than rescaling availability.</small></label>
    <label>Collection / refinery fraction <span><input type="number" min="0" max="100" step="1" value={value.collection_refinery_fraction*100} onChange={event=>update('collection_refinery_fraction',+event.target.value/100)}/><em>%</em></span><small>Maximum share of annual availability entering the refinery plan.</small></label>
    <label>Capacity basis <select value={value.feed_basis} onChange={event=>update('feed_basis',event.target.value as EmpiricalBiomassSchedule['feed_basis'])}><option value="tonnes_per_year">Annual processed target</option><option value="kg_per_hr">Hourly capacity plus annual target</option></select><small>Hourly mode adds an operating-capacity ceiling.</small></label>
    {value.feed_basis==='kg_per_hr'&&<label>Hourly processing capacity <span><input type="number" min="0" step="100" value={value.feed_kg_per_hr} onChange={event=>update('feed_kg_per_hr',+event.target.value)}/><em>kg/h</em></span><small>True instantaneous capacity used during active schedule hours.</small></label>}
  </div><details><summary>Season shape and active months</summary><div className="schedule-primary compact">
    <label>Season start<input type="date" value={value.season_start} onChange={event=>update('season_start',event.target.value)}/></label>
    <label>Season end<input type="date" value={value.season_end} onChange={event=>update('season_end',event.target.value)}/></label>
    <label>Peak date<input type="date" value={value.peak_date} onChange={event=>update('peak_date',event.target.value)}/></label>
    <label>Spread <span><input type="number" min="1" max="366" value={value.spread_days} onChange={event=>update('spread_days',+event.target.value)}/><em>days</em></span></label>
  </div><div className="month-selector">{monthLabels.map((label,index)=><label key={label}><input type="checkbox" checked={value.active_months.includes(index+1)} onChange={event=>update('active_months',event.target.checked?[...value.active_months,index+1].sort((a,b)=>a-b):value.active_months.filter(month=>month!==index+1))}/>{label}</label>)}</div></details>
  <div className="schedule-note"><strong>Default operating scale</strong><span>30,000 t/year · mid-April to mid-November · peak 31 July · 55-day spread</span></div></section>;
}

function ConfigurationReview({ scenario, schedule, mode, onRun, running }: any) {
  const route = scenarioGroups.map(group => group.options.find(item => item[0] === scenario[group.key])?.[1]).filter(Boolean).join(' · ');
  return <section className="review-panel"><div><span className="eyebrow">Ready to run</span><h3>Annual configuration reviewed</h3><p>{route}</p></div><div className="review-facts"><span><b>{schedule.annual_processed_biomass_tonnes.toLocaleString()} t/year</b>processed target</span><span><b>{(schedule.collection_refinery_fraction*100).toFixed(0)}%</b>collection / refinery</span><span><b>{modeLabels[mode as CalculationMode]}</b>evidence basis</span><span><b>{schedule.season_start.slice(5)} → {schedule.season_end.slice(5)}</b>season window</span></div><button className="run-button" onClick={onRun} disabled={running}><Play size={15}/>{running ? 'Calculating…' : 'Run annual plan'}</button></section>;
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
function SectionHeading({title,text}:{title:string;text:string}) { return <header className="configure-section-heading"><span>{title}</span><p>{text}</p></header>; }
function PanelTitle({ icon,title,text }: any) { return <div className="panel-title"><span className="title-icon">{icon}</span><div><h3>{title}</h3><p>{text}</p></div></div>; }
