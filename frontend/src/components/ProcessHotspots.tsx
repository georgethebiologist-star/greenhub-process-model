import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DecisionReport } from '../data/decisionSupport';
import type { SimulationResult } from '../types';
import './decisionSupport.css';

const colors = { electricity: '#729ad2', heating: '#d1a520', cooling: '#d277a3', consumables: '#b77436', labour: '#408f4d', maintenance: '#0c3338', process: '#0c3338' };
const areaLabels: Record<string, string> = {
  feed_preparation_and_primary_separation: 'Feed preparation', protein_recovery: 'Protein recovery',
  anaerobic_digestion: 'Anaerobic digestion', biogas_conditioning_and_upgrading: 'Biogas upgrading',
  digestate_treatment_and_nutrient_recovery: 'Nutrient recovery', utilities: 'Utilities',
};
const emptyTooltip = { background: '#fffdf9', border: '1px solid #c9c2ba', borderRadius: 8, fontSize: 10, color: '#0c3338' };

type ChartRow = { name: string; Electricity?: number; Heating?: number; Cooling?: number; Heat?: number; 'Process emissions'?: number; value?: number | null };

export default function ProcessHotspots({ result, analysis }: { result: SimulationResult; analysis: DecisionReport | null }) {
  const tea = analysis?.tea || {};
  const lca = analysis?.lca || {};
  const units: any[] = result.units || [];
  const annualUtilities = analysis?.annual?.utilities || {};
  const energyWeights = makeUtilityWeights(units);
  const electricity = apportion(annualMWh(annualUtilities.electricity), energyWeights.electricity, 'Electricity');
  const heating = apportion(annualMWh(annualUtilities.heating ?? annualUtilities.heat), energyWeights.heating, 'Heating');
  const cooling = apportion(annualMWh(annualUtilities.cooling), energyWeights.cooling, 'Cooling');
  const energyRows = mergeRows(electricity, heating, cooling);
  const energyUnavailable = !electricity.length && !heating.length && !cooling.length;

  const capexLines: any[] = tea.capex_lines || [];
  const capexRows = aggregate(capexLines, (line) => line.process_step || areaLabels[line.process_area] || humanize(line.process_area || 'Other'), (line) => numericOrNull(line.installed_cost_eur ?? line.direct_cost_eur ?? line.capex_eur));
    
  const opexLines: any[] = tea.opex_lines || [];
  const electricityCost = summarizeOpex('Electricity', opexLines.filter((line) => /electricity/i.test(`${line.process_step || ''} ${line.cost_id || ''}`)), colors.electricity);
  const heatingCost = summarizeOpex('Heating', opexLines.filter((line) => /heat|heating/i.test(`${line.process_step || ''} ${line.equipment_or_cost_item || ''} ${line.cost_id || ''}`)), colors.heating);
  const coolingCost = summarizeOpex('Cooling', opexLines.filter((line) => /cooling/i.test(`${line.process_step || ''} ${line.equipment_or_cost_item || ''} ${line.cost_id || ''}`)), colors.cooling);
  const consumablesCost = summarizeOpex('Consumables', opexLines.filter((line) => /consumable|chemical|reagent/i.test(`${line.process_area || ''} ${line.process_step || ''} ${line.cost_id || ''}`)), colors.consumables);
  const labourCost = summarizeOpex('Labour', opexLines.filter((line) => /labou?r/i.test(`${line.process_step || ''} ${line.equipment_or_cost_item || ''} ${line.cost_id || ''}`)), colors.labour);
  const maintenanceCost = summarizeOpex('Maintenance', opexLines.filter((line) => /maintenan/i.test(`${line.process_area || ''} ${line.process_step || ''} ${line.equipment_or_cost_item || ''} ${line.cost_id || ''}`)), colors.maintenance);
  const energyCost = combineOpex('Energy', [electricityCost, heatingCost, coolingCost], colors.electricity);
  const opexCategories = [energyCost, consumablesCost, labourCost, maintenanceCost];
  const opexRows = [
    { name: 'Energy', Electricity: knownOrNull(electricityCost), Heating: knownOrNull(heatingCost), Cooling: knownOrNull(coolingCost), Consumables: null, Labour: null, Maintenance: null },
    { name: 'Consumables', Electricity: null, Heating: null, Cooling: null, Consumables: knownOrNull(consumablesCost), Labour: null, Maintenance: null },
    { name: 'Labour', Electricity: null, Heating: null, Cooling: null, Consumables: null, Labour: knownOrNull(labourCost), Maintenance: null },
    { name: 'Maintenance', Electricity: null, Heating: null, Cooling: null, Consumables: null, Labour: null, Maintenance: knownOrNull(maintenanceCost) },
  ];
  const opexAllMissing = opexCategories.every((category) => !category.hasAnyValue);

  const climateRows = makeClimateRows(lca.inventory || [], energyWeights);
  const climateTotal = climateRows.reduce((total, row) => total + Number(row.Electricity || 0) + Number(row.Heat || 0) + Number(row['Process emissions'] || 0), 0);

  return <section className="panel analytics-preview" aria-label="Process hotspots">
    <header className="analytics-preview-head"><div><span className="eyebrow">RUN-SPECIFIC HOTSPOTS</span><h2>Process hotspots</h2><p>Energy, capital, operating costs and climate burdens for the current simulation.</p></div></header>
    <div className="analytics-hotspot-grid">
      <section className="analytics-hotspot-card"><h3>Energy by process step <span>· MWh/year</span></h3>
        {energyUnavailable ? <div className="analytics-hotspot-empty">Annual energy or unit-level demand is not available for this run.</div> : <div className="analytics-preview-hotspots"><ResponsiveContainer width="100%" height="100%"><BarChart data={energyRows} layout="vertical" margin={{ top: 8, right: 18, bottom: 8, left: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact} tick={{ fontSize: 9 }}/><YAxis type="category" dataKey="name" width={144} tick={{ fontSize: 9 }}/><Tooltip contentStyle={emptyTooltip} formatter={(value: number, name: string) => [`${number(value)} MWh/year`, name]}/><Legend/><Bar dataKey="Electricity" stackId="utility" fill={colors.electricity}/><Bar dataKey="Heating" stackId="utility" fill={colors.heating}/><Bar dataKey="Cooling" stackId="utility" fill={colors.cooling}/></BarChart></ResponsiveContainer></div>}
        <p className="analytics-hotspot-caveat">Reported annual utility totals are allocated to process steps by their simulated unit demand.</p>
      </section>

      <HotspotBarChart title="CAPEX by process step" unit="€" rows={capexRows} color={colors.heating} empty="No priced CAPEX lines were returned for this run."/>

      <section className="analytics-hotspot-card"><h3>OPEX breakdown <span>· €/year</span></h3>
        {opexAllMissing ? <div className="analytics-hotspot-empty">No annual costs were returned for energy, consumables, labour or maintenance.</div> : <div className="analytics-preview-hotspots"><ResponsiveContainer width="100%" height="100%"><BarChart data={opexRows} layout="vertical" margin={{ top: 8, right: 22, bottom: 8, left: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact} tick={{ fontSize: 9 }}/><YAxis type="category" dataKey="name" width={104} tick={{ fontSize: 10 }}/><Tooltip contentStyle={emptyTooltip} formatter={(value: number, name: string) => [`€${number(value)}/year`, name]}/><Legend/><Bar dataKey="Electricity" stackId="opex" fill={colors.electricity}/><Bar dataKey="Heating" stackId="opex" fill={colors.heating}/><Bar dataKey="Cooling" stackId="opex" fill={colors.cooling}/><Bar dataKey="Consumables" stackId="opex" fill={colors.consumables}/><Bar dataKey="Labour" stackId="opex" fill={colors.labour}/><Bar dataKey="Maintenance" stackId="opex" fill={colors.maintenance}/></BarChart></ResponsiveContainer></div>}
        <div className="hotspot-category-values">{opexCategories.map((category) => <div key={category.name}><span>{category.name}{category === energyCost ? ` · Electricity ${formatCostDetail(electricityCost)} · Heating ${formatCostDetail(heatingCost)} · Cooling ${formatCostDetail(coolingCost)}` : ''}</span><strong>{category.hasAnyValue ? `€${number(category.knownValue)}/year` : 'Not reported'}{category.incomplete ? ' · partial' : ''}</strong></div>)}</div>
      </section>

      <section className="analytics-hotspot-card"><h3>Climate load by process step <span>· t CO₂-eq/year</span></h3>
        {climateRows.length ? <div className="analytics-preview-hotspots"><ResponsiveContainer width="100%" height="100%"><BarChart data={climateRows} layout="vertical" margin={{ top: 8, right: 18, bottom: 8, left: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact} tick={{ fontSize: 9 }}/><YAxis type="category" dataKey="name" width={144} tick={{ fontSize: 9 }}/><Tooltip contentStyle={emptyTooltip} formatter={(value: number, name: string) => [`${number(value)} t CO₂-eq/year`, name]}/><Legend/><Bar dataKey="Electricity" stackId="climate" fill={colors.electricity}/><Bar dataKey="Heat" stackId="climate" fill={colors.heating}/><Bar dataKey="Process emissions" stackId="climate" fill={colors.process}/></BarChart></ResponsiveContainer></div> : <div className="analytics-hotspot-empty">No characterized climate burdens were returned for this run.</div>}
        {climateRows.length > 0 && <p className="analytics-hotspot-caveat">Utility burdens are allocated by unit demand; methane loads are assigned to their reported gas outlet stage. Total shown: {number(climateTotal)} t CO₂-eq/year.</p>}
      </section>
    </div>
  </section>;
}

function makeUtilityWeights(units: any[]) {
  const weights = { electricity: {} as Record<string, number>, heating: {} as Record<string, number>, cooling: {} as Record<string, number> };
  for (const unit of units) {
    const stage = areaLabels[unit.area || unit.process_area] || humanize(unit.area || unit.process_area || 'Other');
    const power = finite(unit.power_kw ?? unit.power?.value);
    if (power !== null && power > 0) add(weights.electricity, stage, power);
    let heating = finite(unit.heating_kw), cooling = finite(unit.cooling_kw);
    if (heating === null || cooling === null) {
      const duties: any[] = unit.heat_duties || [];
      if (duties.length) {
        heating = 0; cooling = 0;
        for (const duty of duties) {
          const value = finite(duty.value ?? duty);
          if (value === null) continue;
          const unitLabel = String(duty.unit || 'kJ/hr').toLowerCase();
          const kw = unitLabel === 'kw' ? value : unitLabel.includes('kj') ? value / 3600 : value;
          if (kw >= 0) heating += kw;
          else cooling += Math.abs(kw);
        }
      }
    }
    if (heating !== null && heating > 0) add(weights.heating, stage, heating);
    if (cooling !== null && cooling > 0) add(weights.cooling, stage, cooling);
  }
  return weights;
}

function apportion(total: number | null, weights: Record<string, number>, label: string) {
  if (total === null) return [] as Array<{ name: string; [key: string]: number | string }>;
  const sum = Object.values(weights).reduce((acc, value) => acc + value, 0);
  if (sum <= 0) return total > 0 ? [{ name: 'Process allocation not available', [label]: total }] : [];
  return Object.entries(weights).filter(([, value]) => value > 0).map(([name, value]) => ({ name, [label]: total * value / sum }));
}

function mergeRows(...collections: Array<Array<{ name: string; [key: string]: number | string }>>): ChartRow[] {
  const rows = new Map<string, ChartRow>();
  for (const collection of collections) for (const item of collection) Object.assign(rows.get(item.name) || (rows.set(item.name, { name: item.name }), rows.get(item.name)!), item);
  return [...rows.values()].sort((a, b) => sumEnergy(b) - sumEnergy(a));
}

function makeClimateRows(inventory: any[], weights: ReturnType<typeof makeUtilityWeights>): ChartRow[] {
  const rows = new Map<string, ChartRow>();
  const addClimate = (stage: string, source: 'Electricity' | 'Heat' | 'Process emissions', valueKg: number) => {
    const row = rows.get(stage) || { name: stage };
    row[source] = Number(row[source] || 0) + valueKg / 1000;
    rows.set(stage, row);
  };
  for (const line of inventory) {
    const burden = finite(line.climate_kg_co2e);
    if (burden === null || burden === 0) continue;
    if (line.group === 'electricity' || line.flow_id === 'electricity') {
      const total = Object.values(weights.electricity).reduce((sum, value) => sum + value, 0);
      if (total > 0) for (const [stage, share] of Object.entries(weights.electricity)) addClimate(stage, 'Electricity', burden * share / total);
      else addClimate('Process allocation not available', 'Electricity', burden);
    } else if (line.group === 'heat' || line.flow_id === 'heat') {
      const total = Object.values(weights.heating).reduce((sum, value) => sum + value, 0);
      if (total > 0) for (const [stage, share] of Object.entries(weights.heating)) addClimate(stage, 'Heat', burden * share / total);
      else addClimate('Process allocation not available', 'Heat', burden);
    } else if (String(line.group).includes('process') || String(line.flow_id).startsWith('process_')) {
      addClimate(stageForEmission(String(line.flow_id || '')), 'Process emissions', burden);
    } else addClimate(humanize(String(line.group || line.flow_id || 'Other')), 'Process emissions', burden);
  }
  return [...rows.values()].sort((a, b) => climateSum(b) - climateSum(a));
}

function summarizeOpex(name: string, lines: any[], color: string) {
  const values = lines.map((line) => finite(line.annual_cost_eur));
  return { name, color, knownValue: values.reduce<number>((sum, value) => sum + (value ?? 0), 0), hasAnyValue: values.some((value) => value !== null), incomplete: values.some((value) => value === null) };
}

function combineOpex(name: string, parts: Array<{ name: string; color: string; knownValue: number; hasAnyValue: boolean; incomplete: boolean }>, color: string) {
  return { name, color, knownValue: parts.reduce((sum, part) => sum + part.knownValue, 0), hasAnyValue: parts.some((part) => part.hasAnyValue), incomplete: parts.some((part) => !part.hasAnyValue || part.incomplete) };
}

function knownOrNull(category: { knownValue: number; hasAnyValue: boolean }) {
  return category.hasAnyValue ? category.knownValue : null;
}

function formatCostDetail(category: { knownValue: number; hasAnyValue: boolean; incomplete: boolean }) {
  return category.hasAnyValue ? `€${number(category.knownValue)}${category.incomplete ? ' partial' : ''}` : 'not reported';
}

function aggregate(lines: any[], nameOf: (line: any) => string, valueOf: (line: any) => number | null) {
  const totals = new Map<string, number>();
  for (const line of lines) { const value = valueOf(line); if (value !== null) totals.set(nameOf(line), (totals.get(nameOf(line)) || 0) + value); }
  return [...totals].map(([name, value]) => ({ name, value })).filter((row) => row.value !== 0).sort((a, b) => b.value - a.value);
}

function HotspotBarChart({ title, unit, rows, color, empty }: { title: string; unit: string; rows: Array<{ name: string; value: number }>; color: string; empty: string }) {
  const height = Math.max(250, rows.length * 27);
  return <section className="analytics-hotspot-card"><h3>{title} <span>· {unit}</span></h3>
    {rows.length ? <div style={{ width: '100%', height }}><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout="vertical" margin={{ top: 4, right: 22, bottom: 4, left: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact} tick={{ fontSize: 9 }}/><YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 9 }}/><Tooltip contentStyle={emptyTooltip} formatter={(value: number) => [`${unit === '€' ? '€' : ''}${number(value)}${unit === '€' ? '' : ` ${unit}`}`, title]}/><Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]}/></BarChart></ResponsiveContainer></div> : <div className="analytics-hotspot-empty">{empty}</div>}
  </section>;
}

