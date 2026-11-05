import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CircleDot,
  Clock3,
  FileDown,
  Gauge,
  GitCompare,
  Layers3,
  Play,
  PackageCheck,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Wrench,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { DEFAULT_PARAMETERS } from './data/greenhubData';
import feedCompositionProfile from '../../Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json';
import { buildPythonRequest, fetchRunResources, runPythonSimulation } from './data/apiClient';
import { cloneEmpiricalBaseline, PREVIEW_BASELINE_STATUS } from './data/baselineFixtures';
import { normalizeResult } from './data/normalizeResult';
import { ReportCenter, ResultsWorkbench } from './components/ResultsWorkbench';
import type { FeedInputs } from './components/InputStudio';
import BaselineTimeSeries from './components/BaselineTimeSeries';
import ModelComparisonPanel from './components/ModelComparisonPanel';
import {decisionApi, type DecisionReport} from './data/decisionSupport';
import DynamicCompleteDashboard from './components/DynamicCompleteDashboard';
import ProcessHotspots from './components/ProcessHotspots';
import ParetoScreening from './components/ParetoScreening';
import InventoryPage from './components/InventoryPage';
import type { CalculationMode, EmpiricalBiomassSchedule, ParameterDefinition, ResultSourceState, ScenarioSelection, SimulationResult } from './types';

type RuntimeSource = 'python' | 'fallback';
type TabId = 'dashboard' | 'configure' | 'explore' | 'reports' | 'advanced' | 'dynamic-proxy' | 'model-comparison';
type ExploreView = 'performance' | 'inventory' | 'hotspots' | 'optimization' | 'model-comparison';
type ConfigureView = 'Biomass' | 'Process' | 'Economics' | 'Environment';
type SavedRun = { label: string; result: SimulationResult; scenario: ScenarioSelection; savedAt: string };
type Artifact = { name: string; type: string; description: string; url?: string; available: boolean; warning?: string };

const defaults: ScenarioSelection = {
  feed_front_end: 'F1', protein_recovery: 'PR3', anaerobic_digestion: 'AD1',
  biogas_upgrading: 'BG2', nutrient_recovery: 'NR4', process_order: 'A',
};
const scheduleDefaults: EmpiricalBiomassSchedule = {
  annual_available_biomass_tonnes: 30000,
  annual_processed_biomass_tonnes: 30000,
  processing_delay_days: 14,
  collection_refinery_fraction: 1,
  feed_basis: 'tonnes_per_year',
  feed_kg_per_hr: 1000,
  season_start: '2026-04-15',
  season_end: '2026-11-15',
  peak_date: '2026-07-31',
  spread_days: 55,
  active_months: Array.from({length: 12}, (_, index) => index + 1),
};
const baselineProductPrices = {
  dry_protein_product:1.6, biostimulant_product:2.5, biomethane:0.88,
  phosphorus_product:0.552, ammonium_product:0.30774, potassium_concentrate:0.45,
  press_cake:0.065, nutrient_rich_solids:0.04,
};
const productPriceLabels:Record<keyof typeof baselineProductPrices,{label:string;unit:string}>={
  dry_protein_product:{label:'Dry protein',unit:'€/kg'}, biostimulant_product:{label:'Biostimulant',unit:'€/L'},
  biomethane:{label:'Biomethane',unit:'€/m³'}, phosphorus_product:{label:'Phosphorus product',unit:'€/kg'},
  ammonium_product:{label:'Ammonium product',unit:'€/kg'}, potassium_concentrate:{label:'Potassium concentrate',unit:'€/kg'},
  press_cake:{label:'Press cake',unit:'€/kg'}, nutrient_rich_solids:{label:'Nutrient-rich solids',unit:'€/kg'},
};
const economicDefaults={staffingPeople:5,paidHoursPerPerson:1500,laborCostEurPerHour:47.9,electricityCostEurMWh:199.1,heatCostEurMWh:79.3,coolingCostEurMWh:'',logisticsCostEurTkm:'0',logisticsDistanceKm:'0',projectLifetimeYears:20,discountRate:0.08,taxRate:0.258,workingCapitalEur:0,residualValueEur:0,capexGrantFraction:0,biomethaneBonusEnabled:false,biomethaneBonusEurM3:1.87,biomethaneBonusYears:15,additionalBenefitEurYear:0,additionalBenefitYears:0};
const monthLabels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const qualityHelp = {
  A: 'Measured or verified', B: 'Strong literature basis', C: 'Engineering estimate',
  D: 'Uncertain or quarantined', E: 'Structural placeholder',
};
const feedQualityHelp = {
  A: 'Measured', B: 'Literature basis', E: 'Reasonable assumption', D: 'Uncertain',
};
const feedCompositionData = feedCompositionProfile.compounds as Record<string,{label:string;wet_mass_fraction:number;data_class:'A'|'B'|'D'|'E';source?:{source:string;doi?:string;basis:string}}>;
type FeedCompound = {id:string;label:string};
const feedCompoundGroups:{title:string;items:FeedCompound[]}[] = [
  {title:'Water',items:[{id:'Water',label:'Moisture'}]},
  {title:'Proteins and peptides',items:[
    {id:'SolubleProtein',label:'Soluble protein'},{id:'SuspendedProtein',label:'Suspended protein'},
    {id:'PrecipitatedProtein',label:'Precipitated protein'},{id:'HeatCoagulatedProtein',label:'Heat-coagulated protein'},
    {id:'DegradedProtein',label:'Degraded protein'},{id:'Peptides',label:'Peptides'},
    {id:'AminoAcids',label:'Amino acids'},{id:'MicrobialBiomass',label:'Microbial biomass'},
  ]},
  {title:'Carbohydrates and plant structure',items:[
    {id:'EntrappedSugars',label:'Sugars'},{id:'Starch',label:'Starch'},
    {id:'Cellulose',label:'Cellulose'},{id:'Hemicellulose',label:'Hemicellulose'},
    {id:'Lignin',label:'Lignin'},{id:'Pectin',label:'Pectin'},
    {id:'Glucose',label:'Glucose'},{id:'Fructose',label:'Fructose'},
    {id:'Sucrose',label:'Sucrose'},{id:'Xylose',label:'Xylose'},
    {id:'Arabinose',label:'Arabinose'},{id:'Galactose',label:'Galactose'},
    {id:'Mannose',label:'Mannose'},{id:'Maltose',label:'Maltose'},
    {id:'AceticAcid',label:'Acetic acid'},{id:'LacticAcid',label:'Lactic acid'},
    {id:'PropionicAcid',label:'Propionic acid'},{id:'ButyricAcid',label:'Butyric acid'},
    {id:'FormicAcid',label:'Formic acid'},{id:'SuccinicAcid',label:'Succinic acid'},
    {id:'CitricAcid',label:'Citric acid'},{id:'MalicAcid',label:'Malic acid'},
    {id:'OxalicAcid',label:'Oxalic acid'},
  ]},
  {title:'Other organic matter',items:[
    {id:'Lipids',label:'Lipids'},{id:'OtherBiodegradableOrganics',label:'Other biodegradable organics'},
    {id:'ParticulateBiodegradableOrganics',label:'Particulate biodegradable organics'},
    {id:'NonBiodegradableOrganics',label:'Non-biodegradable organics'},
    {id:'PersistentOrganics',label:'Persistent organics'},{id:'Pesticides',label:'Pesticides'},
  ]},
  {title:'Nutrients and minerals',items:[
    {id:'Ammonium',label:'Ammonium'},{id:'OrganicNitrogen',label:'Organic nitrogen'},
    {id:'ParticulateNitrogen',label:'Particulate nitrogen'},{id:'OrganicPhosphorus',label:'Organic phosphorus'},
    {id:'DissolvedPhosphorus',label:'Dissolved phosphorus'},{id:'ParticulatePhosphorus',label:'Particulate phosphorus'},
    {id:'ParticulatePotassium',label:'Particulate potassium'},{id:'PotassiumIon',label:'Potassium ion'},
    {id:'HydrogenIon',label:'Hydrogen ion'},{id:'HydroxideIon',label:'Hydroxide ion'},
    {id:'NitrateIon',label:'Nitrate ion'},{id:'NitriteIon',label:'Nitrite ion'},
    {id:'Orthophosphate',label:'Orthophosphate'},{id:'SodiumIon',label:'Sodium ion'},
    {id:'MagnesiumIon',label:'Magnesium ion'},{id:'CalciumIon',label:'Calcium ion'},
    {id:'ChlorideIon',label:'Chloride ion'},{id:'SulfateIon',label:'Sulfate ion'},
    {id:'BicarbonateIon',label:'Bicarbonate ion'},{id:'CarbonateIon',label:'Carbonate ion'},
    {id:'Ash',label:'Ash'},
  ]},
  {title:'Solids and trace material',items:[
    {id:'SuspendedSolids',label:'Suspended solids'},{id:'SolubleInertSolids',label:'Soluble inert solids'},
    {id:'SuspendedInertSolids',label:'Suspended inert solids'},{id:'InertSolids',label:'Inert solids'},
    {id:'Sand',label:'Sand'},{id:'Litter',label:'Litter'},
    {id:'HeavyMetals',label:'Heavy metals'},{id:'Microplastics',label:'Microplastics'},
    {id:'PathogenIndicators',label:'Pathogen indicators'},
  ]},
  {title:'Phytohormones',items:[
    {id:'Indole3AceticAcid',label:'Free auxin (IAA)'},{id:'ProteinBoundIAA',label:'Protein-bound IAA'},
    {id:'Zeatin',label:'Free zeatin'},{id:'PeptideBoundZeatin',label:'Peptide-bound zeatin'},
    {id:'ZeatinRiboside',label:'Zeatin riboside'},{id:'BoundZeatinRiboside',label:'Bound zeatin riboside'},
  ]},
];
const baselineFeedComposition = Object.fromEntries(Object.entries(feedCompositionData).map(([id,record])=>[id,record.wet_mass_fraction*100]));
const feedCompositionLimits=feedCompositionProfile.composition_limits as {minimum_total_fraction:number;maximum_total_fraction:number;normalized_total_fraction:number};
const FEED_COMPOSITION_TOTAL_MIN_PERCENT = feedCompositionLimits.minimum_total_fraction*100;
const FEED_COMPOSITION_TOTAL_MAX_PERCENT = feedCompositionLimits.maximum_total_fraction*100;
const FEED_COMPOSITION_NORMALIZED_TOTAL_PERCENT = feedCompositionLimits.normalized_total_fraction*100;

