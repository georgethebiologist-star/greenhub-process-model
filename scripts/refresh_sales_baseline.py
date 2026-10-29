"""Refresh bundled TEA/LCA/Pareto anchors from a completed recalculated run.

Usage: python scripts/refresh_sales_baseline.py REPORT_JSON RUNS_ROOT SUGAR_AUDIT_JSON
The completed report comes from DecisionSupportService; this script never
synthesizes a simulation or changes process outputs.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = json.loads(Path(sys.argv[1]).read_text())
run = Path(sys.argv[2]) / report['run_id']
audit = json.loads(Path(sys.argv[3]).read_text())
streams = {s['stream_id']: s for s in json.loads((run / 'streams.json').read_text())}
sales_basis = json.loads((ROOT / 'Greenhub/data/tea/product_sales_basis.json').read_text())
frontend = ROOT / 'frontend/src/data'
baseline = json.loads((frontend / 'decisionBaseline.json').read_text())
reference = json.loads((frontend / 'paretoReference.json').read_text())
hours = report['analysis_period']['operating_hours']
components = {r['quantity_component']: r['quantity'] for r in report['tea']['revenue_lines'] if r.get('quantity_component')}
digestate = streams['digestate']['components']
recovery = {'dissolvedPEquivalentKg': digestate.get('DissolvedPhosphorus', {}).get('value', 0) * hours,
            'orthophosphatePKg': digestate.get('Orthophosphate', {}).get('value', 0) * hours * 30.973762 / 94.9714,
            'ammoniumNitrogenKg': (digestate.get('Ammonium', {}).get('value', 0) * 14.0067 / 18.03846 + digestate.get('Ammonia', {}).get('value', 0) * 14.0067 / 17.03052) * hours}
baseline.update(sourceRun=report['run_id'], sourceCommit='',
    revenue=report['tea']['totals']['annual_revenue_eur'], opex=report['tea']['totals']['annual_opex_eur'],
    capital=report['tea']['totals']['screening_capital_basis_eur'],
    revenues=[{'name':r['equipment_or_cost_item'], 'value':r['annual_revenue_eur']} for r in report['tea']['revenue_lines']],
    productSales=[{k:r.get(k) for k in ('product_id','equipment_or_cost_item','quantity','quantity_unit','unit_cost_eur','reference_unit','annual_revenue_eur','quantity_source','quantity_component','warning')} for r in report['tea']['revenue_lines']],
    salesBasis=sales_basis, recovery=recovery, sugarAudit=audit,
    teaMissing=report['tea']['missing_inputs'], lcaMissing=report['lca']['missing_inputs'])
reference.update(sourceRun=report['run_id'], sourceCommit='', compoundProductsKg=components,
                 recovery=recovery, salesBasis=sales_basis, sugarAudit=audit)
for name, data in [('decisionBaseline.json', baseline), ('paretoReference.json', reference)]:
    (frontend / name).write_text(json.dumps(data, indent=2) + '\n')
print('Updated frontend baseline, exact sales quantities and Pareto reference:', report['run_id'])
