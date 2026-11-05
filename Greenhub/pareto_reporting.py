"""Compact, stable API projection for the saved Pareto analysis."""
from __future__ import annotations

import json
from pathlib import Path


TOP_LEVEL_FIELDS = (
    'schema_version', 'created_at_utc', 'seed', 'designs_per_protein_group',
    'feed_preparation', 'optimization_objectives', 'support_scenarios',
    'grant_awarding_organization', 'financial_basis', 'carbon_basis',
    'biomethane_support_conversion', 'grass_utilization_bonus', 'product_eligibility', 'limitations', 'groups',
    'input_provenance',
)
GROUP_FIELDS = (
    'group', 'requested_designs', 'sample_count', 'evaluated_count',
    'rejected_count', 'fronts', 'selected_candidates',
)


def pareto_ui_projection(source: dict) -> dict:
    """Return the same public Pareto payload without the full evaluated sample ledger."""
    groups = {
        name: {field: result.get(field) for field in GROUP_FIELDS}
        for name, result in source.get('groups_payload', {}).items()
    }
    return {field: source.get(field) for field in TOP_LEVEL_FIELDS} | {'groups_payload': groups}


def write_pareto_ui_projection(source: dict, target: Path) -> None:
    """Atomically publish the compact API artifact after the full ledger is saved."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(
        json.dumps(pareto_ui_projection(source), ensure_ascii=False, allow_nan=False),
        encoding='utf-8',
    )
    temporary.replace(target)
