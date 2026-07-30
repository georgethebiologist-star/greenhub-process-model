import type { SimulationResult } from '../types';

export type ResultAvailability = 'available' | 'unavailable' | 'provisional' | 'inactive' | 'planned';

export interface ResultEnvelope {
  result: SimulationResult;
  source: 'typescript-shim' | 'python-api' | 'unknown';
  availability: ResultAvailability;
  warnings: string[];
  limitations: string[];
}

/** Normalizes both the current UI shim and the Python API result envelope. */
export function normalizeResult(payload: unknown, fallback: SimulationResult): ResultEnvelope {
  if (!payload || typeof payload !== 'object') return unavailable(fallback, 'The simulation response was empty.');
  const value = payload as Record<string, any>;
  if (isFrontendResult(value)) return { result: value as SimulationResult, source: 'typescript-shim', availability: 'available', warnings: value.validation?.issues?.filter((x: any) => x.severity === 'warning').map((x: any) => x.message) ?? [], limitations: [] };

  // Python result contracts use summary_kpis, selected_scenarios, graph and export_references.
  const kpis = value.summary_kpis ?? {};
  const warnings = [...(value.warnings ?? []), ...(value.validation?.issues ?? []).map((x: any) => x.message ?? String(x))];
  const limitations = value.limitations ?? [];
  const partial = { ...fallback, run_id: String(value.run_id ?? fallback.run_id), timestamp: String(value.completed_at ?? value.created_at ?? fallback.timestamp), calculation_mode: value.calculation_mode ?? fallback.calculation_mode, scenarios: value.selected_scenarios ?? fallback.scenarios, validation: { ...fallback.validation, status: value.validation?.passed === false ? 'warning' : fallback.validation.status, issues: warnings.map(message => ({ severity: 'warning' as const, message })) } };
  if ('summary_kpis' in value || 'graph' in value || 'export_references' in value) return { result: partial, source: 'python-api', availability: 'provisional', warnings, limitations };
  return unavailable(fallback, 'The response contract is not recognized by the frontend.');
}

function isFrontendResult(value: Record<string, any>): boolean { return Array.isArray(value.units) && Array.isArray(value.streams) && value.metrics && value.process_areas; }
function unavailable(fallback: SimulationResult, warning: string): ResultEnvelope { return { result: fallback, source: 'unknown', availability: 'unavailable', warnings: [warning], limitations: ['Displayed values are the last valid local result.'] }; }
