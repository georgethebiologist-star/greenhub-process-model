"""Shard the existing Pareto ledger and compact redundant projections.

This preserves saved scenario content; it does not simulate or re-rank routes.
Run after a backup-free read/validation when replacing oversized JSON artifacts.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Greenhub.pareto_reporting import (
    load_pareto_group,
    load_pareto_results,
    pareto_ui_projection,
    write_pareto_ui_projection,
)
from scripts.run_rvo_pareto_analysis import (
    MAX_GROUP_ARTIFACT_BYTES,
    OUT,
    _atomic_json_write,
    _write_group_batch_shards,
)


def _replace_oversized_after_backup(target: Path, publish) -> Path | None:
    """Temporarily move a verified-rebuildable oversized artifact out of the way."""

    backup = None
    if target.is_file() and target.stat().st_size >= MAX_GROUP_ARTIFACT_BYTES:
        backup_dir = ROOT / ".codex_tmp" / "pareto_compaction_backup_20261105"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / target.name
        if backup.exists():
            backup.unlink()
        target.replace(backup)
    try:
        publish()
    except Exception:
        if backup is not None and backup.exists():
            if target.exists():
                target.unlink()
            backup.replace(target)
        raise
    return backup


def main() -> None:
    saved = load_pareto_results(OUT)
    expected: dict[str, list[str]] = {}
    for group_name, group in saved.get("groups_payload", {}).items():
        rows = group.get("samples")
        if not isinstance(rows, list):
            raise ValueError(f"Full saved samples are unavailable for {group_name}.")
        expected[group_name] = [str(row.get("sample_id")) for row in rows]
        target = OUT / f"{group_name}_batch.json"
        _replace_oversized_after_backup(
            target, lambda: _write_group_batch_shards(group, target)
        )
        reloaded = load_pareto_group(OUT, group_name)
        actual = [str(row.get("sample_id")) for row in reloaded.get("samples", [])]
        if actual != expected[group_name]:
            raise RuntimeError(f"Sample order/count changed while sharding {group_name}.")

    projection = pareto_ui_projection(saved)
    _replace_oversized_after_backup(
        OUT / "latest.json", lambda: _atomic_json_write(OUT / "latest.json", projection)
    )
    _replace_oversized_after_backup(
        OUT / "rvo_pareto_manifest.json",
        lambda: _atomic_json_write(OUT / "rvo_pareto_manifest.json", projection),
    )
    write_pareto_ui_projection(saved, OUT / "latest_ui.json")

    oversized = [
        (path.name, path.stat().st_size)
        for path in OUT.iterdir()
        if path.is_file() and path.stat().st_size >= 100 * 1024 * 1024
    ]
    if oversized:
        raise RuntimeError(f"Pareto files still exceed 100 MiB: {oversized}")
    print({"sample_counts": {name: len(ids) for name, ids in expected.items()}, "oversized_files": oversized})


if __name__ == "__main__":
    main()
