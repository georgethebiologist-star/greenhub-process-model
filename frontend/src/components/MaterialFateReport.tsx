import React from 'react';
import type { AnnualSummary, MaterialFateStream, ProcessStream, SimulationResult } from '../types';
import elementFractions from '../data/elementFractions.json';

type Fate = NonNullable<AnnualSummary['material_fate']>;
const productLabels: Record<string, string> = {
  dry_protein_product: 'Protein', biostimulant_product: 'Biostimulant concentrate',
  biomethane: 'Biomethane', phosphorus_product: 'Phosphorus product',
  ammonium_product: 'Ammonium product', potassium_concentrate: 'Potassium concentrate',
  nutrient_rich_solids: 'Nutrient-rich solids',
};
const residualPattern = /residual_liquor|nitrogen_depleted_liquor|ion_exchange_treated_liquor|treated_water|phase[67]_wastewater|technology_wastewater|conditioning_wastewater/i;
const tonnes = (kg: number) => (kg / 1000).toLocaleString(undefined, { maximumFractionDigits: 4 });
const label = (id: string) => { const text = id.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/_/g, ' '); return text.charAt(0).toUpperCase() + text.slice(1); };

function fallbackFate(streams: ProcessStream[], hours: number): Fate {
  const elements = (components: Record<string, number>) => {
    const result: Record<string, number> = {};
    for (const [component, mass] of Object.entries(components)) {
      const fractions = (elementFractions as Record<string, Record<string, number>>)[component] || {};
      for (const [element, fraction] of Object.entries(fractions)) result[element] = (result[element] || 0) + mass * fraction;
    }
    return result;
  };
  const make = (id: string, name: string, members: ProcessStream[]): MaterialFateStream => {
    const components: Record<string, number> = {};
    for (const stream of members) for (const [component, flow] of Object.entries(stream.components_kg_hr || {})) {
      components[component] = (components[component] || 0) + flow * hours;
    }
    return { stream_id: id, label: name, mass_kg: Object.values(components).reduce((sum, mass) => sum + mass, 0), components_kg: components, elements_kg: elements(components) };
  };
  const juice = make('grass_juice', 'Grass juice', streams.filter(stream => stream.id === 'raw_liquid_fraction'));
  const terminal = streams.filter(stream => stream.destination === 'boundary');
  const products = Object.entries(productLabels).map(([id, name]) => make(id, name, terminal.filter(stream => stream.id === id || stream.name === id))).filter(item => item.mass_kg > 0);
  const waterStreams = terminal.filter(stream => stream.mass_flow_kgh > 0 && residualPattern.test(`${stream.id} ${stream.name}`));
  const water = make('residual_water', 'Residual water', waterStreams);
  return { basis: 'Displayed representative stream rates × stated operating hours; seasonal composition changes are not included in this saved preview.', grass_juice: juice, products, residual_water: { ...water, streams: waterStreams.map(stream => make(stream.id, label(stream.id), [stream])) } };
}

function FateTable({ stream, juice, kind }: { stream: MaterialFateStream; juice: MaterialFateStream; kind: 'recovered' | 'left' }) {
  const percentage = (amount: number, input: number) => input > 0 ? `${(100 * amount / input).toLocaleString(undefined, { maximumFractionDigits: 2 })}%` : '—';
  const table = (title: string, output: Record<string, number>, input: Record<string, number>) => {
    const rows = Object.entries(output).filter(([, mass]) => mass > 0).sort((a, b) => b[1] - a[1]);
    return <div className="material-fate-table"><h6>{title}</h6><div className="data-table-wrap"><table className="data-table"><thead><tr><th>{title === 'Elements' ? 'Element' : 'Compound / model pool'}</th><th>In grass juice · t/year</th><th>{kind === 'left' ? 'Left in water' : 'In product'} · t/year</th><th>{kind === 'left' ? 'Left' : 'Recovery'} of juice</th></tr></thead><tbody>{rows.map(([name, mass]) => <tr key={name}><td>{label(name)}</td><td>{tonnes(input[name] || 0)}</td><td>{tonnes(mass)}</td><td>{percentage(mass, input[name] || 0)}</td></tr>)}</tbody></table></div></div>;
  };
  return <div className="material-fate-grid">{table('Elements', stream.elements_kg, juice.elements_kg)}{table('Compounds and model pools', stream.components_kg, juice.components_kg)}</div>;
}

export function MaterialFateReport({ result, annual }: { result: SimulationResult; annual: AnnualSummary | null }) {
  const fate = annual?.material_fate || fallbackFate(result.streams, annual?.period.operating_hours || 8760);
  const juice = fate.grass_juice;
  if (!juice.mass_kg) return <p className="material-fate-note">Grass juice component flows are unavailable for this run.</p>;
  const water = fate.residual_water;
  return <section className="material-fate-report" aria-label="Grass juice material fate">
    <div className="story-title"><div><h4>What remains in water and enters products</h4><p>Grass juice: {tonnes(juice.mass_kg)} t/year. Amounts are wet stream component masses; elements are derived from modeled component composition.</p></div></div>
    <p className="material-fate-note">{fate.basis} Percentages use each element or compound pool in grass juice as the denominator. A dash means that pool was absent from the juice; process additions and reactions can produce values above 100%.</p>
    {water.mass_kg > 0 ? <details className="material-fate-outlet" open><summary><strong>Residual water · {tonnes(water.mass_kg)} t/year</strong><span>Left in water, not recovered</span></summary><p>{(water.streams || []).map(stream => `${stream.label} ${tonnes(stream.mass_kg)} t/year`).join(' · ')}</p><FateTable stream={water} juice={juice} kind="left"/></details> : <p className="material-fate-note">No terminal residual-water stream was reported for this route.</p>}
    {fate.products.map(product => <details className="material-fate-outlet" key={product.stream_id}><summary><strong>{product.label} · {tonnes(product.mass_kg)} t/year</strong><span>Recovered product composition</span></summary><FateTable stream={product} juice={juice} kind="recovered"/></details>)}
  </section>;
}
