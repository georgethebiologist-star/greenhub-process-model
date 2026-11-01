import React,{useEffect,useMemo,useState} from 'react';
import {ScatterChart,Scatter,CartesianGrid,XAxis,YAxis,ZAxis,Tooltip,Legend,ResponsiveContainer,ReferenceLine} from 'recharts';
import {generateScreeningBatch,defaultRanges,defaultSettings,type Point,type Settings} from '../data/paretoScreening';
import {exportDecision} from '../data/decisionSupport';
import {backendJobApi,type BackendJob,decisionApi} from '../data/decisionSupport';
import {DecisionResults} from './DecisionSupport';

const fmt=(v:number|undefined|null,d=0)=>v==null||!Number.isFinite(Number(v))?'Incomplete':Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
const money=(v:number|undefined|null)=>v==null||!Number.isFinite(Number(v))?'Incomplete':new Intl.NumberFormat(undefined,{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(v);
const compact=(v:number)=>Math.abs(v)>=1e6?`${(v/1e6).toFixed(1)}m`:Math.abs(v)>=1000?`${(v/1000).toFixed(0)}k`:fmt(v);
const human=(s:string)=>String(s||'').replace(/([A-Z])/g,' $1').replaceAll('_',' ').replace(/^./,v=>v.toUpperCase());
const lastCompletedBackendJobId='eed439a280ad488aa235a19b0efc32af';
type BackendSample=BackendJob['samples'][number]&{objectives?:Record<string,any>;configuration?:Record<string,any>;source_sample_id?:string;rejection_reason?:string;feasibility?:any};
type BackendPoint={sample_id:string;source_sample_id?:string;profit:number;climate:number;pareto:boolean;technicalEligible:boolean;status:string};
type SubsidySettings={rate:number;cap:number;eligibleFraction:number;tax:number};

function objectivePoint(sample:BackendSample):BackendPoint|null {
  const profit=sample.objectives?.operating_profit,climate=sample.objectives?.climate;
  if(sample.status!=='evaluated'||!profit?.eligible||!climate?.eligible||!Number.isFinite(profit.value)||!Number.isFinite(climate.value))return null;
  return {sample_id:sample.sample_id,source_sample_id:sample.source_sample_id,profit:Number(profit.value),climate:Number(climate.value),pareto:false,technicalEligible:sample.feasibility?.eligible_for_ranking===true,status:sample.status};
}
function isDominated(candidate:BackendPoint,other:BackendPoint) {
  const a=candidate.profit<=other.profit&&candidate.climate>=other.climate;
  const strict=candidate.profit<other.profit||candidate.climate>other.climate;
  return a&&strict;
}
function BackendTooltip({active,payload}:any) {
  const point=payload?.[0]?.payload as BackendPoint|undefined;
  return active&&point?<div className="ds-point-tooltip"><strong>{point.source_sample_id||point.sample_id}{point.pareto?' · sampled Pareto point':''}</strong><dl className="ds-point-kpis"><dt>After-tax profit</dt><dd>{money(point.profit)}/year</dd><dt>Climate impact</dt><dd>{fmt(point.climate,1)} kg CO₂e/year</dd><dt>Technical/evidence gate</dt><dd>{point.technicalEligible?'Eligible':'Incomplete / conditional'}</dd></dl><small>Values are from backend objectives; inspect the candidate for full assumptions and LCA completeness.</small></div>:null;
}
function getSampleId(value:any):string|undefined{return value?.payload?.sample_id||value?.sample_id;}

export default function ParetoScreening(){
  const [seed,setSeed]=useState(42),[ranges,setRanges]=useState(()=>structuredClone(defaultRanges)),[settings,setSettings]=useState({...defaultSettings});
  const [subsidy,setSubsidy]=useState<SubsidySettings>({rate:.20,cap:250000,eligibleFraction:.35,tax:.258});
  const [batch,setBatch]=useState(()=>generateScreeningBatch()),[backendJob,setBackendJob]=useState<BackendJob|null>(null),[backendBase,setBackendBase]=useState<any>(null);
  const [backendBusy,setBackendBusy]=useState(false),[backendLoading,setBackendLoading]=useState(true),[backendError,setBackendError]=useState('');
  const [jobIdInput,setJobIdInput]=useState(lastCompletedBackendJobId);
  const [backendPoint,setBackendPoint]=useState<any>(null),[pointBusy,setPointBusy]=useState(false),[scenarioSearch,setScenarioSearch]=useState(''),[error,setError]=useState('');

  const loadJob=async(id:string)=>{
    const normalized=id.trim();if(!normalized){setBackendError('Enter a backend job ID.');return;}
    setBackendLoading(true);setBackendError('');setBackendPoint(null);
    try{const job=await backendJobApi.status(normalized);setBackendJob(job);setJobIdInput(normalized);if(typeof window!=='undefined')window.localStorage.setItem('greenhub.backendParetoJobId',normalized);}
    catch(e){setBackendJob(null);setBackendError(e instanceof Error?e.message:'The backend job could not be loaded. No preview points are substituted.');}
    finally{setBackendLoading(false);}
  };
  useEffect(()=>{
    decisionApi<any>('options').then(o=>setBackendBase(o.defaults)).catch(e=>setBackendError(e.message));
    const savedId=window.localStorage.getItem('greenhub.backendParetoJobId')||jobIdInput;
    if(savedId!==jobIdInput)setJobIdInput(savedId);
    void loadJob(savedId);
  },[]);
  useEffect(()=>{if(!backendJob||!['queued','running','cancelling'].includes(backendJob.status))return;const timer=window.setInterval(()=>backendJobApi.status(backendJob.job_id).then(setBackendJob).catch(e=>setBackendError(e.message)),2500);return()=>window.clearInterval(timer);},[backendJob?.job_id,backendJob?.status]);

  const objectivePoints=useMemo(()=>((backendJob?.samples||[]) as BackendSample[]).map(objectivePoint).filter((p):p is BackendPoint=>p!==null),[backendJob?.samples]);
  const backendFront=useMemo(()=>{
    const savedIds=new Set<string>((backendJob?.pareto_fronts||[]).filter((f:any)=>f.x_objective==='operating_profit'&&f.y_objective==='climate').flatMap((f:any)=>f.points||[]).map((p:any)=>String(p.sample_id)));
    const fromSaved=objectivePoints.filter(p=>savedIds.has(p.sample_id));
    const ids=fromSaved.length?savedIds:new Set(objectivePoints.filter(p=>!objectivePoints.some(q=>q.sample_id!==p.sample_id&&isDominated(p,q))).map(p=>p.sample_id));
    return objectivePoints.map(p=>({...p,pareto:ids.has(p.sample_id)}));
  },[backendJob,objectivePoints]);
  const front=useMemo(()=>backendFront.filter(p=>p.pareto),[backendFront]);
  const allSamples=(backendJob?.samples||[]) as BackendSample[];
  const filteredSamples=useMemo(()=>{const q=scenarioSearch.trim().toLowerCase();return allSamples.filter(s=>!q||`${s.source_sample_id||''} ${s.sample_id}`.toLowerCase().includes(q)).slice(0,100);},[allSamples,scenarioSearch]);
  const editSetting=(key:keyof Settings,value:number)=>setSettings(s=>({...s,[key]:value}));
  const selectBackend=async(id:string)=>{
    if(!id||!backendJob){setBackendPoint(null);return;}
    setPointBusy(true);setBackendPoint(null);setBackendError('');
    try{setBackendPoint(await backendJobApi.candidate(backendJob.job_id,id));}
    catch(e){setBackendError(e instanceof Error?e.message:'Candidate detail could not be loaded.');}
    finally{setPointBusy(false);}
  };
  const startBackend=async()=>{
    if(!backendBase)return;
    setBackendBusy(true);setBackendError('');setBackendPoint(null);
    try{
      const nextBatch=generateScreeningBatch(seed,ranges,settings);setBatch(nextBatch);
      const config=structuredClone(backendBase);
      config.use_screening_price_benchmarks=true;config.use_screening_process_assumptions=true;config.use_screening_lca_factors=true;
      config.financial_assumptions={...config.financial_assumptions,use_screening_price_benchmarks:true};
      const overrides=nextBatch.points.map((p:Point)=>({sample_id:p.id,overrides:{
        'simulation.wet_feed_rate_kg_hr':p.flowKgH,'simulation.plant_capacity_kg_hr':settings.maxFlowKgH,
        'simulation.scenarios.feed_preparation':p.routes.pef?'F2':'F1',
        'simulation.scenarios.protein_recovery':({'Bypass':'PR0','Acid':'PR1','Heat':'PR2','Acid + heat':'PR3'} as const)[p.routes.protein],
        'simulation.scenarios.anaerobic_digestion':({'Bypass':'AD0','Mesophilic':'AD1','Thermophilic':'AD3'} as const)[p.routes.digestion],
        'simulation.scenarios.biogas_upgrading':({'No product · flare':'BG0','Water scrubbing':'BG2','Membrane':'BG3','PSA':'BG4'} as const)[p.routes.gas],
        'simulation.scenarios.nutrient_recovery':({'Bypass':'NR0','Separation':'NR1','Phosphorus':'NR2','Ammonia':'NR3','Combined N/P':'NR4'} as const)[p.routes.fertilizer],
      },candidate_economics:{labour_reduction:p.assumptions.labourReduction,logistics_reduction:p.assumptions.logisticsReduction,energy_reduction:p.assumptions.energyReduction,protein_yield_uplift:p.assumptions.proteinYieldUplift,nutrient_recovery_uplift:p.assumptions.nutrientRecoveryUplift,subsidy_rate:subsidy.rate,subsidy_cap_eur:subsidy.cap,eligible_capex_fraction:subsidy.eligibleFraction,tax_rate:subsidy.tax,project_lifetime_years:settings.years,discount_rate:settings.discount}}));
      const started=await backendJobApi.start({configuration:config,candidate_overrides:overrides,count:overrides.length,seed,mode:'design'});
      setBackendJob(started);setJobIdInput(started.job_id);if(typeof window!=='undefined')window.localStorage.setItem('greenhub.backendParetoJobId',started.job_id);
    }catch(e){setBackendError(e instanceof Error?e.message:String(e));}
    finally{setBackendBusy(false);}
  };
  const regenerate=()=>{try{setBatch(generateScreeningBatch(seed,ranges,settings));setError('');}catch(e){setError(e instanceof Error?e.message:String(e));}};
  const isActive=!!backendJob&&['queued','running','cancelling'].includes(backendJob.status);
  const candidateOptions=allSamples;

  return <section className="panel ds-pareto" aria-label="Backend optimization and Pareto analysis">
    <div className="pareto-backend-heading"><div><span className="ds-badge">BACKEND-EVALUATED SCENARIOS</span><h2>Optimization trade-offs</h2><p>Points come from the saved backend batch or a new GreenHub process + TEA/LCA evaluation. The chart never substitutes pre-seed proxy scores.</p></div><div className="pareto-job-load"><label>Backend job ID<input value={jobIdInput} onChange={e=>setJobIdInput(e.target.value)} aria-label="Backend job ID"/></label><button className="secondary" onClick={()=>void loadJob(jobIdInput)} disabled={backendLoading}>Load backend results</button></div></div>
    {backendLoading&&<p role="status">Loading the saved backend scenario batch…</p>}
    {backendError&&<p role="alert" className="ds-warning">{backendError} Backend values are not replaced with preview data.</p>}
    {!backendJob&&!backendLoading&&<section className="pareto-empty"><strong>No backend batch is loaded.</strong><span>Load a saved job ID or submit a new backend evaluation below. The 2,000-point local sampler is only used to create candidate configurations.</span></section>}
    {backendJob&&<>
      <div className="ds-cards pareto-backend-kpis"><article><span>Requested</span><strong>{fmt(backendJob.requested_count)}</strong><small>Seed {backendJob.seed} · {backendJob.mode||'backend batch'}</small></article><article><span>Backend evaluated</span><strong>{fmt(backendJob.completed_count)}</strong><small>{fmt(backendJob.failed_count)} failed or rejected</small></article><article><span>Objective-ready points</span><strong>{fmt(objectivePoints.length)}</strong><small>Both returned objectives eligible</small></article><article><span>Sampled Pareto points</span><strong>{fmt(front.length)}</strong><small>Among backend objective-ready candidates</small></article></div>
      <div className="pareto-job-status" role="status">Job {backendJob.job_id} · {backendJob.status} · {backendJob.completed_count}/{backendJob.requested_count} evaluated. {backendJob.failed_count} rejected.</div>
      {objectivePoints.length>0?<>
        <div className="pareto-objective-heading"><div><h3>Backend profit vs climate impact</h3><p>Profit: maximize after tax and subsidy-adjusted annual capital recovery. Climate: minimize kg CO₂e/year; lower is better. Points may use a partial climate inventory—review each candidate’s LCA readiness. If the saved backend front is blocked by its technical completeness gate, the displayed frontier is recomputed from the returned eligible objective pairs only.</p></div><span className="ds-badge">PARETO AMONG SAMPLED BACKEND CANDIDATES</span></div>
        <div className="ds-pareto-chart pareto-backend-chart" role="img" aria-label="Backend-evaluated scenario scatter chart of annual profit versus climate impact"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:20,right:25,bottom:42,left:20}}><CartesianGrid strokeDasharray="3 3"/><XAxis type="number" dataKey="profit" name="After-tax profit" tickFormatter={compact} unit=" EUR/year" label={{value:'After-tax profit (EUR/year) · maximize',position:'insideBottom',offset:-24}} domain={['auto','auto']}/><YAxis type="number" dataKey="climate" name="Climate impact" tickFormatter={compact} unit=" kg CO₂e/year" label={{value:'Climate impact (kg CO₂e/year) · minimize',angle:-90,position:'insideLeft',offset:-8}} domain={['auto','auto']}/><ZAxis type="number" range={[34,34]}/><Tooltip content={<BackendTooltip/>} cursor={{strokeDasharray:'3 3'}}/><Legend verticalAlign="top"/><ReferenceLine x={0} stroke="#80958a"/><ReferenceLine y={0} stroke="#80958a"/><Scatter name="Objective-ready backend candidates" data={backendFront.filter(p=>!p.pareto)} fill="#5484bf" fillOpacity={.55} onClick={(v:any)=>{const id=getSampleId(v);if(id)void selectBackend(id);}} isAnimationActive={false}/><Scatter name="Sampled backend Pareto front" data={front} fill="#b77436" onClick={(v:any)=>{const id=getSampleId(v);if(id)void selectBackend(id);}} isAnimationActive={false}/></ScatterChart></ResponsiveContainer></div>
      </>:<div className="pareto-empty"><strong>No candidates currently have both objectives.</strong><span>Failed and incomplete scenarios remain selectable below, but cannot be plotted or ranked as complete points.</span></div>}
      <section className="pareto-scenario-browser"><div><h3>Inspect a backend scenario</h3><p>Select any evaluated, incomplete, or rejected candidate to see its exact configuration and, where available, full process, TEA and LCA outputs.</p></div><div className="pareto-scenario-controls"><label>Find source scenario<input value={scenarioSearch} onChange={e=>setScenarioSearch(e.target.value)} placeholder="Search sample ID"/></label><label>Scenario<select value={backendPoint?.sample_id||''} onChange={e=>void selectBackend(e.target.value)}><option value="">Choose a backend scenario…</option>{filteredSamples.map(s=><option key={s.sample_id} value={s.sample_id}>{s.source_sample_id||s.sample_id} · {s.status}{s.objectives?.operating_profit?.value!=null?` · ${money(s.objectives.operating_profit.value)}/year`:''}</option>)}</select></label></div><small>Showing {fmt(filteredSamples.length)} of {fmt(allSamples.length)} matching scenarios in the selector.</small></section>
      {pointBusy&&<p role="status">Loading full backend result for the selected scenario…</p>}
      {backendPoint&&<BackendScenarioDetails row={backendPoint}/>}
      <div className="ds-actions"><button className="secondary" onClick={()=>exportDecision(backendJob,'greenhub-backend-decision-batch.json')}>Export backend job summary</button>{backendPoint&&<button className="secondary" onClick={()=>exportDecision(backendPoint,`greenhub-${backendPoint.source_sample_id||backendPoint.sample_id}-full-result.json`)}>Export selected scenario + TEA/LCA</button>}{isActive&&<button className="secondary" onClick={()=>backendJobApi.cancel(backendJob.job_id).then(setBackendJob).catch(e=>setBackendError(e.message))}>Cancel backend job</button>}{backendJob.status==='cancelled'&&<button className="secondary" onClick={()=>backendJobApi.resume(backendJob.job_id).then(setBackendJob).catch(e=>setBackendError(e.message))}>Resume saved job</button>}</div>
    </>}
    <details className="pareto-design-controls"><summary>Design a new backend batch · scenario generator and optimization assumptions</summary><p>The local sampler below creates the 2,000 candidate configurations only. It does not calculate the graph values. Results appear above only after the backend evaluates them.</p><div className="ds-controls"><label>Random seed<input type="number" min="0" max="4294967295" step="1" value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label><label>Available biomass (t/year)<input type="number" min="1" value={settings.availableTonnes} onChange={e=>editSetting('availableTonnes',Number(e.target.value))}/></label><label>Annual operating hours<input type="number" min="1" max="8760" value={settings.hours} onChange={e=>editSetting('hours',Number(e.target.value))}/></label><label>Staff at full feed<input type="number" min="2" step="1" value={settings.fullScalePeople} onChange={e=>editSetting('fullScalePeople',Number(e.target.value))}/></label><label>Maximum plant flow (kg/h)<input type="number" min="1" value={settings.maxFlowKgH} onChange={e=>editSetting('maxFlowKgH',Number(e.target.value))}/></label><label>Project lifetime (years)<input type="number" min="1" max="60" value={settings.years} onChange={e=>editSetting('years',Number(e.target.value))}/></label><label>Discount rate (%)<input type="number" min="0" max="100" value={settings.discount*100} onChange={e=>editSetting('discount',Number(e.target.value)/100)}/></label><label>Subsidy rate (%)<input type="number" min="0" max="20" value={subsidy.rate*100} onChange={e=>setSubsidy(s=>({...s,rate:Number(e.target.value)/100}))}/></label><label>Subsidy cap (EUR)<input type="number" min="0" value={subsidy.cap} onChange={e=>setSubsidy(s=>({...s,cap:Number(e.target.value)}))}/></label><label>Eligible CAPEX share (%)<input type="number" min="0" max="100" value={subsidy.eligibleFraction*100} onChange={e=>setSubsidy(s=>({...s,eligibleFraction:Number(e.target.value)/100}))}/></label><label>Tax rate (%)<input type="number" min="0" max="100" value={subsidy.tax*100} onChange={e=>setSubsidy(s=>({...s,tax:Number(e.target.value)/100}))}/></label></div><div className="ds-actions"><button className="secondary" onClick={regenerate}>Preview candidate configurations</button><button className="run-button" onClick={()=>void startBackend()} disabled={backendBusy||!backendBase||isActive}>{backendBusy?'Submitting batch…':'Run 2,000 backend evaluations'}</button></div>{error&&<p role="alert" className="ds-warning">{error}</p>}<p>{fmt(batch.points.length)} candidate configurations currently generated · seed {batch.seed}. Proxy scores are not used as Pareto coordinates.</p></details>
    <details className="pareto-limitations"><summary>Optimization and evidence limitations</summary><ul><li>The frontend sampler chooses route combinations, feed rates and candidate-level optimization assumptions. Each plotted profit/climate value is returned by a backend process plus TEA/LCA evaluation.</li><li>Candidate optimization reductions and subsidy are transparent screening overlays, not verified retrofit performance, subsidy eligibility, or an investment approval. The selected scenario shows the exact overlay assumptions and calculated subsidy.</li><li>Climate points can be partial characterized inventory. They are plotted only when the backend supplies a finite eligible climate objective; inspect LCA readiness and missing inputs per scenario.</li><li>“Pareto among sampled backend candidates” is sample-bounded, not globally optimal. Incomplete objective pairs are retained in the job but omitted from the graph.</li></ul></details>
  </section>;
}

