import type { DecisionReport } from '../data/decisionSupport';

type InventoryLine = Record<string, any>;

export default function InventoryPage({ analysis }: { analysis: DecisionReport | null }) {
  const capex: InventoryLine[] = analysis?.tea?.capex_lines || [];
  const consumables: InventoryLine[] = (analysis?.tea?.opex_lines || []).filter((line: InventoryLine) =>
    /consumable|chemical|reagent/i.test(`${line.process_area || ''} ${line.process_step || ''} ${line.cost_type || ''}`),
  );
  const annualGrassKg = Number(analysis?.annual?.feed_processed?.value) || 0;

  return <div className="story-stack">
    <section className="panel result-section">
      <div className="story-title"><div><h4>Inventory</h4><p>Capital equipment and annual consumables from the current model run.</p></div></div>
      <details className="result-disclosure">
        <summary>Capital inventory <span>{capex.length} items</span></summary>
        <InventoryTable
          headers={['Name', 'Used for', 'Volume / scale', 'Price']}
          rows={capex.map((line) => {
            const capacity = numeric(line.project_capacity) ? `${formatNumber(line.project_capacity)} ${line.project_capacity_unit || ''}`
              : numeric(line.reference_capacity) ? `${formatNumber(line.reference_capacity)} ${line.capacity_unit || ''} (reference)`
                : 'Not reported';
            const price = numeric(line.installed_cost_eur) ? `${formatEuro(line.installed_cost_eur)} installed`
              : numeric(line.direct_cost_eur) ? `${formatEuro(line.direct_cost_eur)} direct` : 'Not reported';
            return [line.equipment_or_cost_item || line.description || line.cost_id || 'Unnamed item',
              [line.process_area, line.process_step].filter(Boolean).map(humanize).join(' · ') || 'Not reported', capacity, price];
          })}
          empty="No capital inventory was returned for this run."
        />
      </details>
      <details className="result-disclosure">
        <summary>Consumables <span>{consumables.length} items</span></summary>
        <InventoryTable
          headers={['Name', 'Quantity / year', 'Per kg grass', 'Cost (€/kg or €/L)', 'Cost / year']}
          rows={consumables.map((line) => {
            const quantity = numeric(line.quantity) ? Number(line.quantity) : null;
            const quantityUnit = String(line.quantity_unit || '');
            const normalizedUnit = quantityUnit.toLowerCase();
            const perGrass = quantity !== null && annualGrassKg > 0
              ? `${formatNumber(quantity / annualGrassKg)} ${normalizedUnit.startsWith('kg') ? 'kg' : normalizedUnit.startsWith('l') ? 'L' : quantityUnit || 'unit'} / kg grass`
              : 'Not modelled';
            const unitPrice = numeric(line.unit_cost_eur) ? Number(line.unit_cost_eur)
              : quantity && numeric(line.annual_cost_eur) ? Number(line.annual_cost_eur) / quantity : null;
            const unitPriceLabel = normalizedUnit.startsWith('kg') ? '€/kg' : normalizedUnit.startsWith('l') ? '€/L' : '';
            const costPerUnit = unitPrice !== null && unitPriceLabel ? `${formatEuro(unitPrice)} ${unitPriceLabel}` : 'Not reported';
            return [line.equipment_or_cost_item || line.process_step || line.cost_id || 'Unnamed consumable',
              quantity !== null ? `${formatNumber(quantity)} ${quantityUnit}` : 'Not modelled', perGrass, costPerUnit,
              numeric(line.annual_cost_eur) ? formatEuro(line.annual_cost_eur) : 'Not modelled'];
          })}
          empty="No consumables were returned for this run."
        />
      </details>
    </section>
  </div>;
}

function InventoryTable({ headers, rows, empty }: { headers: string[]; rows: string[][]; empty: string }) {
  if (!rows.length) return <div className="empty-state">{empty}</div>;
  return <div className="data-table-wrap"><table className="data-table"><thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead>
    <tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, column) => <td key={column}>{cell || 'Not reported'}</td>)}</tr>)}</tbody>
  </table></div>;
}

function numeric(value: unknown): value is number {
  return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
}

function formatNumber(value: unknown) {
  return Number(value).toLocaleString(undefined, { maximumSignificantDigits: 4 });
}

function formatEuro(value: unknown) {
  return `€${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2, maximumSignificantDigits: 5 })}`;
}

function humanize(value: string) {
  return value.replace(/[._-]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}
