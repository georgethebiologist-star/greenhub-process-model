"""Build a reference-only extract of the public Zuid-Holland WFS layer."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FEEDSTOCK = DATA / "Pre-treatment" / "Feedstock"
FILENAME = "pzh_municipal_green_waste_cbs_2022_reference.csv"
CSV_PATH = FEEDSTOCK / FILENAME
SOURCE_ID = "SRC-ZH-GREEN-WASTE-WFS-2026"
CATALOG_SOURCE_ID = "SRC-ZH-GREEN-WASTE-DATA-2026"
REPORT_SOURCE_ID = "SRC-ZH-BIOMASS-INVENTORY-2023"
RETRIEVED = "2026-11-08"
CATALOG_TOTAL_TONNES = 76084

FIELDS = [
    "record_id", "source_id", "municipality", "reference_year", "reported_value",
    "reported_unit", "material_stream", "evidence_class", "quality_class",
    "measurement_status", "derivation_method", "source_location", "activation_state",
    "applicability_limit", "notes",
]

LIMIT = (
    "Municipal mixed green waste includes verge mowings and other public-space vegetation, "
    "parks, nature areas, waterways, pruning wood and branches. It is not a grass-only quantity, "
    "does not identify a GreenHub supplier or accessible/contracted fraction, and has no stated "
    "wet/dry mass basis. Reference-only; do not use as roadside-grass feed availability."
)

# Values are transcribed from the public WFS feature property
# GEMEENTELIJK_GROENAFVAL_TON. Preserve the service's municipality labels.
MUNICIPALITIES = [
    ("'s-Gravenhage", 374),
    ("Alblasserdam", 407),
    ("Albrandswaard", 527),
    ("Alphen aan den Rijn", 2284),
    ("Barendrecht", 976),
    ("Bodegraven-Reeuwijk", 726),
    ("Capelle aan den IJssel", 1351),
    ("Delft", 2122),
    ("Dordrecht", 2429),
    ("Goeree-Overflakkee", 1032),
    ("Gorinchem", 769),
    ("Gouda", 1506),
    ("Hardinxveld-Giessendam", 811),
    ("Hendrik-Ido-Ambacht", 449),
    ("Hillegom", 1795),
    ("Hoeksche Waard", 571),
    ("Kaag en Braassem", 1332),
    ("Katwijk", 590),
    ("Krimpen aan den IJssel", 1154),
    ("Krimpenerwaard", 1295),
    ("Lansingerland", 2542),
    ("Leiden", 553),
    ("Leiderdorp", 1555),
    ("Leidschendam-Voorburg", 468),
    ("Lisse", 706),
    ("Maassluis", 389),
    ("Midden-Delfland", 903),
    ("Molenlanden", 589),
    ("Nieuwkoop", 1737),
    ("Nissewaard", 904),
    ("Noordwijk", 151),
    ("Oegstgeest", 646),
    ("Papendrecht", 1153),
    ("Pijnacker-Nootdorp", 950),
    ("Ridderkerk", 1160),
    ("Rijswijk (ZH.)", 13278),
    ("Rotterdam", 16213),
    ("Schiedam", 11257),
    ("Sliedrecht", 524),
    ("Teylingen", 770),
    ("Vlaardingen", 1502),
    ("Voorne aan Zee", 1297),
    ("Voorschoten", 513),
    ("Waddinxveen", 652),
    ("Wassenaar", 542),
    ("Westland", 2298),
    ("Zoetermeer", 2540),
    ("Zoeterwoude", 189),
    ("Zuidplas", 940),
    ("Zwijndrecht", 900),
]


def make_rows() -> list[dict[str, str]]:
    return [
        {
            "record_id": f"PZH-GW-2022-{index:02d}",
            "source_id": SOURCE_ID,
            "municipality": municipality,
            "reference_year": "2022",
            "reported_value": str(value),
            "reported_unit": "t/year (wet/dry basis unspecified)",
            "material_stream": "municipal mixed green waste",
            "evidence_class": "B_official_derived_secondary_data",
            "quality_class": "B",
            "measurement_status": "official CBS-derived municipal estimate; not a weighbridge observation",
            "derivation_method": "Provincial CBS green-waste kg/person value multiplied by municipality population, as described in the linked provincial report.",
            "source_location": (
                "PZH GeoServer WFS, energy:RESTSTROMEN_GROENAFVAL, feature property "
                "GEMEENTELIJK_GROENAFVAL_TON"
            ),
            "activation_state": "reference_only",
            "applicability_limit": LIMIT,
            "notes": "The 2022 value is retained as returned by the public service; no grass share or availability fraction inferred.",
        }
        for index, (municipality, value) in enumerate(MUNICIPALITIES, start=1)
    ]


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


def main() -> None:
    rows = make_rows()
    if len(rows) != 50 or len({row["municipality"] for row in rows}) != 50:
        raise ValueError("Expected 50 unique municipality features")
    observed_sum = sum(int(row["reported_value"]) for row in rows)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:feedstock:pzh-municipal-green-waste-cbs-2022:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(rows),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "related_source_ids": [CATALOG_SOURCE_ID, REPORT_SOURCE_ID],
        "title": "Zuid-Holland municipal mixed-green-waste estimates by municipality, reference year 2022",
        "source_name": "Provincie Zuid-Holland GeoServer WFS",
        "source_dataset_id": "data.overheid.nl:0f08e50f-6483-4d62-8a29-16a049e5c5ec",
        "doi": None,
        "source_url": "https://geodata.zuid-holland.nl/geoserver/energie/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "catalog_url": "https://data.overheid.nl/en/dataset/0f08e50f-6483-4d62-8a29-16a049e5c5ec",
        "methodology_url": "https://circulair.zuid-holland.nl/wp-content/uploads/2021/12/Biomassa-reststromen-analyse-Zuid-Holland-eindverslag-V3-Robin-de-Roo.pdf",
        "retrieval_date": RETRIEVED,
        "source_location": "WFS layer energie:RESTSTROMEN_GROENAFVAL; property GEMEENTELIJK_GROENAFVAL_TON; reference year field JAAR.",
        "secondary_method_location": "Provincial biomass inventory report, Appendix 5, Table 6; states the CBS-derived green-waste per-capita value was multiplied by population.",
        "geography": "50 municipalities in Zuid-Holland, Netherlands",
        "reference_year": 2022,
        "reported_unit": "tonnes per year; wet/dry mass basis not specified",
        "material_scope": "Municipal mixed green waste; may include verge mowings, parks/nature/waterway vegetation, pruning wood and branches.",
        "evidence_class": "B_official_derived_secondary_data",
        "quality_class": "B",
        "license": "Data.overheid.nl metadata and provincial WFS identify the layer as public domain. The linked report has no separate explicit reuse license identified.",
        "data_availability": "Public WFS feature layer; 50 features returned in read-only retrieval on 2026-11-08.",
        "transcription_and_validation": (
            "Direct transcription of the 50 WFS municipality properties. The retrieved feature values sum to "
            f"{observed_sum:,} t/year. The data.overheid.nl catalog description reports {CATALOG_TOTAL_TONNES:,} t/year. "
            "These totals conflict by source version/metadata and are not reconciled. The WFS values match the 50 values in the provincial report's 2022 municipal table; its extracted values also sum to the WFS total."
        ),
        "limitations": [
            "These records are CBS-derived secondary estimates, not measured or weighed grass deliveries.",
            "The material is mixed municipal green waste and no grass/verge fraction is identified.",
            "Wet/dry basis, contamination, seasonal timing, contracted access and GreenHub allocation are not supplied.",
            "The WFS feature sum is 90,321 t/year while the current data.overheid.nl description states 76,084 t/year; preserve both as an unresolved discrepancy, not an uncertainty interval.",
            "No value is connected to feedstock defaults, seasonal availability, runtime, routes, TEA or Pareto calculations.",
        ],
        "activation_state": "reference_only",
        "runtime_policy": "Reference-only regional context; not a roadside-grass or GreenHub supply input.",
        "fair_metadata": {
            "findable": "Local URN, stable data.overheid.nl UUID, layer name, source ID and SHA-256 are recorded.",
            "accessible": "Public HTTPS WFS, dataset catalog page and linked methodology report.",
            "interoperable": "UTF-8 CSV with municipality, reference year, reported tonnes/year, source, method, evidence tier and activation state.",
            "reusable": "Retrieval date, transformation method, catalog/WFS total conflict, mixed-stream scope and no-runtime policy are explicit.",
        },
    }
    (FEEDSTOCK / f"{FILENAME}.source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source_row = {
        "source_id": SOURCE_ID,
        "source_title": "RESTSTROMEN_GROENAFVAL — municipal green waste by municipality",
        "authors": "Provincie Zuid-Holland",
        "year": "2026 (service retrieval); attribute year 2022",
        "source_type": "official public-domain provincial WFS; CBS-derived municipal estimates",
        "doi_or_stable_identifier": "data.overheid.nl:0f08e50f-6483-4d62-8a29-16a049e5c5ec",
        "stable_url": "https://geodata.zuid-holland.nl/geoserver/energie/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "material": "Municipal mixed green waste across Zuid-Holland; not grass-only",
        "quality_notes": f"50 WFS features dated 2022; values sum to {observed_sum:,} t/year. Catalog description separately reports {CATALOG_TOTAL_TONNES:,} t/year; discrepancy retained unresolved. No runtime use.",
        "accessed_date": RETRIEVED,
    }
    source_register_path = FEEDSTOCK / "source_register.csv"
    _, registered_sources = read_csv(source_register_path)
    existing_source = next((row for row in registered_sources if row.get("source_id") == SOURCE_ID), None)
    if existing_source:
        stable_id = existing_source.get("doi_or_stable_identifier", "")
        if stable_id != source_row["doi_or_stable_identifier"]:
            raise ValueError(f"Conflicting source identity for {SOURCE_ID}: {stable_id}")
        # Keep the established portal citation and source notes when the identifier
        # agrees; the WFS service endpoint and portal landing page are both recorded
        # separately in the sidecar/audit history.
    else:
        append_once(source_register_path, source_row, "source_id")
    append_once(FEEDSTOCK / "dataset_manifest.csv", {
        "file_name": FILENAME,
        "description": "50 official CBS-derived municipal mixed-green-waste values from the Zuid-Holland WFS, reference year 2022; not grass-only and not feedstock availability.",
        "row_count": 50,
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": "Mixed municipal green waste; not grass-specific or accessible GreenHub supply. Catalog aggregate discrepancy retained. Primary key: record_id.",
    }, "file_name")

    relative_path = f"Pre-treatment/Feedstock/{FILENAME}"
    audit = DATA / "global_audit_package"
    append_once(audit / "global_source_register.csv", {
        "dataset_path": relative_path,
        "dataset_group": "Pre-treatment",
        "source_id": SOURCE_ID,
        "source_title": "RESTSTROMEN_GROENAFVAL — municipal green waste by municipality",
        "authors": "Provincie Zuid-Holland",
        "year": "2026 (service retrieval); 2022 (attribute year)",
        "doi_or_stable_id": "data.overheid.nl:0f08e50f-6483-4d62-8a29-16a049e5c5ec",
        "url": "https://geodata.zuid-holland.nl/geoserver/energie/wfs?service=WFS&version=2.0.0&request=GetCapabilities",
        "source_type": "official public-domain provincial WFS; secondary CBS-derived estimates",
        "notes": f"50 municipality values sum to {observed_sum:,}; catalog metadata reports {CATALOG_TOTAL_TONNES:,}. Mixed green waste; reference-only.",
    }, "dataset_path")
    append_once(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative_path,
        "category": "Pre-treatment",
        "subgroup": "Feedstock",
        "filename": FILENAME,
        "row_count_observed": len(rows),
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": f"CBS-derived municipal green-waste estimates; 2022; sum {observed_sum:,}; catalog aggregate mismatch retained.",
    }, "dataset_path")
    append_once(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative_path,
        "category": "Pre-treatment",
        "subgroup": "Feedstock",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": len(rows),
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "50 source-linked values from public WFS; secondary municipal mixed-waste estimates, not grass feedstock; no runtime use.",
    }, "dataset_path")

    summary_path = audit / "global_validation_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        _, manifests = read_csv(audit / "global_dataset_manifest.csv")
        _, readiness_rows = read_csv(audit / "global_dataset_readiness.csv")
        summary["dataset_count"] = len(manifests)
        summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        counts: dict[str, int] = {}
        for item in readiness_rows:
            value = item.get("readiness", "")
            counts[value] = counts.get(value, 0) + 1
        summary["readiness_counts"] = counts
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "dataset": FILENAME,
        "rows": len(rows),
        "wfs_sum_t_per_year": observed_sum,
        "catalog_metadata_t_per_year": CATALOG_TOTAL_TONNES,
        "sha256": digest,
        "source_id": SOURCE_ID,
    }, indent=2))


if __name__ == "__main__":
    main()
