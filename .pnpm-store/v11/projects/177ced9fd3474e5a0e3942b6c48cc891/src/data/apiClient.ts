import type { FeedInputs } from '../components/InputStudio';
import type { AnnualSummary, CalculationMode, EmpiricalBiomassSchedule, PlotCatalogItem, ScenarioSelection } from '../types';

const configuredApiBase = String(import.meta.env.VITE_GREENHUB_API_URL || '').trim();
const defaultApiBase = import.meta.env.PROD ? '/api/v1' : 'http://127.0.0.1:8000/api/v1';
export const API_BASE = (configuredApiBase || defaultApiBase).replace(/\/$/, '');
export const API_TIMEOUT_MS = Math.max(Number(import.meta.env.VITE_GREENHUB_API_TIMEOUT_MS || 15000), 1000);

export class GreenHubApiError extends Error {
  constructor(message: string, public readonly endpoint: string, public readonly status?: number) {
    super(message);
    this.name = 'GreenHubApiError';
  }
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const endpoint = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    const response = await fetch(endpoint, {...init, signal: controller.signal});
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new GreenHubApiError(data?.error?.message || `GreenHub API returned ${response.status}.`, endpoint, response.status);
    }
    if (data === null) throw new GreenHubApiError('The endpoint responded without a valid JSON payload.', endpoint, response.status);
    return data as T;
  } catch (error) {
    if (error instanceof GreenHubApiError) throw error;
    const reason = error instanceof DOMException && error.name === 'AbortError'
      ? `Request timed out after ${Math.round(API_TIMEOUT_MS / 1000)} seconds.`
      : error instanceof Error ? error.message : 'Network request failed.';
    throw new GreenHubApiError(`${reason} Check VITE_GREENHUB_API_URL or the same-origin /api/v1 deployment.`, endpoint);
  } finally {
    window.clearTimeout(timer);
  }
}

export interface BackendResources {
  graph: any | null;
  artifacts: Array<{ name: string; type: string; description: string; url?: string; available: boolean; warning?: string }>;
  plots: PlotCatalogItem[];
  annual: AnnualSummary | null;
}

export function buildPythonRequest(mode: CalculationMode, month: string, scenario: ScenarioSelection, feed: FeedInputs, biomassSchedule: EmpiricalBiomassSchedule) {
  const year = biomassSchedule.season_start.slice(0, 4);
  return {
    schema_version: '1.0.0',
    request_id: `greenhub-ui-${Date.now()}`,
    project_id: 'greenhub-engineering',
    calculation_mode: mode,
    resolution_mode: 'quasi_dynamic',
    selected_month: month,
    scenarios: {
      feed_preparation: scenario.feed_front_end,
      protein_recovery: scenario.protein_recovery,
      anaerobic_digestion: scenario.anaerobic_digestion,
      biogas_upgrading: scenario.biogas_upgrading,
      nutrient_recovery: scenario.nutrient_recovery,
      process_order: scenario.process_order,
    },
    start_date: `${year}-01-01`,
    end_date: `${year}-12-31`,
    time_step: 'monthly',
    annual_biomass_target: biomassSchedule.annual_processed_biomass_tonnes * 1000,
    biomass_schedule: biomassSchedule,
    operating_schedule: {
      operating_days_per_week: feed.operatingDaysPerWeek,
      operating_hours_per_day: feed.operatingHoursPerDay,
      target_throughput_kg_hr: biomassSchedule.feed_kg_per_hr,
    },
    requested_plots: [],
    export_formats: ['json', 'csv'],
    strict_validation: true,
  };
}

export async function runPythonSimulation(payload: object): Promise<any> {
  return apiJson('/simulations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}

export async function fetchRunResources(runId: string, specifications: any[] = []): Promise<BackendResources> {
  const [graphResult, exportResult, annualResult, ...plotResults] = await Promise.allSettled([
    apiJson(`/simulations/${runId}/graph`),
    apiJson(`/simulations/${runId}/exports`),
    apiJson(`/simulations/${runId}/annual-summary`),
    ...specifications.filter(item => item.availability_status === 'available').map(item =>
      apiJson(`/simulations/${runId}/plots/${item.plot_id}`)
    ),
  ]);
  const graph = graphResult.status === 'fulfilled' ? graphResult.value : null;
  const exportPayload = exportResult.status === 'fulfilled' ? exportResult.value : {};
  const annual = annualResult.status === 'fulfilled' ? annualResult.value as AnnualSummary : null;
  if (!annual) {
    const detail = annualResult.status === 'rejected' && annualResult.reason instanceof Error ? annualResult.reason.message : 'Annual summary was not returned.';
    throw new GreenHubApiError(`The run completed but its annual reporting bundle is unavailable. ${detail}`, `${API_BASE}/simulations/${runId}/annual-summary`);
  }
  const artifacts = Object.entries(exportPayload || {}).map(([name, reference]) => ({
    name: humanize(name),
    type: extension(String(reference)),
    description: `Generated by the Python export service for run ${runId.slice(0, 10)}.`,
    available: Boolean(reference),
    url: reference ? `${API_BASE}/simulations/${runId}/artifacts/${encodeURIComponent(String(reference))}` : undefined,
    warning: reference ? undefined : 'This file was not generated for the current run.',
  }));
  const plots = plotResults.flatMap(result => result.status === 'fulfilled' ? [normalizePlotData(result.value)] : []);
  return { graph, artifacts, plots, annual };
}

function normalizePlotData(value: any): PlotCatalogItem {
  const spec = value.specification || {};
  const rows: Array<Record<string, string | number>> = [];
  for (const series of value.series || []) {
    (series.x || []).forEach((x: string | number, index: number) => {
      const existing = rows.find(row => row.label === String(x)) || { label: String(x) };
      existing[series.label || series.series_id] = series.y?.[index] ?? 0;
      if (!rows.includes(existing)) rows.push(existing);
    });
  }
  return { id: spec.plot_id || 'unknown', title: spec.title || 'Backend plot', category: humanize(spec.process_area || 'results'), description: `${spec.y_axis_label || 'Result'}${spec.y_unit ? ` [${spec.y_unit}]` : ''}.`, type: String(spec.plot_id || '').startsWith('SEASONAL-') ? 'line' : 'bar', data: rows, meta: spec };
}

function humanize(value: string) { return value.replace(/[_-]+/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase()); }
function extension(value: string) { const match = value.match(/\.([a-z0-9]+)$/i); return match ? match[1].toUpperCase() : 'Artifact'; }
