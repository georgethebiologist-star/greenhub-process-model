"""Export line-by-line F1 CAPEX using actual BioSTEAM runs at each throughput."""
from __future__ import annotations
import csv, json
from pathlib import Path
from Greenhub.tea_costs import load_tea_cost_register

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results' / 'report_figures'
RUNS = OUT / 'capex_flow_runs'
flows = (500, 1000, 2000, 3000)
register = {row.cost_id: row for row in load_tea_cost_register()}
reports = {}
for flow in flows:
    path = RUNS / f'f1_{flow:04d}kg_h.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    assert report['configuration']['simulation']['wet_feed_rate_kg_hr'] == flow
    assert report['configuration']['simulation']['scenarios']['feed_preparation'] == 'F1'
    assert report['tea']['totals']['screening_estimates']
    reports[flow] = report

all_ids = sorted({line['cost_id'] for report in reports.values() for line in report['tea']['capex_lines']})
rows = []
totals = []
for flow, report in reports.items():
    line_map = {line['cost_id']: line for line in report['tea']['capex_lines']}
    run_dir = ROOT / 'Greenhub' / 'results' / 'runs' / report['run_id']
    units = json.loads((run_dir / 'units.json').read_text(encoding='utf-8'))
    r501 = next(unit for unit in units if unit['unit_id'] == 'R501')
    digester_volume = float(r501['design_results']['Working volume']['value'])
    low_total = mid_total = high_total = 0.0
    annual_opex = float(report['tea']['totals']['annual_opex_eur'])
    magnesium_line = next((line for line in report['tea']['opex_lines'] if line['cost_id'] == 'TEA-051'), None)
    missing = []
    for cost_id in all_ids:
        line = line_map.get(cost_id)
        if line is None:
            continue
        direct = line.get('direct_cost_eur')
        if direct is not None:
            direct = float(direct)
            low = high = direct
            mid = direct
            if cost_id == 'TEA-013':
                low, mid, high = digester_volume * 1200.0, digester_volume * 1500.0, digester_volume * 1800.0
                # Midpoint from the tank range must equal the TEA resolver line.
                if abs(mid - direct) > max(0.02, abs(direct) * 1e-6):
                    raise ValueError(f'TEA-013 does not match BioSTEAM R501 volume at {flow} kg/h')
            low_total += low; mid_total += mid; high_total += high
        else:
            low = mid = high = ''
            missing.append(cost_id)
        source = register.get(cost_id)
        if cost_id == 'TEA-013':
            source_title = 'Dutch screening range for CSTR digester tanks (user-provided)'
            source_url = 'https://energy-solutions.co/articles/sub/anaerobic-digestion-economic-analysis-2027-2035'
            source_basis = 'EUR 1,200–1,800 per m3 tank volume; midpoint EUR 1,500 per m3'
        else:
            source_title = getattr(source, 'source_title', '') or ''
            source_url = getattr(source, 'source_url', '') or ''
            source_basis = line.get('reference_unit') or ''
        rows.append({
            'flow_kg_h': flow, 'flow_t_h': flow / 1000,
            'scenario': 'F1; PEF disabled',
            'run_id': report['run_id'], 'cost_id': cost_id,
            'equipment_package': line.get('equipment_or_cost_item'),
            'source_reference_cost_eur': line.get('reference_value_eur'),
            'source_reference_basis': source_basis,
            'source_title': source_title, 'source_url': source_url,
            'reference_capacity': line.get('reference_capacity'),
            'reference_capacity_unit': line.get('capacity_unit') or '',
            'bioSTEAM_project_capacity': (digester_volume if cost_id == 'TEA-013' else line.get('project_capacity')),
            'project_capacity_unit': ('working volume m3' if cost_id == 'TEA-013' else line.get('project_capacity_unit') or line.get('capacity_unit') or ''),
            'scaling_exponent': line.get('scaling_exponent'),
            'capex_low_eur': round(low, 2) if low != '' else '',
            'capex_mid_eur': round(mid, 2) if mid != '' else '',
            'capex_high_eur': round(high, 2) if high != '' else '',
            'resolver_status': line.get('calculation_status'),
            'annual_opex_eur': '', 'opex_status': '',
            'magnesium_chloride_kg_year': '', 'magnesium_chloride_cost_eur_year': '',
            'installed_capex': False,
        })
    totals.append({
        'flow_kg_h': flow, 'flow_t_h': flow / 1000,
        'scenario': 'F1; PEF disabled', 'run_id': report['run_id'],
        'cost_id': 'TOTAL', 'equipment_package': 'Priced selected F1 CAPEX subtotal',
        'source_reference_cost_eur': '', 'source_reference_basis': '', 'source_title': '', 'source_url': '',
        'reference_capacity': '', 'reference_capacity_unit': '',
        'bioSTEAM_project_capacity': '', 'project_capacity_unit': '', 'scaling_exponent': '',
        'capex_low_eur': round(low_total, 2), 'capex_mid_eur': round(mid_total, 2),
        'capex_high_eur': round(high_total, 2),
        'resolver_status': f'partial direct CAPEX; {len(missing)} selected line(s) unpriced: {", ".join(missing) or "none"}',
        'annual_opex_eur': round(annual_opex, 2),
        'opex_status': report['tea']['totals'].get('opex_status'),
        'magnesium_chloride_kg_year': round(float(magnesium_line.get('quantity') or 0.0), 9) if magnesium_line else '',
        'magnesium_chloride_cost_eur_year': round(float(magnesium_line.get('annual_cost_eur') or 0.0), 9) if magnesium_line else '',
        'installed_capex': False,
    })

rows.extend(totals)
with (OUT / 'capex_breakdown_by_flow.csv').open('w', newline='', encoding='utf-8-sig') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
print('flow_kg_h,run_id,R501_working_volume_m3,partial_mid_capex_eur')
for flow, report in reports.items():
    row = next(item for item in totals if item['flow_kg_h'] == flow)
    units = json.loads((ROOT / 'Greenhub' / 'results' / 'runs' / report['run_id'] / 'units.json').read_text(encoding='utf-8'))
    volume = next(unit['design_results']['Working volume']['value'] for unit in units if unit['unit_id'] == 'R501')
    print(f"{flow},{report['run_id']},{volume:.6f},{row['capex_mid_eur']:.2f}")
