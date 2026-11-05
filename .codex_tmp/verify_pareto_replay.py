import json
from pathlib import Path

from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.application.simulation_service import SimulationService

source = Path('.codex_tmp/pareto_qa_parity2/rvo_pareto_manifest.json')
doc = json.loads(source.read_text(encoding='utf-8'))
service = DecisionSupportService(SimulationService(run_root=Path('.codex_tmp/pareto_replay_runs')))
checks = []
for group, block in doc['groups_payload'].items():
    rows = block['samples']
    for level in (0, 20, 50):
        row = next(r for r in rows if r['status'] == 'evaluated' and r['support_case'] == f'C0-GB{level}')
        config = row['configuration']
        config['simulation']['request_id'] = f"pareto-replay-{group}-gb{level}"
        report = service.evaluate(config)
        saved = row['tea_totals']
        direct = report['tea']['totals']
        compared = ('proxy_npv_eur', 'annual_revenue_eur', 'annual_opex_eur', 'high_direct_capex_eur', 'total_public_support_pv_eur')
        deltas = {key: abs(float(saved[key]) - float(direct[key])) for key in compared}
        limits = {key: max(0.01, abs(float(saved[key])) * 1e-9) for key in compared}
        if any(deltas[key] > limits[key] for key in compared):
            raise AssertionError(f"Mismatch {group} grass €{level}/t: {deltas}")
        checks.append({'group': group, 'grass_bonus_eur_per_wet_t': level, 'npv_eur': direct['proxy_npv_eur'], 'deltas': deltas})
print(json.dumps({'replay_count': len(checks), 'checks': checks}, indent=2))
