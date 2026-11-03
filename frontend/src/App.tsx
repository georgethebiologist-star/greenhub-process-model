import React, { useEffect, useMemo, useRef, useState } from 'react';
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
import { DEFAULT_PARAMETERS } from './data/greenhubData';
import { buildPythonRequest, fetchRunResources, runPythonSimulation } from './data/apiClient';
import { cloneEmpiricalBaseline, PREVIEW_BASELINE_STATUS } from './data/baselineFixtures';
import { normalizeResult } from './data/normalizeResult';
import { ReportCenter, ResultsWorkbench } from './components/ResultsWorkbench';
import { InputStudio, type FeedInputs } from './components/InputStudio';
import BaselineTimeSeries from './components/BaselineTimeSeries';
import ModelComparisonPanel from './components/ModelComparisonPanel';
import {decisionApi, type DecisionReport} from './data/decisionSupport';
import DynamicCompleteDashboard from './components/DynamicCompleteDashboard';
import AnalyticsPreview from './components/AnalyticsPreview';
import ParetoScreening from './components/ParetoScreening';
import BiostimulantScreen from './components/BiostimulantScreen';
import type { CalculationMode, EmpiricalBiomassSchedule, ParameterDefinition, ResultSourceState, ScenarioSelection, SimulationResult } from './types';

type RuntimeSource = 'python' | 'fallback';
type TabId = 'dashboard' | 'configure' | 'explore' | 'reports' | 'advanced' | 'dynamic-proxy' | 'model-comparison';
type ExploreView = 'performance' | 'hotspots' | 'optimization' | 'model-comparison';
type SavedRun = { label: string; result: SimulationResult; scenario: ScenarioSelection; savedAt: string };
type Artifact = { name: string; type: string; description: string; url?: string; available: boolean; warning?: string };

const defaults: ScenarioSelection = {
  feed_front_end: 'F1', protein_recovery: 'PR3', anaerobic_digestion: 'AD1',
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
  { key: 'feed_front_end' as const, title: 'Feed preparation', affects: 'Liquid yield and solids split', options: [['F0','Measured liquid fraction','active'],['F1','Roadside grass without PEF','active']] },
  { key: 'protein_recovery' as const, title: 'Protein recovery', affects: 'Protein yield and downstream COD', options: [['PR0','Bypass protein recovery','active'],['PR1','Acid precipitation','active'],['PR2','Heat coagulation','active'],['PR3','Combined acid and heat','active'],['PR4','Lactic fermentation','planned'],['PR5','CO₂-assisted precipitation','planned'],['PR6','Ultrafiltration','planned'],['PR7','Biostimulant membrane recovery (clarified juice; no pre-fermentation)','configurable']] },
  { key: 'anaerobic_digestion' as const, title: 'Anaerobic digestion', affects: 'Biogas production and digestate', options: [['AD0','No digestion','active'],['AD1','Baseline digestion','active'],['AD2','Protein-rich liquid route','active'],['AD3','Alternative AD configuration','active'],['AD4','Advanced digestion route','active'],['AD5','Reserved digestion route','planned']] },
  { key: 'biogas_upgrading' as const, title: 'Biogas upgrading', affects: 'Biomethane recovery and utilities', options: [['BG0','No upgrading','active'],['BG1','Conditioning only','active'],['BG2','Baseline upgrading','active'],['BG3','Water scrubbing','active'],['BG4','Membrane separation','active'],['BG5','Amine absorption','active'],['BG6','Reserved upgrading route','planned']] },
  { key: 'nutrient_recovery' as const, title: 'Nutrient recovery', affects: 'P/N/K products and energy demand', options: [['NR0','No targeted recovery','active'],['NR1','Solid-liquid separation','active'],['NR2','Struvite recovery','active'],['NR3','Ammonia capture','active'],['NR4','Integrated P and N recovery','active'],['NR5','Calcium-phosphate recovery','active'],['NR6','Ion-exchange ammonia recovery','active'],['NR7','Integrated P/N/K recovery','active']] },
];

