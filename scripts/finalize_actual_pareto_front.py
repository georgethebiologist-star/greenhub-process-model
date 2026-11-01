import json
from pathlib import Path

root = Path('Greenhub/results/actual_pareto_2000/decision_batches')
jid = (root / 'job.txt').read_text(encoding='utf-8').strip()
path = root / f'{jid}.json'
doc = json.loads(path.read_text(encoding='utf-8'))
reports = [{'sample_id': s['sample_id'], 'outputs': s.get('outputs'), 'status': s.get('status'), 'error': s.get('rejection_reason')} for s in doc['samples']]
eligible = []
for report in reports:
    objectives = (report.get('outputs') or {}).get('objectives') or {}
    profit = objectives.get('operating_profit', {})
    climate = objectives.get('climate', {})
    if report['status'] == 'evaluated' and all(o.get('eligible') and isinstance(o.get('value'), (int, float)) for o in (profit, climate)):
        eligible.append({'sample_id': report['sample_id'], 'x': profit['value'], 'y': climate['value']})
front = [p for p in eligible if not any(q != p and q['x'] >= p['x'] and q['y'] >= p['y'] and (q['x'] > p['x'] or q['y'] > p['y']) for q in eligible)]
doc['screening_pareto_front'] = {'label': 'Objective-eligible screening Pareto front; technical evidence gate remains conditional', 'x_objective': 'operating_profit', 'y_objective': 'climate', 'points': front, 'eligible_points': eligible, 'technical_gate': 'not investment-grade: feasibility.eligible_for_ranking is false for the current partial LCA/process evidence'}
doc['candidate_economics_audit'] = {'reported_in_tea_candidate_economics': sum(1 for s in doc['samples'] if ((s.get('outputs') or {}).get('tea') or {}).get('candidate_economics')), 'tax_rate': 0.258, 'subsidy_rate': 0.20, 'subsidy_cap_eur': 250000.0, 'eligible_capex_fraction': 0.35}
tmp = path.with_name(path.stem + '.front.tmp')
tmp.write_text(json.dumps(doc, allow_nan=False), encoding='utf-8')
tmp.replace(path)
print(json.dumps({'screening_front': len(front), 'eligible': len(eligible), 'economics': doc['candidate_economics_audit']}))
