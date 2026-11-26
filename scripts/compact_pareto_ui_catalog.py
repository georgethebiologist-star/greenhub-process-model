"""Publish a 200-point Pareto UI catalog from already evaluated scenarios.

This only compacts the UI projection. Per-scenario evaluations and stable IDs
remain in the saved group batches and sample shards; no process simulation,
objective, or Pareto frontier is recalculated.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import gzip
import shutil
import sys
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Greenhub.pareto_reporting import compact_pareto_scenario_catalog, load_pareto_group

RESULTS = ROOT / "Greenhub" / "results" / "pareto_rvo_2026"
PREVIEW = ROOT / "frontend" / "public" / "data" / "greenhub-pareto-latest.json"
MAX_GROUP_POINTS = 100
MAX_BYTES = 100 * 1024 * 1024
PROJECTION_PATHS = (
    RESULTS / "latest.json",
    RESULTS / "latest_ui.json",
    RESULTS / "rvo_pareto_manifest.json",
    PREVIEW,
)
COLLECTION_DELAY_FIELDS = (
    "collection_delay_harvest_tonnes",
    "collection_delay_release_tonnes",
    "collection_delay_inventory_entering_tonnes",
    "collection_delay_inventory_remaining_tonnes",
    "collection_delay_inventory_peak_tonnes",
    "collection_delay_inventory_mass_residual_tonnes",
)
COLLECTION_DELAY_SOURCE_FIELDS = {
    "collection_delay_harvest_tonnes": "harvested_biomass_kg",
    "collection_delay_release_tonnes": "collected_biomass_kg",
    "collection_delay_inventory_entering_tonnes": "collection_delay_inventory_entering_kg",
    "collection_delay_inventory_remaining_tonnes": "collection_delay_inventory_remaining_kg",
    "collection_delay_inventory_peak_tonnes": "collection_delay_inventory_peak_kg",
    "collection_delay_inventory_mass_residual_tonnes": "collection_delay_inventory_residual_kg",
}


def _restore_collection_delay_ledger(candidate: dict, samples: dict[str, dict]) -> int:
    """Rebuild the deterministic schedule ledger from saved UI/API inputs."""
    from Greenhub.application.biomass_schedule import schedule_feed_rows
    from Greenhub.application.contracts import SimulationRequest
    from Greenhub.time_grid import generate_time_grid

    sample_id = candidate.get("sample_id")
    saved = samples.get(sample_id)
    if saved is None:
        raise ValueError(f"Candidate {sample_id} has no saved evaluation.")
    simulation = (candidate.get("configuration") or {}).get("simulation") or {}
    request = SimulationRequest.from_dict(simulation)
    schedule = request.biomass_schedule
    if schedule is None:
        raise ValueError(f"Candidate {sample_id} has no runnable biomass schedule.")
    grid = generate_time_grid(request.start_date, request.end_date, request.time_step or "monthly")
    source_months = {
        row.get("time"): row
        for row in schedule_feed_rows(
            schedule, grid, processing_delay_days=schedule.processing_delay_days,
        )
    }
    saved_months = {
        row.get("time_label"): row
        for row in ((saved.get("annual") or {}).get("biomass_schedule") or {}).get("monthly", [])
    }
    projected_months = candidate.get("seasonal_feed_profile") or []
    if not projected_months:
        # Some selected-front points were published as lean chart rows. Their
        # evaluated annual report already contains the monthly process and
        # storage results, so recover that UI detail without rerunning chemistry.
        projected_months = [
            dict(row) for row in ((saved.get("annual") or {}).get("biomass_schedule") or {}).get("monthly", [])
        ]
        if not projected_months:
            raise ValueError(f"Candidate {sample_id} has neither monthly UI detail nor a saved monthly report.")
        candidate["seasonal_feed_profile"] = projected_months
    for month in projected_months:
        period = month.get("time_label")
        source = source_months.get(period)
        if source is None:
            raise ValueError(f"Candidate {sample_id} has no saved seasonal row for {period}.")
        saved_month = saved_months.get(period) or {}
        expected_base = {
            "available_biomass_tonnes": float(source.get("available_wet_biomass_kg", 0.0)) / 1000.0,
            "collected_at_harvest_tonnes": float(source.get("harvested_biomass_kg", 0.0)) / 1000.0,
            "collected_for_processing_tonnes": float(source.get("collected_biomass_kg", 0.0)) / 1000.0,
        }
        for field, expected in expected_base.items():
            projected_value = month.get(field)
            saved_value = saved_month.get(field)
            for label, observed in (("UI", projected_value), ("saved service", saved_value)):
                if observed is not None and abs(float(observed) - expected) > max(1e-7, abs(expected) * 1e-9):
                    raise ValueError(
                        f"Candidate {sample_id}/{period} {label} {field} does not match the canonical schedule."
                    )
        for field in COLLECTION_DELAY_FIELDS:
            source_field = COLLECTION_DELAY_SOURCE_FIELDS[field]
            if source_field not in source:
                raise ValueError(f"Canonical schedule {sample_id}/{period} lacks {source_field}.")
            value = float(source[source_field]) / 1000.0
            saved_value = saved_month.get(field)
            if saved_value is not None and abs(float(saved_value) - value) > max(1e-7, abs(value) * 1e-9):
                raise ValueError(f"Saved service {sample_id}/{period} {field} differs from the canonical schedule.")
            month[field] = value
    return len(projected_months)


def compact_saved_projection(source: dict, source_groups: dict[str, dict]) -> tuple[dict, dict[str, dict]]:
    """Compact candidate lists while checking IDs/configs against saved samples."""
    import copy

    projection = copy.deepcopy(source)
    summary = {}
    groups = projection.get("groups_payload") or {}
    for group_name in ("protein_enabled", "protein_bypass"):
        ui_group = groups.get(group_name)
        if not isinstance(ui_group, dict):
            raise ValueError(f"Missing published Pareto group {group_name}.")
        full_group = source_groups.get(group_name) or {}
        samples = {row.get("sample_id"): row for row in full_group.get("samples", []) if row.get("sample_id")}
        old_catalog = ui_group.get("scenario_catalog") or []
        if not samples or not old_catalog:
            raise ValueError(f"Missing saved samples or UI candidates for {group_name}.")
        selected = ui_group.get("selected_candidates") or {}
        candidates = list(old_catalog)
        for selected_rows in selected.values():
            candidates.extend(selected_rows or [])
        restored = 0
        for candidate in candidates:
            restored += _restore_collection_delay_ledger(candidate, samples)
        for candidate in old_catalog:
            saved = samples.get(candidate.get("sample_id"))
            if saved is None:
                raise ValueError(f"UI candidate {candidate.get('sample_id')} is absent from saved {group_name} samples.")
            if candidate.get("configuration") != saved.get("configuration"):
                raise ValueError(f"UI configuration differs from saved sample {candidate.get('sample_id')}.")

        compact = compact_pareto_scenario_catalog(old_catalog, MAX_GROUP_POINTS)
        old_ids = {row.get("sample_id") for row in old_catalog}
        compact_ids = [row.get("sample_id") for row in compact]
        if len(compact_ids) != len(set(compact_ids)) or not set(compact_ids) <= old_ids:
            raise ValueError(f"Compacted {group_name} catalog changed or duplicated scenario IDs.")
        if not {row.get("support_case") for row in compact} >= {row.get("support_case") for row in old_catalog}:
            raise ValueError(f"Compacted {group_name} catalog dropped a support case.")
        ui_group["scenario_catalog"] = compact
        summary[group_name] = {
            "before": len(old_catalog),
            "after": len(compact),
            "scenario_ids_preserved": True,
            "support_cases": len({row.get("support_case") for row in compact}),
            "harvest_regimes": sorted({
                (row.get("seasonal_availability_profile") or {}).get("regime_id")
                for row in compact
            }),
            "collection_delay_inventory_month_rows_restored": restored,
        }
    return projection, summary


def _projection_without_catalog(payload: dict) -> dict:
    import copy

    comparable = copy.deepcopy(payload)
    for group in (comparable.get("groups_payload") or {}).values():
        group.pop("scenario_catalog", None)
    return comparable


def _replace_with_recoverable_fallback(temp_path: Path, target: Path, payload: bytes) -> None:
    """Replace atomically where possible; otherwise retain a compressed rollback copy."""
    try:
        temp_path.replace(target)
        return
    except PermissionError:
        # Some Windows readers deny delete/rename while allowing writes. Keep a
        # compressed, same-directory recovery copy until the in-place write is
        # parsed and verified, then remove only that temporary backup.
        backup_path = None
        with tempfile.NamedTemporaryFile(
            prefix=f".{target.name}.{uuid4().hex}.", suffix=".rollback.gz",
            dir=target.parent, delete=False,
        ) as backup_handle:
            backup_path = Path(backup_handle.name)
            with target.open("rb") as source, gzip.GzipFile(fileobj=backup_handle, mode="wb") as backup:
                shutil.copyfileobj(source, backup, length=1024 * 1024)
        try:
            with target.open("wb") as destination:
                destination.write(payload)
                destination.flush()
            if target.read_bytes() != payload:
                raise IOError(f"In-place projection verification failed: {target.name}")
        except Exception:
            with gzip.open(backup_path, "rb") as backup, target.open("wb") as destination:
                shutil.copyfileobj(backup, destination, length=1024 * 1024)
                destination.flush()
            raise
        finally:
            if backup_path is not None and backup_path.exists():
                backup_path.unlink()


def main() -> None:
    current = json.loads(PROJECTION_PATHS[0].read_text(encoding="utf-8"))
    for path in PROJECTION_PATHS[1:]:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if _projection_without_catalog(existing) != _projection_without_catalog(current):
            raise RuntimeError(f"Non-catalog UI/API results differ in {path}; refusing to replace it.")
    source_groups = {name: load_pareto_group(RESULTS, name) for name in ("protein_enabled", "protein_bypass")}
    compact, summary = compact_saved_projection(current, source_groups)
    encoded = json.dumps(compact, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    payload = encoded.encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise RuntimeError(f"Compacted UI projection exceeds 100 MiB ({len(payload)} bytes).")

    staged = []
    token = uuid4().hex
    try:
        for target in PROJECTION_PATHS:
            temp_path = target.with_name(f".{target.name}.{token}.tmp")
            temp_path.write_bytes(payload)
            if temp_path.stat().st_size > MAX_BYTES:
                raise RuntimeError(f"Staged artifact exceeds 100 MiB: {target.name}")
            parsed = json.loads(temp_path.read_text(encoding="utf-8"))
            if parsed != compact:
                raise RuntimeError(f"Staged artifact did not validate: {target.name}")
            staged.append((temp_path, target))

        # Stage and validate every replacement before any public path changes.
        for temp_path, target in staged:
            _replace_with_recoverable_fallback(temp_path, target, payload)
        output_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in PROJECTION_PATHS}
        if len(set(output_hashes.values())) != 1:
            raise RuntimeError("Published API and offline projections are not identical.")
        if any(path.stat().st_size > MAX_BYTES for path in PROJECTION_PATHS):
            raise RuntimeError("A published Pareto UI artifact exceeds 100 MiB.")
    finally:
        for temp_path, _ in staged:
            if temp_path.exists():
                temp_path.unlink()

    print(json.dumps({
        "groups": summary,
        "total_scenario_catalog_points": sum(row["after"] for row in summary.values()),
        "projection_bytes": PROJECTION_PATHS[0].stat().st_size,
        "projection_sha256": next(iter(output_hashes.values())),
        "api_and_offline_projection_identical": True,
        "saved_evaluations_and_scenario_ids_preserved": True,
    }, indent=2))


if __name__ == "__main__":
    main()
