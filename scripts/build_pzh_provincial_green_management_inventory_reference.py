"""Download and curate Zuid-Holland roadside/ditch-bank management inventory.

This is a Phase 1 evidence extract only. Managed area and maintenance frequency
are not treated as harvested biomass, delivery, or seasonal availability.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FEEDSTOCK = DATA / "Pre-treatment" / "Feedstock"
FEATURE_FILE = "pzh_provincial_roadside_and_ditch_management_inventory_2026_reference.csv"
SUMMARY_FILE = "pzh_provincial_roadside_and_ditch_management_by_frequency_2026_reference.csv"
SOURCE_ID = "SRC-PZH-GREEN-MANAGEMENT-2026"
RETRIEVED_DATE = "2026-11-08"
WFS_BASE = "https://geodata.zuid-holland.nl/geoserver/ows"
DATA_OVERHEID_ID = "a1dbcfc3-2533-46af-9483-7a102488b911"
NGR_UUID = "9B2A50A8-E419-4536-9771-AD2470D66E12"

SOURCE_FIELDS = [
    "Traject", "Trajectdeel", "Beheerobjectomschrijving", "Type", "Helling",
    "Maaien", "Eco", "OH_Freq", "Zone", "Oppervlakte", "Opp_correctie",
    "BEHEERDER", "EIGENAAR", "WIJK", "OPMERKINGEN", "ONDERHOUDSPLOEG",
]
FEATURE_FIELDS = ["feature_id", *SOURCE_FIELDS, "source_id", "evidence_class", "quality_class", "activation_state"]
SUMMARY_FIELDS = [
    "record_id", "source_id", "feature_type", "maintenance_frequency_source_code",
    "mowing_description_source_text", "feature_count", "area_sum_m2",
    "slope_corrected_area_sum_m2", "records_missing_area", "records_missing_corrected_area",
    "records_missing_frequency", "records_missing_mowing_description", "evidence_class",
    "quality_class", "activation_state", "interpretation_limit",
]

LIMIT = (
    "Official management-object inventory, not harvested grass tonnage or verified execution. "
    "Feature areas include only objects classified as berm or slootkant; ditch banks are kept "
    "separate from road verges. Maintenance frequency is a plan/code, not a dated mowing event. "
    "No yield, collected fraction, supplier contract, wet/dry mass, contamination, storage loss, "
    "or plant-delivery record is supplied. Do not convert area to tonnes or runtime availability."
)


def fetch_source_csv() -> tuple[list[dict[str, str]], str]:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "verkeer:ABS_W_GROEN",
        "outputFormat": "csv",
        "count": "40000",
        "propertyName": ",".join(SOURCE_FIELDS),
    }
    url = f"{WFS_BASE}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "GreenHub-data-curation/1.0"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    text = payload.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "FID" not in rows[0]:
        raise ValueError("WFS response was empty or lacked the expected FID column")
    return rows, fetched_at


def num(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value)


def curated_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [row for row in source_rows if row.get("Type", "").strip().casefold() in {"berm", "slootkant"}]
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for row in selected:
        fid = row.get("FID", "").strip()
        if not fid or fid in seen:
            raise ValueError(f"Missing or duplicate WFS feature id: {fid!r}")
        seen.add(fid)
        result.append({
            "feature_id": fid,
            **{name: row.get(name, "") or "" for name in SOURCE_FIELDS},
            "source_id": SOURCE_ID,
            "evidence_class": "B_official_administrative_management_record",
            "quality_class": "B",
            "activation_state": "reference_only",
        })
    if not result:
        raise ValueError("No berm or slootkant management features were returned")
    return result


def grouped_rows(features: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[tuple[str, str, str], dict[str, object]] = defaultdict(
        lambda: {
            "count": 0, "area": 0.0, "corrected_area": 0.0,
            "missing_area": 0, "missing_corrected_area": 0,
            "missing_frequency": 0, "missing_mowing": 0,
        }
    )
    for row in features:
        key = (row["Type"], row["OH_Freq"], row["Maaien"])
        group = groups[key]
        group["count"] = int(group["count"]) + 1
        area = num(row["Oppervlakte"])
        corrected = num(row["Opp_correctie"])
        if area is None:
            group["missing_area"] = int(group["missing_area"]) + 1
        else:
            group["area"] = float(group["area"]) + area
        if corrected is None:
            group["missing_corrected_area"] = int(group["missing_corrected_area"]) + 1
        else:
            group["corrected_area"] = float(group["corrected_area"]) + corrected
        if not row["OH_Freq"].strip():
            group["missing_frequency"] = int(group["missing_frequency"]) + 1
        if not row["Maaien"].strip():
            group["missing_mowing"] = int(group["missing_mowing"]) + 1

    result = []
    for index, (key, group) in enumerate(sorted(groups.items()), start=1):
        feature_type, frequency, mowing = key
        result.append({
            "record_id": f"PZH-GREEN-MGMT-2026-{index:03d}",
            "source_id": SOURCE_ID,
            "feature_type": feature_type,
            "maintenance_frequency_source_code": frequency,
            "mowing_description_source_text": mowing,
            "feature_count": str(group["count"]),
            "area_sum_m2": f"{float(group['area']):.2f}",
            "slope_corrected_area_sum_m2": f"{float(group['corrected_area']):.2f}",
            "records_missing_area": str(group["missing_area"]),
            "records_missing_corrected_area": str(group["missing_corrected_area"]),
            "records_missing_frequency": str(group["missing_frequency"]),
            "records_missing_mowing_description": str(group["missing_mowing"]),
            "evidence_class": "B_official_administrative_record_derived_summary",
            "quality_class": "B",
            "activation_state": "reference_only",
            "interpretation_limit": LIMIT,
        })
    return result


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def append_once(path: Path, row: dict[str, object], key: str) -> None:
    fields, existing = read_csv(path)
    matches = [item for item in existing if item.get(key) == str(row.get(key, ""))]
    if matches:
        if len(matches) != 1 or any(matches[0].get(field, "") != str(row.get(field, "")) for field in fields):
            raise ValueError(f"Conflicting registration in {path}: {row.get(key)}")
        return
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writerow({field: row.get(field, "") for field in fields})


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def register_dataset(filename: str, description: str, rows: list[dict[str, str]], fields: list[str], digest: str) -> None:
    relative_path = f"Pre-treatment/Feedstock/{filename}"
    readiness = "D3"
    audit = DATA / "global_audit_package"
    append_once(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative_path, "category": "Pre-treatment", "subgroup": "Feedstock",
        "filename": filename, "row_count_observed": len(rows), "header_count": len(fields),
        "headers": "; ".join(fields), "standardized_status_values": "B;reference_only",
        "detected_readiness": readiness,
        "notes": "Public-domain management inventory/summary; no harvested tonnes or runtime eligibility.",
    }, "dataset_path")
    append_once(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative_path, "category": "Pre-treatment", "subgroup": "Feedstock",
        "readiness": readiness, "duplicate_ids": 0, "duplicate_rows": 0,
        "numeric_rows": len(rows), "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": (
            len(rows) if filename == SUMMARY_FILE
            else sum(not row.get("Traject", "").strip() and not row.get("Trajectdeel", "").strip() for row in rows)
        ), "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Feature/maintenance areas are not harvest, delivery, or biomass-yield data; reference-only.",
    }, "dataset_path")
    append_once(FEEDSTOCK / "dataset_manifest.csv", {
        "file_name": filename, "description": description, "row_count": len(rows),
        "schema_version": "1.0", "encoding": "UTF-8 with BOM", "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": LIMIT + f" SHA-256: {digest}.",
    }, "file_name")


def main() -> None:
    source_rows, retrieved_at = fetch_source_csv()
    features = curated_rows(source_rows)
    summaries = grouped_rows(features)
    if len(source_rows) != 37188:
        raise ValueError(f"Unexpected source feature count {len(source_rows)}; inspect layer version before accepting")
    if len(features) != 16358:
        raise ValueError(f"Unexpected selected feature count {len(features)}; inspect classification before accepting")
    write_csv(FEEDSTOCK / FEATURE_FILE, FEATURE_FIELDS, features)
    write_csv(FEEDSTOCK / SUMMARY_FILE, SUMMARY_FIELDS, summaries)

    berm = [row for row in features if row["Type"].strip().casefold() == "berm"]
    ditch = [row for row in features if row["Type"].strip().casefold() == "slootkant"]
    berm_corr = sum(num(row["Opp_correctie"]) or 0.0 for row in berm)
    ditch_corr = sum(num(row["Opp_correctie"]) or 0.0 for row in ditch)
    dataset_overview = [
        (FEATURE_FILE, "feature-level provincial green-management objects classified as roadside berm or ditch bank", features, FEATURE_FIELDS),
        (SUMMARY_FILE, "derived area and record-count totals by source feature class, maintenance-frequency code, and mowing-description text", summaries, SUMMARY_FIELDS),
    ]
    source_url = f"{WFS_BASE}?service=WFS&version=2.0.0&request=GetFeature&typeNames=verkeer%3AABS_W_GROEN"
    for filename, description, rows, fields in dataset_overview:
        path = FEEDSTOCK / filename
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sidecar = {
            "dataset_id": f"urn:greenhub:dataset:feedstock:pzh-green-management-{filename.removesuffix('_reference.csv')}:v1",
            "dataset_version": "1.0.0",
            "dataset_file": filename,
            "record_count": len(rows),
            "sha256": digest,
            "source_id": SOURCE_ID,
            "title": description,
            "source_name": "Provincie Zuid-Holland, Areaal beheer - Groen (ABS_W_GROEN)",
            "source_dataset_id": f"data.overheid.nl:{DATA_OVERHEID_ID}",
            "national_georegister_uuid": NGR_UUID,
            "doi": None,
            "source_url": source_url,
            "wfs_capabilities_url": "https://geodata.zuid-holland.nl/geoserver/verkeer/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
            "catalog_url": f"https://data.overheid.nl/en/dataset/{DATA_OVERHEID_ID}",
            "feature_catalog_url": f"https://www.nationaalgeoregister.nl/geonetwork/srv/dut/catalog.search#/metadata/{NGR_UUID}",
            "retrieval_date": RETRIEVED_DATE,
            "retrieved_at_utc": retrieved_at,
            "source_layer": "verkeer:ABS_W_GROEN",
            "source_feature_count": len(source_rows),
            "selection": "Type case-insensitively equals 'berm' or 'slootkant'; geometry and non-requested fields omitted.",
            "geography": "Provincial roads and waterways managed by the Province of Zuid-Holland, Netherlands",
            "units": {
                "Oppervlakte": "m2, area of feature",
                "Opp_correctie": "m2, area corrected for slope",
            },
            "evidence_class": "B_official_administrative_management_record",
            "quality_class": "B",
            "license": "Public domain according to data.overheid.nl metadata; source catalog entry updated 2026-05-29.",
            "limitations": [
                LIMIT,
                "A management inventory is not proof that mowing occurred, that grass was collected, or that the object is under a GreenHub supply contract.",
                "No biomass yield, harvested mass, dry-matter content, date-specific mowing record, contamination, storage, or delivery record is supplied.",
                "Empty maintenance and mowing fields are preserved as empty; they are not inferred.",
                "Only berm and slootkant feature classes are included; the latter is a separate ditch-bank stream and is not included in roadside-berm totals.",
                "No conversion from m2 to tonnes, annual yield, nutrient load, TEA, LCA, runtime, or default input is performed.",
            ],
            "validation": {
                "returned_wfs_features": len(source_rows),
                "selected_berm_features": len(berm),
                "selected_slootkant_features": len(ditch),
                "berm_slope_corrected_area_m2": round(berm_corr, 2),
                "slootkant_slope_corrected_area_m2": round(ditch_corr, 2),
            },
            "activation_state": "reference_only",
            "runtime_policy": "Not eligible as a feedstock quantity; use only as area/management evidence until yield, execution, collection and contract data are supplied.",
            "fair_metadata": {
                "findable": "Local URN, source ID, DataOverheid identifier, NGR UUID, layer name, and content hash are recorded.",
                "accessible": "Public HTTPS WFS and catalog endpoints; source fields and exact query/filter are recorded.",
                "interoperable": "UTF-8 CSV with source field names, documented square-metre units, stable feature identifiers, and separate berm/ditch-bank classes.",
                "reusable": "Retrieval timestamp, filter, checksums, public-domain metadata, source limitations, and no-runtime policy are explicit.",
            },
        }
        path.with_name(path.name + ".source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        register_dataset(filename, description, rows, fields, digest)
        append_once(FEEDSTOCK / "source_register.csv", {
            "source_id": SOURCE_ID,
            "source_title": "Areaal beheer - Groen — provincial roadside and waterway green-management objects",
            "authors": "Provincie Zuid-Holland",
            "year": f"2026 (retrieved {RETRIEVED_DATE}; catalog updated 2026-05-29)",
            "source_type": "official public-domain management-object GIS/WFS inventory",
            "doi_or_stable_identifier": f"data.overheid.nl:{DATA_OVERHEID_ID}; NGR UUID:{NGR_UUID}",
            "stable_url": source_url,
            "material": "Provincial road-verge (berm) and ditch-bank (slootkant) management features; not measured biomass",
            "quality_notes": "WFS layer reports geometry area and slope-corrected area in m2 plus management-frequency/mowing fields. Feature inventory is not execution, collected mass, or supplier availability. Ditch banks remain a separate stream. Public-domain catalog metadata; reference-only.",
            "accessed_date": RETRIEVED_DATE,
        }, "source_id")
        append_once(DATA / "global_audit_package" / "global_source_register.csv", {
            "dataset_path": f"Pre-treatment/Feedstock/{filename}",
            "dataset_group": "Pre-treatment", "source_id": SOURCE_ID,
            "source_title": "Areaal beheer - Groen — provincial roadside and waterway green-management objects",
            "authors": "Provincie Zuid-Holland", "year": "2026 (retrieved); catalog updated 2026-05-29",
            "doi_or_stable_id": f"data.overheid.nl:{DATA_OVERHEID_ID}; NGR UUID:{NGR_UUID}",
            "url": source_url, "source_type": "official public-domain management-object GIS/WFS inventory",
            "notes": f"{len(rows)} {'feature' if filename == FEATURE_FILE else 'summary'} rows. Berm and ditch-bank managed-area evidence only; no harvested biomass or runtime use.",
        }, "dataset_path")

    summary_path = DATA / "global_audit_package" / "global_validation_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        _, manifests = read_csv(DATA / "global_audit_package" / "global_dataset_manifest.csv")
        _, readiness_rows = read_csv(DATA / "global_audit_package" / "global_dataset_readiness.csv")
        summary["dataset_count"] = len(manifests)
        summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        counts: dict[str, int] = {}
        for item in readiness_rows:
            level = item.get("readiness", "")
            counts[level] = counts.get(level, 0) + 1
        summary["readiness_counts"] = counts
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "source_feature_count": len(source_rows), "selected_feature_count": len(features),
        "berm_feature_count": len(berm), "berm_corrected_area_m2": round(berm_corr, 2),
        "ditch_bank_feature_count": len(ditch), "ditch_bank_corrected_area_m2": round(ditch_corr, 2),
        "summary_groups": len(summaries), "retrieved_at_utc": retrieved_at,
    }, indent=2))


if __name__ == "__main__":
    main()
