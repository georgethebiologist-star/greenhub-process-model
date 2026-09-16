import { API_BASE } from './apiClient';

export interface DynamicScenario {
  annual_available_biomass_tonnes: number;
  annual_processed_biomass_tonnes: number;
  collection_refinery_fraction: number;
  feed_basis: 'tonnes_per_year' | 'kg_per_hr';
  feed_kg_per_hr: number;
  season_start: string;
  season_end: string;
  peak_date: string;
  spread_days: number;
  full_year: boolean;
  active_months: number[];
  annualize: boolean;
  protein_method: string;
  protein_recovery_fraction: number | null;
  drying_method: string;
  target_product_moisture: number;
  gas_route: string;
  resource_recovery_methods: string[];
  allow_assumptions: boolean;
  show_strict_mode_blockers: boolean;
  include_press_cake_in_ad: false;
}
export interface Evidence {
  name: string; value: unknown; unit: string; policy_id: string; source_status: string;
  certainty_class: string; source_file: string; source_id: string; warning: string;
  time_labels?: string[]; usage?: string; provenance?: unknown;
}
export interface DynamicOptions {
  defaults: DynamicScenario; protein_methods: string[]; drying_methods: string[];
  gas_routes: string[]; resource_recovery_methods: string[];
  analysis_factors: Record<string, { value: number; unit: string; source_status: string }>;
}
export interface DynamicReport {
  scenario: DynamicScenario;
  monthly: Array<{ time_label: string; operating_hours: number; metrics: Record<string, Record<string, number | null>> }>;
  annual_summary: Record<string, Record<string, number | null>>;
  annualized_estimate: Record<string, Record<string, number | null>> | null;
  biomass_schedule: {
    monthly: Array<{time_label: string; available_biomass_tonnes: number; processed_biomass_tonnes: number; unused_biomass_tonnes: number; utilization_fraction: number}>;
    annual_available_tonnes: number; annual_processed_tonnes: number; annual_unused_tonnes: number;
    utilization_fraction: number; peak_month_processed_tonnes: number; unmet_target_tonnes: number;
  };
  assumptions: Evidence[]; assumption_counts: Record<string, number>; assumptions_count: number;
  top_assumptions: string[]; warning_counts: Record<string, number>; warnings_count: number;
  blocker_counts: Record<string, number>; blockers_count: number;
  readiness: {status: string; validated_simulation_ready: false; can_drive_complete_biosteam_proxy: boolean; assumptions_enabled: boolean};
  analysis: {
    proxy_analysis_ready: boolean; assumptions: Evidence[]; warnings: string[];
    economic: null | {revenue_eur_per_year: Record<string, number>; costs_eur_per_year: Record<string, number>;
      total_revenue_eur_per_year: number; total_cost_eur_per_year: number; net_operating_margin_eur_per_year: number;
      cost_eur_per_tonne_feed: number | null; cost_eur_per_kg_dried_protein: number | null; cost_eur_per_m3_biomethane: number | null; allocation_note: string};
    environmental: null | {contributions_kg_co2e_per_year: Record<string, number>; net_kg_co2e_per_year: number;
      kg_co2e_per_tonne_feed: number | null; kg_co2e_per_kg_dried_protein: number | null};
  };
}
async function jsonResponse<T>(response: Response): Promise<T> {
  const data = await response.json();
  if (!response.ok) throw new Error(data?.error?.message || `Proxy API returned ${response.status}`);
  return data;
}
export async function fetchDynamicOptions(): Promise<DynamicOptions> {
  return jsonResponse(await fetch(`${API_BASE}/dynamic-complete/options`));
}
export async function runDynamicScenario(scenario: DynamicScenario, analysis_factors: Record<string, number>): Promise<DynamicReport> {
  return jsonResponse(await fetch(`${API_BASE}/dynamic-complete/scenario-summary`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({scenario, analysis_factors}),
  }));
}
