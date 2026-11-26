"""Retry failed deterministic cases and replace only their failed archive rows.

Run after ``run_greenhub_sensitivity.py`` completes. Initial failed records are
preserved in ``failed_attempts_initial.jsonl`` for audit; the report archive is
rewritten as bounded gzip shards.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_greenhub_sensitivity as sensitivity
from Greenhub.sensitivity_archive import (
    iter_report_records,
    report_archives,
    write_report_manifest,
    write_report_records,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_folder", type=Path)
    args = parser.parse_args()
    root = args.run_folder.resolve()
    archives = report_archives(root)
    if not archives:
        parser.error(f"Missing full report archive in: {root}")
    metadata = json.loads((root / "run_status.json").read_text(encoding="utf-8"))
    seed = int(metadata["seed"])
    catalog = sensitivity.source_catalog()
    records: dict[int, dict] = {}
    base = None
    for record in iter_report_records(root):
        sample = int(record["sample"])
        records[sample] = record
        if record.get("report") and base is None:
            base = record["configuration"]
    failures = [n for n, record in records.items()
                if (record.get("summary") or {}).get("status") != "evaluated"]
    if not failures:
        print("No failed samples to retry.")
        return 0
    if base is None:
        raise SystemExit("No successful archived configuration is available as the run template.")

    original_path = root / "failed_attempts_initial.jsonl"
    with original_path.open("w", encoding="utf-8") as stream:
        for sample in failures:
            stream.write(json.dumps(records[sample], ensure_ascii=False) + "\n")

    from Greenhub.application.decision_support_service import DecisionSupportService
    from Greenhub.application.simulation_service import SimulationService
    workbook = (ROOT / metadata["master_input_workbook_snapshot"]).resolve()
    retry_root = root / "retry_attempts"
    retry_root.mkdir(exist_ok=True)
    retry_log = root / "retry_attempts.jsonl"
    replacements = {}
    with retry_log.open("w", encoding="utf-8") as audit:
        for sample in failures:
            rng = random.Random(seed + sample - 1)
            inputs = sensitivity.sample_input(rng, catalog)
            config = sensitivity.configure_sample(base, catalog, inputs, rng)
            case_root = retry_root / f"case_{sample:04d}"
            service = evaluator = None
            try:
                sensitivity.pin_loaded_workbook_paths(workbook)
                service = SimulationService(run_root=case_root)
                evaluator = DecisionSupportService(simulations=service)
                sensitivity.pin_loaded_workbook_paths(workbook)
                report = evaluator.evaluate(config)
                flat = sensitivity.flatten_numeric(report)
                objective = sensitivity.objective_extract(report)
                row = {
                    "sample": sample, "status": "evaluated", **inputs, **objective,
                    "juice_yield": inputs["juice_yield_kg_per_kg_wet_feed"],
                    "protein_multiplier": inputs["protein_g_kg_dm"] / catalog["base_protein_g_per_kg_dm"],
                    "carbohydrate_multiplier": (inputs["cellulose_fraction_dm"] + inputs["hemicellulose_fraction_dm"]) / catalog["base_cellulose_hemicellulose_fraction_dm"],
                    "capex_grant_fraction": config["candidate_economics"]["capex_grant_fraction"],
                    "nitrogen_g_kg_dm": inputs["varta_nutrients_g_kg_dm"]["nitrogen_g_kg_dm"],
                    "phosphorus_g_kg_dm": inputs["varta_nutrients_g_kg_dm"]["phosphorus_g_kg_dm"],
                    "potassium_g_kg_dm": inputs["varta_nutrients_g_kg_dm"]["potassium_g_kg_dm"],
                    "biomethane_bonus_eur_per_m3": config["candidate_economics"]["biomethane_bonus_eur_per_m3"],
                }
                replacements[sample] = {
                    "sample": sample, "summary": row, "inputs": inputs,
                    "configuration": config, "numeric_endpoints": flat, "report": report,
                }
                audit.write(json.dumps({"sample": sample, "retry_status": "evaluated", "run_id": report.get("run_id")}) + "\n")
            except Exception as exc:
                audit.write(json.dumps({"sample": sample, "retry_status": "failed", "error": f"{type(exc).__name__}: {exc}"}) + "\n")
            finally:
                if service is not None:
                    for run_id in tuple(service.repository.list_ids()):
                        service.repository._runs.pop(run_id, None)
                del evaluator, service
                if case_root.exists():
                    shutil.rmtree(case_root)

    write_report_records(root, (replacements.get(sample, records[sample]) for sample in sorted(records)))
    write_report_manifest(root, len(records))
    print(json.dumps({"original_failures": failures, "retries_succeeded": sorted(replacements),
                      "retry_failures": sorted(set(failures) - set(replacements)),
                      "archives": [str(path) for path in report_archives(root)], "initial_attempt_audit": str(original_path),
                      "retry_audit": str(retry_log)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