function normalizeFeedCompositionForRequest(values:Record<string,number>) {
  const entries=Object.entries(values).map(([id,value])=>[id,Number(value)] as const);
  if(entries.some(([,value])=>!Number.isFinite(value)||value<0))throw new Error('Feed compound values must be finite and non-negative.');
  const totalPercent=entries.reduce((sum,[,value])=>sum+value,0);
  if(totalPercent<FEED_COMPOSITION_TOTAL_MIN_PERCENT||totalPercent>FEED_COMPOSITION_TOTAL_MAX_PERCENT)throw new Error(`Feed composition total must be between ${FEED_COMPOSITION_TOTAL_MIN_PERCENT}% and ${FEED_COMPOSITION_TOTAL_MAX_PERCENT}% wet mass. Current total: ${totalPercent.toFixed(3)}%.`);
  return Object.fromEntries(entries.map(([id,value])=>[id,value/totalPercent*FEED_COMPOSITION_NORMALIZED_TOTAL_PERCENT/100]));
}
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
const processParameterDefinitions = [
  {id:'phase4.acid_dose_kg_per_m3',label:'Protein-route acid dose',unit:'kg/m³ liquid',defaultValue:1.5,min:0,max:100,step:0.1,when:(s:ScenarioSelection)=>['PR1','PR2','PR3'].includes(s.protein_recovery)},
  {id:'phase5.target_cod_olr_kg_m3_day',label:'Digester COD loading',unit:'kg COD/m³/day',defaultValue:2.5,min:0.000001,max:100,step:0.1,when:(s:ScenarioSelection)=>s.anaerobic_digestion!=='AD0'},
  {id:'phase5.digester_temperature_c',label:'Digester temperature',unit:'°C',defaultValue:35,min:0,max:80,step:1,when:(s:ScenarioSelection)=>s.anaerobic_digestion!=='AD0'},
  {id:'phase5.cod_conversion_fraction',label:'COD conversion',unit:'fraction',defaultValue:0.75,min:0,max:1,step:0.01,when:(s:ScenarioSelection)=>s.anaerobic_digestion!=='AD0'},
  {id:'phase6.upgrading_minimum_methane_mol_fraction_dry',label:'Upgrader methane threshold',unit:'mol fraction',defaultValue:0.35,min:0,max:1,step:0.01,when:(s:ScenarioSelection)=>s.biogas_upgrading!=='BG0'},
  {id:'phase7.struvite_phosphate_recovery_fraction',label:'Phosphate recovery',unit:'fraction',defaultValue:0.85,min:0,max:1,step:0.01,when:(s:ScenarioSelection)=>['NR2','NR4','NR5','NR7'].includes(s.nutrient_recovery)},
  {id:'phase7.ammonia_absorber_capture_efficiency',label:'Ammonia capture',unit:'fraction',defaultValue:0.99,min:0,max:1,step:0.01,when:(s:ScenarioSelection)=>['NR3','NR4','NR6','NR7'].includes(s.nutrient_recovery)},
];