function BackendScenarioDetails({row}:{row:any}){
  const report=row.outputs;const tea=report?.tea||{};const totals=tea.totals||{};const economics=tea.candidate_economics||{};const assumptions=economics.assumptions||row.configuration?.candidate_economics||{};const lca=report?.lca||{};const impacts=lca.totals||{};const annual=report?.annual||{};const simulation=row.configuration?.simulation||{};
  const profit=report?.objectives?.operating_profit?.value;
  const climate=report?.objectives?.climate?.value??impacts.partial_climate_kg_co2e_per_year;
  const scenario=simulation.scenarios||{};
  return <section className="ds-selected-point pareto-backend-detail" aria-label="Selected backend scenario details">
    <div className="pareto-detail-head"><div><span className="eyebrow">Backend candidate · {row.status}</span><h3>{row.source_sample_id||row.sample_id}</h3><p>{report?.model_type||simulation.resolution_mode||'Process resolution not reported'} · {row.feasibility?.eligible_for_ranking?'eligible for ranking':'technical/evidence gate conditional or incomplete'}</p></div><span className={`ds-badge ${lca.readiness?.climate_objective_eligible?'':'ds-preview-flag'}`}>{lca.readiness?.climate_objective_eligible?'CLIMATE OBJECTIVE ELIGIBLE':'LCA INCOMPLETE / SCREENING'}</span></div>
    {row.rejection_reason&&<p className="ds-warning">Backend rejection: {row.rejection_reason}</p>}
    <div className="ds-cards pareto-candidate-kpis"><Kpi label="After-tax profit objective" value={money(profit)} unit="EUR/year · backend objective"/><Kpi label="Subsidy applied" value={money(economics.subsidy_eur??totals.subsidy_eur)} unit="candidate overlay"/><Kpi label="Optimization savings" value={money(economics.optimization_savings_eur_per_year??totals.optimization_savings_eur_per_year)} unit="EUR/year · OPEX overlay"/><Kpi label="Adjusted CAPEX" value={money(totals.subsidy_adjusted_capex_eur??economics.subsidy_adjusted_capex_eur)} unit="EUR · after subsidy"/><Kpi label="Climate impact" value={fmt(climate,1)} unit={impacts.climate_kg_co2e_per_year!=null?'kg CO₂e/year':'kg CO₂e · partial reported scope'}/><Kpi label="Annual wet feed" value={fmt(annual.feed_processed?.value/1000,1)} unit="tonnes / reported year"/><Kpi label="Protein product" value={fmt(annual.products?.dry_protein_product?.value/1000,2)} unit="tonnes / reported year"/><Kpi label="Biomethane" value={fmt(annual.products?.biomethane?.value/1000,2)} unit="tonnes / reported year"/></div>
    <details open><summary>Scenario configuration · routes, throughput, basis and candidate assumptions</summary><div className="pareto-configuration-grid"><ConfigFact label="Model / evidence" value={`${simulation.resolution_mode||'—'} · ${simulation.calculation_mode||'—'}`}/><ConfigFact label="Wet feed rate" value={`${fmt(simulation.wet_feed_rate_kg_hr,1)} kg/h`}/><ConfigFact label="Plant capacity" value={`${fmt(simulation.plant_capacity_kg_hr,1)} kg/h`}/><ConfigFact label="Operating schedule" value={`${fmt(simulation.operating_schedule?.operating_days_per_week)} days/week · ${fmt(simulation.operating_schedule?.operating_hours_per_day)} h/day`}/><ConfigFact label="Feed preparation" value={scenario.feed_preparation||'—'}/><ConfigFact label="Protein recovery" value={scenario.protein_recovery||'—'}/><ConfigFact label="Anaerobic digestion" value={scenario.anaerobic_digestion||'—'}/><ConfigFact label="Biogas upgrading" value={scenario.biogas_upgrading||'—'}/><ConfigFact label="Nutrient recovery" value={`${scenario.nutrient_recovery||'—'} · order ${scenario.process_order||'—'}`}/><ConfigFact label="Subsidy assumptions" value={`${fmt((assumptions.subsidy_rate??0)*100,1)}% rate · cap ${money(assumptions.subsidy_cap_eur)} · eligible CAPEX ${(Number(assumptions.eligible_capex_fraction??0)*100).toFixed(1)}%`}/><ConfigFact label="Finance assumptions" value={`${fmt((assumptions.tax_rate??0)*100,1)}% tax · ${fmt(assumptions.project_lifetime_years)} years · ${fmt((assumptions.discount_rate??0)*100,1)}% discount`}/></div><details><summary>Full exact request/configuration JSON</summary><pre>{JSON.stringify(row.configuration,null,2)}</pre></details></details>
    {report&&<><details open><summary>Optimization overlay and subsidy calculations</summary><div className="ds-cards pareto-candidate-kpis"><Kpi label="Base revenue" value={money(totals.base_annual_revenue_eur)} unit="EUR/year"/><Kpi label="Revenue uplift" value={money(economics.revenue_uplift_eur_per_year??totals.optimization_revenue_uplift_eur_per_year)} unit="EUR/year · optimization assumption"/><Kpi label="Base OPEX" value={money(totals.base_annual_opex_eur)} unit="EUR/year"/><Kpi label="Optimized OPEX" value={money(totals.optimized_annual_opex_eur)} unit="EUR/year"/><Kpi label="Tax applied" value={money(economics.tax_eur_per_year??totals.tax_eur_per_year)} unit="EUR/year"/><Kpi label="Annual capital recovery after subsidy" value={money(economics.annual_capital_recovery_after_subsidy_eur)} unit="EUR/year"/><Kpi label="Optimized after-tax profit" value={money(economics.optimized_after_tax_profit_eur_per_year??totals.optimized_after_tax_profit_eur_per_year)} unit="EUR/year"/><Kpi label="Subsidy-adjusted capital basis" value={money(totals.subsidy_adjusted_capex_eur)} unit="EUR"/></div><details><summary>Optimization assumptions and source config</summary><pre>{JSON.stringify({assumptions,calculated:economics,totals:{base_capex:totals.screening_capital_basis_eur,subsidy:totals.subsidy_eur,adjusted_capex:totals.subsidy_adjusted_capex_eur,annual_recovery:economics.annual_capital_recovery_after_subsidy_eur,optimized_profit:totals.optimized_after_tax_profit_eur_per_year}},null,2)}</pre></details></details><details open><summary>Full backend TEA + LCA report, balances and process outputs</summary><p className="pareto-overlay-warning">The TEA report retains base-case NPV/IRR/payback. The optimized-after-tax-profit objective and subsidy-adjusted capital recovery above are separate candidate overlays; they are not recalculated into the base financial KPIs.</p><DecisionResults report={report}/></details></>}
  </section>;
}
function Kpi({label,value,unit}:{label:string;value:string;unit:string}){return <article><span>{label}</span><strong>{value}</strong><small>{unit}</small></article>;}
function ConfigFact({label,value}:{label:string;value:string}){return <div><span>{label}</span><strong>{value}</strong></div>;}
