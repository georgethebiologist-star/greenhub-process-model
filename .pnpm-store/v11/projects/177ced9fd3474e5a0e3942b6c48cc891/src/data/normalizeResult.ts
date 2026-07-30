import type { ProcessAreaId, SimulationResult } from '../types';

export type ResultAvailability = 'available' | 'unavailable' | 'provisional' | 'inactive' | 'planned';
export interface ResultEnvelope { result: SimulationResult; source: 'typescript-shim' | 'python-api' | 'unknown'; availability: ResultAvailability; warnings: string[]; limitations: string[]; raw?: any; }

export function normalizeResult(payload: unknown, fallback: SimulationResult): ResultEnvelope {
  if (!payload || typeof payload !== 'object') return unavailable(fallback, 'The simulation response was empty.');
  const value = payload as any;
  if (value.metrics && Array.isArray(value.units) && Array.isArray(value.streams)) return { result: value, source: 'typescript-shim', availability: 'available', warnings: warningMessages(value.validation?.issues), limitations: [], raw: value };
  if (!value.summary_kpis && !value.graph && !value.export_references) return unavailable(fallback, 'The response contract is not recognized by the frontend.');

  const product = (id: string) => numberValue((value.products || []).find((item: any) => item.product_id === id)?.mass_flow);
  const totalPower = (value.units || []).reduce((sum: number, unit: any) => sum + numberValue(unit.power), 0);
  const totalHeat = (value.units || []).flatMap((unit: any) => unit.heat_duties || []).reduce((sum: number, duty: any) => sum + Math.abs(numberValue(duty)) / 3600, 0);
  const selected = value.selected_scenarios || {};
  const graphNodes = new Map((value.graph?.nodes || []).map((node: any) => [node.unit_id, node]));
  const areas = Object.fromEntries((value.process_areas || []).map((area: any) => [area.process_area_id, {
    id: area.process_area_id as ProcessAreaId,
    name: area.display_name,
    description: `${area.model_maturity || 'structural'} model area`,
    units: area.unit_ids || [], streams: [...(area.inlet_stream_ids || []), ...(area.outlet_stream_ids || [])],
    key_assumptions: [], limitations: area.warnings || [],
  }])) as SimulationResult['process_areas'];
  const balances = value.balances || [];
  const overall = balances.find((item: any) => item.balance_id === 'overall_mass');
  const element = (name: string) => balances.find((item: any) => item.balance_id === `element_${name}`);
  const balanceItem = (name: string) => { const item = element(name); return { in: numberValue(item?.inlet), out: numberValue(item?.outlet), closure: closure(item) }; };
  const readiness = value.dataset_readiness || {};
  const readinessTotal = Object.values(readiness).reduce((sum: number, count: any) => sum + Number(count || 0), 0);
  const readinessGood = Number(readiness.A || readiness.measured || 0) + Number(readiness.B || readiness.literature || 0);
  const issues = (value.validation?.issues || []).map((issue: any) => ({ severity: issue.severity === 'error' ? 'error' : issue.severity === 'warning' ? 'warning' : 'info', message: issue.message || String(issue) }));
  const warnings = [...(value.warnings || []), ...issues.filter((item: any) => item.severity !== 'info').map((item: any) => item.message)];

  const result: SimulationResult = {
    run_id: String(value.run_id || fallback.run_id), timestamp: String(value.completed_at || value.created_at || fallback.timestamp),
    calculation_mode: value.calculation_mode || fallback.calculation_mode, selected_month: fallback.selected_month,
    scenarios: { feed_front_end: selected.feed_preparation || 'F2', protein_recovery: selected.protein_recovery || 'PR3', anaerobic_digestion: selected.anaerobic_digestion || 'AD1', biogas_upgrading: selected.biogas_upgrading || 'BG2', nutrient_recovery: selected.nutrient_recovery || 'NR4', process_order: selected.process_order || 'A' },
    process_areas: areas,
    units: (value.units || []).map((unit: any) => { const node: any = graphNodes.get(unit.unit_id); return { id: unit.unit_id, name: unit.display_name, area: unit.process_area as ProcessAreaId, type: node?.technology || 'BioSTEAM unit', duty_kw: (unit.heat_duties || []).reduce((sum: number, duty: any) => sum + Math.abs(numberValue(duty)) / 3600, 0), power_kw: numberValue(unit.power), temperature_c: 0, pressure_bar: 0, status: node?.active === false ? 'disabled' : 'active', status_reason: (unit.warnings || []).join(' ') || undefined }; }),
    streams: (value.streams || []).map((stream: any) => ({ id: stream.stream_id, name: stream.aliases?.[0] || stream.stream_id, origin: stream.source_unit || 'boundary', destination: stream.sink_unit || 'boundary', mass_flow_kgh: numberValue(stream.total_mass), dry_solids_pct: 0, cod_kgh: componentSum(stream.components, ['COD']), nitrogen_kgh: componentSum(stream.components, ['N', 'NH3', 'NH4']), phosphorus_kgh: componentSum(stream.components, ['P', 'PO4']), potassium_kgh: componentSum(stream.components, ['K']) })),
    balances: { mass_in_kgh: numberValue(overall?.inlet), mass_out_kgh: numberValue(overall?.outlet), mass_closure_pct: closure(overall), cod_in_kgh: 0, cod_out_kgh: 0, cod_closure_pct: 0, elemental: { carbon: balanceItem('carbon'), nitrogen: balanceItem('nitrogen'), phosphorus: balanceItem('phosphorus'), potassium: balanceItem('potassium'), sulfur: balanceItem('sulfur') } },
    metrics: { biogas_m3h: 0, methane_purity_pct: 0, biomethane_flow_m3h: product('biomethane'), protein_recovered_kgh: product('dry_protein_product'), protein_purity_pct: 0, struvite_yield_kgh: product('phosphorus_product'), ammonia_sulfate_kgh: product('ammonium_product'), calcium_phosphate_kgh: 0, potassium_concentrate_kgh: product('potassium_concentrate'), data_readiness_score: readinessTotal ? readinessGood / readinessTotal * 100 : 0, net_heat_kw: -totalHeat, net_power_kw: -totalPower, total_power_kw: totalPower, total_heat_kw: totalHeat, p_recovery_pct: 0, n_recovery_pct: 0, k_recovery_pct: 0, cod_conversion_pct: 0 },
    parameters: (value.resolved_parameters || []).map((parameter: any) => ({ parameter_id: parameter.parameter_id, name: humanize(parameter.parameter_id), category: 'advanced', process_area: areaFromParameter(parameter.parameter_id), description: parameter.selection_reason || 'Resolved by the Python parameter service.', current_value: parameter.value ?? '', unit: parameter.unit || '', default_value: parameter.value ?? '', quality_class: qualityFromStatus(parameter.status), is_editable: false, notes: [parameter.source, ...(parameter.warnings || [])].filter(Boolean).join(' · ') })),
    plots: [], scenario_comparisons: fallback.scenario_comparisons,
    validation: { status: value.validation?.passed ? (value.validation?.warning_count ? 'warning' : 'pass') : 'fail', residual_error_kgh: Math.abs(numberValue(overall?.residual)), issues },
  };
  return { result, source: 'python-api', availability: warnings.length ? 'provisional' : 'available', warnings, limitations: value.limitations || [], raw: value };
}