export default function App() {
  const [tab, setTab] = useState<TabId>(window.location.hash==='#decision-support'?'explore':'dashboard');
  const [exploreView, setExploreView] = useState<ExploreView>('optimization');
  const [mode, setMode] = useState<CalculationMode>('structural');
  const [month, setMonth] = useState('July');
  const [scenario, setScenario] = useState<ScenarioSelection>(defaults);
  const [configureView, setConfigureView] = useState<ConfigureView>('Biomass');
  const [biostimulantRoute, setBiostimulantRoute] = useState({technology_id:'TUF',flux_method:'empirical',flux_L_m2_h:22,flux_source:'User-supplied GreenHub membrane dataset: TUF baseline flux 22 L/(m²·h).',feed_to_reference_concentration_ratio:'',flux_model_source:'',viscosity_Pa_s:'',viscosity_source:'',retention_matrix_source:'User-supplied GreenHub component co-retention matrix and hormone retention dataset.',component_retention_overrides:'{}',component_retention_override_sources:'{}',use_hormone_benchmarks:false,hormone_benchmark_source:'',transmembrane_pressure_bar:'',pressure_source:'',pump_efficiency_fraction:'',pump_efficiency_source:'',crossflow_electricity_kwh_m3_feed:'',crossflow_electricity_source:'',cip_solution_volume_L_per_step:'',cip_makeup_fraction_per_cycle:'',cip_input_source:''});
  const [economicsInputs, setEconomicsInputs] = useState({...economicDefaults,totalCapexOverride:'',productPrices:baselineProductPrices});
  const [environmentInputs, setEnvironmentInputs] = useState({electricityKgCo2eKwh:0.264,heatKgCo2eKwh:30.96/277.7777777778});
  const [parameters, setParameters] = useState<ParameterDefinition[]>(DEFAULT_PARAMETERS);
  const [processInputParameters, setProcessInputParameters] = useState<Record<string,number>>(()=>Object.fromEntries(processParameterDefinitions.map(item=>[item.id,item.defaultValue])));
  const [feed, setFeed] = useState<FeedInputs>({ feedAmountKgh: 500, operatingDaysPerWeek: 7, operatingHoursPerDay: 24, moisturePct: 78, liquidFractionPct: 62, proteinPct: 18, nitrogenPct: 1.1, phosphorusPct: 0.12 });
  const [biomassSchedule, setBiomassSchedule] = useState<EmpiricalBiomassSchedule>(scheduleDefaults);
  const [storageConditions, setStorageConditions] = useState({enabled:false,storageDays:0,aerobicFraction:0,temperatureC:20,moistureActivity:1});
  const [feedComposition, setFeedComposition] = useState<Record<string,number>>(baselineFeedComposition);
  const fallbackPreview = useMemo(() => cloneEmpiricalBaseline(), []);
  const [result, setResult] = useState<SimulationResult>(fallbackPreview);
  const [empiricalComparison, setEmpiricalComparison] = useState<SimulationResult|null>(null);
  const [comparisonRunning, setComparisonRunning] = useState(false);
  const [comparisonError, setComparisonError] = useState('');
  const [analysisReport, setAnalysisReport] = useState<DecisionReport|null>(null);
  const [runContext, setRunContext] = useState<Record<string,unknown>|null>(null);
  const [modelWarnings, setModelWarnings] = useState<string[]>([]);
  const analysisRequest = useRef(0);
  const [runtime, setRuntime] = useState<RuntimeSource>('fallback');
  const [sourceState, setSourceState] = useState<ResultSourceState>(PREVIEW_BASELINE_STATUS);
  const [graph, setGraph] = useState<any | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [limitations, setLimitations] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [pendingParetoCandidate, setPendingParetoCandidate] = useState<any|null>(null);
  const [savedRuns, setSavedRuns] = useState<SavedRun[]>(() => {
    try { return JSON.parse(localStorage.getItem('greenhub.savedRuns') || '[]'); } catch { return []; }
  });
  const [parameterView, setParameterView] = useState<'basic'|'advanced'>('basic');
  const autoRunStarted = useRef(false);

  useEffect(() => { localStorage.setItem('greenhub.savedRuns', JSON.stringify(savedRuns)); }, [savedRuns]);
  useEffect(() => {
    setSourceState(current => current.is_live ? {
      ...current,
      status: 'stale_previous_result',
      label: 'Inputs changed · previous run shown',
      detail: 'Displayed results use the previous input values. Run the simulation to calculate the updated case.',
      is_live: false,
    } : current);
  }, [biomassSchedule,feed,feedComposition,storageConditions,scenario,mode,month,economicsInputs,environmentInputs,biostimulantRoute]);

  function markRunStaleAfterInputEdit() {
    setSourceState(current => current.is_live ? {
      ...current,
      status: 'stale_previous_result',
      label: 'Inputs changed · previous run shown',
      detail: 'Displayed results use the previous input values. Run the simulation to calculate the updated case.',
      is_live: false,
    } : current);
  }

  async function executeRun(saveAs?: string, navigateToResults = true) {
    const requestNumber=++analysisRequest.current;
    setRunning(true);
    setAnalysisReport(null);
    setSourceState(current => ({...current,label:'Connecting to Python',detail:'Submitting the annual configuration and requesting its reporting bundle.'}));
    try {
      const normalizedFeedComposition=normalizeFeedCompositionForRequest(feedComposition);
      setFeedComposition(Object.fromEntries(Object.entries(normalizedFeedComposition).map(([id,value])=>[id,value*100])));
      const storage = storageConditions.enabled?{model:'grass_reactions',storage_days:storageConditions.storageDays,aerobic_fraction:storageConditions.aerobicFraction,temperature_c:storageConditions.temperatureC,moisture_activity:storageConditions.moistureActivity,allow_assumptions:true}:null;
      const pr7 = scenario.protein_recovery === 'PR7';
      const processRequest=buildPythonRequest(mode, month, scenario, feed, biomassSchedule, 'quasi_dynamic', pr7 ? null : storage, normalizedFeedComposition, processDesignOverrides);
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
      if(envelope.source!=='python-api'||!raw?.run_id||raw.request_id!==processRequest.request_id||envelope.result.run_id!==raw.run_id||raw.run_id===result.run_id)throw new Error('The Python backend did not return a new result for this request. Previous results remain marked as stale.');
      const resources = await fetchRunResources(envelope.result.run_id, raw.plots || []);
      const next = {
        ...envelope.result,
        selected_month: month,
        plots: resources.plots.length ? resources.plots : envelope.result.plots,
        annual: resources.annual,
      };
      if(requestNumber!==analysisRequest.current)return;
      setResult(next);
      setGraph(resources.graph || raw.graph || null);
      setArtifacts(resources.artifacts);
      setLimitations(envelope.limitations);
      setModelWarnings(envelope.warnings);
      setRuntime('python');
      const annualResult=resources.annual;
      const reportedTarget=annualResult?.biomass_schedule?.user_requested_target_tonnes??biomassSchedule.annual_processed_biomass_tonnes;
      const actualThroughput=annualResult?annualResult.feed_processed.value/1000:null;
      const shortfall=actualThroughput==null?0:Math.max(reportedTarget-actualThroughput,0);
      const bottleneck=annualResult?.biomass_schedule?.throughput_bottleneck_unit_name||annualResult?.biomass_schedule?.throughput_bottleneck_unit_id;
      const throughputDetail=actualThroughput==null?'':` Requested ${reportedTarget.toLocaleString()} t/year; model processed ${actualThroughput.toLocaleString(undefined,{maximumFractionDigits:1})} t/year${shortfall>1?` (${shortfall.toLocaleString(undefined,{maximumFractionDigits:1})} t/year below target${bottleneck?`; bottleneck: ${bottleneck}`:''})`:''}.`;
      setSourceState({status:'live_python',label:'Success',detail:'Model produced quasi-dynamic results',is_live:true});
      setRunContext({model:'quasi_dynamic',calculation_mode:mode,reference_month:month,process_request:processRequest,economic_inputs:economicsInputs,environment_inputs:environmentInputs});
      if (saveAs) saveSnapshot(saveAs, next);
      if (navigateToResults) { setTab('explore'); setExploreView('performance'); }
      void (async()=>{try {
        const options=await decisionApi<any>('options',undefined,'GET');
        const configuration=structuredClone(options.defaults);
        configuration.simulation=processRequest;
        configuration.use_screening_lca_factors=true;
        configuration.use_screening_process_assumptions=false;
        configuration.lca={...configuration.lca,
          boundary:'factory gate-to-gate operational climate screening',
          included_groups:['electricity','heat','process_emissions'],
          exclusions:{
            materials:'Upstream production of process chemicals and consumables is outside the factory gate.',
            transport:'Offsite feedstock and product transport is outside the factory gate.',
            storage_emissions:'No storage degradation or fermentation is activated in this run.',
            waste:'Downstream waste treatment is outside the factory gate.',
            feedstock_production:'Grass cultivation and land-use effects are upstream of the factory gate.',
            equipment:'Embodied impacts from equipment manufacture are outside this operational boundary.',
          },
          inventory_completeness:{
            electricity:{status:'complete',note:'Modeled annual plant electricity with the selected Netherlands average-grid screening factor.'},
            heat:{status:'complete',note:'Modeled annual process heat with the selected Netherlands average heat-network screening factor.'},
            process_emissions:{status:'complete',note:'Modeled terminal process-gas flows; terminal gas fate is explicitly screened as emitted.'},
          },
          terminal_gas_fate:'emitted',
        };
        const screeningProductIds=Object.keys(options.screening_tea_product_prices||{}).filter(id=>(id!=='biostimulant_product'||pr7)&&id!=='recovered_water');
        const explicitProductPrices=Object.fromEntries(Object.entries(economicsInputs.productPrices).map(([id,value])=>[
          id,{...(options.screening_tea_product_prices?.[id]||{}),value_eur_per_unit:Number(value)},
        ]));
        configuration.financial_assumptions={...configuration.financial_assumptions,use_screening_price_benchmarks:true,screening_product_ids:screeningProductIds,product_prices:{...(configuration.financial_assumptions?.product_prices||{}),...explicitProductPrices}};
        configuration.tea={...configuration.tea,staffing_people:economicsInputs.staffingPeople,paid_hours_per_person:economicsInputs.paidHoursPerPerson,screening_estimates:true};
        const annualBiomethaneM3=Number(annualResult?.volumetric_products?.biomethane?.value??0);
        configuration.candidate_economics={
          project_lifetime_years:economicsInputs.projectLifetimeYears,discount_rate:economicsInputs.discountRate,
          tax_rate:economicsInputs.taxRate,working_capital_eur:economicsInputs.workingCapitalEur,residual_value_eur:economicsInputs.residualValueEur,
          total_capex_override_eur:economicsInputs.totalCapexOverride===''?null:Number(economicsInputs.totalCapexOverride),
          staffing_people:economicsInputs.staffingPeople,paid_hours_per_person:economicsInputs.paidHoursPerPerson,
          labor_cost_eur_per_person_hour:economicsInputs.laborCostEurPerHour,
          electricity_cost_eur_per_mwh:economicsInputs.electricityCostEurMWh,
          heat_cost_eur_per_mwh:economicsInputs.heatCostEurMWh,
          cooling_cost_eur_per_mwh:economicsInputs.coolingCostEurMWh===''?null:Number(economicsInputs.coolingCostEurMWh),
          logistics_cost_eur_per_t_km:economicsInputs.logisticsCostEurTkm===''?0:Number(economicsInputs.logisticsCostEurTkm),
          logistics_distance_km:economicsInputs.logisticsDistanceKm===''?0:Number(economicsInputs.logisticsDistanceKm),
          capex_grant_fraction:economicsInputs.capexGrantFraction,opex_support_years:Math.max(economicsInputs.biomethaneBonusEnabled?economicsInputs.biomethaneBonusYears:0,economicsInputs.additionalBenefitYears),
          biomethane_bonus_enabled:economicsInputs.biomethaneBonusEnabled,annual_biomethane_m3:annualBiomethaneM3,
          biomethane_bonus_eur_per_m3:economicsInputs.biomethaneBonusEurM3,biomethane_bonus_years:economicsInputs.biomethaneBonusYears,
          additional_benefit_eur_per_year:economicsInputs.additionalBenefitEurYear,additional_benefit_years:economicsInputs.additionalBenefitYears,
          ...(economicsInputs.capexGrantFraction>0?{grant_awarding_organization:'RVO (DEI+)',grant_scenario_name:'CAPEX grant'}:{}),
          ...((economicsInputs.biomethaneBonusEnabled||economicsInputs.additionalBenefitEurYear>0)?{operating_support_awarding_organization:'RVO SDE++',opex_support_scenario_name:'Operating support'}:{}),
        };
        configuration.climate_factors={
          electricity:{factor_id:'electricity',value:Number(environmentInputs.electricityKgCo2eKwh),quantity_unit:'kWh',source_status:'user_screening_override',basis:'User-entered Dutch electricity screening factor; baseline midpoint of the supplied 0.254–0.274 kg CO₂e/kWh range.',geography:'Netherlands',reference_year:2025,source_url:'https://www.electricitymaps.com/grid-in-review-2025/the-netherlands; https://carbonrecycling.co.uk/emission-factors/electricity/netherlands',source_table_page:'2025 Dutch electricity intensity; user-supplied screening range',retrieval_date:'2026-11-04',evidence_class:'national_average_proxy',applicability:'Operational average-grid factor; replace with supplier-specific value when available.',conversion_method:'identity',uncertainty:'0.254–0.274 kg CO₂e/kWh supplied range; not a probability distribution',warning:'National average proxy, not a site supplier factor.'},
          heat:{factor_id:'heat',value:Number(environmentInputs.heatKgCo2eKwh),quantity_unit:'kWh',source_status:'user_screening_override',basis:'User-entered Dutch average heat-network factor; baseline 30.96 kg CO₂e/GJ converted using 1 GJ = 277.7778 kWh.',geography:'Netherlands',reference_year:2022,source_url:'https://cedelft.eu/publications/chain-emissions-for-heat-grids-in-2022-and-2030/',source_table_page:'End-user heat-grid factor, 2022',retrieval_date:'2026-11-04',evidence_class:'national_average_factor',applicability:'Dutch average heat-network factor; plant-specific network mix may differ.',conversion_method:'kg CO₂e/GJ ÷ 277.7778 kWh/GJ',uncertainty:'No probability distribution supplied.',warning:'Average heat-network factor, not a supplier-specific plant factor.'},
        };
        const report=await decisionApi<DecisionReport>('evaluate',{configuration});
        if(requestNumber===analysisRequest.current)setAnalysisReport(report);
      } catch(error) {
        console.error('Post-route TEA/LCA calculation was unavailable.',error);
        if(requestNumber===analysisRequest.current){const detail=error instanceof Error?error.message:'Post-route TEA/LCA assessment could not be loaded.';setLimitations(current=>[...current.filter(item=>!item.startsWith('Post-route assessment:')),`Post-route assessment: ${detail}`]);}
      }} )();
    } catch (error) {
      if(requestNumber!==analysisRequest.current)return;
      const detail=error instanceof Error ? error.message : 'The simulation request could not be completed.';
      const status=typeof error==='object'&&error!==null&&'status' in error?Number((error as {status?:unknown}).status):undefined;
      const rejected=Number.isFinite(status)&&status!>=400&&status!<500;
      const label=rejected?`Simulation request rejected (HTTP ${status})`:status?`Backend error (HTTP ${status})`:runtime==='python'?'Simulation failed · previous live result kept':'Backend unavailable · preview shown';
      setLimitations([detail]);
      setModelWarnings([]);
      setSourceState({status:rejected?'request_failed':runtime==='python'?'stale_previous_result':'backend_unavailable',label,detail,is_live:false,...(runtime==='fallback'?{fixture_version:PREVIEW_BASELINE_STATUS.fixture_version}:{})});
      if (navigateToResults) { setTab('explore'); setExploreView('performance'); }
    } finally { if(requestNumber===analysisRequest.current)setRunning(false); }
  }

  async function runEmpiricalComparison() {
    if (runtime !== 'python') return;
    setComparisonRunning(true); setComparisonError('');
    try {
      const normalizedFeedComposition=normalizeFeedCompositionForRequest(feedComposition);
      const processRequest=buildPythonRequest(mode, month, scenario, feed, biomassSchedule, 'steady_state', null, normalizedFeedComposition, processDesignOverrides);
      const raw = await runPythonSimulation(processRequest);
      const envelope = normalizeResult(raw, result);
      if(envelope.source!=='python-api'||!raw?.run_id||raw.request_id!==processRequest.request_id||envelope.result.run_id!==raw.run_id||raw.run_id===result.run_id)throw new Error('The Python backend did not return a new result for this comparison request.');
      const resources = await fetchRunResources(envelope.result.run_id, raw.plots || []);
      setEmpiricalComparison({...envelope.result, annual:resources.annual, plots:resources.plots.length?resources.plots:envelope.result.plots});
    } catch (error) {
      setComparisonError(error instanceof Error?error.message:'The empirical comparison run failed.');
    } finally { setComparisonRunning(false); }
  }

  function runParetoCandidate(candidate:any) {
    const configuration=candidate?.configuration||{};
    const request=configuration.simulation||{};
    const selected=request.scenarios||{};
    const rate=Number(request.wet_feed_rate_kg_hr??request.plant_capacity_kg_hr);
    const annualTarget=Number.isFinite(rate)&&rate>0?rate*8760/1000:biomassSchedule.annual_processed_biomass_tonnes;
    const econ=configuration.candidate_economics||{};
    setScenario(current=>({...current,
      feed_front_end:selected.feed_preparation||selected.feed_front_end||current.feed_front_end,
      protein_recovery:selected.protein_recovery||'PR0',
      anaerobic_digestion:selected.anaerobic_digestion||'AD0',
      biogas_upgrading:selected.biogas_upgrading||'BG0',
      nutrient_recovery:selected.nutrient_recovery||'NR0',
      process_order:selected.process_order||current.process_order,
    }));
    setMode((request.calculation_mode||'structural') as CalculationMode);
    setMonth(request.selected_month||'July');
    setBiomassSchedule(current=>({...current,
      annual_available_biomass_tonnes:Math.max(current.annual_available_biomass_tonnes,annualTarget),
      annual_processed_biomass_tonnes:annualTarget,
      collection_refinery_fraction:1,
      feed_basis:'tonnes_per_year',
      feed_kg_per_hr:rate>0?rate:current.feed_kg_per_hr,
    }));
    if(request.operating_schedule)setFeed(current=>({...current,
      operatingDaysPerWeek:Number(request.operating_schedule.operating_days_per_week)||current.operatingDaysPerWeek,
      operatingHoursPerDay:Number(request.operating_schedule.operating_hours_per_day)||current.operatingHoursPerDay,
    }));
    setEconomicsInputs(current=>({...current,
      totalCapexOverride:'',
      projectLifetimeYears:Number(econ.project_lifetime_years)||current.projectLifetimeYears,
      discountRate:Number(econ.discount_rate)||current.discountRate,
      taxRate:Number(econ.tax_rate??current.taxRate),
      capexGrantFraction:Number(econ.capex_grant_fraction)||0,
      biomethaneBonusEnabled:Number(econ.opex_premium_eur_per_nm3_biomethane)>0,
      biomethaneBonusEurM3:Number(econ.opex_premium_eur_per_nm3_biomethane)||current.biomethaneBonusEurM3,
      biomethaneBonusYears:Number(econ.opex_support_years)||current.biomethaneBonusYears,
      additionalBenefitEurYear:0,
      additionalBenefitYears:0,
    }));
    setPendingParetoCandidate(candidate);
  }

  useEffect(()=>{
    if(!pendingParetoCandidate)return;
    const label=pendingParetoCandidate.scenario_label||pendingParetoCandidate.sample_id||'Pareto candidate';
    setPendingParetoCandidate(null);
    void executeRun(`Pareto · ${label}`,true);
  },[pendingParetoCandidate]);

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
  const capexEstimateFromRun=analysisReport?.tea?.candidate_economics?.capex_estimate_before_override_eur
    ?? analysisReport?.tea?.candidate_economics?.high_direct_capex_eur
    ?? analysisReport?.tea?.totals?.high_direct_capex_eur
    ?? analysisReport?.tea?.totals?.partial_direct_capex_eur;
  const changedParameters = parameters.filter(item => item.current_value !== item.default_value);
  const visibleParameters = parameters.filter(item => parameterView === 'advanced' ? item.category === 'advanced' : item.category === 'basic');
  const activeProcessParameters=processParameterDefinitions.filter(item=>item.when(scenario));
  const processDesignOverrides=activeProcessParameters.map(item=>({parameter_id:item.id,value:processInputParameters[item.id]??item.defaultValue,unit:item.unit,reason:'User-entered Configure > Process advanced parameter'}));
  const tabs: [TabId, string, LucideIcon][] = [
    ['dashboard', 'Dashboard', Gauge], ['configure', 'Configure', Settings2], ['explore', 'Results', BarChart3],
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
    <nav className="primary-nav" aria-label="Application sections">
      {tabs.map(([id,label,Icon]) => <button key={id} className={tab === id || (id==='explore' && (tab==='model-comparison')) ? 'active' : ''} onClick={() => setTab(id)}><Icon size={16}/>{label}</button>)}
    </nav>
    <main className="workspace">
      {running && <section className="run-progress" role="status" aria-live="polite"><span className="progress-spinner"/><div><strong>Calculating the annual GreenHub plan</strong><p>Processing monthly feed availability, unit performance, products, utilities and balance checks.</p></div></section>}
      {tab === 'dashboard' && <Overview result={result} activeUnits={activeUnits} analysis={analysisReport} warnings={modelWarnings} limitations={limitations} onConfigure={() => setTab('configure')} onResults={() => {setTab('explore');setExploreView('performance');}}/>}
      {tab === 'configure' && <div className={`page-stack${configureView==='Economics'?' economic-configure-page':''}`}>
        <PageIntro eyebrow="Configure" title="Change process inputs" text="Edit the baseline inputs by category. Values entered here take priority for the next simulation."/>
        <div className="section-switcher configure-switcher" role="tablist" aria-label="Input categories">{(['Biomass','Process','Economics','Environment'] as ConfigureView[]).map(view=><button key={view} role="tab" aria-selected={configureView===view} className={configureView===view?'active':''} onClick={()=>setConfigureView(view)}>{view}</button>)}</div>
        {configureView==='Biomass'&&<>
        <SectionHeading title="Feed schedule" text="Set annual grass availability, its collection season, and the wait before processing starts."/>
        <FeedScheduleControls value={biomassSchedule} onChange={next=>{setBiomassSchedule(next);markRunStaleAfterInputEdit();}}/>
        <section className="panel storage-controls biomass-storage-panel">
          {scenario.protein_recovery==='PR7' ? <p className="method-note">Storage degradation is unavailable for PR7: this route starts with clarified juice and has no pre-fermentation step.</p> : <>
            <label className="storage-toggle"><input type="checkbox" checked={storageConditions.enabled} onChange={event=>{setStorageConditions(current=>({...current,enabled:event.target.checked,storageDays:event.target.checked&&current.storageDays===0?14:current.storageDays}));markRunStaleAfterInputEdit();}}/><span><strong>Include biochemical storage degradation</strong><small>Add storage reactions separately from the processing wait above.</small></span></label>
            {storageConditions.enabled&&<div className="ds-controls"><label>Reaction residence <span><input type="number" min="0" max="366" value={storageConditions.storageDays} onChange={event=>{setStorageConditions(current=>({...current,storageDays:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>days</em></span></label><label>Air exposure fraction <span><input type="number" min="0" max="1" step="0.05" value={storageConditions.aerobicFraction} onChange={event=>{setStorageConditions(current=>({...current,aerobicFraction:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>fraction</em></span></label><label>Storage temperature <span><input type="number" min="-20" max="60" value={storageConditions.temperatureC} onChange={event=>{setStorageConditions(current=>({...current,temperatureC:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>°C</em></span></label><label>Moisture activity <span><input type="number" min="0" max="1" step="0.05" value={storageConditions.moistureActivity} onChange={event=>{setStorageConditions(current=>({...current,moistureActivity:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>fraction</em></span></label></div>}
          </>}
        </section>
        <FeedCompositionEditor value={feedComposition} onChange={(id,next)=>{setFeedComposition(current=>({...current,[id]:next}));markRunStaleAfterInputEdit();}}/>
        </>}
        {configureView==='Process'&&<>
        <SectionHeading title="Process route" text="Set the operating schedule, select products, and choose a supported technology for each selected route."/>
        <section className="panel draft-input-panel">
          <div className="panel-title"><span className="title-icon"><Clock3 size={17}/></span><div><h3>Operating schedule</h3><p>Annual target determines the feed processed; days and hours set the plant operating pattern.</p></div></div>
          <div className="draft-input-grid">
            <label>Operating days per week<span><input type="number" min="0" max="7" step="0.5" value={feed.operatingDaysPerWeek} onChange={event=>{setFeed(current=>({...current,operatingDaysPerWeek:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>days/week</em></span></label>
            <label>Operating hours per day<span><input type="number" min="0" max="24" step="0.5" value={feed.operatingHoursPerDay} onChange={event=>{setFeed(current=>({...current,operatingHoursPerDay:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>hours/day</em></span></label>
            <label>Annual processing target<span><input type="number" min="0" step="100" value={biomassSchedule.annual_processed_biomass_tonnes} onChange={event=>{setBiomassSchedule(current=>({...current,annual_processed_biomass_tonnes:Math.max(0,Number(event.target.value)||0)}));markRunStaleAfterInputEdit();}}/><em>t/year</em></span></label>
          </div>
        </section>
        <section className="panel product-route-panel">
          <div className="panel-title"><span className="title-icon"><PackageCheck size={17}/></span><div><h3>Product selection</h3><p>Select products first, then choose the technology route. Protein and biostimulant are mutually exclusive.</p></div></div>
          <div className="product-route-list">
            <ProductRouteRow title="Protein" checked={scenario.protein_recovery!=='PR0'&&scenario.protein_recovery!=='PR7'} onToggle={checked=>{setScenario(current=>({...current,protein_recovery:checked?'PR3':'PR0'}));markRunStaleAfterInputEdit();}}>
              <select aria-label="Protein technology" value={scenario.protein_recovery==='PR0'||scenario.protein_recovery==='PR7'?'PR3':scenario.protein_recovery} disabled={scenario.protein_recovery==='PR0'||scenario.protein_recovery==='PR7'} onChange={event=>{setScenario(current=>({...current,protein_recovery:event.target.value}));markRunStaleAfterInputEdit();}}>{scenarioGroups[1].options.filter(item=>['PR1','PR2','PR3'].includes(item[0])).map(item=><option key={item[0]} value={item[0]}>{item[1]}</option>)}</select>
            </ProductRouteRow>
            <ProductRouteRow title="Biostimulant" checked={scenario.protein_recovery==='PR7'} onToggle={checked=>{setScenario(current=>({...current,protein_recovery:checked?'PR7':'PR0'}));markRunStaleAfterInputEdit();}}>
              <select aria-label="Biostimulant membrane technology" value={biostimulantRoute.technology_id} disabled={scenario.protein_recovery!=='PR7'} onChange={event=>setBiostimulantRoute(current=>({...current,technology_id:event.target.value,flux_method:event.target.value==='MEUF'?'empirical':current.flux_method,flux_L_m2_h:event.target.value==='LNF'?12:event.target.value==='MEUF'?22.5:22,flux_source:`User-supplied GreenHub membrane dataset: ${event.target.value} baseline flux selection.`}))}><option value="TUF">Tight UF (TUF)</option><option value="LNF">Loose NF (LNF)</option><option value="MEUF">Micellar-enhanced UF (MEUF)</option></select>
            </ProductRouteRow>
            <ProductRouteRow title="Biomethane" checked={scenario.anaerobic_digestion!=='AD0'&&scenario.biogas_upgrading!=='BG0'} onToggle={checked=>{setScenario(current=>({...current,anaerobic_digestion:checked?'AD1':'AD0',biogas_upgrading:checked?'BG2':'BG0'}));markRunStaleAfterInputEdit();}}>
              <div className="product-route-selects"><select aria-label="Anaerobic digestion technology" value={scenario.anaerobic_digestion} disabled={scenario.anaerobic_digestion==='AD0'} onChange={event=>{setScenario(current=>({...current,anaerobic_digestion:event.target.value}));markRunStaleAfterInputEdit();}}>{scenarioGroups[2].options.filter(item=>['AD1','AD2','AD3','AD4'].includes(item[0])).map(item=><option key={item[0]} value={item[0]}>{item[1]}</option>)}</select><select aria-label="Biogas upgrading technology" value={scenario.biogas_upgrading} disabled={scenario.biogas_upgrading==='BG0'} onChange={event=>{setScenario(current=>({...current,biogas_upgrading:event.target.value}));markRunStaleAfterInputEdit();}}>{scenarioGroups[3].options.filter(item=>['BG1','BG2','BG3','BG4','BG5'].includes(item[0])).map(item=><option key={item[0]} value={item[0]}>{item[1]}</option>)}</select></div>
            </ProductRouteRow>
            <ProductRouteRow title="Nutrient products" checked={scenario.nutrient_recovery!=='NR0'} onToggle={checked=>{setScenario(current=>({...current,nutrient_recovery:checked?'NR4':'NR0'}));markRunStaleAfterInputEdit();}}>
              <select aria-label="Nutrient recovery technology" value={scenario.nutrient_recovery} disabled={scenario.nutrient_recovery==='NR0'} onChange={event=>{setScenario(current=>({...current,nutrient_recovery:event.target.value as ScenarioSelection['nutrient_recovery']}));markRunStaleAfterInputEdit();}}>{scenarioGroups[4].options.filter(item=>item[2]!=='planned').map(item=><option key={item[0]} value={item[0]}>{item[1]}</option>)}</select>
            </ProductRouteRow>
          </div>
        </section>
        <details className="panel process-advanced-inputs">
          <summary>Advanced parameters</summary>
          <p className="draft-input-note">Parameters shown depend on the selected technologies. Values are sent with the next simulation request.</p>
          <div className="draft-input-grid process-parameter-grid">
            {activeProcessParameters.map(item=><label key={item.id}>{item.label}<span><input type="number" min={item.min} max={item.max} step={item.step} value={processInputParameters[item.id]??item.defaultValue} onChange={event=>{setProcessInputParameters(current=>({...current,[item.id]:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>{item.unit}</em></span></label>)}
          </div>
          {scenario.protein_recovery==='PR7'&&<div className="process-advanced-membrane"><h4>Biostimulant membrane settings</h4><div className="ds-controls">
            <label>Flux method<select value={biostimulantRoute.flux_method} onChange={event=>{setBiostimulantRoute(current=>({...current,flux_method:event.target.value}));markRunStaleAfterInputEdit();}}><option value="empirical">Empirical screening flux</option><option value="resistance_model" disabled={biostimulantRoute.technology_id==='MEUF'}>Resistance model</option></select></label>
            {biostimulantRoute.flux_method==='empirical'&&<label>Permeate flux<span><input type="number" min="0.001" step="any" value={biostimulantRoute.flux_L_m2_h} onChange={event=>{setBiostimulantRoute(current=>({...current,flux_L_m2_h:Number(event.target.value),flux_source:''}));markRunStaleAfterInputEdit();}}/><em>L/(m²·h)</em></span></label>}
          </div><small>Membrane retention and flux evidence gates remain part of the run validation.</small></div>}
        </details>
        </>}
        {configureView==='Economics'&&<>
          <SectionHeading title="Economic inputs" text=""/>
          <section className="panel economic-input-panel"><div className="panel-title"><span className="title-icon"><Gauge size={17}/></span><div><h3>CAPEX</h3></div></div>
            <div className="draft-input-grid economic-grid capex-grid"><label>Total CAPEX (calculated by you)<span><input type="number" min="0" step="1000" placeholder="Input your calculated CAPEX" value={economicsInputs.totalCapexOverride} onChange={event=>{setEconomicsInputs(current=>({...current,totalCapexOverride:event.target.value}));markRunStaleAfterInputEdit();}}/><em>€</em></span></label><div className="economic-capex-auto"><button type="button" className="economic-reset" onClick={()=>{setEconomicsInputs(current=>({...current,totalCapexOverride:''}));markRunStaleAfterInputEdit();}}>Use automatic CAPEX</button><span>{capexEstimateFromRun==null?'Calculated after simulation':`Calculated CAPEX: €${Number(capexEstimateFromRun).toLocaleString(undefined,{maximumFractionDigits:0})}`}</span></div><p className="economic-capex-warning"><AlertTriangle size={14} aria-hidden="true"/><strong>LEAVE THIS FIELD UNTOUCHED IF YOU WANT CALCULATE CAPEX AUTOMATICALLY</strong></p></div>
          </section>
          <section className="panel economic-input-panel"><div className="panel-title"><span className="title-icon"><SlidersHorizontal size={17}/></span><div><h3>Operating costs</h3></div></div>
            <div className="draft-input-grid economic-grid">
              <EconomicNumberInput label="Staff" value={economicsInputs.staffingPeople} defaultValue={economicDefaults.staffingPeople} unit="people" step="1" onChange={value=>{setEconomicsInputs(current=>({...current,staffingPeople:Number(value)}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Paid hours per person" value={economicsInputs.paidHoursPerPerson} defaultValue={economicDefaults.paidHoursPerPerson} unit="hours/year" step="1" onChange={value=>{setEconomicsInputs(current=>({...current,paidHoursPerPerson:Number(value)}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Labor rate" value={economicsInputs.laborCostEurPerHour} defaultValue={economicDefaults.laborCostEurPerHour} unit="€/person/hour" step="0.1" onChange={value=>{setEconomicsInputs(current=>({...current,laborCostEurPerHour:Number(value)}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Electricity rate" value={economicsInputs.electricityCostEurMWh/1000} defaultValue={economicDefaults.electricityCostEurMWh/1000} unit="€/kWh" step="0.001" onChange={value=>{setEconomicsInputs(current=>({...current,electricityCostEurMWh:Number(value)*1000}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Heat rate" value={economicsInputs.heatCostEurMWh} defaultValue={economicDefaults.heatCostEurMWh} unit="€/MWh" step="1" onChange={value=>{setEconomicsInputs(current=>({...current,heatCostEurMWh:Number(value)}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Cooling rate" value={economicsInputs.coolingCostEurMWh} defaultValue="" placeholder="No rate set" unit="€/MWh" step="1" onChange={value=>{setEconomicsInputs(current=>({...current,coolingCostEurMWh:value}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Logistics rate" value={economicsInputs.logisticsCostEurTkm} defaultValue="0" placeholder="0" unit="€/t·km" step="0.001" onChange={value=>{setEconomicsInputs(current=>({...current,logisticsCostEurTkm:value}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Feed haul distance" value={economicsInputs.logisticsDistanceKm} defaultValue="0" placeholder="0" unit="km" step="1" onChange={value=>{setEconomicsInputs(current=>({...current,logisticsDistanceKm:value}));markRunStaleAfterInputEdit();}}/>
            </div>
          </section>
          <section className="panel economic-input-panel"><div className="panel-title"><span className="title-icon"><Clock3 size={17}/></span><div><h3>Finance inputs</h3></div></div>
            <div className="draft-input-grid economic-grid">
              <EconomicNumberInput label="Project lifetime" value={economicsInputs.projectLifetimeYears} defaultValue={economicDefaults.projectLifetimeYears} unit="years" min={1} max={200} step="1" onChange={value=>{setEconomicsInputs(current=>({...current,projectLifetimeYears:Number(value)}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Discount rate" value={economicsInputs.discountRate*100} defaultValue={economicDefaults.discountRate*100} unit="%" min={0} max={100} step="0.1" onChange={value=>{setEconomicsInputs(current=>({...current,discountRate:Number(value)/100}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Tax rate" value={economicsInputs.taxRate*100} defaultValue={economicDefaults.taxRate*100} unit="%" min={0} max={100} step="0.1" onChange={value=>{setEconomicsInputs(current=>({...current,taxRate:Number(value)/100}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Working capital" value={economicsInputs.workingCapitalEur} defaultValue={economicDefaults.workingCapitalEur} unit="€" step="1000" onChange={value=>{setEconomicsInputs(current=>({...current,workingCapitalEur:Number(value)}));markRunStaleAfterInputEdit();}}/>
              <EconomicNumberInput label="Residual value" value={economicsInputs.residualValueEur} defaultValue={economicDefaults.residualValueEur} unit="€" step="1000" onChange={value=>{setEconomicsInputs(current=>({...current,residualValueEur:Number(value)}));markRunStaleAfterInputEdit();}}/>
            </div>
          </section>
          <section className="panel economic-input-panel"><div className="panel-title"><span className="title-icon"><ShieldCheck size={17}/></span><div><h3>Subsidies and benefits</h3></div></div>
            <div className="grant-options" role="group" aria-label="Upfront CAPEX grant coverage">{[0,30,45,60].map(percent=><label key={percent} className={economicsInputs.capexGrantFraction===percent/100?'selected':''}><input type="checkbox" checked={economicsInputs.capexGrantFraction===percent/100} onChange={()=>{setEconomicsInputs(current=>({...current,capexGrantFraction:percent/100}));markRunStaleAfterInputEdit();}}/><span>{percent}% CAPEX</span></label>)}</div>
            <label className="storage-toggle economics-toggle"><input type="checkbox" checked={economicsInputs.biomethaneBonusEnabled} onChange={event=>{setEconomicsInputs(current=>({...current,biomethaneBonusEnabled:event.target.checked}));markRunStaleAfterInputEdit();}}/><span><strong>Include biomethane bonus</strong></span></label>
            {economicsInputs.biomethaneBonusEnabled&&<div className="draft-input-grid economic-grid subsidy-fields"><EconomicNumberInput label="Bonus rate" value={economicsInputs.biomethaneBonusEurM3} defaultValue={economicDefaults.biomethaneBonusEurM3} unit="€/m³" step="0.01" onChange={value=>{setEconomicsInputs(current=>({...current,biomethaneBonusEurM3:Number(value)}));markRunStaleAfterInputEdit();}}/><EconomicNumberInput label="Bonus duration" value={economicsInputs.biomethaneBonusYears} defaultValue={economicDefaults.biomethaneBonusYears} unit="years" max={200} step="1" onChange={value=>{setEconomicsInputs(current=>({...current,biomethaneBonusYears:Number(value)}));markRunStaleAfterInputEdit();}}/></div>}
            <div className="draft-input-grid economic-grid subsidy-fields"><EconomicNumberInput label="Additional benefit" value={economicsInputs.additionalBenefitEurYear} defaultValue={economicDefaults.additionalBenefitEurYear} unit="€/year" step="1000" onChange={value=>{setEconomicsInputs(current=>({...current,additionalBenefitEurYear:Number(value)}));markRunStaleAfterInputEdit();}}/><EconomicNumberInput label="Benefit duration" value={economicsInputs.additionalBenefitYears} defaultValue={economicDefaults.additionalBenefitYears} unit="years" max={200} step="1" onChange={value=>{setEconomicsInputs(current=>({...current,additionalBenefitYears:Number(value)}));markRunStaleAfterInputEdit();}}/></div>
          </section>
          <section className="panel economic-input-panel"><div className="panel-title"><span className="title-icon"><PackageCheck size={17}/></span><div><h3>Product prices</h3></div></div>
            <div className="draft-input-grid economic-grid">{(Object.keys(productPriceLabels) as (keyof typeof baselineProductPrices)[]).map(id=><EconomicNumberInput key={id} label={productPriceLabels[id].label} value={economicsInputs.productPrices[id]} defaultValue={baselineProductPrices[id]} unit={productPriceLabels[id].unit} step="any" onChange={value=>{setEconomicsInputs(current=>({...current,productPrices:{...current.productPrices,[id]:Number(value)}}));markRunStaleAfterInputEdit();}}/>)}</div>
          </section>
        </>}
        {configureView==='Environment'&&<>
          <SectionHeading title="Environmental assumptions" text="Factory-gate operational climate factors. No avoided-emissions or product-storage credit is applied here."/>
          <section className="panel draft-input-panel"><div className="draft-input-grid">
            <label>Electricity emissions factor<span><input type="number" min="0" step="0.001" value={environmentInputs.electricityKgCo2eKwh} onChange={event=>{setEnvironmentInputs(current=>({...current,electricityKgCo2eKwh:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>kg CO₂e/kWh</em></span><small>Baseline midpoint: 0.264; supplied range 0.254–0.274.</small></label>
            <label>Heat emissions factor<span><input type="number" min="0" step="0.001" value={environmentInputs.heatKgCo2eKwh} onChange={event=>{setEnvironmentInputs(current=>({...current,heatKgCo2eKwh:Number(event.target.value)}));markRunStaleAfterInputEdit();}}/><em>kg CO₂e/kWh</em></span><small>Baseline 30.96 kg CO₂e/GJ, converted to 0.1115 kg CO₂e/kWh.</small></label>
          </div><p className="draft-input-note">Electricity reference: Netherlands average, 2025. Heat reference: Netherlands average heat-network mix, 2022. These are screening averages rather than supplier-specific factors.</p></section>
        </>}
      </div>}
      {tab === 'explore' && <div className="page-stack"><PageIntro eyebrow="Results" title="Performance and decisions" text={exploreView==='optimization'?'BioSTEAM Pareto results':'Process performance and contribution data'}/><div className="section-switcher" role="tablist" aria-label="Results views">{([['performance','Performance'],['inventory','Inventory'],['hotspots','Hotspots'],['optimization','Optimization'],['model-comparison','Model comparison']] as [ExploreView,string][]).map(([id,label])=><button role="tab" aria-selected={exploreView===id} className={exploreView===id?'active':''} key={id} onClick={()=>setExploreView(id)}>{label}</button>)}</div>{exploreView==='performance'&&<ResultsWorkbench result={result} graph={graph} artifacts={artifacts} analysis={analysisReport} limitations={limitations} runtime={runtime==='python'?(result.resolution_mode==='steady_state'?'Steady-state process model':'Quasi-dynamic process model'):'Preview baseline'} sourceState={sourceState} savedRuns={savedRuns} onSaveRun={saveSnapshot}/ >}{exploreView==='inventory'&&<InventoryPage analysis={analysisReport}/ >}{exploreView==='hotspots'&&<ProcessHotspots result={result} analysis={analysisReport}/ >}{exploreView==='optimization'&&<ParetoScreening onApplyCandidate={runParetoCandidate} applying={running}/ >}{exploreView==='model-comparison'&&<ModelComparisonPanel dynamic={result} empirical={empiricalComparison} live={runtime==='python'} busy={comparisonRunning} onRun={runEmpiricalComparison} error={comparisonError}/>}</div>}
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

function Overview({ result, activeUnits, analysis, warnings=[], limitations=[], onConfigure, onResults }: any) {
  const annual = result.annual;
  const visibleAreas=Object.values(result.process_areas).filter((area:any)=>!['feedstock_and_characterization','shared_utilities_and_supporting_operations'].includes(area.id));
  const areaLimitations=visibleAreas.flatMap((area:any)=>area.limitations||[]);
  const warningNotes=[...new Set([...(warnings||[]),...(result.validation?.issues||[]).filter((issue:any)=>issue.severity==='warning'||issue.severity==='error').map((issue:any)=>issue.message)].filter(Boolean))];
  const limitationNotes=[...new Set([...(limitations||[]),...areaLimitations].filter(Boolean))];
  const tea=analysis?.tea?.totals||{},candidate=analysis?.tea?.candidate_economics||{},finance=analysis?.tea?.financial_kpis||{},lca=analysis?.lca?.totals||{};
  const climateKg=lca.climate_kg_co2e_per_year??lca.partial_climate_kg_co2e_per_year;
  const value=(number:any,digits=0)=>number==null||!Number.isFinite(Number(number))?'Incomplete':Number(number).toLocaleString(undefined,{maximumFractionDigits:digits});
  const outcomes=[
    ['Feed processed',value(annual?.feed_processed?.value!=null?annual.feed_processed.value/1000:null), 't/year', 'green'],
    ['NPV',value(tea.proxy_npv_eur??candidate.proxy_npv_eur??finance.npv_eur), '€', 'blue'],
    ['CAPEX',value(tea.high_direct_capex_eur??tea.partial_direct_capex_eur??tea.total_installed_capex_eur), '€', 'yellow'],
    ['OPEX',value(tea.annual_opex_eur), '€/year', 'yellow'],
    ['Profit per year',value(tea.operating_profit_during_support_eur_per_year??tea.partial_operating_margin_eur_per_year??tea.net_operating_margin_eur_per_year), '€/year', 'rose'],
    ['Emissions',value(climateKg==null?null:Number(climateKg)/1000,1), 't CO₂e/year', 'blue'],
  ];
  return <div className="page-stack">
    <section className="overview-head">
      <div><h1>Overview</h1></div>
      <div className="overview-actions"><button className="run-button" onClick={onConfigure}><Settings2 size={16}/>Configure pathway</button><button className="secondary" onClick={onResults}><Activity size={16}/>View results</button></div>
    </section>
    <section className="kpi-grid">{outcomes.map(([label,amount,unit,color]: any[]) => <div className="kpi" key={String(label)} title={label==='Profit per year'?'Includes annual operating support while active, including the biomethane bonus. Excludes CAPEX grants, tax and capital recovery; CAPEX grants affect upfront investment and NPV.':label==='OPEX'?'Known screened OPEX lines only. Unresolved cost items remain listed as missing in the TEA report.':label==='CAPEX'?'High direct screening CAPEX. Equipment scaling and unscaled reference packages are shown in the TEA cost detail.':undefined}><span>{label}</span><div className={`kpi-value-line ${String(color)}`}><strong>{amount}</strong><small>{unit}</small></div></div>)}</section>
    <BaselineTimeSeries annual={annual} nutrientRecovery={result.scenarios.nutrient_recovery}/>
    <section className="overview-grid">
      <div className="panel"><PanelTitle icon={<Layers3/>} title="Current process pathway" text={`${activeUnits} active units across ${visibleAreas.length} process areas.`}/><div className="process-strip">{visibleAreas.map((area:any,index:number) => <React.Fragment key={area.id}><div className="process-node"><span>{String(index+1).padStart(2,'0')}</span><strong>{areaLabels[area.id] || area.name}</strong><small>{area.units.length} units</small></div>{index < visibleAreas.length-1 && <b>→</b>}</React.Fragment>)}</div></div>
    </section>
    <details className="overview-notes"><summary>Warnings and model limitations</summary><div className="overview-notes-content">{warningNotes.length>0&&<section><h3>Warnings</h3><ul>{warningNotes.map((note:string,index:number)=><li key={`warning-${index}`}>{note.replace(/[_]+/g,' ')}</li>)}</ul></section>}{limitationNotes.length>0&&<section><h3>Model limitations</h3><ul>{limitationNotes.map((note:string,index:number)=><li key={`limitation-${index}`}>{note.replace(/[_]+/g,' ')}</li>)}</ul></section>}{warningNotes.length===0&&limitationNotes.length===0&&<p>No run-specific warnings or limitations were returned. Results still depend on the selected model routes and available input evidence.</p>}</div></details>
  </div>;
}

function ProductRouteRow({title,checked,onToggle,children}:{title:string;checked:boolean;onToggle:(checked:boolean)=>void;children:React.ReactNode}) {
  return <div className={`product-route-row${checked?' selected':''}`}><label className="product-route-check"><input type="checkbox" checked={checked} onChange={event=>onToggle(event.target.checked)}/><strong>{title}</strong></label><div className="product-route-choice">{children}</div></div>;
}

function FeedScheduleControls({value,onChange}:{value:EmpiricalBiomassSchedule;onChange:(next:EmpiricalBiomassSchedule)=>void}) {
  const update = <K extends keyof EmpiricalBiomassSchedule>(key:K, next:EmpiricalBiomassSchedule[K]) => onChange({...value,[key]:next});
  const seasonMonth=(date:string)=>Number(date.slice(5,7))||1;
  const monthDate=(date:string,month:number)=>`${date.slice(0,4)}-${String(month).padStart(2,'0')}-15`;
  const setSeasonMonth=(edge:'start'|'end',month:number)=>{
    if(edge==='start'){
      const endMonth=seasonMonth(value.season_end);
      onChange({...value,season_start:monthDate(value.season_start,month),...(month>endMonth?{season_end:monthDate(value.season_end,month)}:{})});
    } else {
      const startMonth=seasonMonth(value.season_start);
      onChange({...value,season_end:monthDate(value.season_end,month),...(month<startMonth?{season_start:monthDate(value.season_start,month)}:{})});
    }
  };
  return <section className="panel empirical-schedule"><div className="schedule-primary">
    <label>Annual available biomass <span><input type="number" min="0" step="100" value={value.annual_available_biomass_tonnes} onChange={event=>update('annual_available_biomass_tonnes',Number(event.target.value)||0)}/><em>t/year</em></span></label>
    <label>Storage time <span><input type="number" min="0" max="365" step="1" value={value.processing_delay_days} onChange={event=>update('processing_delay_days',Math.max(0,Math.min(365,Math.trunc(Number(event.target.value)||0))))}/><em>days</em></span><small>Processing begins this many days after each biomass collection date.</small></label>
    <label>Available from <select value={seasonMonth(value.season_start)} onChange={event=>setSeasonMonth('start',Number(event.target.value))}>{monthLabels.map((label,index)=><option value={index+1} key={label}>{label}</option>)}</select></label>
    <label>Available to <select value={seasonMonth(value.season_end)} onChange={event=>setSeasonMonth('end',Number(event.target.value))}>{monthLabels.map((label,index)=><option value={index+1} key={label}>{label}</option>)}</select></label>
  </div></section>;
}

function FeedCompositionEditor({value,onChange}:{value:Record<string,number>;onChange:(id:string,next:number)=>void}) {
  const [openGroups,setOpenGroups]=useState(()=>new Set(['Water','Proteins and peptides','Carbohydrates and plant structure','Phytohormones']));
  const enteredTotalPercent=Object.values(value).reduce((sum,item)=>sum+(Number(item)||0),0);
  const compositionInRange=enteredTotalPercent>=FEED_COMPOSITION_TOTAL_MIN_PERCENT&&enteredTotalPercent<=FEED_COMPOSITION_TOTAL_MAX_PERCENT;
  return <section className="panel feed-composition-panel">
    <div className="panel-title"><span className="title-icon"><Layers3 size={17}/></span><div><h3>Feed composition</h3><p>Wet-mass amounts are shown in g/kg or mg/kg grass. Reset restores the sourced default.</p><small className={`composition-total-status${compositionInRange?'':' invalid'}`}>Input total {enteredTotalPercent.toFixed(2)}% · {compositionInRange?'normalized to 100% for simulation':'enter a total from 90% to 110% to run'}</small></div></div>
    <div className="feed-composition-layout">
      <aside className="feed-quality-legend" aria-label="Data class legend"><strong>Data class</strong>{Object.entries(feedQualityHelp).map(([key,text])=><div className="feed-quality-legend-row" key={key}><span className={`quality q-${key}`} title={text}>{key}</span><small>{text}</small></div>)}</aside>
      <div className="feed-compound-groups">{feedCompoundGroups.map(group=><details key={group.title} className="feed-compound-group" open={openGroups.has(group.title)} onToggle={event=>{const isOpen=event.currentTarget.open;setOpenGroups(current=>{const next=new Set(current);isOpen?next.add(group.title):next.delete(group.title);return next;});}}><summary>{group.title}<span>{group.items.length} compounds</span></summary><div className="feed-compound-list">{group.items.map(item=>{
        const percent=value[item.id]??0;
        const evidence=feedCompositionData[item.id];
        const itemQuality=evidence?.data_class??'D';
        const gramsPerKg=percent*10;
        const useMilligrams=gramsPerKg>0&&gramsPerKg<0.01;
        const displayedValue=useMilligrams?gramsPerKg*1000:gramsPerKg;
        return <div className="feed-compound-row" key={item.id}>
        <label className="feed-compound-name" htmlFor={`compound-${item.id}`}>{evidence?.label??item.label}</label>
        <div className="feed-compound-editor"><button type="button" className="compound-reset" onClick={()=>onChange(item.id,baselineFeedComposition[item.id]??0)} aria-label={`Reset ${item.label} to default`} title="Reset to default">Reset</button><span className="feed-composition-input"><input id={`compound-${item.id}`} type="number" min="0" step="any" value={Number(displayedValue.toPrecision(8))} onChange={event=>{const entered=Math.max(0,Number(event.target.value)||0);onChange(item.id,useMilligrams?entered/10000:entered/10);}} aria-label={`${item.label} amount per kilogram of wet grass`}/><em>{useMilligrams?'mg/kg':'g/kg'}{useMilligrams&&<span className="unit-caution" title="Check the unit carefully." aria-label="Check the unit carefully."><AlertTriangle size={11}/></span>}</em></span></div>
        <span className={`quality q-${itemQuality}`} title={`${itemQuality}: ${feedQualityHelp[itemQuality]}${evidence?.source?` · ${evidence.source.source}${evidence.source.doi?` · DOI ${evidence.source.doi}`:''} · ${evidence.source.basis}`:''}`} aria-label={`Data class ${itemQuality}`}>{itemQuality}</span>
      </div>})}</div></details>)}</div>
    </div>
  </section>;
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
function SectionHeading({title,text}:{title:string;text:string}) { return <header className="configure-section-heading"><span>{title}</span>{text&&<p>{text}</p>}</header>; }

function EconomicNumberInput({label,value,defaultValue,unit,step='any',min=0,max,placeholder,onChange,...rest}:{label:string;value:string|number;defaultValue:string|number;unit:string;step?:string;min?:number;max?:number;placeholder?:string;onChange:(value:string)=>void;key?:string}) {
  return <label className="economic-field">{label}<div className="economic-input-row"><button type="button" className="economic-reset" title="Reset to default" onClick={()=>onChange(String(defaultValue))}>Default</button><span><input type="number" min={min} max={max} step={step} placeholder={placeholder} value={value} onChange={event=>onChange(event.target.value)}/><em>{unit}</em></span></div></label>;
}
function PanelTitle({ icon,title,text }: any) { return <div className="panel-title"><span className="title-icon">{icon}</span><div><h3>{title}</h3><p>{text}</p></div></div>; }
