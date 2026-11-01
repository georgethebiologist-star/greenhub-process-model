import json
from pathlib import Path

root = Path('Greenhub/results/actual_pareto_2000/decision_batches')
jid = (root / 'job.txt').read_text(encoding='utf-8').strip()
path = root / f'{jid}.json'
doc = json.loads(path.read_text(encoding='utf-8'))
for row in doc.get('samples', []):
    out = row.get('outputs') or {}
    if 'objectives' in out:
        compact = {k: out.get(k) for k in ('objectives', 'feasibility', 'provenance', 'candidate_economics', 'products', 'tea') if k in out}
        row['outputs'] = compact
        row['feasibility'] = compact.get('feasibility', row.get('feasibility'))
        row['provenance'] = compact.get('provenance', row.get('provenance'))
temp = path.with_name(path.stem + '.compact.tmp')
temp.write_text(json.dumps(doc, allow_nan=False), encoding='utf-8')
temp.replace(path)
print(doc['completed_count'], len(doc.get('samples', [])))