function numberValue(value: any): number { return Number(value?.value ?? value ?? 0) || 0; }
function closure(item: any): number { const inlet = numberValue(item?.inlet); return inlet ? Math.max(0, 100 * (1 - Math.abs(numberValue(item?.residual)) / inlet)) : 0; }
function componentSum(components: any, keys: string[]): number { return Object.entries(components || {}).filter(([name]) => keys.some(key => name.toUpperCase().includes(key))).reduce((sum, [, value]) => sum + numberValue(value), 0); }
function warningMessages(issues: any[] = []) { return issues.filter(item => item.severity === 'warning').map(item => item.message); }
function humanize(value: string) { return value.replace(/[._-]+/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase()); }
function areaFromParameter(id: string): ProcessAreaId { if (id.includes('phase4') || id.includes('protein')) return 'protein_recovery'; if (id.includes('phase5') || id.includes('digestion')) return 'anaerobic_digestion'; if (id.includes('phase6') || id.includes('biogas')) return 'biogas_upgrading'; if (id.includes('phase7') || id.includes('nutrient')) return 'nutrient_recovery'; return 'front_end'; }
function qualityFromStatus(status: string): 'A'|'B'|'C'|'D'|'E' { if (status === 'measured') return 'A'; if (status === 'literature_default') return 'B'; if (status === 'calibrated') return 'B'; if (status === 'blocked' || status === 'missing') return 'D'; return 'C'; }
function unavailable(fallback: SimulationResult, warning: string): ResultEnvelope { return { result: fallback, source: 'unknown', availability: 'unavailable', warnings: [warning], limitations: ['Displayed values are from the development fallback.'] }; }
