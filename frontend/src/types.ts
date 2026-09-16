export type CalculationMode = 'structural' | 'literature_default' | 'calibrated';
export type ResolutionMode = 'strict' | 'fallback';
export type ResultSourceStatus = 'live_python' | 'live_api' | 'preview_baseline' | 'backend_unavailable' | 'stale_previous_result';

export interface ResultSourceState {
  status: ResultSourceStatus;
  label: string;
  detail: string;
  is_live: boolean;
  fixture_version?: string;
}

export type ProcessAreaId =
  | 'front_end'
  | 'protein_recovery'
  | 'anaerobic_digestion'
  | 'biogas_upgrading'
  | 'nutrient_recovery';

export type NutrientScenarioId =
  | 'NR0'
  | 'NR1'
  | 'NR2'
  | 'NR3'
  | 'NR4'
  | 'NR5'
  | 'NR6'
  | 'NR7';

export type ProcessOrder = 'A' | 'B' | 'C' | 'D';

export interface AreaScenarioSelections {
  front_end: {
    feed_type: string;
    maceration_intensity: string;
  };
  protein_recovery: {
    method: string;
    ph_target: number;
  };
  anaerobic_digestion: {
    technology: string;
    olr_target: number;
    operating_temp_c: number;
  };
  biogas_upgrading: {
    system: string;
    target_ch4_purity: number;
  };
  nutrient_recovery: {
    scenario: NutrientScenarioId;
    process_order: ProcessOrder;
  };
}

export interface ScenarioSelection {
  feed_front_end: string;
  maceration_intensity?: string;
  protein_recovery: string;
  protein_ph_target?: number;
  anaerobic_digestion: string;
  ad_olr_target?: number;
  ad_temp_c?: number;
  biogas_upgrading: string;
  upgrading_purity_target?: number;
  nutrient_recovery: NutrientScenarioId;
  process_order: ProcessOrder;
}

export interface ParameterOverride {
  parameter_id: string;
  value: number | string | boolean;
  unit?: string;
  reason?: string;
}

export interface SimulationRequest {
  schema_version?: string;
  request_id?: string;
  project_id?: string;
  calculation_mode?: CalculationMode;
  resolution_mode?: ResolutionMode;
  selected_month?: string;
  scenarios?: ScenarioSelection;
  design_overrides?: ParameterOverride[];
}

export interface EmpiricalBiomassSchedule {
  annual_available_biomass_tonnes: number;
  annual_processed_biomass_tonnes: number;
  collection_refinery_fraction: number;
  feed_basis: 'tonnes_per_year' | 'kg_per_hr';
  feed_kg_per_hr: number;
  season_start: string;
  season_end: string;
  peak_date: string;
  spread_days: number;
  active_months: number[];
}

export interface ProcessAreaInfo {
  id: ProcessAreaId;
  name: string;
  description: string;
  units: string[];
  streams: string[];
  key_assumptions: string[];
  limitations: string[];
}

export interface UnitOperation {
  id: string;
  name: string;
  area: ProcessAreaId;
  type: string;
  duty_kw: number;
  power_kw: number;
  temperature_c: number;
  pressure_bar: number;
  status: 'active' | 'bypass' | 'disabled';
  status_reason?: string;
}

export interface ProcessStream {
  id: string;
  name: string;
  origin: string;
  destination: string;
  mass_flow_kgh: number;
  dry_solids_pct: number;
  cod_kgh: number;
  nitrogen_kgh: number;
  phosphorus_kgh: number;
  potassium_kgh: number;
}

export interface SystemBalances {
  mass_in_kgh: number;
  mass_out_kgh: number;
  mass_closure_pct: number;
  cod_in_kgh: number;
  cod_out_kgh: number;
  cod_closure_pct: number;
  elemental: {
    carbon: { in: number; out: number; closure: number };
    nitrogen: { in: number; out: number; closure: number };
    phosphorus: { in: number; out: number; closure: number };
    potassium: { in: number; out: number; closure: number };
    sulfur: { in: number; out: number; closure: number };
  };
}

export interface RecoveryMetrics {
  biogas_m3h: number;
  methane_purity_pct: number;
  biomethane_flow_m3h: number;
  protein_recovered_kgh: number;
  protein_purity_pct: number;
  struvite_yield_kgh: number;
  ammonia_sulfate_kgh: number;
  calcium_phosphate_kgh: number;
  potassium_concentrate_kgh: number;
  data_readiness_score: number;
  net_heat_kw: number;
  net_power_kw: number;
  total_power_kw: number;
  total_heat_kw: number;
  p_recovery_pct: number;
  n_recovery_pct: number;
  k_recovery_pct: number;
  cod_conversion_pct: number;
}

