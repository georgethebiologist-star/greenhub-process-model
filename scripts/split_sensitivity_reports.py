"""Split a sensitivity run's endpoint archive into verified <95 MiB gzip shards."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Greenhub.sensitivity_archive import (
    iter_report_records,
    report_archives,
    write_report_records,
    write_report_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_folder", type=Path)
    parser.add_argument("--records-per-shard", type=int, default=250)
    args = parser.parse_args()
    run_dir = args.run_folder.resolve()
    source_archives = report_archives(run_dir)
    if not source_archives:
        parser.error(f"No endpoint report archive found in {run_dir}")
    paths = write_report_records(
        run_dir,
        iter_report_records(run_dir),
        records_per_archive=args.records_per_shard,
    )
    manifest = write_report_manifest(run_dir)
    status_path = run_dir / "run_status.json"
    if status_path.exists():
        status["report_archives"] = [
            {"file": path.name, "size_bytes": path.stat().st_size} for path in paths
        ]
        status["report_archive_limit_bytes"] = MAX_ARCHIVE_BYTES
        status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
