"""Recalculate saved local sensitivity finance without rerunning process cases."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_greenhub_sensitivity as runner
from reprice_sensitivity_report_economics import reprice_record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_folder", type=Path)
    args = parser.parse_args()
    local_dir = args.run_folder.resolve() / "local_sensitivity"
    archive = local_dir / "local_reports.jsonl.gz"
    if not archive.is_file():
        parser.error(f"Missing local report archive: {archive}")
    temporary = archive.with_name("local_reports.repriced.tmp.gz")
    rows = []
    with gzip.open(archive, "rt", encoding="utf-8") as source, gzip.open(
        temporary, "wt", encoding="utf-8", newline=""
    ) as target:
        for line in source:
            record = reprice_record(json.loads(line))
            target.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            rows.append(record.get("input") or {})

    verified = 0
    with gzip.open(temporary, "rt", encoding="utf-8") as stream:
        for line in stream:
            json.loads(line)
            verified += 1
    if verified != len(rows):
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Local report verification count mismatch: {verified} != {len(rows)}")
    os.replace(temporary, archive)

    fields = sorted({key for row in rows for key in row})
    with (local_dir / "local_sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    if rows:
        runner.make_local_tornado(local_dir, rows, rows[0])
    method_path = local_dir / "local_sensitivity_method.json"
    if method_path.exists():
        method = json.loads(method_path.read_text(encoding="utf-8"))
        method["finance_accounting_basis"] = (
            "Product-sales margin is sales minus partial OPEX; operating profit includes the separate grass logistics bonus; "
            "public grants and biomethane support are excluded from operating profit."
        )
        method_path.write_text(json.dumps(method, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "repriced_local_cases": verified,
        "process_simulations_repeated": 0,
        "archive_size_bytes": archive.stat().st_size,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
