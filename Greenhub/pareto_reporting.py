"""Compact, stable API projection for the saved Pareto analysis."""
from __future__ import annotations

import json
from pathlib import Path


TOP_LEVEL_FIELDS = (
    'schema_version', 'created_at_utc', 'seed', 'designs_per_protein_group',
    'feed_preparation', 'optimization_objectives', 'support_scenarios',
    'grant_awarding_organization', 'financial_basis', 'carbon_basis',
    'biomethane_support_conversion', 'grass_utilization_bonus', 'product_eligibility', 'limitations', 'groups',
    'input_provenance', 'trial_composition',
)
GROUP_FIELDS = (
    'group', 'requested_designs', 'sample_count', 'evaluated_count',
    'rejected_count', 'fronts', 'selected_candidates', 'scenario_catalog',
)


def compact_pareto_scenario_catalog(candidates: list[dict], max_points: int = 100) -> list[dict]:
    """Bound each UI route catalog while retaining support and seasonal strata.

    Detailed evaluations remain in the saved sample shards. This projection
    keeps runnable representative configurations and only selects existing
    candidate records; it never synthesizes or renames scenario IDs.
    """
    if max_points < 0:
        raise ValueError("max_points must be non-negative.")
    if len(candidates) <= max_points:
        return list(candidates)
    if max_points == 0:
        return []
    return _compact_pareto_catalog_design_first(candidates, max_points)

    support_groups: dict[str, list[dict]] = {}
    for candidate in candidates:
        support_case = str(candidate.get("support_case") or "unspecified")
        support_groups.setdefault(support_case, []).append(candidate)
    support_cases = list(support_groups)
    if max_points < len(support_cases):
        indexes = (
            [0] if max_points == 1 else
            [round(i * (len(support_cases) - 1) / (max_points - 1)) for i in range(max_points)]
        )
        support_cases = [support_cases[index] for index in indexes]
        support_groups = {case: support_groups[case] for case in support_cases}

    base, remainder = divmod(max_points, len(support_cases))
    extra_cases = set(
        support_cases[index]
        for index in (
            [round(i * (len(support_cases) - 1) / (remainder - 1)) for i in range(remainder)]
            if remainder > 1 else ([len(support_cases) // 2] if remainder == 1 else [])
        )
    )
    quotas = {case: base + (case in extra_cases) for case in support_cases}

    selected: list[dict] = []
    selected_ids: set[str] = set()
    remaining_by_case: dict[str, list[dict]] = {}
    for case in support_cases:
        regime_groups: dict[str, list[dict]] = {}
        for candidate in support_groups[case]:
            profile = candidate.get("seasonal_availability_profile") or {}
            regime = str(profile.get("regime_id") or "unspecified")
            regime_groups.setdefault(regime, []).append(candidate)
        for regime_rows in regime_groups.values():
            regime_rows.sort(key=lambda row: (str(row.get("design_id") or ""), str(row.get("sample_id") or "")))

        picked_for_case: list[dict] = []
        # Round-robin across harvest regimes so even a small budget keeps the
        # seasonal configurations distinct; use central rows for deterministic
        # coverage rather than privileging the first sampled design.
        while len(picked_for_case) < quotas[case]:
            made_progress = False
            for regime_rows in regime_groups.values():
                available = [row for row in regime_rows if row.get("sample_id") not in selected_ids]
                if not available:
                    continue
                candidate = available[(len(available) - 1) // 2]
                sample_id = str(candidate.get("sample_id") or "")
                if not sample_id:
                    raise ValueError("Every Pareto scenario candidate requires a sample_id.")
                selected_ids.add(sample_id)
                picked_for_case.append(candidate)
                made_progress = True
                if len(picked_for_case) >= quotas[case]:
                    break
            if not made_progress:
                break
        selected.extend(picked_for_case)
        remaining_by_case[case] = [
            row for row in support_groups[case] if row.get("sample_id") not in selected_ids
        ]

    # Sparse route/support groups can leave unused budget. Reallocate it
    # deterministically without exceeding the requested cap.
    while len(selected) < max_points:
        made_progress = False
        for case in support_cases:
            remaining = remaining_by_case[case]
            if not remaining:
                continue
            regimes: dict[str, list[dict]] = {}
            for row in remaining:
                profile = row.get("seasonal_availability_profile") or {}
                regime = str(profile.get("regime_id") or "unspecified")
                regimes.setdefault(regime, []).append(row)
            regime = next(iter(regimes))
            candidate = regimes[regime][(len(regimes[regime]) - 1) // 2]
            remaining.remove(candidate)
            selected.append(candidate)
            sample_id = str(candidate.get("sample_id") or "")
            if not sample_id or sample_id in selected_ids:
                raise ValueError("Pareto scenario sample IDs must be present and unique.")
            selected_ids.add(sample_id)
            made_progress = True
            if len(selected) >= max_points:
                break
        if not made_progress:
            break
    return selected


def compact_pareto_scenario_catalog(candidates: list[dict], max_points: int = 100) -> list[dict]:
    """Bound each UI route catalog while retaining support and seasonal strata.

    Detailed evaluations remain in the saved sample shards. This projection
    keeps runnable representative configurations and only selects existing
    candidate records; it never synthesizes or renames scenario IDs.
    """
    if max_points < 0:
        raise ValueError("max_points must be non-negative.")
    if len(candidates) <= max_points:
        return list(candidates)
    if max_points == 0:
        return []
    return _compact_pareto_catalog_design_first(candidates, max_points)

    support_groups: dict[str, list[dict]] = {}
    for candidate in candidates:
        support_case = str(candidate.get("support_case") or "unspecified")
        support_groups.setdefault(support_case, []).append(candidate)
    support_cases = list(support_groups)
    if max_points < len(support_cases):
        indexes = (
            [0] if max_points == 1 else
            [round(i * (len(support_cases) - 1) / (max_points - 1)) for i in range(max_points)]
        )
        support_cases = [support_cases[index] for index in indexes]
        support_groups = {case: support_groups[case] for case in support_cases}

    base, remainder = divmod(max_points, len(support_cases))
    extra_cases = set(
        support_cases[index]
        for index in (
            [round(i * (len(support_cases) - 1) / (remainder - 1)) for i in range(remainder)]
            if remainder > 1 else ([len(support_cases) // 2] if remainder == 1 else [])
        )
    )
    quotas = {case: base + (case in extra_cases) for case in support_cases}

    selected: list[dict] = []
    selected_ids: set[str] = set()
    remaining_by_case: dict[str, list[dict]] = {}
    for case in support_cases:
        regime_groups: dict[str, list[dict]] = {}
        for candidate in support_groups[case]:
            profile = candidate.get("seasonal_availability_profile") or {}
            regime = str(profile.get("regime_id") or "unspecified")
            regime_groups.setdefault(regime, []).append(candidate)
        for regime_rows in regime_groups.values():
            regime_rows.sort(key=lambda row: (str(row.get("design_id") or ""), str(row.get("sample_id") or "")))

        picked_for_case: list[dict] = []
        # Round-robin across harvest regimes so even a small budget keeps the
        # seasonal configurations distinct; use central rows for deterministic
        # coverage rather than privileging the first sampled design.
        while len(picked_for_case) < quotas[case]:
            made_progress = False
            for regime_rows in regime_groups.values():
                available = [row for row in regime_rows if row.get("sample_id") not in selected_ids]
                if not available:
                    continue
                candidate = available[(len(available) - 1) // 2]
                sample_id = str(candidate.get("sample_id") or "")
                if not sample_id:
                    raise ValueError("Every Pareto scenario candidate requires a sample_id.")
                selected_ids.add(sample_id)
                picked_for_case.append(candidate)
                made_progress = True
                if len(picked_for_case) >= quotas[case]:
                    break
            if not made_progress:
                break
        selected.extend(picked_for_case)
        remaining_by_case[case] = [
            row for row in support_groups[case] if row.get("sample_id") not in selected_ids
        ]

    # Sparse route/support groups can leave unused budget. Reallocate it
    # deterministically without exceeding the requested cap.
    while len(selected) < max_points:
        made_progress = False
        for case in support_cases:
            remaining = remaining_by_case[case]
            if not remaining:
                continue
            regimes: dict[str, list[dict]] = {}
            for row in remaining:
                profile = row.get("seasonal_availability_profile") or {}
                regime = str(profile.get("regime_id") or "unspecified")
                regimes.setdefault(regime, []).append(row)
            regime = next(iter(regimes))
            candidate = regimes[regime][(len(regimes[regime]) - 1) // 2]
            remaining.remove(candidate)
            selected.append(candidate)
            sample_id = str(candidate.get("sample_id") or "")
            if not sample_id or sample_id in selected_ids:
                raise ValueError("Pareto scenario sample IDs must be present and unique.")
            selected_ids.add(sample_id)
            made_progress = True
            if len(selected) >= max_points:
                break
        if not made_progress:
            break
    return selected


def _compact_pareto_catalog_design_first(candidates: list[dict], max_points: int) -> list[dict]:
    """Prioritize process-design diversity, then fill with finance overlays.

    Pareto candidate rows often differ only by grant/bonus assumptions. Those
    are useful sensitivities, but must not crowd all distinct process designs
    out of a bounded UI catalog. This selection keeps at least one existing
    candidate per design where the point budget allows, then balances remaining
    rows across support cases. It never edits IDs or synthesizes configurations.
    """
    if max_points <= 0 or not candidates:
        return []
    support_cases: list[str] = []
    by_design: dict[str, list[dict]] = {}
    for row in candidates:
        sample_id = str(row.get('sample_id') or '')
        if not sample_id:
            raise ValueError('Every Pareto scenario candidate requires a sample_id.')
        design_id = str(row.get('design_id') or sample_id)
        support_case = str(row.get('support_case') or 'unspecified')
        if support_case not in support_cases:
            support_cases.append(support_case)
        by_design.setdefault(design_id, []).append(row)

    design_ids = sorted(by_design)
    if len(design_ids) > max_points:
        indexes = [round(i * (len(design_ids) - 1) / (max_points - 1)) for i in range(max_points)] if max_points > 1 else [len(design_ids) // 2]
        design_ids = [design_ids[index] for index in indexes]

    selected: list[dict] = []
    selected_ids: set[str] = set()
    selected_by_support: dict[str, int] = {support_case: 0 for support_case in support_cases}
    for design_index, design_id in enumerate(design_ids):
        rows = sorted(by_design[design_id], key=lambda row: (str(row.get('support_case') or 'unspecified'), str(row['sample_id'])))
        preference = sorted(support_cases, key=lambda support: (selected_by_support[support], support_cases.index(support)))
        candidate = next((row for support in preference for row in rows if str(row.get('support_case') or 'unspecified') == support), rows[0])
        selected.append(candidate)
        selected_ids.add(str(candidate['sample_id']))
        support_case = str(candidate.get('support_case') or 'unspecified')
        selected_by_support[support_case] = selected_by_support.get(support_case, 0) + 1

    selected_by_design = {design_id: 1 for design_id in design_ids}
    while len(selected) < max_points:
        made_progress = False
        for support_case in sorted(support_cases, key=lambda support: (selected_by_support[support], support_cases.index(support))):
            available = [
                row for design_id in design_ids for row in by_design[design_id]
                if str(row.get('support_case') or 'unspecified') == support_case
                and str(row.get('sample_id') or '') not in selected_ids
            ]
            if not available:
                continue
            # Fill in support-case rounds so one finance overlay cannot consume
            # the remaining catalog budget before other cases are represented.
            candidate = min(
                available,
                key=lambda row: (
                    selected_by_design.get(str(row.get('design_id') or row['sample_id']), 0),
                    str(row.get('design_id') or row['sample_id']),
                    str(row['sample_id']),
                ),
            )
            sample_id = str(candidate['sample_id'])
            design_id = str(candidate.get('design_id') or sample_id)
            selected.append(candidate)
            selected_ids.add(sample_id)
            selected_by_design[design_id] = selected_by_design.get(design_id, 0) + 1
            selected_by_support[support_case] = selected_by_support.get(support_case, 0) + 1
            made_progress = True
            if len(selected) >= max_points:
                break
        if not made_progress:
            break
    return selected


def pareto_ui_projection(source: dict) -> dict:
    """Return the same public Pareto payload without the full evaluated sample ledger."""
    groups = {
        name: {field: result.get(field) for field in GROUP_FIELDS}
        for name, result in source.get('groups_payload', {}).items()
    }
    return {field: source.get(field) for field in TOP_LEVEL_FIELDS} | {'groups_payload': groups}


def write_pareto_ui_projection(source: dict, target: Path) -> None:
    """Atomically publish the compact API artifact after the full ledger is saved."""
    _write_projection(pareto_ui_projection(source), target)


def _write_projection(projection: dict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(
        json.dumps(projection, ensure_ascii=False, allow_nan=False),
        encoding='utf-8',
    )
    temporary.replace(target)


def publish_pareto_ui_artifacts(source: dict, results_target: Path, preview_target: Path) -> None:
    """Publish identical bounded scenario catalogs for API and offline UI use."""
    projection = pareto_ui_projection(source)
    for target in (results_target, preview_target):
        _write_projection(projection, target)


def load_pareto_results(results_dir: Path) -> dict:
    """Load the compact publication and reattach its full, per-group result shards."""
    latest_path = results_dir / 'latest.json'
    payload = json.loads(latest_path.read_text(encoding='utf-8'))
    groups = payload.get('groups_payload') or {}
    if groups and all(isinstance(group.get('samples'), list) for group in groups.values()):
        return payload
    group_names = tuple(groups) or ('protein_enabled', 'protein_bypass')
    for name in group_names:
        shard = results_dir / f'{name}_batch.json'
        if not shard.is_file():
            raise FileNotFoundError(f'Missing Pareto scenario shard: {shard.name}')
        full_group = load_pareto_group(results_dir, name)
        payload.setdefault('groups_payload', {})[name] = full_group
    return payload


def load_pareto_group(results_dir: Path, group_name: str) -> dict:
    """Load a legacy monolithic group or reassemble its bounded sample shards."""
    group_path = results_dir / f'{group_name}_batch.json'
    group = json.loads(group_path.read_text(encoding='utf-8'))
    if isinstance(group.get('samples'), list):
        return group
    sample_shards = group.get('sample_shards') or []
    if not sample_shards:
        return group
    samples = []
    for filename in sample_shards:
        shard_path = results_dir / filename
        shard = json.loads(shard_path.read_text(encoding='utf-8'))
        samples.extend(shard.get('samples') or [])
    return {**group, 'samples': samples}
