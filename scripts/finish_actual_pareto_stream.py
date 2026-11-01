from __future__ import annotations
import json, multiprocessing, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.scenario_exploration import pareto_front

SERVICE = None
def init_worker():
    global SERVICE
    SERVICE = DecisionSupportService()

def evaluate(item):
    index, config, sample_id, source_id = item
    try:
        out = SERVICE.evaluate(config)
        compact = {k: out.get(k) for k in ('objectives','feasibility','provenance','candidate_economics','products','tea') if k in out}
        return index, {'index': index, 'sample_id': sample_id, 'source_sample_id': source_id,
                       'configuration': config, 'status': 'evaluated', 'outputs': compact,
                       'feasibility': compact.get('feasibility'), 'provenance': compact.get('provenance')}
    except Exception as error:
        return index, {'index': index, 'sample_id': sample_id, 'source_sample_id': source_id,
                       'configuration': config, 'status': 'rejected',
                       'rejection_reason': f'{type(error).__name__}: {error}'}

def main():
    root = Path('Greenhub/results/actual_pareto_2000/decision_batches')
    jid = (root/'job.txt').read_text(encoding='utf-8').strip()
    path = root/f'{jid}.json'
    base = json.loads(path.read_text(encoding='utf-8'))
    stream = root/f'{jid}.remaining.jsonl'
    progress = root/f'{jid}.remaining.progress'
    existing = {row['index'] for row in base.get('samples', [])}
    source_ids = base.get('source_sample_ids') or []
    pending = [(i, cfg, f'backend-{jid[:8]}-{i+1:04d}', source_ids[i] if i < len(source_ids) else None)
               for i, cfg in enumerate(base['configurations']) if i not in existing]
    done = set()
    if stream.exists():
        for line in stream.read_text(encoding='utf-8').splitlines():
            if line.strip(): done.add(json.loads(line)['index'])
    pending = [item for item in pending if item[0] not in done]
    context = multiprocessing.get_context('spawn')
    with ProcessPoolExecutor(max_workers=8, mp_context=context, initializer=init_worker) as pool:
        futures = [pool.submit(evaluate, item) for item in pending]
        for n, future in enumerate(as_completed(futures), 1):
            _, row = future.result()
            with stream.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(row, allow_nan=False) + '\n')
            progress.write_text(json.dumps({'completed_remaining': n, 'total_remaining': len(pending),
                                            'updated_at': datetime.now(timezone.utc).isoformat()}), encoding='utf-8')
    remaining = [json.loads(line) for line in stream.read_text(encoding='utf-8').splitlines() if line.strip()]
    rows = base.get('samples', []) + remaining
    reports = [{'sample_id': row['sample_id'], 'outputs': row.get('outputs'), 'status': row.get('status'),
                'error': row.get('rejection_reason')} for row in rows]
    base['samples'] = sorted(rows, key=lambda row: row['index'])
    base['completed_count'] = sum(row['status'] == 'evaluated' for row in rows)
    base['failed_count'] = sum(row['status'] == 'rejected' for row in rows)
    base['pareto_fronts'] = [pareto_front(reports, 'operating_profit', metric)
                            for metric in ('climate', 'installed_capex', 'route_trl')]
    base['status'] = 'completed'
    base['updated_at'] = datetime.now(timezone.utc).isoformat()
    final = path.with_name(path.stem + '.final.tmp')
    final.write_text(json.dumps(base, allow_nan=False), encoding='utf-8')
    final.replace(path)
    print(json.dumps({'job_id': jid, 'status': base['status'], 'completed': base['completed_count'], 'failed': base['failed_count']}))

if __name__ == '__main__':
    main()
