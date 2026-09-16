import { DYNAMIC_BASELINE_OPTIONS, DYNAMIC_BASELINE_REPORT, EMPIRICAL_BASELINE_RESULT } from '../src/data/baselineFixtures';

function requireValue(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const empirical = EMPIRICAL_BASELINE_RESULT.annual;
requireValue(empirical, 'Empirical fixture must include an annual report.');
requireValue(empirical.monthly.length === 12, 'Empirical fixture must cover all twelve months.');
requireValue(Math.abs(empirical.biomass_schedule.annual_processed_tonnes - 30000) < 1e-6, 'Empirical fixture must integrate to 30,000 t/year.');
requireValue(empirical.chart_data.schedule.length === 12, 'Empirical fixture must include schedule chart data.');
requireValue(empirical.chart_data.small_products.length === 12, 'Empirical fixture must include product chart data.');
requireValue(empirical.process_pathway.length === 6, 'Empirical fixture must include the six-stage process story.');

requireValue(DYNAMIC_BASELINE_OPTIONS.defaults.include_press_cake_in_ad === false, 'Dynamic fixture must preserve the press-cake boundary.');
requireValue(DYNAMIC_BASELINE_REPORT.monthly.length === 12, 'Dynamic fixture must cover all twelve months.');
requireValue(DYNAMIC_BASELINE_REPORT.annual_summary.feed_processed.tonnes_per_year === 30000, 'Dynamic fixture must integrate to 30,000 t/year.');
requireValue(DYNAMIC_BASELINE_REPORT.assumptions.length > 0, 'Dynamic fixture must include evidence records.');
requireValue(Boolean(DYNAMIC_BASELINE_REPORT.analysis.economic), 'Dynamic fixture must include the economic proxy.');
requireValue(Boolean(DYNAMIC_BASELINE_REPORT.analysis.environmental), 'Dynamic fixture must include the environmental proxy.');

console.log('Fallback fixtures are complete and internally consistent.');