function annualMWh(row: any): number | null {
  const value = finite(row?.value), unit = String(row?.unit || '').toLowerCase();
  if (value === null) return null;
  if (unit.includes('kwh')) return value / 1000;
  if (unit.includes('mwh')) return value;
  return null;
}

function stageForEmission(flow: string) {
  if (flow.includes('uncaptured_biogas')) return 'Anaerobic digestion';
  if (flow.includes('reject_gas')) return 'Biogas upgrading';
  if (flow.includes('phase7')) return 'Nutrient recovery';
  return 'Process emissions';
}

function add(record: Record<string, number>, key: string, value: number) { record[key] = (record[key] || 0) + value; }
function numericOrNull(value: unknown) { return finite(value); }
function finite(value: unknown): number | null { if (value === null || value === undefined || value === '') return null; const amount = Number(value); return Number.isFinite(amount) ? amount : null; }
function sumEnergy(row: ChartRow) { return Number(row.Electricity || 0) + Number(row.Heating || 0) + Number(row.Cooling || 0); }
function climateSum(row: ChartRow) { return Number(row.Electricity || 0) + Number(row.Heat || 0) + Number(row['Process emissions'] || 0); }
function compact(value: number) { return Math.abs(value) >= 1000 ? `${(value / 1000).toFixed(0)}k` : `${value.toFixed(value < 10 ? 1 : 0)}`; }
function number(value: number) { return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
function humanize(value: string) { return String(value || '').replace(/[._-]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }
