import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DecisionReport } from '../data/decisionSupport';
import type { SimulationResult } from '../types';
import './decisionSupport.css';

const colors = { electricity: '#729ad2', heating: '#d1a520', cooling: '#d277a3', consumables: '#b77436', labour: '#408f4d', maintenance: '#0c3338' };
const emptyTooltip = { background: '#fffdf9', border: '1px solid #c9c2ba', borderRadius: 8, fontSize: 10, color: '#0c3338' };
const capexStageColors: Record<string, string> = {
  Pretreatment: colors.consumables, 'Protein recovery': colors.cooling,
  'Biomethane production': colors.electricity, 'Ammonia recovery': colors.labour,
  'Struvite recovery': colors.heating, 'Potassium recovery': colors.consumables,
  'Shared utilities': colors.maintenance,
};
const opexColors: Record<string, string> = {
  Labour: colors.labour, Heat: colors.heating, Electricity: colors.electricity, Consumables: colors.maintenance,
};

export default function ProcessHotspots({ result, analysis, limitations = [] }: { result: SimulationResult; analysis: DecisionReport | null; limitations?: string[] }) {
  const tea = analysis?.tea || {};
  const units: any[] = result.units || [];
  const annualUtilities = analysis?.annual?.utilities || {};
  const energyWeights = makeUtilityWeights(units);
  const electricityRows = apportion(annualMWh(annualUtilities.electricity), energyWeights.electricity, 'Electricity');
  const heatRows = apportion(annualMWh(annualUtilities.heating ?? annualUtilities.heat), energyWeights.heating, 'Heat');
  const energyUnavailable = !electricityRows.length && !heatRows.length;

  const capexLines: any[] = tea.capex_lines || [];
  const capexRows = aggregate(capexLines, capexStage, (line) => numericOrNull(line.installed_cost_eur ?? line.direct_cost_eur ?? line.capex_eur));
    
  const opexLines: any[] = tea.opex_lines || [];
  const costText = (line: any) => `${line.process_area || ''} ${line.process_step || ''} ${line.equipment_or_cost_item || ''} ${line.cost_id || ''}`;
  const labour = sumOpex(opexLines.filter((line) => /labou?r/i.test(costText(line))));
  const heat = sumOpex(opexLines.filter((line) => /heat|heating/i.test(costText(line))));
  const electricityOpex = sumOpex(opexLines.filter((line) => /electricity/i.test(costText(line))));
  const otherKnown = sumOpex(opexLines.filter((line) => !/labou?r|heat|heating|electricity/i.test(costText(line))));
  const opexRows = [
    { name: 'Labour', value: labour.value, color: opexColors.Labour },
    { name: 'Heat', value: heat.value, color: opexColors.Heat },
    { name: 'Electricity', value: electricityOpex.value, color: opexColors.Electricity },
    { name: 'Consumables', value: otherKnown.value, color: opexColors.Consumables },
  ].filter((row) => row.value !== null && row.value !== 0) as Array<{ name: string; value: number; color: string }>;
  const opexAllMissing = !opexRows.length;
  const analysisFailure = limitations.find(item => item.startsWith('Post-route assessment:'));

  return <section className="panel analytics-preview" aria-label="Process hotspots">
    <header className="analytics-preview-head"><div><h2>Process hotspots</h2>{analysisFailure&&<p className="analytics-hotspot-error" role="status">Post-route analysis failed: {analysisFailure.replace(/^Post-route assessment:\s*/, '')}</p>}</div></header>
    <div className="analytics-hotspot-grid">
      <StageEnergyChart title="Electricity by stage" rows={electricityRows} empty={energyUnavailable ? 'Electricity and unit demand are not available for this run.' : 'Electricity demand was not reported.'}/>
      <StageEnergyChart title="Heat by stage" rows={heatRows} empty="Heat demand was not reported." color={colors.heating}/>
      <HotspotBarChart title="CAPEX by process stage" unit="€" rows={capexRows} empty="No priced CAPEX lines were returned for this run."/>
      <HotspotBarChart title="OPEX contribution" unit="€/year" rows={opexRows} empty="No annual costs were returned for labour, heat or electricity."/>
    </div>
  </section>;
}

function StageEnergyChart({ title, rows, empty, color = colors.electricity }: { title: string; rows: Array<{ name: string; [key: string]: number | string }>; empty: string; color?: string }) {
  return <section className="analytics-hotspot-card"><h3>{title} <span>· MWh/year</span></h3>
    {rows.length ? <div className="analytics-preview-hotspots"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout="vertical" margin={{ top: 12, right: 28, bottom: 12, left: 12 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact} tick={{ fontSize: 14 }}/><YAxis type="category" dataKey="name" width={190} tick={{ fontSize: 14 }}/><Tooltip contentStyle={emptyTooltip} formatter={(value: number) => [`${number(value)} MWh/year`, title]}/><Bar dataKey={Object.keys(rows[0]).find((key) => key !== 'name') || 'value'} fill={color} radius={[0, 4, 4, 0]}/></BarChart></ResponsiveContainer></div> : <div className="analytics-hotspot-empty">{empty}</div>}
  </section>;
}

function makeUtilityWeights(units: any[]) {
  const weights = { electricity: {} as Record<string, number>, heating: {} as Record<string, number>, cooling: {} as Record<string, number> };
  for (const unit of units) {
    const stage = capexStage({ process_area: unit.process_area, process_step: unit.unit_id, equipment_or_cost_item: unit.display_name });
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

function sumOpex(lines: any[]) {
  const values = lines.map((line) => numericOrNull(line.annual_cost_eur));
  return { value: values.some((value) => value !== null) ? values.reduce<number>((sum, value) => sum + (value ?? 0), 0) : null };
}

function aggregate(lines: any[], nameOf: (line: any) => string, valueOf: (line: any) => number | null) {
  const totals = new Map<string, number>();
  for (const line of lines) { const value = valueOf(line); if (value !== null) totals.set(nameOf(line), (totals.get(nameOf(line)) || 0) + value); }
  return [...totals].map(([name, value]) => ({ name, value, color: capexStageColors[name] || colors.maintenance })).filter((row) => row.value !== 0).sort((a, b) => b.value - a.value);
}

function HotspotBarChart({ title, unit, rows, empty }: { title: string; unit: string; rows: Array<{ name: string; value: number; color?: string }>; empty: string }) {
  const height = Math.max(250, rows.length * 27);
  return <section className="analytics-hotspot-card"><h3>{title} <span>· {unit}</span></h3>
    {rows.length ? <div style={{ width: '100%', height }}><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout="vertical" margin={{ top: 12, right: 28, bottom: 12, left: 12 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/><XAxis type="number" tickFormatter={compact} tick={{ fontSize: 14 }}/><YAxis type="category" dataKey="name" width={190} tick={{ fontSize: 14 }}/><Tooltip contentStyle={emptyTooltip} formatter={(value: number) => [`${unit === '€' || unit === '€/year' ? '€' : ''}${number(value)}${unit === '€' ? '' : unit === '€/year' ? '/year' : ` ${unit}`}`, title]}/><Bar dataKey="value" radius={[0, 4, 4, 0]}>{rows.map((row) => <Cell key={row.name} fill={row.color || colors.electricity}/>)}</Bar></BarChart></ResponsiveContainer></div> : <div className="analytics-hotspot-empty">{empty}</div>}
  </section>;
}

function annualMWh(row: any): number | null {
  const value = finite(row?.value), unit = String(row?.unit || '').toLowerCase();
  if (value === null) return null;
  if (unit.includes('kwh')) return value / 1000;
  if (unit.includes('mwh')) return value;
  return null;
}

function add(record: Record<string, number>, key: string, value: number) { record[key] = (record[key] || 0) + value; }
function numericOrNull(value: unknown) { return finite(value); }
function finite(value: unknown): number | null { if (value === null || value === undefined || value === '') return null; const amount = Number(value); return Number.isFinite(amount) ? amount : null; }
function compact(value: number) { return Math.abs(value) >= 1000 ? `${(value / 1000).toFixed(0)}k` : `${value.toFixed(value < 10 ? 1 : 0)}`; }
function number(value: number) { return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
function humanize(value: string) { return String(value || '').replace(/[._-]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }

function capexStage(line: any) {
  const text = `${line.process_area || ''} ${line.process_step || ''} ${line.equipment_or_cost_item || ''} ${line.unit_id || ''}`.toLowerCase();
  if (/reception|bunker|feed preparation|preparation|cleaning|press|fiber|fibre/.test(text)) return 'Pretreatment';
  if (/protein/.test(text)) return 'Protein recovery';
  if (/ammonia|ammonium|nitrogen|h721|m721|a721|a722|v722|a731|r731/.test(text)) return 'Ammonia recovery';
  if (/phosphorus|struvite|r711|s711|w711|d711/.test(text)) return 'Struvite recovery';
  if (/potassium|m741|e741|d741|v741|water\/nutrient concentration|concentration train|reverse osmosis|\bro\b|\bnf\b|\bed\b|evaporat/.test(text)) return 'Potassium recovery';
  if (/digestion|digester|biogas|biomethane|gas safety|gas conditioning|upgrad|digestate.*separat|separat.*digestate/.test(text)) return 'Biomethane production';
  return 'Shared utilities';
}