export default function App() {
  const [tab, setTab] = useState<TabId>(window.location.hash==='#decision-support'?'explore':'dashboard');
  const [exploreView, setExploreView] = useState<ExploreView>('optimization');
  const [mode, setMode] = useState<CalculationMode>('structural');
  const [month, setMonth] = useState('July');
  const [scenario, setScenario] = useState<ScenarioSelection>(defaults);
  const [biostimulantRoute, setBiostimulantRoute] = useState({technology_id:'TUF',flux_method:'empirical',flux_L_m2_h:22,flux_source:'User-supplied GreenHub membrane dataset: TUF baseline flux 22 L/(m²·h).',feed_to_reference_concentration_ratio:'',flux_model_source:'',viscosity_Pa_s:'',viscosity_source:'',retention_matrix_source:'User-supplied GreenHub component co-retention matrix and hormone retention dataset.',component_retention_overrides:'{}',component_retention_override_sources:'{}',use_hormone_benchmarks:false,hormone_benchmark_source:'',transmembrane_pressure_bar:'',pressure_source:'',pump_efficiency_fraction:'',pump_efficiency_source:'',crossflow_electricity_kwh_m3_feed:'',crossflow_electricity_source:'',cip_solution_volume_L_per_step:'',cip_makeup_fraction_per_cycle:'',cip_input_source:''});
  const [pr7PriceLevel, setPr7PriceLevel] = useState<'off'|'low'|'nominal'|'high'>('off');
  const [parameters, setParameters] = useState<ParameterDefinition[]>(DEFAULT_PARAMETERS);
  const [feed, setFeed] = useState<FeedInputs>({ feedAmountKgh: 500, operatingDaysPerWeek: 7, operatingHoursPerDay: 24, moisturePct: 78, liquidFractionPct: 62, proteinPct: 18, nitrogenPct: 1.1, phosphorusPct: 0.12 });
  const [biomassSchedule, setBiomassSchedule] = useState<EmpiricalBiomassSchedule>(scheduleDefaults);
  const [storageConditions, setStorageConditions] = useState({enabled:false,storageDays:0,aerobicFraction:0,temperatureC:20,moistureActivity:1});
  const fallbackPreview = useMemo(() => cloneEmpiricalBaseline(), []);
  const [result, setResult] = useState<SimulationResult>(fallbackPreview);
  const [empiricalComparison, setEmpiricalComparison] = useState<SimulationResult|null>(null);
  const [comparisonRunning, setComparisonRunning] = useState(false);
  const [comparisonError, setComparisonError] = useState('');
  const [analysisReport, setAnalysisReport] = useState<DecisionReport|null>(null);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [runContext, setRunContext] = useState<Record<string,unknown>|null>(null);
  const analysisRequest = useRef(0);
  const [runtime, setRuntime] = useState<RuntimeSource>('fallback');
  const [sourceState, setSourceState] = useState<ResultSourceState>(PREVIEW_BASELINE_STATUS);
  const [graph, setGraph] = useState<any | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [limitations, setLimitations] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [savedRuns, setSavedRuns] = useState<SavedRun[]>(() => {
    try { return JSON.parse(localStorage.getItem('greenhub.savedRuns') || '[]'); } catch { return []; }
  });
  const [parameterView, setParameterView] = useState<'basic'|'advanced'>('basic');
  const autoRunStarted = useRef(false);

  useEffect(() => { localStorage.setItem('greenhub.savedRuns', JSON.stringify(savedRuns)); }, [savedRuns]);

  async function executeRun(saveAs?: string, navigateToResults = true) {
    const requestNumber=++analysisRequest.current;
    setRunning(true);
    setAnalysisBusy(true); setAnalysisError(''); setAnalysisReport(null);
    setSourceState(current => ({...current,label:'Connecting to Python',detail:'Submitting the annual configuration and requesting its reporting bundle.'}));
    try {
      const storage = storageConditions.enabled?{model:'grass_reactions',storage_days:storageConditions.storageDays,aerobic_fraction:storageConditions.aerobicFraction,temperature_c:storageConditions.temperatureC,moisture_activity:storageConditions.moistureActivity,allow_assumptions:true}:null;
      const pr7 = scenario.protein_recovery === 'PR7';
      const processRequest=buildPythonRequest(mode, month, scenario, feed, biomassSchedule, 'quasi_dynamic', pr7 ? null : storage);
      if (pr7) {
        // PR7 deliberately preserves uncovered liquid pools in a separate outlet.
        // Return the diagnostic result and its failed completeness validation so
        // users can inspect the known balances while retaining the unresolved-data gate.
        processRequest.strict_validation = false;
        if (biomassSchedule.feed_basis === 'kg_per_hr') processRequest.plant_capacity_kg_hr = biomassSchedule.feed_kg_per_hr;
        const overrides = JSON.parse(biostimulantRoute.component_retention_overrides || '{}');
        const sources = JSON.parse(biostimulantRoute.component_retention_override_sources || '{}');
        if (!overrides || Array.isArray(overrides) || typeof overrides !== 'object' || !sources || Array.isArray(sources) || typeof sources !== 'object') throw new Error('PR7 retention fractions and evidence notes must be JSON objects.');
        processRequest.biostimulant_route = {
          technology_id: biostimulantRoute.technology_id,
          retention_matrix_source: biostimulantRoute.retention_matrix_source,
          component_retention_overrides: Object.fromEntries(Object.entries(overrides).map(([key,value])=>[key,Number(value)])),
          component_retention_override_sources: sources,
          use_hormone_benchmarks:biostimulantRoute.use_hormone_benchmarks,
          ...(biostimulantRoute.use_hormone_benchmarks?{hormone_benchmark_source:biostimulantRoute.hormone_benchmark_source}:{}),
        };
        const hasCipVolume = biostimulantRoute.cip_solution_volume_L_per_step !== '';
        const hasCipMakeup = biostimulantRoute.cip_makeup_fraction_per_cycle !== '';
        if (hasCipVolume !== hasCipMakeup) throw new Error('CIP reagent screening requires both solution volume and make-up fraction.');
        if (hasCipVolume && (!biostimulantRoute.cip_input_source.trim() || !(Number(biostimulantRoute.cip_solution_volume_L_per_step)>0) || !(Number(biostimulantRoute.cip_makeup_fraction_per_cycle)>=0 && Number(biostimulantRoute.cip_makeup_fraction_per_cycle)<=1))) throw new Error('CIP reagent screening requires positive solution volume, make-up fraction in [0, 1], and an evidence note.');
        if (!hasCipVolume && biostimulantRoute.cip_input_source.trim()) throw new Error('CIP evidence note requires both CIP calculation inputs.');
        if (hasCipVolume) Object.assign(processRequest.biostimulant_route,{
          cip_solution_volume_L_per_step:Number(biostimulantRoute.cip_solution_volume_L_per_step),
          cip_makeup_fraction_per_cycle:Number(biostimulantRoute.cip_makeup_fraction_per_cycle),
          cip_input_source:biostimulantRoute.cip_input_source,
        });
        if (biostimulantRoute.use_hormone_benchmarks && !biostimulantRoute.hormone_benchmark_source.trim()) throw new Error('Benchmark hormone feed requires a source/evidence note.');
        if (biostimulantRoute.flux_method==='resistance_model') {
          if (biostimulantRoute.feed_to_reference_concentration_ratio==='' || biostimulantRoute.transmembrane_pressure_bar==='' || biostimulantRoute.viscosity_Pa_s==='' || !biostimulantRoute.viscosity_source.trim() || !biostimulantRoute.flux_model_source.trim() || !biostimulantRoute.pressure_source.trim()) throw new Error('Resistance-model flux requires TMP, Cf/C0, an unfermented-juice viscosity, and evidence notes for each.');
          Object.assign(processRequest.biostimulant_route,{
            feed_to_reference_concentration_ratio:Number(biostimulantRoute.feed_to_reference_concentration_ratio),
            flux_model_source:biostimulantRoute.flux_model_source,
            viscosity_Pa_s:Number(biostimulantRoute.viscosity_Pa_s),
            viscosity_source:biostimulantRoute.viscosity_source,
            transmembrane_pressure_bar:Number(biostimulantRoute.transmembrane_pressure_bar),
            pressure_source:biostimulantRoute.pressure_source,
          });
        } else {
          if (!(Number(biostimulantRoute.flux_L_m2_h)>0) || !biostimulantRoute.flux_source.trim()) throw new Error('Empirical flux requires a positive value and a source note.');
          Object.assign(processRequest.biostimulant_route,{flux_L_m2_h:Number(biostimulantRoute.flux_L_m2_h),flux_source:biostimulantRoute.flux_source});
        }
        const hasPressure = biostimulantRoute.transmembrane_pressure_bar!=='';
        const hasEfficiency = biostimulantRoute.pump_efficiency_fraction!=='';
        if (hasPressure && !biostimulantRoute.pressure_source.trim()) throw new Error('TMP requires a source note.');
        if (hasEfficiency && (!hasPressure || !biostimulantRoute.pump_efficiency_source.trim())) throw new Error('Pressure-work electricity requires TMP and a pump-efficiency source note.');
        if (hasPressure) Object.assign(processRequest.biostimulant_route,{
          transmembrane_pressure_bar:Number(biostimulantRoute.transmembrane_pressure_bar),
          pressure_source:biostimulantRoute.pressure_source,
        });
        if (hasEfficiency) Object.assign(processRequest.biostimulant_route,{
          pump_efficiency_fraction:Number(biostimulantRoute.pump_efficiency_fraction),
          pump_efficiency_source:biostimulantRoute.pump_efficiency_source,
        });
        const hasCrossflowEnergy = biostimulantRoute.crossflow_electricity_kwh_m3_feed!=='';
        if (hasCrossflowEnergy && (!(Number(biostimulantRoute.crossflow_electricity_kwh_m3_feed)>=0) || !biostimulantRoute.crossflow_electricity_source.trim())) throw new Error('Crossflow electricity requires a non-negative specific demand and source/evidence note.');
        if (!hasCrossflowEnergy && biostimulantRoute.crossflow_electricity_source.trim()) throw new Error('Crossflow electricity source requires a specific electricity value.');
        if (hasCrossflowEnergy) Object.assign(processRequest.biostimulant_route,{
          crossflow_electricity_kwh_m3_feed:Number(biostimulantRoute.crossflow_electricity_kwh_m3_feed),
          crossflow_electricity_source:biostimulantRoute.crossflow_electricity_source,
        });
      }
      const raw = await runPythonSimulation(processRequest);
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
      setSourceState({status:'live_python',label:pr7?'Live seasonal PR7 result':'Live quasi-dynamic result',detail:pr7?'Monthly clarified-juice membrane runs use the seasonal biomass schedule; the 14-day pre-membrane fermentation/storage step is excluded, while downstream digestion follows the separate AD selection.':'Monthly feed and process timesteps were calculated; optional plots were unavailable.',is_live:true});
      setRunContext({model:'quasi_dynamic',calculation_mode:mode,reference_month:month,process_request:processRequest});
      if (saveAs) saveSnapshot(saveAs, next);
      if (navigateToResults) { setTab('explore'); setExploreView('performance'); }
      void (async()=>{try {
        const options=await decisionApi<any>('options');
        const configuration=structuredClone(options.defaults);
        configuration.simulation=processRequest;
        const screeningProductIds=Object.keys(options.screening_tea_product_prices||{}).filter(id=>id!=='biostimulant_product');
        const bioPrice=options.screening_tea_product_prices?.biostimulant_product;
        const bioRange=options.screening_tea_product_price_ranges?.biostimulant_product;
        const selectedBioPrice=pr7&&pr7PriceLevel!=='off'&&bioPrice&&bioRange?{
          biostimulant_product:{...bioPrice,value_eur_per_unit:bioRange[pr7PriceLevel==='low'?'low_eur_per_unit':pr7PriceLevel==='high'?'high_eur_per_unit':'base_eur_per_unit']}
        }:{};
        configuration.financial_assumptions={...configuration.financial_assumptions,use_screening_price_benchmarks:true,screening_product_ids:screeningProductIds,product_prices:{...(configuration.financial_assumptions?.product_prices||{}),...selectedBioPrice}};
        configuration.tea={...configuration.tea,staffing_people:5,paid_hours_per_person:1500,screening_estimates:true};
        const report=await decisionApi<DecisionReport>('evaluate',{configuration});
        if(requestNumber===analysisRequest.current)setAnalysisReport(report);
      } catch(error) {
        if(requestNumber===analysisRequest.current)setAnalysisError(error instanceof Error?error.message:'Post-route TEA/LCA calculation was unavailable.');
      } finally {if(requestNumber===analysisRequest.current)setAnalysisBusy(false);}})();
    } catch (error) {
      if(requestNumber===analysisRequest.current)setAnalysisBusy(false);
      const next = cloneEmpiricalBaseline();
      setResult(next);
      setGraph(null);
      setArtifacts([]);
      setLimitations(['The scientific service is unavailable. Preview values are shown so the interface remains usable, but they are not an authoritative run.']);
      setRuntime('fallback');
      setRunContext(null);
      setSourceState({status:'backend_unavailable',label:'Backend unavailable · preview baseline',detail:error instanceof Error ? error.message : 'The live service could not be reached.',is_live:false,fixture_version:PREVIEW_BASELINE_STATUS.fixture_version});
      if (saveAs) saveSnapshot(saveAs, next);
      if (navigateToResults) { setTab('explore'); setExploreView('performance'); }
    } finally { setRunning(false); }
  }

  async function runEmpiricalComparison() {
    if (runtime !== 'python') return;
    setComparisonRunning(true); setComparisonError('');
    try {
      const raw = await runPythonSimulation(buildPythonRequest(mode, month, scenario, feed, biomassSchedule, 'steady_state'));
      const envelope = normalizeResult(raw, result);
      const resources = await fetchRunResources(envelope.result.run_id, raw.plots || []);
      setEmpiricalComparison({...envelope.result, annual:resources.annual, plots:resources.plots.length?resources.plots:envelope.result.plots});
    } catch (error) {
      setComparisonError(error instanceof Error?error.message:'The empirical comparison run failed.');
    } finally { setComparisonRunning(false); }
  }

  useEffect(() => {
    if (autoRunStarted.current) return;
    autoRunStarted.current = true;
    void executeRun(undefined, false);
  }, []);

  function saveSnapshot(label: string, source = result) {
    const snapshot = { label, result: source, scenario: source.scenarios || scenario, savedAt: new Date().toISOString() };
    setSavedRuns(previous => [...previous.filter(item => item.label !== label), snapshot]);
  }

  const activeUnits = result.units.filter(unit => unit.status === 'active').length;
  const changedParameters = parameters.filter(item => item.current_value !== item.default_value);
  const visibleParameters = parameters.filter(item => parameterView === 'advanced' ? item.category === 'advanced' : item.category === 'basic');
  const tabs: [TabId, string, LucideIcon][] = [
    ['dashboard', 'Dashboard', Gauge], ['configure', 'Configure', Settings2], ['explore', 'Explore', BarChart3],
    ['reports', 'Reports', FileDown],
  ];

  return <div className="app-shell">
    <header className="topbar">
      <button className="brand" onClick={() => setTab('dashboard')} aria-label="Open GreenHub dashboard">
        <img className="brand-icon" src="/assets/spaak/Spaak%20logo%20icoon%20(1).png" alt=""/>
        <img className="brand-wordmark" src="/assets/spaak/logo-text.svg" alt="Spaak"/>
        <span className="product-name"><strong>GreenHub</strong><small>Process model</small></span>
      </button>
      <div className="top-actions">
        <span className={`model-status ${runtime}`}><CircleDot size={12}/>{sourceState.label}</span>
        <button className="secondary settings-menu" onClick={() => setTab('advanced')}><Wrench size={14}/>Model settings</button>
        <button className="run-button" onClick={() => executeRun()} disabled={running}><Play size={15}/>{running ? 'Calculating…' : 'Run simulation'}</button>
      </div>
    </header>
    <div className={`runtime-banner ${runtime} source-${sourceState.status}`} role="status">
      <span>{sourceState.label}</span>
      <p>{sourceState.detail}{sourceState.fixture_version ? ` Fixture: ${sourceState.fixture_version}.` : ''}</p>
    </div>
    <div className="scenario-context" aria-label="Active scenario summary"><strong>{scenario.protein_recovery==='PR7'?'Selected route':'Baseline'}</strong><span>{result.annual?.biomass_schedule?.annual_processed_tonnes?.toLocaleString(undefined,{maximumFractionDigits:0})||'—'} t/year processed</span><span>{[scenario.feed_front_end,scenario.protein_recovery,scenario.anaerobic_digestion,scenario.biogas_upgrading,scenario.nutrient_recovery].map(id=>scenarioGroups.flatMap(group=>group.options).find(option=>option[0]===id)?.[1]||id).join(' · ')}</span><span>{result.annual?.period?.start_date||'Steady-state'} – {result.annual?.period?.end_date||''}</span></div>
    <nav className="primary-nav" aria-label="Application sections">
      {tabs.map(([id,label,Icon]) => <button key={id} className={tab === id || (id==='explore' && (tab==='model-comparison')) ? 'active' : ''} onClick={() => setTab(id)}><Icon size={16}/>{label}</button>)}
    </nav>
    <main className="workspace">
      {running && <section className="run-progress" role="status" aria-live="polite"><span className="progress-spinner"/><div><strong>Calculating the annual GreenHub plan</strong><p>Processing monthly feed availability, unit performance, products, utilities and balance checks.</p></div></section>}
      {tab === 'dashboard' && <><Overview result={result} activeUnits={activeUnits} runtime={runtime} limitations={limitations} analysis={analysisReport} analysisBusy={analysisBusy} analysisError={analysisError} onConfigure={() => setTab('configure')} onResults={() => {setTab('explore');setExploreView('performance');}}/><ResultsWorkbench result={result} graph={graph} artifacts={artifacts} runtime={runtime === 'python' ? (result.resolution_mode==='steady_state'?'Steady-state process model':'Quasi-dynamic process model') : 'Preview baseline'} sourceState={sourceState} savedRuns={savedRuns} onSaveRun={saveSnapshot} initialView="pathway"/></>}
      {tab === 'configure' && <div className="page-stack">
        <PageIntro eyebrow="Configure" title="Set the process pathway" text="Choose the process route, review the inputs that affect the model, then calculate the annual plan."/>
        <SectionHeading title="Feed schedule" text="Define annual availability and refinery intake. Supply keeps its seasonal shape; lower processing targets create a monthly plateau and explicit unused biomass."/>
        <FeedScheduleControls value={biomassSchedule} onChange={setBiomassSchedule}/>
        <section className="panel storage-controls">
          {scenario.protein_recovery==='PR7' ? <p className="method-note">Pre-membrane storage degradation is excluded from PR7, which starts with clarified juice and has no fermentation step.</p> : <>
            <label className="storage-toggle"><input type="checkbox" checked={storageConditions.enabled} onChange={event=>setStorageConditions(current=>({...current,enabled:event.target.checked}))}/><span><strong>Include storage degradation</strong><small>Optional; uses the available grass-reaction subset and reports its assumptions and blockers.</small></span></label>
            {storageConditions.enabled&&<div className="ds-controls"><label>Upstream storage residence (days)<input type="number" min="0" max="366" value={storageConditions.storageDays} onChange={event=>setStorageConditions(current=>({...current,storageDays:Number(event.target.value)}))}/></label><label>Aerobic exposure fraction<input type="number" min="0" max="1" step="0.05" value={storageConditions.aerobicFraction} onChange={event=>setStorageConditions(current=>({...current,aerobicFraction:Number(event.target.value)}))}/><small>Fraction of residence time exposed to air.</small></label><label>Storage temperature (°C)<input type="number" min="-20" max="60" value={storageConditions.temperatureC} onChange={event=>setStorageConditions(current=>({...current,temperatureC:Number(event.target.value)}))}/></label><label>Moisture activity<input type="number" min="0" max="1" step="0.05" value={storageConditions.moistureActivity} onChange={event=>setStorageConditions(current=>({...current,moistureActivity:Number(event.target.value)}))}/></label></div>}
          </>}
        </section>
        <SectionHeading title="Process route" text="Choose supported technology routes. Scenario IDs remain internal to the model."/>
        <section className="scenario-grid">{scenarioGroups.map(group => <ScenarioCard key={group.key} group={group} value={String(scenario[group.key])} onChange={value => setScenario(current => ({ ...current, [group.key]: value }))}/>)}</section>
        {scenario.protein_recovery==='PR7'&&<section className="panel">
          <PanelTitle icon={<Activity/>} title="PR7 membrane inputs" text="PR7 runs monthly on clarified juice across the seasonal feed schedule, without fermentation or storage. Select the supplied empirical flux or calculate flux from the resistance equation; uncovered component retentions remain evidence-gated. Diagnostic results can return with unresolved pools kept separate and completeness validation marked failed."/>
          <div className="ds-controls">
            <label>Membrane<select value={biostimulantRoute.technology_id} onChange={event=>setBiostimulantRoute(current=>({...current,technology_id:event.target.value,flux_method:event.target.value==='MEUF'?'empirical':current.flux_method,flux_L_m2_h:event.target.value==='LNF'?12:event.target.value==='MEUF'?22.5:22,flux_source:`User-supplied GreenHub membrane dataset: ${event.target.value} baseline flux selection.`}))}><option value="TUF">Tight UF (TUF)</option><option value="LNF">Loose NF (LNF)</option><option value="MEUF">Micellar-enhanced UF (MEUF)</option></select></label>
            {biostimulantRoute.technology_id==='MEUF'&&<small>MEUF SDS dose (8 mmol/L CMC at 1.2–1.5×) and 94.5% recovery are screened separately. SDS and acid-loop mass are not in the BioSTEAM balance; bulk SDS price and recovery energy remain unpriced.</small>}
            <label>Flux method<select value={biostimulantRoute.flux_method} onChange={event=>setBiostimulantRoute(current=>({...current,flux_method:event.target.value}))}><option value="empirical">Empirical screening flux</option><option value="resistance_model" disabled={biostimulantRoute.technology_id==='MEUF'}>Resistance model (TUF/LNF)</option></select></label>
            {biostimulantRoute.flux_method==='empirical'&&<><label>Permeate flux <span><input type="number" min="0.001" step="any" value={biostimulantRoute.flux_L_m2_h} onChange={event=>setBiostimulantRoute(current=>({...current,flux_L_m2_h:Number(event.target.value),flux_source:''}))}/><em>L/(m²·h)</em></span></label><label>Flux evidence note<input value={biostimulantRoute.flux_source} onChange={event=>setBiostimulantRoute(current=>({...current,flux_source:event.target.value}))}/></label></>}
            {biostimulantRoute.flux_method==='resistance_model'&&<><label>Feed/reference concentration ratio <span><input type="number" min="0.000001" step="any" value={biostimulantRoute.feed_to_reference_concentration_ratio} onChange={event=>setBiostimulantRoute(current=>({...current,feed_to_reference_concentration_ratio:event.target.value}))}/><em>Cf/C0</em></span></label><label>Ratio evidence note<input value={biostimulantRoute.flux_model_source} onChange={event=>setBiostimulantRoute(current=>({...current,flux_model_source:event.target.value}))}/></label><label>Unfermented juice viscosity <span><input type="number" min="0.000000001" step="any" value={biostimulantRoute.viscosity_Pa_s} onChange={event=>setBiostimulantRoute(current=>({...current,viscosity_Pa_s:event.target.value}))}/><em>Pa·s</em></span></label><label>Viscosity evidence note<input value={biostimulantRoute.viscosity_source} onChange={event=>setBiostimulantRoute(current=>({...current,viscosity_source:event.target.value}))}/></label><small>The supplied 1.35 mPa·s refers to fermented juice and is not used. Enter a measured viscosity for this no-fermentation feed; TMP and Cf/C0 also need evidence notes.</small></>}
            <label>Retention matrix evidence note<input value={biostimulantRoute.retention_matrix_source} onChange={event=>setBiostimulantRoute(current=>({...current,retention_matrix_source:event.target.value}))}/></label>
            <label className="storage-toggle"><input type="checkbox" checked={biostimulantRoute.use_hormone_benchmarks} onChange={event=>setBiostimulantRoute(current=>({...current,use_hormone_benchmarks:event.target.checked,hormone_benchmark_source:event.target.checked?'User-supplied clarified-juice hormone benchmark dataset; screening proxy, not GreenHub measurement.':''}))}/><span><strong>Include benchmark hormone pools</strong><small>Optional sensitivity input using user-supplied concentrations and fractions. The supplied free/bound split is discussed for a 14-day anaerobic state and is unvalidated for this no-fermentation PR7 feed.</small></span></label>
            {biostimulantRoute.use_hormone_benchmarks&&<label>Benchmark source / evidence note<input value={biostimulantRoute.hormone_benchmark_source} onChange={event=>setBiostimulantRoute(current=>({...current,hormone_benchmark_source:event.target.value}))}/><small>These values and fractions are not measured GreenHub feed results; the free/bound split is unvalidated for fresh, unfermented juice. Duplicate input is rejected if named hormone pools already occur upstream.</small></label>}
            <details><summary>Additional component retention exceptions</summary><p>Retention gates depend on the actual juice flows. The stored sample lists Lipids, NonBiodegradableOrganics, OrganicNitrogen, OtherBiodegradableOrganics, PersistentOrganics, and Pesticides, but a specific run may differ. The supplied class matrix covers TUF and LNF; MEUF class retentions for proteins, peptides/amino acids, sugars, and salts were not supplied. Pools without a documented retention are preserved in an unresolved outlet and block complete product allocation. Other solid-phase pools use an explicit full-retention screening assumption that still needs feed-specific verification.</p><label>Component retention fractions<textarea rows={4} value={biostimulantRoute.component_retention_overrides} onChange={event=>setBiostimulantRoute(current=>({...current,component_retention_overrides:event.target.value}))}/></label><label>Evidence note for each component<textarea rows={4} value={biostimulantRoute.component_retention_override_sources} onChange={event=>setBiostimulantRoute(current=>({...current,component_retention_override_sources:event.target.value}))}/></label></details>
          </div>
            <p className="compact-warning">Benchmark hormone mode is optional and off by default. When enabled it adds a separately tracked screening analyte feed at the clarified-juice boundary; this is not a GreenHub measurement. The optional CIP screen estimates chemical make-up only. Membrane replacement, crossflow pumping, cleaning water/heat, downtime, conditioning, and a qualified product price remain outside the current screen.</p>
        </section>}
        {scenario.protein_recovery==='PR7'&&<section className="panel"><PanelTitle icon={<Activity/>} title="PR7 pressure and energy" text="TMP is required for the resistance-based flux method. Add pump efficiency as a separate sourced input to estimate idealized permeate-side electricity. A separate sourced crossflow-specific electricity input can be added; controls and other auxiliaries remain unresolved."/><div className="ds-controls"><label>Transmembrane pressure <span><input type="number" min="0.001" step="any" value={biostimulantRoute.transmembrane_pressure_bar} onChange={event=>setBiostimulantRoute(current=>({...current,transmembrane_pressure_bar:event.target.value}))}/><em>bar</em></span></label><label>Pressure evidence note<input value={biostimulantRoute.pressure_source} onChange={event=>setBiostimulantRoute(current=>({...current,pressure_source:event.target.value}))}/></label><label>Pump efficiency <span><input type="number" min="0.001" max="1" step="any" value={biostimulantRoute.pump_efficiency_fraction} onChange={event=>setBiostimulantRoute(current=>({...current,pump_efficiency_fraction:event.target.value}))}/><em>fraction</em></span></label><label>Efficiency evidence note<input value={biostimulantRoute.pump_efficiency_source} onChange={event=>setBiostimulantRoute(current=>({...current,pump_efficiency_source:event.target.value}))}/></label><label>Crossflow electricity <span><input type="number" min="0" step="any" value={biostimulantRoute.crossflow_electricity_kwh_m3_feed} onChange={event=>setBiostimulantRoute(current=>({...current,crossflow_electricity_kwh_m3_feed:event.target.value}))}/><em>kWh/m³ feed</em></span></label><label>Crossflow evidence note<input value={biostimulantRoute.crossflow_electricity_source} onChange={event=>setBiostimulantRoute(current=>({...current,crossflow_electricity_source:event.target.value}))}/></label><small>Optional measured or sourced crossflow recirculation specific electricity. It is added to the plant electricity utility and must exclude any permeate-side pressure-work estimate entered above.</small></div></section>}
        {scenario.protein_recovery==='PR7'&&<section className="panel"><PanelTitle icon={<Activity/>} title="PR7 CIP reagent screen" text="Optional annual chemical make-up cost. Uses the registered 48 operating-hour interval and supplied working concentrations; solution volume and make-up fraction need an evidence note."/><div className="ds-controls"><label>Working solution volume per step <span><input type="number" min="0.001" step="any" value={biostimulantRoute.cip_solution_volume_L_per_step} onChange={event=>setBiostimulantRoute(current=>({...current,cip_solution_volume_L_per_step:event.target.value}))}/><em>L/event</em></span><small>Same volume assumed for the sequential NaOH and citric-acid steps.</small></label><label>Make-up fraction per CIP cycle <span><input type="number" min="0" max="1" step="any" value={biostimulantRoute.cip_makeup_fraction_per_cycle} onChange={event=>setBiostimulantRoute(current=>({...current,cip_makeup_fraction_per_cycle:event.target.value}))}/><em>fraction</em></span><small>Share of each step’s working solution replaced per event, from 0 to 1.</small></label><label>Volume / make-up evidence note<input value={biostimulantRoute.cip_input_source} onChange={event=>setBiostimulantRoute(current=>({...current,cip_input_source:event.target.value}))}/></label></div><small>Calculated costs use indicative EUR reagent prices and a stated 1 kg/L dilute-solution density approximation. The subtotal excludes CIP water, heating, labor, downtime, wastewater, and any recovery credit.</small></section>}
        <BiostimulantScreen runId={runtime === 'python' ? result.run_id : undefined}/>
        {scenario.protein_recovery==='PR7'&&<section className="panel"><PanelTitle icon={<Activity/>} title="PR7 concentrate revenue" text="Select an explicit price for the screening TEA; the default keeps this unvalidated product price out of project revenue."/><label>Biostimulant price<select value={pr7PriceLevel} onChange={event=>setPr7PriceLevel(event.target.value as 'off'|'low'|'nominal'|'high')}><option value="off">Off</option><option value="low">Low (€1.50/L)</option><option value="nominal">Nominal (€2.50/L)</option><option value="high">High (€3.50/L)</option></select><small>Applies to simulated PR7 retentate litres. The supplied price basis assumes 10× concentration; review actual VCF, product specification, qualification, and offtake. Low/high are sensitivity endpoints, not probability bounds or validated market quotes.</small></label></section>}
        <section className="panel order-panel"><div><span className="eyebrow">Process sequence</span><h3>Nutrient-recovery order</h3><p>Controls the downstream separation sequence where supported.</p></div><select value={scenario.process_order} onChange={event => setScenario(current => ({...current, process_order: event.target.value as any}))}><option value="A">Separation → phosphorus → nitrogen → potassium</option><option value="B">Separation → nitrogen → phosphorus → potassium</option><option value="C">Phosphorus before separation</option><option value="D">Separation only</option></select></section>
        <InputStudio feed={feed} setFeed={setFeed} scenario={scenario} onRun={() => executeRun()} running={running}/>
        <SectionHeading title="Evidence / model mode" text="The evidence basis changes parameter resolution. The reference month remains visible because empirical composition is month-specific."/>
        <section className="panel configure-evidence"><label><span>Evidence basis</span><select value={mode} onChange={event => setMode(event.target.value as CalculationMode)}><option value="structural">Structural model</option><option value="literature_default">Literature defaults</option><option value="calibrated">Calibrated data</option></select><small>Controls which eligible evidence layer supplies process parameters.</small></label><label><span>Reference composition month</span><select value={month} onChange={event => setMonth(event.target.value)}>{['January','February','March','April','May','June','July','August','September','October','November','December'].map(item => <option key={item}>{item}</option>)}</select><small>Used where a route requires one representative monthly composition.</small></label><div><span>Model basis</span><strong>Quasi-dynamic pathway</strong><small>Each process unit retains its reported evidence and calculation basis.</small></div></section>
        <section className="panel advanced-link"><div><span className="eyebrow">Advanced parameters</span><h3>{changedParameters.length ? `${changedParameters.length} reviewed values differ from defaults` : 'Review evidence and technical parameters'}</h3><p>Detailed assumptions remain separate from the primary operating-scale controls.</p></div><button className="secondary" onClick={() => setTab('advanced')}>Open advanced parameters</button></section>
        <ConfigurationReview scenario={scenario} schedule={biomassSchedule} mode={mode} onRun={() => executeRun()} running={running}/>
      </div>}
      {tab === 'explore' && <div className="page-stack"><PageIntro eyebrow="Explore" title="Performance and decisions" text={exploreView==='optimization'?'BioSTEAM Pareto results':'Process performance and contribution data'}/><div className="section-switcher" role="tablist" aria-label="Explore views">{([['performance','Performance'],['hotspots','Hotspots'],['optimization','Optimization'],['model-comparison','Model comparison']] as [ExploreView,string][]).map(([id,label])=><button role="tab" aria-selected={exploreView===id} className={exploreView===id?'active':''} key={id} onClick={()=>setExploreView(id)}>{label}</button>)}</div>{exploreView==='performance'&&<ResultsWorkbench result={result} graph={graph} artifacts={artifacts} runtime={runtime==='python'?(result.resolution_mode==='steady_state'?'Steady-state process model':'Quasi-dynamic process model'):'Preview baseline'} sourceState={sourceState} savedRuns={savedRuns} onSaveRun={saveSnapshot}/ >}{exploreView==='hotspots'&&<AnalyticsPreview/>}{exploreView==='optimization'&&<ParetoScreening/>}{exploreView==='model-comparison'&&<ModelComparisonPanel dynamic={result} empirical={empiricalComparison} live={runtime==='python'} busy={comparisonRunning} onRun={runEmpiricalComparison} error={comparisonError}/>}</div>}
      {tab === 'reports' && <div className="page-stack"><PageIntro eyebrow="Reports" title="Download and share the run" text="Exports include the exact process request and the returned post-route decision analysis, when available."/><ReportCenter result={result} artifacts={artifacts} runtime={runtime === 'python' ? 'Quasi-dynamic process model' : 'Preview baseline'} exportContext={{process_run:runContext,post_route_decision_analysis:analysisReport}}/></div>}
      {tab === 'advanced' && <div className="page-stack">
        <PageIntro eyebrow="Advanced" title="Model settings" text="Detailed evidence, parameter values, model diagnostics, and secondary planning tools."/>
        <section className="panel advanced-shortcuts"><div><h3>Secondary tools</h3><p>Keep the supported quasi-dynamic run as the main workflow; use these views for diagnostics or comparison only.</p></div><button className="secondary" onClick={()=>{setTab('explore');setExploreView('model-comparison');}}>Model comparison</button><button className="secondary" onClick={()=>setTab('dynamic-proxy')}>Planning proxy</button></section>
        <section className="advanced-grid">
          <div className="panel evidence-panel"><PanelTitle icon={<SlidersHorizontal/>} title="Model basis" text="These settings control which evidence layer and reference period the model uses."/><label><span>Evidence basis</span><select value={mode} onChange={event => setMode(event.target.value as CalculationMode)}><option value="structural">Structural model</option><option value="literature_default">Literature defaults</option><option value="calibrated">Calibrated data</option></select></label><label><span>Reference month</span><select value={month} onChange={event => setMonth(event.target.value)}>{['January','February','March','April','May','June','July','August','September','October','November','December'].map(item => <option key={item}>{item}</option>)}</select></label></div>
          <AdvancedRunDetails result={result} limitations={limitations}/>
        </section>
        <div className="parameter-toolbar"><button className={parameterView === 'basic' ? 'active' : ''} onClick={() => setParameterView('basic')}>Core assumptions</button><button className={parameterView === 'advanced' ? 'active' : ''} onClick={() => setParameterView('advanced')}>Detailed assumptions</button><span>{visibleParameters.length} items</span></div>
        <section className="parameter-layout"><div className="panel parameter-list">{visibleParameters.map(parameter => <ParameterRow key={parameter.parameter_id} parameter={parameter} onChange={value => setParameters(current => current.map(item => item.parameter_id === parameter.parameter_id ? {...item,current_value:value} : item))}/>)}</div><aside className="panel quality-panel"><ShieldCheck size={20}/><h3>Evidence quality</h3>{Object.entries(qualityHelp).map(([key,text]) => <div className="quality-line" key={key}><span className={`quality q-${key}`}>{key}</span><span>{text}</span></div>)}<p>Detailed provenance remains available in the generated run reports.</p></aside></section>
        <Comparison runs={savedRuns} current={result} onSave={saveSnapshot} onClear={() => setSavedRuns([])}/>
      </div>}
      {tab === 'dynamic-proxy' && <div className="page-stack"><PageIntro eyebrow="Advanced model" title="Dynamic planning proxy" text="An isolated planning tool with explicit assumptions; it is not the primary process simulation."/><DynamicCompleteDashboard/></div>}
    </main>
    <footer><span>Spaak Circular Solutions · GreenHub process model</span><span>{sourceState.label}</span></footer>
  </div>;
}

function AnalysisSummary({report,loading,error,onExplore}:{report:DecisionReport|null;loading:boolean;error:string;onExplore:()=>void}) {
  if (loading) return <section className="panel dashboard-analysis" role="status"><strong>Calculating post-route TEA and LCA</strong><span>Process results are already available; analysis completeness will be reported separately.</span></section>;
  if (!report) return <section className="panel dashboard-analysis"><div><span className="eyebrow">Economic and environmental analysis</span><h3>Not calculated</h3><p>{error||'Run the backend analysis to calculate TEA and climate inventory. Missing inputs will remain incomplete, not zero.'}</p></div><button className="secondary" onClick={onExplore}>Open Explore</button></section>;
  const tea=report.tea?.totals||{}, finance=report.tea?.financial_kpis||{}, lca=report.lca?.totals||{};
  const climateEligible=report.lca?.readiness?.climate_objective_eligible===true;
  const climate=climateEligible?lca.climate_kg_co2e_per_year:lca.partial_climate_kg_co2e_per_year;
  const irr=finance.irr==null?null:Number(finance.irr)*100;
  const rows=[
    ['Reported revenue',tea.annual_revenue_eur,tea.revenue_status||'incomplete','EUR/year'],
    ['Operating margin',tea.net_operating_margin_eur_per_year,tea.profit_status||'incomplete','EUR/year · known lines'],
    ['OPEX break-even revenue',tea.annual_opex_eur,tea.opex_status||'partial OPEX only','EUR/year · excludes CAPEX'],
    ['Simple payback',finance.simple_payback_years,finance.financial_kpi_status||'incomplete','years'],
    ['IRR',irr,finance.financial_kpi_status||'incomplete','%'],
    ['NPV',finance.npv_eur,finance.financial_kpi_status||'incomplete','EUR'],
    [climateEligible?'Climate impact':'Characterized climate subtotal',climate,climateEligible?'eligible within declared scope':'incomplete inventory',climate==null?'Not reported':'kg CO₂e/year'],
  ];
  return <section className="panel dashboard-analysis"><div className="dashboard-analysis-head"><div><span className="eyebrow">Post-route decision analysis</span><h3>TEA &amp; climate</h3></div><button className="text-button" onClick={onExplore}>Explore details →</button></div><div className="dashboard-analysis-grid">{rows.map(([label,value,status,unit])=><article key={String(label)}><span>{label}</span><strong>{value==null||!Number.isFinite(Number(value))?'Incomplete':Number(value).toLocaleString(undefined,{maximumFractionDigits:1})}</strong><small>{unit} · {status}</small></article>)}</div><details><summary>Model assumptions &amp; limitations</summary><p>TEA uses registered screening product-price benchmarks and remains conditional on product grade, completeness, installed-capital evidence, and financial assumptions. OPEX break-even is only the reported cost subtotal and excludes CAPEX, financing and tax. Climate is the only characterized impact category currently surfaced; it is incomplete unless the backend marks its declared scope eligible.</p><ul>{[...report.warnings,...report.limitations].slice(0,12).map((item:string,index:number)=><li key={index}>{item}</li>)}</ul></details></section>;
}

function Overview({ result, activeUnits, runtime, limitations, analysis, analysisBusy, analysisError, onConfigure, onResults }: any) {
  const metrics = result.metrics;
  const annual = result.annual;
  const nutrientTotal = annual ? ['phosphorus_product','ammonium_product','potassium_concentrate','nutrient_rich_solids'].reduce((sum,key)=>sum+(annual.products[key]?.value||0),0) : null;
  const outcomes = annual ? [
    ['Feed processed', annual.feed_processed.value / 1000, 't/year', 'green'],
    [result.scenarios.protein_recovery==='PR7'?'Biostimulant retentate':'Protein product', (annual.products[result.scenarios.protein_recovery==='PR7'?'biostimulant_product':'dry_protein_product']?.value || 0) / 1000, 't/year wet mass', 'green'],
    ['Biomethane', annual.volumetric_products?.biomethane?.value || 0, 'm³/year', 'blue'],
    ['Electricity', (annual.utilities.electricity?.value || 0) / 1000, 'MWh/year', 'rose'],
    ['Mass closure', annual.balance.overall_closure_pct, '%', annual.balance.passed ? 'green' : 'rose'],
    ['Nutrient products', (nutrientTotal||0) / 1000, 't/year', 'yellow'],
  ] : [
    ['Feed rate', result.balances.mass_in_kgh, 'kg/h', 'green'],
    ['Protein product', metrics.protein_recovered_kgh, 'kg/h', 'green'],
    ['Biomethane', metrics.biomethane_flow_m3h, 'm³/h', 'blue'],
    ['Net power', metrics.net_power_kw, 'kW', 'rose'],
    ['Mass closure', result.balances.mass_closure_pct, '%', 'green'],
  ];
  return <div className="page-stack">
    <section className="overview-head">
      <div><span className="eyebrow">GreenHub · active baseline</span><h1>Roadside grass to products</h1><p>{annual?.biomass_schedule ? `${annual.biomass_schedule.annual_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year · ${annual.period.start_date||'year-round'} to ${annual.period.end_date||'year-end'} · ${annual.method_label}` : 'A reproducible backend baseline is loading. Preview values remain marked until the live run succeeds.'}</p></div>
      <div className="overview-actions"><button className="run-button" onClick={onConfigure}><Settings2 size={16}/>Configure pathway</button><button className="secondary" onClick={onResults}><Activity size={16}/>View results</button></div>
    </section>
    <section className="kpi-grid">{outcomes.map(([label,value,unit,color]: any[]) => <div className="kpi" key={String(label)}><span>{label}</span><strong className={String(color)}>{typeof value==='number'&&Number.isFinite(value)?value.toLocaleString(undefined,{maximumFractionDigits:1}):String(value)}</strong><small>{unit}</small></div>)}</section>
    <BaselineTimeSeries annual={annual}/>
    <AnalysisSummary report={analysis} loading={analysisBusy} error={analysisError} onExplore={onResults}/>
    {annual?.biomass_schedule&&<section className="panel"><PanelTitle icon={<Gauge/>} title="Annual biomass schedule" text="The quasi-dynamic calculation integrates the configured seasonal availability and monthly refinery intake. This is a scenario schedule, not a new measured harvest series."/><div className="schedule-facts"><div><span>Available</span><strong>{annual.biomass_schedule.annual_available_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Processed</span><strong>{annual.biomass_schedule.annual_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Unused</span><strong>{annual.biomass_schedule.annual_unused_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t/year</strong></div><div><span>Utilization</span><strong>{(annual.biomass_schedule.utilization_fraction*100).toFixed(1)}%</strong></div><div><span>Peak month</span><strong>{annual.biomass_schedule.peak_month_processed_tonnes.toLocaleString(undefined,{maximumFractionDigits:0})} t</strong></div></div></section>}
    <section className="overview-grid">
      <div className="panel"><PanelTitle icon={<Layers3/>} title="Current process pathway" text={`${activeUnits} active units across ${Object.keys(result.process_areas).length} process areas.`}/><div className="process-strip">{Object.values(result.process_areas).map((area:any,index:number) => <React.Fragment key={area.id}><div className="process-node"><span>{String(index+1).padStart(2,'0')}</span><strong>{areaLabels[area.id] || area.name}</strong><small>{area.units.length} units · {area.limitations.length ? 'review notes' : 'active'}</small></div>{index < Object.keys(result.process_areas).length-1 && <b>→</b>}</React.Fragment>)}</div></div>
      <div className="panel"><PanelTitle icon={runtime === 'python' ? <CheckCircle2/> : <AlertTriangle/>} title={runtime === 'python' ? 'Model connected' : 'Preview mode'} text={runtime === 'python' ? 'Results originate from the Python scientific service.' : 'Run the model before using values for decisions.'}/><div className="trust-list"><span><i className="status-dot active"/>Active simulated</span><span><i className="status-dot planned"/>Planned or data-gated</span><span><i className="status-dot warning"/>Provisional assumption</span></div>{limitations.slice(0,2).map((item:string,index:number) => <p className="compact-warning" key={index}>{item}</p>)}</div>
    </section>
  </div>;
}

function ScenarioCard({ group, value, onChange }: any) {
  const selected = group.options.find((item:any[]) => item[0] === value) || group.options[0];
  const selectable = selected[2] === 'active' || selected[2] === 'configurable';
  return <section className="panel scenario-card"><div className="scenario-heading"><div><span className="eyebrow">{group.title}</span><h3>{selected[1]}</h3></div><span className={`status ${selected[2] === 'configurable' ? 'active' : selected[2]}`}>{selected[2] === 'configurable' ? 'configured' : selected[2]}</span></div><select value={value} onChange={event => onChange(event.target.value)}>{group.options.map((item:any[]) => <option value={item[0]} key={item[0]} disabled={item[2] === 'planned'}>{item[1]}{item[2] === 'planned' ? ' (planned)' : ''}</option>)}</select><p>{group.affects}</p><small>{selected[2] === 'planned' ? 'Data gate incomplete; this route is unavailable for execution.' : selected[2] === 'configurable' ? 'Requires explicit membrane inputs; runs use the seasonal feed schedule.' : selectable ? 'Available in the current scientific model.' : ''}</small></section>;
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