export interface ParameterDefinition {
  parameter_id: string;
  name: string;
  category: 'basic' | 'advanced';
  process_area: ProcessAreaId;
  description: string;
  current_value: number | string | boolean;
  unit: string;
  default_value: number | string | boolean;
  quality_class: 'A' | 'B' | 'C' | 'D' | 'E';
  min_value?: number;
  max_value?: number;
  is_editable: boolean;
  notes?: string;
}

export interface PlotCatalogItem {
  id: string;
  title: string;
  category: string;
  description: string;
  type: 'bar' | 'line' | 'composed' | 'sankey_sim' | 'matrix';
  data: Array<Record<string, number | string>>;
  meta?: Record<string, any>;
}

export interface ScenarioComparisonItem {
  scenario_id: NutrientScenarioId;
  title: string;
  biogas_m3h: number;
  protein_kgh: number;
  struvite_kgh: number;
  amsult_kgh: number;
  net_power_kw: number;
  p_recovery_pct: number;
  n_recovery_pct: number;
}

export interface SimulationResult {
  run_id: string;
  timestamp: string;
  calculation_mode: CalculationMode;
  selected_month: string;
  scenarios: ScenarioSelection;
  process_areas: Record<ProcessAreaId, ProcessAreaInfo>;
  units: UnitOperation[];
  streams: ProcessStream[];
  balances: SystemBalances;
  metrics: RecoveryMetrics;
  parameters: ParameterDefinition[];
  plots: PlotCatalogItem[];
  scenario_comparisons: ScenarioComparisonItem[];
  validation: {
    status: 'pass' | 'warning' | 'fail';
    residual_error_kgh: number;
    issues: Array<{ severity: 'info' | 'warning' | 'error'; message: string }>;
  };
  annual?: AnnualSummary | null;
}

export interface AnnualValue {
  value: number;
  unit: string;
}

export interface AnnualSummary {
  method: 'quasi_dynamic_integration' | 'steady_state_annualization';
  method_label: string;
  basis: string;
  period: {
    start_date: string | null;
    end_date: string | null;
    operating_hours: number;
    schedule_source: string;
  };
  feed_processed: AnnualValue;
  products: Record<string, AnnualValue>;
  utilities: Record<string, AnnualValue>;
  balance: {
    overall_closure_pct: number;
    process_mass_residual_kg: number;
    storage_mass_residual_kg: number;
    element_residuals_kg: Record<string, number>;
    passed: boolean;
  };
  monthly: Array<{
    period: string;
    feed_processed_kg: number;
    products_kg: Record<string, number>;
    intermediate_streams_kg: Record<string, number>;
    volumetric_products_m3: Record<string, number>;
    utilities_kwh: Record<string, number>;
    mass_residual_kg: number;
  }>;
  biomass_schedule: {
    monthly: Array<{
      time_label: string;
      available_biomass_tonnes: number;
      planned_processed_biomass_tonnes: number;
      processed_biomass_tonnes: number;
      actual_processed_biomass_tonnes?: number;
      unused_biomass_tonnes: number;
      utilization_fraction: number;
      utilization_percent?: number;
      operating_hours?: number;
      basis_feed_kg_per_hr?: number;
    }>;
    annual_available_tonnes: number;
    annual_processed_tonnes: number;
    annual_unused_tonnes: number;
    utilization_fraction: number;
    peak_month_processed_tonnes: number;
    peak_throughput_kg_per_hr: number;
    policy_id: string;
    warning: string;
  };
  chart_data: {
    schedule: Array<Record<string, number | string>>;
    bulk_streams: Array<Record<string, number | string>>;
    small_products: Array<Record<string, number | string>>;
    biomethane: Array<Record<string, number | string>>;
    energy: Array<Record<string, number | string>>;
    mass_balance: Array<Record<string, number | string>>;
    annual_product_mix: Array<Record<string, number | string>>;
    groups: Record<string, string[]>;
  };
  display_utilities: Record<string, AnnualValue>;
  process_pathway: Array<{
    stage_id: string;
    label: string;
    active_unit_names: string[];
    unit_count: number;
    products_kg_hr: Record<string, number>;
    power_kw: number | null;
    heat_duty_kw: number | null;
    limitations: string[];
    data_quality: string;
  }>;
  reporting_status: {model: string; schedule_policy: string; validated_simulation_ready: boolean; note: string};
  warnings: string[];
}
