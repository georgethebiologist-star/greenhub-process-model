import React, { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { apiJson } from '../data/apiClient';

type ScreenResponse = {
  status: string;
  resistance_flux_result: null | {
    technology_id: string;
    pressure_bar: number;
    feed_to_reference_concentration_ratio: number;
    predicted_flux_L_m2_h: number;
    empirical_baseline_flux_L_m2_h: number;
  };
  film_retention_diagnostics: null | {
    technology_id: string;
    status: string;
    flux_L_m2_h?: number;
    applied_to_process_split: boolean;
    comparison_basis?: string;
    reason?: string;
    analytes: Array<{
      solute_id: string;
      weighted_state_retention_fraction: number;
      process_split_free_retention_fraction: number;
      process_split_bound_retention_fraction: number;
      film_free_retention_fraction: number;
      film_free_peclet_number: number;
      reflection_coefficient: number;
      bound_film_retention_fraction: number | null;
      bound_prediction_status: string;
    }>;
  };
  meuf_surfactant_screen: null | {
    status: string;
    surfactant: string;
    CMC_mmol_L: number;
    recovery_fraction: number;
    dose_low: { dose_mmol_L: number; gross_SDS_kg_year: number; recovered_SDS_kg_year: number; unrecovered_makeup_SDS_kg_year: number };
    dose_high: { dose_mmol_L: number; gross_SDS_kg_year: number; recovered_SDS_kg_year: number; unrecovered_makeup_SDS_kg_year: number };
    missing_for_TEA_LCA: string[];
    price_reference_only: { value: number; units: string; source_reference: string; source_status: string; source_date: string; model_use: string };
    price_references_only?: { value: number; units: string; source_reference: string; source_status: string; source_date: string; model_use: string }[];
  };
  cip_reagent_screen: null | {
    status: string;
    cip_events_year: number;
    solution_volume_L_per_step_per_event: number;
    makeup_fraction_per_cycle: number;
    naoh: { active_naoh_kg_year: number; purchased_50wt_solution_kg_year: number; cost_eur_year: number; price_eur_t: number };
    citric_acid: { citric_acid_kg_year: number; cost_eur_year: number; price_eur_t: number };
    total_reagent_cost_eur_year: number;
    cost_boundary: string;
    screening_lca: null | {
      status: string;
      naoh_production_kg_CO2e_year: number;
      citric_acid_production_kg_CO2e_year: number;
      total_chemical_production_kg_CO2e_year: number;
      factors: Array<{ chemical_id: string; value: string; quantity_unit: string; geography: string; reference_year: string; source_title: string; source_url: string; warning: string }>;
      excluded: string[];
    };
  };
  hormone_capture: Array<{
    solute_id: string;
    captured_total_kg_year: number;
    captured_free_kg_year: number | null;
    captured_bound_kg_year: number | null;
    total_retention_fraction: number;
    evidence_status: string;
    state_specific_capture_status: string;
  }>;
  membrane_screen: {
    membrane_area_m2: number;
    product_volume_L_year: number;
    gross_revenue_EUR_year: number;
    price_EUR_L: number;
    concentration_factor: number;
    flux_L_m2_h: number;
    flux_basis: string;
    membrane_module_capex_low_EUR: number;
    membrane_module_capex_high_EUR: number;
    annualized_replacement_low_EUR_year: number;
    annualized_replacement_high_EUR_year: number;
    fx_eur_per_usd: number;
    fx_date: string;
    fx_source: string;
  };
  tea_readiness: { status: string; missing_or_excluded: string[]; reference_only?: Array<{ item: string; value: string; source: string; note: string }> };
  lca_readiness: { status: string; missing_or_excluded: string[]; reference_only?: Array<{ item: string; value: string; source: string; note: string }> };
  energy_tea_lca_screen: {
    scope: string;
    climate_status: string;
    energy_climate_kg_co2e_year: number | null;
    known_energy_climate_subtotal_kg_co2e_year: number | null;
    climate_missing_inputs: string[];
    tea_status: string;
    energy_cost_eur_year: number | null;
    known_energy_cost_subtotal_eur_year: number | null;
    tea_missing_inputs: string[];
    by_utility: Record<string, {
      annual_energy_kwh: number | null;
      emission_factor_kg_co2e_kwh: number | null;
      energy_cost_eur_kwh: number | null;
      energy_climate_kg_co2e_year: number | null;
      energy_cost_eur_year: number | null;
      source_notes: Record<string, string>;
    }>;
    input_sources: Record<string, string>;
  };
  hydraulic_energy_estimate: null | {
    basis: string;
    permeate_volume_m3_year: number;
    transmembrane_pressure_bar: number;
    pump_efficiency_fraction: number;
    electricity_kwh_year: number;
    electricity_mwh_year: number;
  };
  biosteam_unit: null | {
    status: string;
    technology_id: string;
    operating_hours_year: number;
    flux_L_m2_h: number;
    membrane_area_m2: number | null;
    minimum_membrane_area_m2: number;
    maximum_membrane_area_m2: number | null;
    target_concentration_factor?: number;
    actual_volume_concentration_factor?: number | null;
    feed_volume_m3_hr?: number;
    product_volume_m3_hr?: number;
    product_stream_id: string;
    permeate_stream_id: string;
    unresolved_stream_id: string;
    product_kg_hr: Record<string, number>;
    permeate_kg_hr: Record<string, number>;
    unresolved_components_kg_hr: Record<string, number>;
    unresolved_mass_kg_hr: number;
    product_kg_year: number;
    permeate_kg_year: number;
    unresolved_kg_year: number;
    mass_closure_error_kg_hr: number;
    warnings: string[];
  };
  component_mass_split: null | {
    complete_mass_split: boolean;
    unmapped_component_ids: string[];
    assumed_solid_phase_component_ids: string[];
    screening_assumptions: string[];
    mass_error_kg_hr: number | null;
    retentate_by_class_kg_hr: Record<string, number>;
    permeate_by_class_kg_hr: Record<string, number>;
    unresolved_kg_hr: Record<string, number>;
  };
  mass_balance_readiness: null | {
    complete: boolean;
    component_fate_complete?: boolean;
    mass_balanced?: boolean;
    unmapped_nonzero_components: string[];
    unmapped_component_flows_kg_hr: Record<string, number>;
    mass_error_kg_hr: number | null;
  };
  component_mass_split_source: string | null;
  component_flows_source?: string | null;
  component_stream_id: string | null;
  component_retention_override_sources: Record<string, string>;
  component_balance: null | {
    complete: boolean;
    assumed_solid_phase_component_ids?: string[];
    screening_assumptions?: string[];
    feed_mass_kg_hr: number;
    retentate_mass_kg_hr: number | null;
    permeate_mass_kg_hr: number | null;
    mass_error_kg_hr: number | null;
    elements_kg_hr: Record<string, { feed: number; retentate: number; permeate: number; closure_error: number }> | null;
    elemental_balance_status: string;
  };
  feed_volume_consistency: null | {
    entered_volume_m3_year: number;
    stream_mass_flow_kg_hr: number;
    stream_implied_volume_m3_year: number;
    density_basis_kg_m3: number;
    density_source: string;
    difference_pct: number | null;
    status: string;
  };
};

export default function BiostimulantScreen({ runId }: { runId?: string }) {
  const [volume, setVolume] = useState('');
  const [hours, setHours] = useState('');
  const [concentrationFactor, setConcentrationFactor] = useState('10');
  const [priceEurL, setPriceEurL] = useState('2.50');
  const [cipInputs, setCipInputs] = useState({ solution_volume_L_per_step: '', makeup_fraction_per_cycle: '', source: '' });
  const [includeCipLca, setIncludeCipLca] = useState(false);
  const [technology, setTechnology] = useState('');
  const [fluxMethod, setFluxMethod] = useState<'empirical'|'resistance_model'>('empirical');
  const [resistanceInputs, setResistanceInputs] = useState({pressure_bar:'',pressure_source:'',feed_to_reference_concentration_ratio:'',ratio_source:'',viscosity_Pa_s:'',viscosity_source:''});
  const [useModelFlow, setUseModelFlow] = useState(false);
  const [componentFlowsJson, setComponentFlowsJson] = useState('');
  const [componentFlowsSource, setComponentFlowsSource] = useState('');
  const [overrideValues, setOverrideValues] = useState('{}');
  const [overrideSources, setOverrideSources] = useState('{}');
  const [utilityInputs, setUtilityInputs] = useState<Record<string, string>>({
    annual_electricity_mwh: '', electricity_kg_co2e_kwh: '', electricity_price_eur_kwh: '',
    annual_heat_mwh: '', heat_kg_co2e_kwh: '', heat_price_eur_kwh: '',
    transmembrane_pressure_bar: '', pump_efficiency_fraction: '',
  });
  const [utilitySources, setUtilitySources] = useState('{}');
  const [result, setResult] = useState<ScreenResponse | null>(null);
  const [comparison, setComparison] = useState<Array<{ technology_id: string; membrane_screen: ScreenResponse['membrane_screen']; hormone_capture: ScreenResponse['hormone_capture']; biosteam_unit: ScreenResponse['biosteam_unit'] }>>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  function componentFlowPayload() {
    const hasManual = componentFlowsJson.trim().length > 0;
    if (useModelFlow && hasManual) throw new Error('Choose either a completed model run or caller-supplied clarified-juice flows, not both.');
    if (!hasManual || useModelFlow) return {};
    const values = JSON.parse(componentFlowsJson);
    if (!values || typeof values !== 'object' || Array.isArray(values) || Object.keys(values).length === 0) {
      throw new Error('Component flows must be a non-empty JSON object keyed by GreenHub component ID.');
    }
    if (Object.entries(values).some(([key, value]) => !key.trim() || typeof value !== 'number' || !Number.isFinite(value) || value < 0)) {
      throw new Error('Each component flow must have a component ID and a finite non-negative value in kg/h.');
    }
    if (!componentFlowsSource.trim()) throw new Error('Add a source/evidence note for the caller-supplied component flows.');
    return { component_flows_kg_hr: values, component_flows_source: componentFlowsSource.trim() };
  }

  function overridePayload() {
    if (!useModelFlow && !componentFlowsJson.trim()) return {};
    const values = JSON.parse(overrideValues || '{}');
    const sources = JSON.parse(overrideSources || '{}');
    if (!values || typeof values !== 'object' || Array.isArray(values) || !sources || typeof sources !== 'object' || Array.isArray(sources)) {
      throw new Error('Retention overrides and source notes must each be JSON objects.');
    }
    if (Object.keys(values).some(key => typeof values[key] !== 'number' || values[key] < 0 || values[key] > 1)) {
      throw new Error('Each retention override must be a number from 0 to 1.');
    }
    if (Object.keys(values).sort().join('|') !== Object.keys(sources).sort().join('|') || Object.values(sources).some(value => typeof value !== 'string' || !value.trim())) {
      throw new Error('Provide a non-empty source/evidence note for every retention override.');
    }
    return { component_retention_overrides: values, component_retention_override_sources: sources };
  }

  function utilityPayload() {
    const localInputs = Object.fromEntries(Object.entries(utilityInputs).filter(([, value]) => value !== '').map(([key, value]) => [key, Number(value)]));
    const inputs = Object.fromEntries(Object.entries(localInputs).map(([key, value]) => [
      key === 'annual_electricity_mwh' ? 'annual_electricity_kwh' : key === 'annual_heat_mwh' ? 'annual_heat_kwh' : key,
      key === 'annual_electricity_mwh' || key === 'annual_heat_mwh' ? value * 1000 : value,
    ]));
    const sources = JSON.parse(utilitySources || '{}');
    if (!sources || typeof sources !== 'object' || Array.isArray(sources)) throw new Error('Operational input sources must be a JSON object.');
    const inputKeys = Object.keys(inputs);
    if (inputKeys.some(key => !Number.isFinite(inputs[key]) || inputs[key] < 0)) throw new Error('Operational input values must be finite and non-negative.');
    if (inputKeys.sort().join('|') !== Object.keys(sources).sort().join('|') || Object.values(sources).some(value => typeof value !== 'string' || !value.trim())) {
      throw new Error('Provide a non-empty source/evidence note for every operational input.');
    }
    return inputKeys.length ? { ...inputs, operational_input_sources: sources } : {};
  }

  function cipPayload() {
    const hasVolume = cipInputs.solution_volume_L_per_step !== '';
    const hasMakeup = cipInputs.makeup_fraction_per_cycle !== '';
    if (hasVolume !== hasMakeup) throw new Error('CIP reagent screening requires both solution volume and make-up fraction.');
    if (!hasVolume && cipInputs.source.trim()) throw new Error('CIP evidence note requires both CIP calculation inputs.');
    if (!hasVolume) {
      if (includeCipLca) throw new Error('CIP chemical climate screening requires the complete CIP inputs.');
      return {};
    }
    const volume = Number(cipInputs.solution_volume_L_per_step);
    const makeup = Number(cipInputs.makeup_fraction_per_cycle);
    if (!(volume > 0) || !(makeup >= 0 && makeup <= 1) || !cipInputs.source.trim()) throw new Error('Enter a positive CIP volume, a make-up fraction in [0, 1], and its evidence note.');
    return { cip_solution_volume_L_per_step: volume, cip_makeup_fraction_per_cycle: makeup, cip_input_source: cipInputs.source.trim(), include_cip_screening_lca: includeCipLca };
  }

  function resistanceFluxPayload() {
    if (fluxMethod !== 'resistance_model') return {};
    if (technology === 'MEUF') throw new Error('The resistance model is parameterized only for TUF and LNF.');
    const {pressure_bar,feed_to_reference_concentration_ratio,viscosity_Pa_s,pressure_source,ratio_source,viscosity_source}=resistanceInputs;
    if (!(Number(pressure_bar)>0) || !(Number(feed_to_reference_concentration_ratio)>0) || !(Number(viscosity_Pa_s)>0) || !pressure_source.trim() || !ratio_source.trim() || !viscosity_source.trim()) {
      throw new Error('Resistance flux requires positive TMP, Cf/C0 and measured no-fermentation viscosity, each with a source/evidence note.');
    }
    return {resistance_flux_model:{pressure_bar:Number(pressure_bar),pressure_source:pressure_source.trim(),feed_to_reference_concentration_ratio:Number(feed_to_reference_concentration_ratio),ratio_source:ratio_source.trim(),viscosity_Pa_s:Number(viscosity_Pa_s),viscosity_source:viscosity_source.trim()}};
  }

  async function calculate(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setResult(null);
    setBusy(true);
    try {
      const response = await apiJson<ScreenResponse>('/biostimulant/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feed_volume_m3_year: Number(volume),
          technology_id: technology,
          operating_hours_year: Number(hours),
          concentration_factor: Number(concentrationFactor),
          price_EUR_L: Number(priceEurL),
          ...(useModelFlow && runId ? { run_id: runId } : {}),
          ...componentFlowPayload(),
          ...overridePayload(),
          ...utilityPayload(),
          ...cipPayload(),
          ...resistanceFluxPayload(),
        }),
      });
      setResult(response);
      setComparison([]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Screening calculation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function compareTechnologies() {
    setError('');
    setResult(null);
    setComparison([]);
    setBusy(true);
    try {
      const resistancePayload = fluxMethod === 'resistance_model' ? resistanceFluxPayload() : {};
      const screened = await Promise.all(['TUF', 'LNF', 'MEUF'].map(async technology_id => {
        const response = await apiJson<ScreenResponse>('/biostimulant/screen', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ feed_volume_m3_year: Number(volume), technology_id, operating_hours_year: Number(hours), concentration_factor: Number(concentrationFactor), price_EUR_L: Number(priceEurL), ...(useModelFlow && runId ? { run_id: runId } : {}), ...componentFlowPayload(), ...overridePayload(), ...utilityPayload(), ...cipPayload(), ...(technology_id==='MEUF'?{}:resistancePayload) }),
        });
        return { technology_id, membrane_screen: response.membrane_screen, hormone_capture: response.hormone_capture, biosteam_unit: response.biosteam_unit };
      }));
      setComparison(screened);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Technology comparison failed.');
    } finally {
      setBusy(false);
    }
  }

  const n = (value: number, digits = 1) => value.toLocaleString(undefined, { maximumFractionDigits: digits });
  const captureChart = result?.hormone_capture.map(item => ({ analyte: item.solute_id, free_mg_year: (item.captured_free_kg_year ?? 0) * 1e6, bound_mg_year: (item.captured_bound_kg_year ?? 0) * 1e6 })) ?? [];
  const splitClasses = result?.component_mass_split
    ? [...new Set([...Object.keys(result.component_mass_split.retentate_by_class_kg_hr), ...Object.keys(result.component_mass_split.permeate_by_class_kg_hr)])]
    : [];
  if (result?.component_mass_split && Object.keys(result.component_mass_split.unresolved_kg_hr).length > 0) splitClasses.push('Unresolved pools');
  const splitChart = result?.component_mass_split ? [
    { outlet: 'Retentate', ...Object.fromEntries(splitClasses.map(name => [name, name === 'Unresolved pools' ? 0 : result.component_mass_split!.retentate_by_class_kg_hr[name] || 0])) },
    { outlet: 'Permeate', ...Object.fromEntries(splitClasses.map(name => [name, name === 'Unresolved pools' ? 0 : result.component_mass_split!.permeate_by_class_kg_hr[name] || 0])) },
    ...(Object.keys(result.component_mass_split.unresolved_kg_hr).length ? [{ outlet: 'Unresolved', ...Object.fromEntries(splitClasses.map(name => [name, name === 'Unresolved pools' ? Object.values(result.component_mass_split!.unresolved_kg_hr).reduce((sum, value) => sum + value, 0) : 0])) }] : []),
  ] : [];
  const splitColors = ['#408f4d', '#729ad2', '#d277a3', '#d1a520', '#e4b839', '#0c3338', '#a9a098'];
  const energyClimateChart = result ? Object.entries(result.energy_tea_lca_screen.by_utility).filter(([, row]) => row.energy_climate_kg_co2e_year !== null).map(([utility, row]) => ({ utility, climate: row.energy_climate_kg_co2e_year })) : [];
  const energyCostChart = result ? Object.entries(result.energy_tea_lca_screen.by_utility).filter(([, row]) => row.energy_cost_eur_year !== null).map(([utility, row]) => ({ utility, cost: row.energy_cost_eur_year })) : [];
  const cipMaterialChart = result?.cip_reagent_screen ? [
    { reagent: 'NaOH 50%', mass: result.cip_reagent_screen.naoh.purchased_50wt_solution_kg_year },
    { reagent: 'Citric acid', mass: result.cip_reagent_screen.citric_acid.citric_acid_kg_year },
  ] : [];
  const cipCostChart = result?.cip_reagent_screen ? [
    { reagent: 'NaOH 50%', cost: result.cip_reagent_screen.naoh.cost_eur_year },
    { reagent: 'Citric acid', cost: result.cip_reagent_screen.citric_acid.cost_eur_year },
  ] : [];
  const cipClimateChart = result?.cip_reagent_screen?.screening_lca ? [
    { reagent: 'NaOH', climate: result.cip_reagent_screen.screening_lca.naoh_production_kg_CO2e_year },
    { reagent: 'Citric acid', climate: result.cip_reagent_screen.screening_lca.citric_acid_production_kg_CO2e_year },
  ] : [];
  const externalReferences = result ? [...(result.tea_readiness.reference_only || []), ...(result.lca_readiness.reference_only || [])] : [];
  const hormoneComparison = ['IAA', 'Zeatin', 'ZeatinRiboside'].map(analyte => Object.fromEntries([
    ['analyte', analyte],
    ...comparison.map(item => [item.technology_id, (item.hormone_capture.find(row => row.solute_id === analyte)?.captured_total_kg_year ?? 0) * 1e6]),
  ]));
  const utilityFields = [
    ['annual_electricity_mwh', 'Electricity use', 'MWh/year'],
    ['electricity_kg_co2e_kwh', 'Electricity emission factor', 'kg CO₂-eq/kWh'],
    ['electricity_price_eur_kwh', 'Electricity price', '€/kWh'],
    ['annual_heat_mwh', 'Heat use', 'MWh/year'],
    ['heat_kg_co2e_kwh', 'Heat emission factor', 'kg CO₂-eq/kWh'],
    ['heat_price_eur_kwh', 'Heat price', '€/kWh'],
    ['transmembrane_pressure_bar', 'TMP for pressure-work screen', 'bar'],
    ['pump_efficiency_fraction', 'Pump efficiency', 'fraction'],
  ];

  return <section className="panel biostimulant-screen">
    <div className="section-heading"><div><span className="eyebrow">PR7 · Membrane screen</span><h2>Biostimulant membrane recovery</h2><p>Direct clarified grass juice feed; no 14-day fermentation/storage before membrane treatment. In the full plant, downstream digestion remains controlled by the separate AD selection. When model component flows are supplied and every component is mapped, the selected membrane unit runs in an isolated BioSTEAM simulation. It does not alter the main plant run.</p></div></div>
    <form className="ds-controls" onSubmit={calculate}>
      <label>Juice feed <span><input type="number" min="0" step="any" required value={volume} onChange={event => setVolume(event.target.value)}/><em>m³/year</em></span></label>
      <label>Membrane<select required value={technology} onChange={event => {setTechnology(event.target.value);if(event.target.value==='MEUF')setFluxMethod('empirical');}}><option value="">Select technology</option><option value="TUF">Tight UF (TUF)</option><option value="LNF">Loose NF (LNF)</option><option value="MEUF">Micellar UF (MEUF)</option></select></label>
      <label>Flux basis<select value={fluxMethod} disabled={technology==='MEUF'} onChange={event=>setFluxMethod(event.target.value as 'empirical'|'resistance_model')}><option value="empirical">Empirical baseline</option><option value="resistance_model">Resistance equation</option></select><small>MEUF uses the supplied empirical baseline.</small></label>
      {fluxMethod==='resistance_model'&&technology!=='MEUF'&&<><label>Transmembrane pressure <span><input type="number" min="0.001" step="any" value={resistanceInputs.pressure_bar} onChange={event=>setResistanceInputs(current=>({...current,pressure_bar:event.target.value}))}/><em>bar</em></span></label><label>TMP evidence note<input value={resistanceInputs.pressure_source} onChange={event=>setResistanceInputs(current=>({...current,pressure_source:event.target.value}))}/></label><label>Feed/reference concentration ratio <span><input type="number" min="0.000001" step="any" value={resistanceInputs.feed_to_reference_concentration_ratio} onChange={event=>setResistanceInputs(current=>({...current,feed_to_reference_concentration_ratio:event.target.value}))}/><em>Cf/C0</em></span></label><label>Concentration evidence note<input value={resistanceInputs.ratio_source} onChange={event=>setResistanceInputs(current=>({...current,ratio_source:event.target.value}))}/></label><label>Unfermented juice viscosity <span><input type="number" min="0.000000001" step="any" value={resistanceInputs.viscosity_Pa_s} onChange={event=>setResistanceInputs(current=>({...current,viscosity_Pa_s:event.target.value}))}/><em>Pa·s</em></span></label><label>Viscosity evidence note<input value={resistanceInputs.viscosity_source} onChange={event=>setResistanceInputs(current=>({...current,viscosity_source:event.target.value}))}/><small>The 1.35 mPa·s value refers to fermented juice and is not reused.</small></label></>}
      <label>Operating time <span><input type="number" min="0.01" step="any" required value={hours} onChange={event => setHours(event.target.value)}/><em>h/year</em></span></label>
      <label>Target concentration factor <span><input type="number" min="1.001" step="any" required value={concentrationFactor} onChange={event => setConcentrationFactor(event.target.value)}/><em>×</em></span></label>
      <label>Concentrate price <span><input type="number" min="0" step="any" required value={priceEurL} onChange={event => setPriceEurL(event.target.value)}/><em>€/L</em></span><small>User-supplied screening range: €1.50–€3.50/L at VCF 10; validate specification and offtake.</small></label>
      <label className="biostimulant-flow-source"><input type="checkbox" checked={useModelFlow} disabled={!runId} onChange={event => setUseModelFlow(event.target.checked)}/><span>Use clarified-juice component flows from the latest completed model run{!runId && <small> Run the model first.</small>}</span></label>
      <details className="biostimulant-overrides"><summary>Caller-supplied clarified-juice component flows</summary><p>Optional alternative to selecting a completed model run. Enter actual component flow rates at the clarified-juice boundary in kg/h. Hormone pool IDs: Indole3AceticAcid, ProteinBoundIAA, Zeatin, PeptideBoundZeatin, ZeatinRiboside, BoundZeatinRiboside. Include them only when supported by data. These flows drive the isolated membrane unit, not the integrated plant simulation.</p><label>Component flows (kg/h), JSON<textarea rows={5} value={componentFlowsJson} onChange={event => setComponentFlowsJson(event.target.value)}/></label><label>Flow source / evidence note<input value={componentFlowsSource} onChange={event => setComponentFlowsSource(event.target.value)} placeholder="Sample ID, analytical method, date, and basis"/></label></details>
      {(useModelFlow || componentFlowsJson.trim()) && <details className="biostimulant-overrides"><summary>Documented component retentions</summary><p>Optional JSON maps for feed components not covered by the supplied class matrix. Enter the same component IDs in both fields; each note is returned with the result.</p><label>Retention fractions<textarea rows={4} value={overrideValues} onChange={event => setOverrideValues(event.target.value)} placeholder={'{"Lignin": 0.9}'}/></label><label>Source / evidence notes<textarea rows={4} value={overrideSources} onChange={event => setOverrideSources(event.target.value)} placeholder={'{"Lignin": "source, test, or explicit assumption basis"}'}/></label></details>}
      <details className="biostimulant-overrides"><summary>Optional TEA/LCA energy inputs</summary><p>Enter actual annual energy and sourced local prices/factors. Alternatively, provide both TMP and pump efficiency for a permeate-side pressure-work estimate; do not also enter annual electricity for that estimate. Blank values stay missing.</p><div className="biostimulant-energy-inputs">{utilityFields.map(([key, label, unit]) => <label key={key}>{label}<span><input type="number" min="0" max={key === 'pump_efficiency_fraction' ? 1 : undefined} step="any" value={utilityInputs[key]} onChange={event => setUtilityInputs(current => ({ ...current, [key]: event.target.value }))}/><em>{unit}</em></span></label>)}</div><label>Source / evidence notes <small>JSON keys use API field names, e.g. annual_electricity_kwh or transmembrane_pressure_bar.</small><textarea rows={4} value={utilitySources} onChange={event => setUtilitySources(event.target.value)} placeholder={'{"annual_electricity_kwh": "metered/simulated inventory, source/date", "electricity_kg_co2e_kwh": "factor source and year", "transmembrane_pressure_bar": "selected TMP basis", "pump_efficiency_fraction": "pump specification/source"}'}/></label></details>
      <details className="biostimulant-overrides"><summary>Optional CIP reagent-cost screen</summary><p>Uses the registered 48 operating-hour interval and working-solution concentrations. The same volume is assumed for each sequential chemical step; enter the fraction of each batch made up/replaced per event. The calculation reports reagent subtotal only.</p><div className="biostimulant-energy-inputs"><label>Working solution per step <span><input type="number" min="0.001" step="any" value={cipInputs.solution_volume_L_per_step} onChange={event => setCipInputs(current => ({ ...current, solution_volume_L_per_step: event.target.value }))}/><em>L/event</em></span></label><label>Make-up fraction per cycle <span><input type="number" min="0" max="1" step="any" value={cipInputs.makeup_fraction_per_cycle} onChange={event => setCipInputs(current => ({ ...current, makeup_fraction_per_cycle: event.target.value }))}/><em>fraction</em></span></label></div><label>Volume and make-up evidence note<input value={cipInputs.source} onChange={event => setCipInputs(current => ({ ...current, source: event.target.value }))}/></label><label className="biostimulant-flow-source"><input type="checkbox" checked={includeCipLca} onChange={event=>setIncludeCipLca(event.target.checked)}/><span>Include registered upstream chemical climate factors</span></label><small>Optional attributional screen for NaOH and citric acid production only; not a full route LCA. Cleaning wastewater, CIP energy and membrane manufacture remain excluded.</small></details>
      <button className="secondary" type="submit" disabled={busy}>{busy ? 'Calculating…' : 'Screen route'}</button>
      <button className="text-button" type="button" disabled={busy || !volume || !hours} onClick={compareTechnologies}>{busy ? 'Comparing…' : 'Compare TUF, LNF, MEUF'}</button>
    </form>
    {error && <p className="compact-warning" role="alert">{error}</p>}
    {result && <div className="biostimulant-screen-results" aria-live="polite">
      <small>Hormone concentrations and free/bound fractions are user-supplied screening inputs. The free/bound split is discussed for a 14-day anaerobic state and is unvalidated for this no-fermentation feed boundary.</small>
      {result.biosteam_unit && <>
        <div className="biostimulant-balance-status">
          <strong>{result.biosteam_unit.status}</strong>
          <span>{result.biosteam_unit.technology_id} · {result.biosteam_unit.membrane_area_m2 == null ? (result.biosteam_unit.maximum_membrane_area_m2 == null ? `known-permeate area floor ≥${n(result.biosteam_unit.minimum_membrane_area_m2)} m²; upper area unresolved` : `membrane area ${n(result.biosteam_unit.minimum_membrane_area_m2)}–${n(result.biosteam_unit.maximum_membrane_area_m2)} m² range`) : `${n(result.biosteam_unit.membrane_area_m2)} m² membrane area`} · {n(result.biosteam_unit.operating_hours_year)} h/year · target VCF {n(result.biosteam_unit.target_concentration_factor ?? 0)}</span>
          <small>BioSTEAM retentate {n(result.biosteam_unit.product_kg_year)} kg/year ({n((result.biosteam_unit.product_volume_m3_hr || 0) * 1000)} L/h) · permeate {n(result.biosteam_unit.permeate_kg_year)} kg/year · unresolved {n(result.biosteam_unit.unresolved_kg_year)} kg/year · actual VCF {result.biosteam_unit.actual_volume_concentration_factor == null ? 'n/a' : n(result.biosteam_unit.actual_volume_concentration_factor)} · mass closure error {n(result.biosteam_unit.mass_closure_error_kg_hr, 9)} kg/h</small>
        </div>
        <div className="data-table-wrap"><table className="data-table"><thead><tr><th>BioSTEAM product component</th><th>Flow (kg/h)</th></tr></thead><tbody>{Object.entries(result.biosteam_unit.product_kg_hr).map(([ID, flow]) => <tr key={ID}><td>{ID}</td><td>{n(flow, 6)}</td></tr>)}</tbody></table></div>
        {Object.keys(result.biosteam_unit.unresolved_components_kg_hr).length > 0 && <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Pool without retention</th><th>Unresolved outlet (kg/h)</th></tr></thead><tbody>{Object.entries(result.biosteam_unit.unresolved_components_kg_hr).map(([ID, flow]) => <tr key={ID}><td>{ID}</td><td>{n(flow, 6)}</td></tr>)}</tbody></table></div>}
      </>}
      <div className="schedule-facts">
        <div><span>Membrane area</span><strong>{n(result.membrane_screen.membrane_area_m2)} m²</strong></div>
        <div><span>Target VCF</span><strong>{n(result.membrane_screen.concentration_factor)}×</strong></div>
        <div><span>Retentate volume</span><strong>{n(result.membrane_screen.product_volume_L_year)} L/year</strong></div>
        <div><span>Gross sales screen</span><strong>€{n(result.membrane_screen.gross_revenue_EUR_year, 0)}/year at €{n(result.membrane_screen.price_EUR_L, 2)}/L</strong></div>
        <div><span>Flux basis</span><strong>{n(result.membrane_screen.flux_L_m2_h)} L/(m²·h) · {result.membrane_screen.flux_basis}</strong></div>
        <div><span>Module CAPEX</span><strong>€{n(result.membrane_screen.membrane_module_capex_low_EUR, 0)}–€{n(result.membrane_screen.membrane_module_capex_high_EUR, 0)}</strong></div>
        <div><span>Module replacement allowance</span><strong>€{n(result.membrane_screen.annualized_replacement_low_EUR_year, 0)}–€{n(result.membrane_screen.annualized_replacement_high_EUR_year, 0)}/year</strong></div>
      </div>
      {result.resistance_flux_result&&<div className="biostimulant-balance-status"><strong>Resistance-model flux calculated</strong><span>{result.resistance_flux_result.technology_id} · {n(result.resistance_flux_result.predicted_flux_L_m2_h,2)} L/(m²·h) at {n(result.resistance_flux_result.pressure_bar,2)} bar and Cf/C0 {n(result.resistance_flux_result.feed_to_reference_concentration_ratio,3)}</span><small>Empirical nominal baseline: {n(result.resistance_flux_result.empirical_baseline_flux_L_m2_h,2)} L/(m²·h). The 1.35 mPa·s fermented-juice viscosity is not reused.</small></div>}
      {result.film_retention_diagnostics?.analytes.length ? <><h3>Retention model check</h3><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Analyte</th><th>Weighted retention (%)</th><th>Applied free retention (%)</th><th>Bound retention (%)</th><th>Free film prediction (%)</th><th>Peclet</th></tr></thead><tbody>{result.film_retention_diagnostics.analytes.map(item => <tr key={item.solute_id}><td>{item.solute_id}</td><td>{n(item.weighted_state_retention_fraction * 100, 1)}</td><td>{n(item.process_split_free_retention_fraction * 100, 1)}</td><td>{n(item.process_split_bound_retention_fraction * 100, 1)}</td><td>{n(item.film_free_retention_fraction * 100, 1)}</td><td>{n(item.film_free_peclet_number, 3)}</td></tr>)}</tbody></table><small>{result.film_retention_diagnostics.comparison_basis} The free-pool value shown is applied for TUF and is the registered empirical value for LNF. The film prediction is diagnostic for LNF.</small></div></> : null}
      {result.cip_reagent_screen && <div className="biostimulant-balance-status"><strong>CIP reagent make-up screen: €{n(result.cip_reagent_screen.total_reagent_cost_eur_year, 2)}/year</strong><span>{n(result.cip_reagent_screen.cip_events_year, 1)} events/year · NaOH stock {n(result.cip_reagent_screen.naoh.purchased_50wt_solution_kg_year, 3)} kg/year · citric acid {n(result.cip_reagent_screen.citric_acid.citric_acid_kg_year, 3)} kg/year</span><small>{result.cip_reagent_screen.cost_boundary}; working-solution density 1 kg/L.</small>{result.cip_reagent_screen.screening_lca&&<small>CIP chemical-production burden: {n(result.cip_reagent_screen.screening_lca.total_chemical_production_kg_CO2e_year, 3)} kg CO₂-eq/year, NaOH {n(result.cip_reagent_screen.screening_lca.naoh_production_kg_CO2e_year, 3)} + citric acid {n(result.cip_reagent_screen.screening_lca.citric_acid_production_kg_CO2e_year, 3)}. {result.cip_reagent_screen.screening_lca.status}</small>}</div>}
      {result.cip_reagent_screen&&<div className="biostimulant-comparison-grid"><div><h4>CIP reagent use</h4><ResponsiveContainer width="100%" height={210}><BarChart data={cipMaterialChart} margin={{top:8,right:12,bottom:4,left:8}}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="reagent"/><YAxis unit=" kg/y" tick={{fontSize:10}} width={70}/><Tooltip formatter={(value:number)=>[`${n(value,3)} kg/year`,'Purchased reagent']}/><Bar dataKey="mass" fill="#729ad2" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div><div><h4>CIP reagent cost</h4><ResponsiveContainer width="100%" height={210}><BarChart data={cipCostChart} margin={{top:8,right:12,bottom:4,left:8}}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="reagent"/><YAxis unit=" €/y" tick={{fontSize:10}} width={70}/><Tooltip formatter={(value:number)=>[`€${n(value,2)}/year`,'Reagent cost']}/><Bar dataKey="cost" fill="var(--yellow)" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div>{cipClimateChart.length>0&&<div><h4>CIP chemical climate</h4><ResponsiveContainer width="100%" height={210}><BarChart data={cipClimateChart} margin={{top:8,right:12,bottom:4,left:8}}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="reagent"/><YAxis unit=" kg/y" tick={{fontSize:10}} width={70}/><Tooltip formatter={(value:number)=>[`${n(value,3)} kg CO₂-eq/year`,'Upstream production']}/><Bar dataKey="climate" fill="#408f4d" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer><small>Opt-in upstream chemical production only.</small></div>}</div>}
      {result.meuf_surfactant_screen && <div className="biostimulant-balance-status"><strong>MEUF SDS inventory screen · not added to BioSTEAM balance</strong><span>CMC {n(result.meuf_surfactant_screen.CMC_mmol_L, 2)} mmol/L · dose {n(result.meuf_surfactant_screen.dose_low.dose_mmol_L, 2)}–{n(result.meuf_surfactant_screen.dose_high.dose_mmol_L, 2)} mmol/L · recovery {n(result.meuf_surfactant_screen.recovery_fraction * 100, 1)}%</span><small>Gross SDS {n(result.meuf_surfactant_screen.dose_low.gross_SDS_kg_year)}–{n(result.meuf_surfactant_screen.dose_high.gross_SDS_kg_year)} kg/year · unrecovered make-up {n(result.meuf_surfactant_screen.dose_low.unrecovered_makeup_SDS_kg_year)}–{n(result.meuf_surfactant_screen.dose_high.unrecovered_makeup_SDS_kg_year)} kg/year. Missing: {result.meuf_surfactant_screen.missing_for_TEA_LCA.join('; ')}.</small>{(result.meuf_surfactant_screen.price_references_only ?? [result.meuf_surfactant_screen.price_reference_only]).map((price, index) => <small key={`${price.source_reference}-${index}`}>Price reference only: €{n(price.value, 2)}/{price.units.replace('EUR/', '')} ({price.source_status}); not applied to TEA. <a href={price.source_reference} target="_blank" rel="noreferrer">Source</a>.</small>)}</div>}
      <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Analyte</th><th>Free captured (kg/year)</th><th>Bound captured (kg/year)</th><th>Total (kg/year)</th><th>Retention</th><th>Input status</th></tr></thead><tbody>{result.hormone_capture.map(item => <tr key={item.solute_id}><td>{item.solute_id}</td><td>{item.captured_free_kg_year === null ? 'n/a' : n(item.captured_free_kg_year, 6)}</td><td>{item.captured_bound_kg_year === null ? 'n/a' : n(item.captured_bound_kg_year, 6)}</td><td>{n(item.captured_total_kg_year, 6)}</td><td>{n(item.total_retention_fraction * 100)}%</td><td>{item.evidence_status}</td></tr>)}</tbody></table><small>{result.hormone_capture[0]?.state_specific_capture_status}</small></div>
      <div className="biostimulant-capture-chart"><h3>Captured hormone equivalents</h3><ResponsiveContainer width="100%" height={230}><BarChart data={captureChart} margin={{ top: 10, right: 16, bottom: 4, left: 8 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="analyte" tick={{ fontSize: 11 }}/><YAxis unit=" mg/year" tick={{ fontSize: 10 }} width={80}/><Tooltip formatter={(value: number, name: string) => [`${n(value, 3)} mg/year`, name]}/><Legend/><Bar dataKey="free_mg_year" name="Free" stackId="capture" fill="#729ad2"/><Bar dataKey="bound_mg_year" name="Bound" stackId="capture" fill="#408f4d" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div>
      <div className="schedule-facts"><div><span>TEA status</span><strong>{result.tea_readiness.status}</strong></div><div><span>LCA status</span><strong>{result.lca_readiness.status}</strong></div></div>
      <div className="schedule-facts"><div><span>Energy climate status</span><strong>{result.energy_tea_lca_screen.climate_status}</strong></div><div><span>Energy climate load</span><strong>{result.energy_tea_lca_screen.energy_climate_kg_co2e_year !== null ? `${n(result.energy_tea_lca_screen.energy_climate_kg_co2e_year)} kg CO₂-eq/year` : result.energy_tea_lca_screen.known_energy_climate_subtotal_kg_co2e_year !== null ? `Known subtotal ${n(result.energy_tea_lca_screen.known_energy_climate_subtotal_kg_co2e_year)} kg CO₂-eq/year` : 'Not calculated'}</strong></div><div><span>Energy cost status</span><strong>{result.energy_tea_lca_screen.tea_status}</strong></div><div><span>Energy cost</span><strong>{result.energy_tea_lca_screen.energy_cost_eur_year !== null ? `€${n(result.energy_tea_lca_screen.energy_cost_eur_year)}/year` : result.energy_tea_lca_screen.known_energy_cost_subtotal_eur_year !== null ? `Known subtotal €${n(result.energy_tea_lca_screen.known_energy_cost_subtotal_eur_year)}/year` : 'Not calculated'}</strong></div></div>
      {result.hydraulic_energy_estimate && <div className="biostimulant-balance-status"><strong>Pressure-work electricity: {n(result.hydraulic_energy_estimate.electricity_mwh_year)} MWh/year</strong><span>{n(result.hydraulic_energy_estimate.permeate_volume_m3_year)} m³/year permeate · {n(result.hydraulic_energy_estimate.transmembrane_pressure_bar)} bar TMP · {n(result.hydraulic_energy_estimate.pump_efficiency_fraction * 100)}% efficiency</span><small>{result.hydraulic_energy_estimate.basis}</small></div>}
      {(energyClimateChart.length > 0 || energyCostChart.length > 0) && <div className="biostimulant-comparison-grid">{energyClimateChart.length > 0 && <div><h4>Energy climate contribution</h4><ResponsiveContainer width="100%" height={210}><BarChart data={energyClimateChart} margin={{ top: 8, right: 10, bottom: 2, left: 6 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="utility"/><YAxis unit=" kg CO₂-eq/y" tick={{ fontSize: 9 }} width={92}/><Tooltip formatter={(value: number) => [`${n(value)} kg CO₂-eq/year`, 'Energy burden']}/><Bar dataKey="climate" fill="#408f4d" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div>}{energyCostChart.length > 0 && <div><h4>Energy operating cost</h4><ResponsiveContainer width="100%" height={210}><BarChart data={energyCostChart} margin={{ top: 8, right: 10, bottom: 2, left: 6 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="utility"/><YAxis unit=" €/y" tick={{ fontSize: 10 }}/><Tooltip formatter={(value: number) => [`€${n(value)}/year`, 'Energy cost']}/><Bar dataKey="cost" fill="var(--yellow)" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div>}</div>}
      {(result.energy_tea_lca_screen.climate_missing_inputs.length > 0 || result.energy_tea_lca_screen.tea_missing_inputs.length > 0) && <small>Missing utility inputs: {[...new Set([...result.energy_tea_lca_screen.climate_missing_inputs, ...result.energy_tea_lca_screen.tea_missing_inputs])].join(', ')}</small>}
      {Object.keys(result.energy_tea_lca_screen.input_sources).length > 0 && <details><summary>Utility input evidence</summary><ul>{Object.entries(result.energy_tea_lca_screen.input_sources).map(([key, note]) => <li key={key}><strong>{key}:</strong> {note}</li>)}</ul></details>}
      {result.component_mass_split && <div className="biostimulant-balance-status"><strong>{result.component_mass_split.complete_mass_split ? 'Component allocation complete' : 'Allocation incomplete; unresolved outlet retained'}</strong><span>{result.component_stream_id || result.component_mass_split_source}</span>{result.component_mass_split.unmapped_component_ids.length > 0 && <small>Needs retention data: {result.component_mass_split.unmapped_component_ids.join(', ')}</small>}{result.component_mass_split.screening_assumptions.map(note => <small key={note}>{note}</small>)}{result.component_mass_split.mass_error_kg_hr !== null && <small>Mass closure error: {n(result.component_mass_split.mass_error_kg_hr, 9)} kg/h</small>}</div>}
      {result.mass_balance_readiness?.mass_balanced && <small>Total mass is balanced; component fate is incomplete where pools are listed below.</small>}
      {result.mass_balance_readiness && !result.mass_balance_readiness.complete && <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Pool without retention</th><th>Clarified juice (kg/h)</th><th>Retention needed</th></tr></thead><tbody>{Object.entries(result.mass_balance_readiness.unmapped_component_flows_kg_hr).map(([ID, flow]) => <tr key={ID}><td>{ID}</td><td>{n(flow, 6)}</td><td><span className="status warning">Required</span></td></tr>)}</tbody></table><small>Provide a documented component-specific retention and evidence note for each nonzero flow to allocate it between retentate and permeate. The BioSTEAM mass balance retains its mass at the unresolved outlet.</small></div>}
      {Object.keys(result.component_retention_override_sources).length > 0 && <details><summary>Retention override evidence</summary><ul>{Object.entries(result.component_retention_override_sources).map(([ID, source]) => <li key={ID}><strong>{ID}:</strong> {source}</li>)}</ul></details>}
      {result.component_balance?.complete && result.component_balance.elements_kg_hr && <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Balance (kg/h)</th><th>Feed</th><th>Retentate</th><th>Permeate</th><th>Closure error</th></tr></thead><tbody><tr><td>Total mass</td><td>{n(result.component_balance.feed_mass_kg_hr, 6)}</td><td>{n(result.component_balance.retentate_mass_kg_hr ?? 0, 6)}</td><td>{n(result.component_balance.permeate_mass_kg_hr ?? 0, 6)}</td><td>{n(result.component_balance.mass_error_kg_hr ?? 0, 9)}</td></tr>{Object.entries(result.component_balance.elements_kg_hr).map(([element, values]) => <tr key={element}><td>{element}</td><td>{n(values.feed, 6)}</td><td>{n(values.retentate, 6)}</td><td>{n(values.permeate, 6)}</td><td>{n(values.closure_error, 9)}</td></tr>)}</tbody></table></div>}
      {result.component_balance?.complete && !result.component_balance.elements_kg_hr && <small>Element balance withheld: {result.component_balance.elemental_balance_status.replaceAll('_', ' ')}.</small>}
      {splitChart.length > 0 && <div className="biostimulant-capture-chart"><h3>Membrane mass split</h3><ResponsiveContainer width="100%" height={270}><BarChart data={splitChart} margin={{ top: 10, right: 16, bottom: 4, left: 8 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="outlet"/><YAxis unit=" kg/h" tick={{ fontSize: 10 }}/><Tooltip formatter={(value: number, name: string) => [`${n(value, 4)} kg/h`, name.replaceAll('_', ' ')]}/><Legend formatter={name => String(name).replaceAll('_', ' ')}/>{splitClasses.map((name, index) => <Bar key={name} dataKey={name} stackId="mass" name={name} fill={splitColors[index % splitColors.length]}/>)}</BarChart></ResponsiveContainer><small>Benchmark phytohormones are reported separately and are included here only if present in the selected feed stream.</small></div>}
      {result.feed_volume_consistency && <div className="biostimulant-balance-status"><strong>Juice volume check: {result.feed_volume_consistency.status}</strong><span>Entered {n(result.feed_volume_consistency.entered_volume_m3_year)} m³/year · model stream implies {n(result.feed_volume_consistency.stream_implied_volume_m3_year)} m³/year ({n(result.feed_volume_consistency.difference_pct ?? 0)}% difference)</span><small>Density {n(result.feed_volume_consistency.density_basis_kg_m3)} kg/m³ · {result.feed_volume_consistency.density_source}</small></div>}
      <small>Gross sales use feed volume divided by target VCF. The €1.50–€3.50/L price range was supplied for VCF 10; confirm the price basis if you change VCF. The optional BioSTEAM split reports its actual retentate VCF separately; water hold-up is derived from target VCF and is not measured membrane rejection. Price is a screening proxy, not validated sale revenue. Module costs are uninstalled EUR screening ranges converted from supplied USD/m² quotes at ECB 1 EUR = {n(1 / result.membrane_screen.fx_eur_per_usd, 4)} USD ({result.membrane_screen.fx_date}). Installed CAPEX, complete OPEX, and full-route LCA remain incomplete; partial cost and operational LCA screens are shown above.</small>
      <details><summary>TEA and LCA data gaps</summary><ul>{[...result.tea_readiness.missing_or_excluded, ...result.lca_readiness.missing_or_excluded].map(item => <li key={item}>{item}</li>)}</ul>{externalReferences.length>0&&<><strong>External references · not applied to model totals</strong><ul>{externalReferences.map((item,index)=><li key={`${item.item}-${index}`}><strong>{item.item}:</strong> {item.value}. {item.note} <a href={item.source} target="_blank" rel="noreferrer">Source</a></li>)}</ul></>}</details>
    </div>}
    {comparison.length > 0 && <div className="biostimulant-screen-results" aria-live="polite">
      <h3>Membrane comparison</h3>
      <small>Compared outputs: area (m²), gross sales (€/year), and uninstalled module CAPEX (EUR; source USD quotes converted at dated ECB FX).</small>
      <div className="biostimulant-comparison-grid"><div><h4>Membrane area</h4><ResponsiveContainer width="100%" height={210}><BarChart data={comparison.map(item => ({ technology: item.technology_id, area: item.membrane_screen.membrane_area_m2 }))} margin={{ top: 8, right: 10, bottom: 2, left: 4 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="technology"/><YAxis tick={{ fontSize: 10 }}/><Tooltip formatter={(value: number) => [`${n(value)} m²`, 'Area']}/><Bar dataKey="area" fill="#408f4d" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div><div><h4>Gross sales</h4><ResponsiveContainer width="100%" height={210}><BarChart data={comparison.map(item => ({ technology: item.technology_id, revenue: item.membrane_screen.gross_revenue_EUR_year }))} margin={{ top: 8, right: 10, bottom: 2, left: 4 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="technology"/><YAxis tick={{ fontSize: 10 }}/><Tooltip formatter={(value: number) => [`€${n(value, 0)}/year`, 'Gross sales']}/><Bar dataKey="revenue" fill="var(--yellow)" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div><div><h4>Hormone capture</h4><ResponsiveContainer width="100%" height={230}><BarChart data={hormoneComparison} margin={{ top: 8, right: 8, bottom: 2, left: 8 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="analyte" tick={{ fontSize: 10 }}/><YAxis unit=" mg/y" tick={{ fontSize: 9 }} width={70}/><Tooltip formatter={(value: number) => [`${n(value, 2)} mg/year`, 'Captured']}/><Legend/><Bar dataKey="TUF" fill="#408f4d"/><Bar dataKey="LNF" fill="#729ad2"/><Bar dataKey="MEUF" fill="#d277a3"/></BarChart></ResponsiveContainer></div></div>
      <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Technology</th><th>Area (m²)</th><th>Gross sales (€/year)</th><th>Module CAPEX (EUR)</th></tr></thead><tbody>{comparison.map(item => <tr key={item.technology_id}><td>{item.technology_id}</td><td>{n(item.membrane_screen.membrane_area_m2)}</td><td>{n(item.membrane_screen.gross_revenue_EUR_year, 0)}</td><td>€{n(item.membrane_screen.membrane_module_capex_low_EUR, 0)}–€{n(item.membrane_screen.membrane_module_capex_high_EUR, 0)}</td></tr>)}</tbody></table></div>
      {comparison.some(item => item.biosteam_unit) && <><h3>Simulated outlet comparison</h3><small>Isolated BioSTEAM membrane-unit results from the same selected feed; unresolved mass remains outside the saleable retentate.</small><div className="biostimulant-comparison-grid"><div><h4>Outlet mass</h4><ResponsiveContainer width="100%" height={230}><BarChart data={comparison.filter(item => item.biosteam_unit).map(item => ({ technology: item.technology_id, retentate: item.biosteam_unit!.product_kg_hr ? Object.values(item.biosteam_unit!.product_kg_hr).reduce((sum, value) => sum + value, 0) : 0, unresolved: item.biosteam_unit!.unresolved_mass_kg_hr }))} margin={{ top: 8, right: 10, bottom: 2, left: 4 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="technology"/><YAxis unit=" kg/h" tick={{ fontSize: 10 }}/><Tooltip formatter={(value: number) => [`${n(value, 4)} kg/h`]}/><Legend/><Bar dataKey="retentate" name="Retentate" fill="#408f4d" stackId="outlet"/><Bar dataKey="unresolved" name="Unresolved" fill="#d277a3" stackId="outlet"/></BarChart></ResponsiveContainer></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Technology</th><th>Retentate (kg/h)</th><th>Unresolved (kg/h)</th><th>Known-stream area floor (m²)</th><th>Upper area (m²)</th><th>Mass error (kg/h)</th></tr></thead><tbody>{comparison.filter(item => item.biosteam_unit).map(item => { const unit = item.biosteam_unit!; const retentateMass = Object.values(unit.product_kg_hr).reduce((sum, value) => sum + value, 0); return <tr key={item.technology_id}><td>{item.technology_id}</td><td>{n(retentateMass, 4)}</td><td>{n(unit.unresolved_mass_kg_hr, 4)}</td><td>≥ {n(unit.minimum_membrane_area_m2, 2)}</td><td>{unit.maximum_membrane_area_m2 == null ? 'unresolved' : n(unit.maximum_membrane_area_m2, 2)}</td><td>{n(unit.mass_closure_error_kg_hr, 9)}</td></tr>; })}</tbody></table></div></div></>}
      <small>All three routes use the same juice volume, concentration factor, price, and operating time. These are screening estimates based on user-supplied nominal fluxes and module-cost ranges.</small>
    </div>}
  </section>;
}
