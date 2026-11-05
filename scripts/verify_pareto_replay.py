"""Replay a stratified Pareto sample through the same service used by the UI."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.application.simulation_service import SimulationService


RESULTS = ROOT / "Greenhub" / "results" / "pareto_rvo_2026"
COMPARE = (
    "annual_revenue_eur",
    "annual_opex_eur",
    "high_direct_capex_eur",
    "total_public_support_pv_eur",
    "proxy_npv_eur",
    "proxy_irr",
    "proxy_simple_payback_years",
)
RECONCILED_CASES = ('C0-GB0', 'C0-GB10', 'C0-GB20', 'C0-GB30', 'C0-GB40', 'C0-GB50',
                    'C30-GB0', 'C45-GB30', 'C60-GB50')


def main() -> None:
    selected = []
    # Verify current, user-facing projected candidates against the same service
    # used by Configure. Cover every grass-bonus level and multiple CAPEX-grant
    # combinations for both process routes.
    support_cases = tuple(f"C0-GB{rate}" for rate in (0, 10, 20, 30, 40, 50)) + ("C60-GB50",)
    projection = json.loads((RESULTS / 'latest_ui.json').read_text(encoding='utf-8'))
    for group in ("protein_enabled", "protein_bypass"):
        candidates = projection['groups_payload'][group]['selected_candidates']
        for support in RECONCILED_CASES:
            rows = candidates.get(f'net_carbon_vs_npv_{support}') or []
            if not rows:
                raise AssertionError(f"No projected candidate in {group}/{support}")
            row = rows[0]
            row.setdefault('group', group)
            selected.append(row)

    mismatches = []
    for row in selected:
        # Each API-equivalent evaluation exports plots and detailed run files.
        # Isolate and clean them per replay so a large verification sample does
        # not accumulate hundreds of megabytes in one temporary directory.
        with TemporaryDirectory(prefix="greenhub-pareto-replay-") as temporary:
            service = DecisionSupportService(SimulationService(run_root=Path(temporary)))
            replay = service.evaluate(row["configuration"])
            actual = replay["tea"]["totals"]
            expected = row["tea_totals"]
            checks = {}
            for key in COMPARE:
                left, right = actual.get(key), expected.get(key)
                if left is None or right is None:
                    checks[key] = left is right
                else:
                    checks[key] = abs(float(left) - float(right)) <= max(0.01, abs(float(right)) * 1e-10)
                if not checks[key]:
                    mismatches.append((row["sample_id"], key, right, left))
            print(json.dumps({
                "sample_id": row["sample_id"],
                "group": row["group"],
                "support_case": row["support_case"],
                "npv": row["values"]["npv"],
                "expected_npv": expected.get("proxy_npv_eur"),
                "replayed_npv": actual.get("proxy_npv_eur"),
                "passed": all(checks.values()),
            }))
    if mismatches:
        raise AssertionError(f"Pareto/UI replay mismatch(es): {mismatches[:10]}")
    print(f"PASS: {len(selected)} Pareto configurations matched the UI decision-support service.")


if __name__ == "__main__":
    main()
