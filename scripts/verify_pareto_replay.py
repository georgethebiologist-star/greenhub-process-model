"""Replay a stratified Pareto sample through the same service used by the UI."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.application.simulation_service import SimulationService
from Greenhub.pareto_reporting import load_pareto_group


RESULTS = Path(os.environ.get(
    "GREENHUB_PARETO_REPLAY_RESULTS_DIR",
    ROOT / "Greenhub" / "results" / "pareto_rvo_2026",
))
COMPARE = (
    "annual_revenue_eur",
    "annual_opex_eur",
    "high_direct_capex_eur",
    "total_public_support_pv_eur",
    "proxy_npv_eur",
    "proxy_irr",
    "proxy_simple_payback_years",
)
COMPARE_LCA = (
    "climate_kg_co2e_per_year",
    "partial_climate_kg_co2e_per_year",
    "kg_co2e_per_tonne_wet_feed",
    "kg_co2e_per_tonne_dry_feed",
)
COMPARE_OBJECTIVES = ("net_carbon", "npv", "subsidy_granted", "climate")
COMPARE_SEASONAL_FIELDS = (
    "available_biomass_tonnes",
    "collected_at_harvest_tonnes",
    "collected_for_processing_tonnes",
    "collection_delay_harvest_tonnes",
    "collection_delay_release_tonnes",
    "collection_delay_inventory_entering_tonnes",
    "collection_delay_inventory_remaining_tonnes",
    "collection_delay_inventory_peak_tonnes",
    "collection_delay_inventory_mass_residual_tonnes",
    "processed_biomass_tonnes",
    "uncollected_biomass_tonnes",
    "operating_hours",
    "basis_feed_kg_per_hr",
    "storage_inventory_entering_tonnes",
    "biomass_received_after_storage_conditions_tonnes",
    "storage_withdrawn_tonnes",
    "storage_overflow_tonnes",
    "storage_degradation_loss_tonnes",
    "ending_inventory_tonnes",
    "storage_mass_residual_tonnes",
)
RECONCILED_CASES = ('C0-GB0', 'C0-GB10', 'C0-GB20', 'C0-GB30', 'C0-GB40', 'C0-GB50',
                    'C30-GB0', 'C45-GB30', 'C60-GB50')
REPLAY_ALL_SELECTABLE = os.environ.get('GREENHUB_PARETO_REPLAY_ALL_SELECTABLE', '1') != '0'


def representative_design_rows(catalog):
    """Select one saved configuration per physical design, preferring C0-GB0.

    A compact UI catalog may retain a design only under other support cases.
    Fallback must be per design, not only when the entire group lacks C0-GB0.
    """
    selected = {}
    for row in catalog:
        if row.get('support_case') == 'C0-GB0':
            selected.setdefault(row.get('design_id'), row)
    for row in catalog:
        selected.setdefault(row.get('design_id'), row)
    selected.pop(None, None)
    return selected


def _same_number(left, right):
    if left is None or right is None:
        return left is right
    return abs(float(left) - float(right)) <= max(0.01, abs(float(right)) * 1e-10)


def process_request_cache_key(configuration):
    """Key reuse only by canonical process inputs, never finance/LCA overlays."""
    signature = {
        "simulation": configuration.get("simulation"),
        "use_screening_process_assumptions": configuration.get(
            "use_screening_process_assumptions", False
        ),
    }
    return json.dumps(signature, sort_keys=True, separators=(",", ":"))


def main() -> None:
    selected = []
    # Verify current, user-facing projected candidates against the same service
    # used by Configure. Cover every grass-bonus level and multiple CAPEX-grant
    # combinations for both process routes.
    support_cases = tuple(f"C0-GB{rate}" for rate in (0, 10, 20, 30, 40, 50)) + ("C60-GB50",)
    projection = json.loads((RESULTS / 'latest_ui.json').read_text(encoding='utf-8'))
    full_samples = {}
    ui_catalog_rows = {}
    physical_design_count = 0
    for group in ("protein_enabled", "protein_bypass"):
        batch_path = RESULTS / f'{group}_batch.json'
        if batch_path.exists():
            # Publications use bounded sample shards; reading only the batch
            # index silently skipped product, utility and balance comparisons.
            batch = load_pareto_group(RESULTS, group)
            full_samples[group] = {row['sample_id']: row for row in batch.get('samples', [])}
        candidates = projection['groups_payload'][group]['selected_candidates']
        catalog = projection['groups_payload'][group].get('scenario_catalog', [])
        ui_catalog_rows[group] = {item.get('sample_id'): item for item in catalog if item.get('sample_id')}
        for support in RECONCILED_CASES:
            rows = candidates.get(f'net_carbon_vs_npv_{support}') or []
            if not rows:
                raise AssertionError(f"No projected candidate in {group}/{support}")
            row = rows[0]
            row.setdefault('group', group)
            selected.append(row)
        # Replay every physical route/seasonal design, not only the front
        # representatives shown in the chart.
        design_rows = representative_design_rows(catalog)
        catalog_design_ids = {row.get('design_id') for row in catalog}
        if set(design_rows) != catalog_design_ids:
            raise AssertionError(f"Physical-design replay coverage incomplete for {group}: missing {sorted(catalog_design_ids - set(design_rows))}")
        physical_design_count += len(design_rows)
        for row in design_rows.values():
            row.setdefault('group', group)
            selected.append(row)
        # Full mode verifies every point exposed by the scenario selector.
        # Representative mode covers each physical design above and the
        # configured support cases, without replaying many finance-only
        # overlays that share the same process configuration.
        if REPLAY_ALL_SELECTABLE:
            for row in catalog:
                row.setdefault('group', group)
                selected.append(row)
        if REPLAY_ALL_SELECTABLE:
            for candidate_rows in candidates.values():
                for row in candidate_rows or []:
                    row.setdefault('group', group)
                    selected.append(row)

    # Front representatives and one-per-design rows can overlap.
    selected = list({row['sample_id']: row for row in selected}.values())

    mismatches = []
    process_run_cache = {}
    # Share one temporary run repository for the audit. Finance and LCA are
    # recomputed for every selected configuration, but an exact-identical
    # canonical process request can reuse its already-executed process result.
    # This is important for support/price overlays: they are post-route and
    # must not trigger a duplicate BioSTEAM run or alter process chemistry.
    with TemporaryDirectory(prefix="greenhub-pareto-replay-") as temporary:
        service = DecisionSupportService(SimulationService(run_root=Path(temporary)))
        for row in selected:
            configuration = row["configuration"]
            cache_key = process_request_cache_key(configuration)
            request_configuration = dict(configuration)
            if cache_key in process_run_cache:
                request_configuration["existing_run_id"] = process_run_cache[cache_key]
            replay = service.evaluate(request_configuration)
            process_run_cache.setdefault(cache_key, replay["run_id"])
            actual = replay["tea"]["totals"]
            expected = row["tea_totals"]
            checks = {}
            for key in COMPARE:
                left, right = actual.get(key), expected.get(key)
                checks[key] = _same_number(left, right)
                if not checks[key]:
                    mismatches.append((row["sample_id"], key, right, left))
            actual_lca = replay["lca"]["totals"]
            for key in COMPARE_LCA:
                left, right = actual_lca.get(key), row.get("lca_totals", {}).get(key)
                checks[f"lca.{key}"] = _same_number(left, right)
                if not checks[f"lca.{key}"]:
                    mismatches.append((row["sample_id"], f"lca.{key}", right, left))
            for key in COMPARE_OBJECTIVES:
                left = (replay.get("objectives", {}).get(key) or {}).get("value")
                right = (row.get("values", {}).get(key))
                checks[f"objective.{key}"] = _same_number(left, right)
                if not checks[f"objective.{key}"]:
                    mismatches.append((row["sample_id"], f"objective.{key}", right, left))
            full = full_samples.get(row['group'], {}).get(row['sample_id'])
            if full and full.get('annual'):
                expected_annual = full['annual']
                replay_annual = replay['annual']
                for product_id, expected_product in expected_annual.get('products', {}).items():
                    left = (replay_annual.get('products', {}).get(product_id) or {}).get('value')
                    right = expected_product.get('value')
                    checks[f'product.{product_id}'] = _same_number(left, right)
                    if not checks[f'product.{product_id}']:
                        mismatches.append((row['sample_id'], f'product.{product_id}', right, left))
                for utility_id in ('electricity', 'heating', 'cooling', 'fresh_water', 'fresh_water_mass'):
                    left = (replay_annual.get('utilities', {}).get(utility_id) or {}).get('value')
                    right = (expected_annual.get('utilities', {}).get(utility_id) or {}).get('value')
                    checks[f'utility.{utility_id}'] = _same_number(left, right)
                    if not checks[f'utility.{utility_id}']:
                        mismatches.append((row['sample_id'], f'utility.{utility_id}', right, left))
                for balance_id in ('process_mass_residual_kg', 'storage_mass_residual_kg'):
                    left = (replay_annual.get('balance') or {}).get(balance_id)
                    right = (expected_annual.get('balance') or {}).get(balance_id)
                    checks[f'balance.{balance_id}'] = _same_number(left, right)
                    if not checks[f'balance.{balance_id}']:
                        mismatches.append((row['sample_id'], f'balance.{balance_id}', right, left))
                expected_schedule = expected_annual.get('biomass_schedule') or {}
                replay_schedule = replay_annual.get('biomass_schedule') or {}
                input_schedule = (row.get('configuration', {}).get('simulation') or {}).get('biomass_schedule') or {}
                for annual_key, input_key, target_key in (
                    ('annual_available_tonnes', 'annual_available_biomass_tonnes', 'annual_available_tonnes'),
                    # The request value is a processing target; actual annual
                    # processed tonnes can be lower when the equipment limit binds.
                    ('annual_processed_tonnes', 'annual_processed_biomass_tonnes', 'requested_processed_tonnes'),
                ):
                    right = expected_schedule.get(annual_key)
                    left = replay_schedule.get(annual_key)
                    checks[f'seasonal.{annual_key}'] = _same_number(left, right)
                    checks[f'seasonal.input_{input_key}'] = _same_number(expected_schedule.get(target_key), input_schedule.get(input_key))
                    if not checks[f'seasonal.{annual_key}'] or not checks[f'seasonal.input_{input_key}']:
                        mismatches.append((row['sample_id'], f'seasonal.{annual_key}', right, left, expected_schedule.get(target_key), input_schedule.get(input_key)))
                saved_months = expected_schedule.get('monthly') or []
                replay_months = replay_schedule.get('monthly') or []
                # The graph's selected-candidate payload is intentionally lean;
                # monthly detail lives in the selectable per-scenario catalog.
                ui_detail = ui_catalog_rows.get(row['group'], {}).get(row['sample_id'], {})
                projected_months = (
                    row.get('seasonal_feed_profile')
                    or ui_detail.get('seasonal_feed_profile')
                    or []
                )
                checks['seasonal.month_count'] = len(saved_months) == len(replay_months) == len(projected_months) == 12
                if not checks['seasonal.month_count']:
                    mismatches.append((row['sample_id'], 'seasonal.month_count', 12, (len(saved_months), len(replay_months), len(projected_months))))
                input_months = input_schedule.get('monthly_availability_tonnes') or []
                checks['seasonal.input_monthly_availability'] = (
                    len(input_months) == 12
                    and _same_number(sum(input_months), input_schedule.get('annual_available_biomass_tonnes'))
                )
                if not checks['seasonal.input_monthly_availability']:
                    mismatches.append((row['sample_id'], 'seasonal.input_monthly_availability', input_schedule.get('annual_available_biomass_tonnes'), sum(input_months)))
                if checks['seasonal.month_count']:
                    for month_index, (saved_month, replay_month, projected_month) in enumerate(zip(saved_months, replay_months, projected_months)):
                        period = saved_month.get('time_label') or saved_month.get('period') or str(month_index + 1)
                        checks[f'seasonal.period.{period}'] = (
                            saved_month.get('time_label', period) == replay_month.get('time_label', period)
                            and saved_month.get('time_label', period) == projected_month.get('time_label', period)
                        )
                        if not checks[f'seasonal.period.{period}']:
                            mismatches.append((row['sample_id'], f'seasonal.period.{period}', saved_month.get('time_label'), (replay_month.get('time_label'), projected_month.get('time_label'))))
                        for field in COMPARE_SEASONAL_FIELDS:
                            saved_value = saved_month.get(field)
                            replay_value = replay_month.get(field)
                            projected_value = projected_month.get(field)
                            # The current UI projection backfills the collection-delay
                            # ledger from the canonical request because older saved
                            # batch reports predate these fields. Compare the actual
                            # UI values to the current API-equivalent replay; compare
                            # saved reports only when they contain the field.
                            ui_api_key = f'seasonal.ui_to_replay.{period}.{field}'
                            checks[ui_api_key] = _same_number(projected_value, replay_value)
                            if not checks[ui_api_key]:
                                mismatches.append((row['sample_id'], ui_api_key, projected_value, replay_value))
                            if saved_value is not None:
                                saved_api_key = f'seasonal.saved_to_replay.{period}.{field}'
                                checks[saved_api_key] = _same_number(saved_value, replay_value)
                                if not checks[saved_api_key]:
                                    mismatches.append((row['sample_id'], saved_api_key, saved_value, replay_value))
            print(json.dumps({
                "sample_id": row["sample_id"],
                "group": row["group"],
                "support_case": row["support_case"],
                "npv": row["values"]["npv"],
                "expected_npv": expected.get("proxy_npv_eur"),
                "replayed_npv": actual.get("proxy_npv_eur"),
                "mismatches": [item for item in mismatches if item[0] == row["sample_id"]][:12],
                "passed": all(checks.values()),
            }), flush=True)
    if mismatches:
        raise AssertionError(f"Pareto/UI replay mismatch(es): {mismatches[:10]}")
    mode = "all selectable scenarios" if REPLAY_ALL_SELECTABLE else "representative physical designs and support cases"
    print(f"PASS: {len(selected)} Pareto configurations ({mode}), covering {physical_design_count} physical route/seasonal designs, matched the UI decision-support service and monthly biomass outputs.")


if __name__ == "__main__":
    main()
