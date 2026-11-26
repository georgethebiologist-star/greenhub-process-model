"""Build a small, source-located extract of Wantz et al. farm-test energy points.

Only the two experiment-specific electrical measurements stated in the public
author-uploaded preprint are transcribed. The source PDF is not redistributed.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Bigas production + upgrade/Water_Scrubbing"
CSV_PATH = FOLDER / "wantz_2023_hpsw_experiment_energy_points_reference.csv"
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC008"
FIELDS = [
    "record_id", "experiment_id", "metric", "reported_value", "qualifier", "unit",
    "basis_or_denominator", "operating_context", "measurement_window", "source_id",
    "source_location", "evidence_class", "quality_class", "activation_state",
    "uncertainty_or_limit", "notes",
]


def _row(experiment: str, suffix: str, metric: str, value: str, unit: str, basis: str,
         *, qualifier: str = "", window: str = "") -> dict[str, str]:
    limitations = (
        "Single reported point; no point-level uncertainty or replicate statistic stated. "
        "Prototype and raw-gas/feed context differ from GreenHub; not a generic upgrader "
        "design value. Do not activate as a model default."
    )
    if metric == "specific_electricity_consumption":
        limitations += " Source reports this as approximately 0.8 kWh per Nm3 raw biogas."
    return {
        "record_id": f"WANTZ23-{experiment}-{suffix}",
        "experiment_id": experiment,
        "metric": metric,
        "reported_value": value,
        "qualifier": qualifier,
        "unit": unit,
        "basis_or_denominator": basis,
        "operating_context": "Epurogaz HPWS farm installation at Lamothe, Seysses, France.",
        "measurement_window": window,
        "source_id": SOURCE_ID,
        "source_location": "Results and discussion, electricity measurements for Experiments 31 and 35",
        "evidence_class": "published_primary_measurement",
        "quality_class": "B",
        "activation_state": "reference_only",
        "uncertainty_or_limit": limitations,
        "notes": "Literal transcription; no scale-up, interpolation, or recalculation.",
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    points = [
        {"id": "EXP31", "gas": "30", "water": "8", "absorption_pressure": "9.7", "desorption_pressure": "0.33", "power": "25"},
        {"id": "EXP35", "gas": "20", "water": "6", "absorption_pressure": "10.0", "desorption_pressure": "0.2", "power": "16.6"},
    ]
    for point in points:
        exp = point["id"]
        rows.extend([
            _row(exp, "RAW-GAS-FLOW", "raw_biogas_flow", point["gas"], "Nm3/h", "raw biogas feed"),
            _row(exp, "WATER-FLOW", "scrubbing_water_flow", point["water"], "m3/h", "circulating scrubbing water"),
            _row(exp, "ABS-PRESSURE", "absorption_pressure", point["absorption_pressure"], "bar absolute", "absorber operating pressure"),
            _row(exp, "DES-PRESSURE", "vacuum_desorption_pressure", point["desorption_pressure"], "bar absolute", "flash-tank water-regeneration pressure"),
            _row(exp, "ELECTRICAL-POWER", "measured_electrical_power", point["power"], "kW", "electrical demand of the tested apparatus", qualifier="approximately", window="Electricity meter measurement over 2 h"),
            _row(exp, "SPECIFIC-ELECTRICITY", "specific_electricity_consumption", "0.8", "kWh/Nm3 raw biogas", "raw biogas treated", qualifier="approximately", window="Source-normalized from electrical measurements; around 0.8 kWh/Nm3"),
        ])
    return rows


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:water-scrubbing:wantz-2023-hpsw-energy-points:v1",
        "source_id": SOURCE_ID,
        "title": "Innovative high-pressure water scrubber for biogas upgrading at farm-scale using vacuum for water regeneration",
        "authors": ["Eliot Wantz", "Mathis Lemonnier", "David Benizri", "Nicolas Dietrich", "Gilles Hébrard"],
        "publication_year": 2023,
        "doi": "10.1016/j.apenergy.2023.121781",
        "published_version_url": "https://doi.org/10.1016/j.apenergy.2023.121781",
        "transcription_source_url": "https://www.researchgate.net/publication/373689139_Innovative_high-pressure_water_scrubber_for_biogas_upgrading_at_farm-scale_using_vacuum_for_water_regeneration",
        "transcription_source_version": "Author-uploaded preprint submitted 2023-02-27; publication record identifies Applied Energy 350, article 121781.",
        "source_location": "Results and discussion, electricity measurements for Experiments 31 and 35; the manuscript states a two-hour meter window and approximately 0.8 kWh/Nm3 raw biogas for both points.",
        "geography": "Farm anaerobic-digester installation at Lamothe, Seysses, France.",
        "retrieval_date": "2026-11-08",
        "evidence_class": "B-tier measured literature comparator",
        "license_or_rights": "No explicit reuse license was identified for the manuscript; the author-uploaded page warns content may be subject to copyright. The source PDF is not included. Review rights before external redistribution.",
        "data_handling": "Twelve short factual records transcribe two operating-point contexts and their measured electrical demand. The source-normalized specific consumption is kept as approximate as reported; no value is inferred from the rounded power and flow figures.",
        "activation_state": "reference_only",
        "quality_class": "B",
        "sha256_csv": digest,
        "limitations": [
            "These are two farm-scale water-scrubber operating points on biogas, not roadside-grass-specific measurements or GreenHub calibration.",
            "The paper reports total electrical demand for the tested apparatus; equipment loads and auxiliary contributions are configuration-specific.",
            "Point-level uncertainty and replicate statistics are not given for these readings; power is described as approximate.",
            "The paper's abstract-level claims of improved efficiency and methane recovery are separate from these electrical observations and are not reinterpreted here.",
            "No model parameter, default, UI value, route, TEA/LCA calculation, or Pareto result is activated or changed.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_source_register()
    _update_manifest(len(rows))
    print(f"wrote {len(rows)} reference records; sha256={digest}")


def _rewrite_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _update_source_register() -> None:
    path = FOLDER / "source_register.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    source = next((row for row in rows if row["source_id"] == SOURCE_ID), None)
    if source is None:
        source = {
            "source_id": SOURCE_ID,
            "source_title": "Innovative high-pressure water scrubber for biogas upgrading at farm-scale using vacuum for water regeneration",
            "authors": "Eliot Wantz; Mathis Lemonnier; David Benizri; Nicolas Dietrich; Gilles Hébrard",
            "year": "2023",
            "source_type": "peer-reviewed primary field/pilot study",
            "doi_or_stable_identifier": "10.1016/j.apenergy.2023.121781",
            "source_url": "https://doi.org/10.1016/j.apenergy.2023.121781",
            "accessed_date": "2026-11-08",
            "primary_or_secondary": "primary experimental study",
            "notes": "",
        }
        rows.append(source)
    source["accessed_date"] = "2026-11-08"
    source["notes"] = (
        "Abstract-level summary plus two experiment-specific electricity measurements transcribed from the public "
        "author-uploaded preprint, Results and discussion (Experiments 31 and 35). No source PDF is redistributed; "
        "no explicit reuse license identified; all records remain reference-only."
    )
    _rewrite_csv(path, rows, fields)


def _update_manifest(row_count: int) -> None:
    path = FOLDER / "dataset_manifest.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    entry = {
        "filename": CSV_PATH.name,
        "relative_path": CSV_PATH.relative_to(ROOT).as_posix(),
        "description": "Two experiment-specific farm-scale water-scrubber electrical measurement points; reference-only",
        "row_count": str(row_count),
        "encoding": "UTF-8",
        "delimiter": ",",
        "schema": "pilot operating-point observation schema",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
    }
    existing = next((row for row in rows if row["filename"] == CSV_PATH.name), None)
    if existing is None:
        rows.append(entry)
    else:
        existing.update(entry)
    _rewrite_csv(path, rows, fields)


if __name__ == "__main__":
    main()
