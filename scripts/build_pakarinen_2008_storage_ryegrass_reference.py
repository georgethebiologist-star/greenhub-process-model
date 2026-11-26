"""Build a small, traceable Phase 2/5 extract from Pakarinen et al. (2008).

Only the six no-additive laboratory observations for the low- and high-solids
ryegrass-dominant crop are transcribed. Values remain reference-only and are
not GreenHub roadside-grass defaults, storage kinetics, or AD calibration.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
STORAGE = DATA / "storage"
FILENAME = "ryegrass_ensiling_storage_methane_yield_pakarinen_2008_reference.csv"
CSV_PATH = STORAGE / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-PAKARINEN-ENERGY-CROP-STORAGE-2008"
DOI = "10.1016/j.biortech.2008.01.007"
DOI_URL = f"https://doi.org/{DOI}"
JYX_URL = "https://jyx.jyu.fi/bitstreams/ac243a25-b5f4-42db-8bcd-02e12eebb3c2/download"

FIELDS = [
    "record_id", "source_id", "phase", "material", "geography", "trial_scale",
    "storage_method", "initial_solids_class", "prewilting_hours", "storage_temperature_c",
    "additive", "storage_duration_months", "ph", "scod_mg_per_g_ts",
    "total_solids_pct", "volatile_solids_pct", "vs_per_ts_pct", "vs_loss_pct",
    "methane_potential_m3_per_kg_vs", "methane_potential_sd_m3_per_kg_vs",
    "methane_yield_m3_per_t_current_wet", "methane_yield_m3_per_t_original_wet",
    "source_location", "replication_context", "evidence_class", "quality_class",
    "activation_state", "applicability_limit", "notes",
]

SOURCE_COMMON = (
    "Pakarinen et al. Table 2; cultivated ryegrass-dominant crop from Laukaa, Finland. "
    "The seed mixture included oat as a companion crop; source says the harvested first-cut "
    "material was mainly ryegrass. Laboratory ensiling was anaerobic, in N2-flushed 5-L "
    "water-lock silos at 20 C. No-additive rows only."
)
LIMIT = (
    "Cultivated Finnish ryegrass-dominant crop, not Dutch roadside/VARTA grass. "
    "Reference-only; do not transfer as a GreenHub storage-loss coefficient, kinetic curve, "
    "methane-yield default, or emissions factor."
)


def _row(record_id: str, solids_class: str, wilting_h: int, duration_months: int,
         ph: str, scod: str, ts: str, vs: str, vs_ts: str, vs_loss: str,
         methane_potential: str, methane_sd: str, methane_current_wet: str,
         methane_original_wet: str, notes: str = "") -> dict[str, str]:
    return {
        "record_id": record_id,
        "source_id": SOURCE_ID,
        "phase": "2;5",
        "material": "Ryegrass-dominant crop; oat was a companion crop",
        "geography": "Laukaa, Finland",
        "trial_scale": "laboratory ensiling; 154-500 g wet crop per silo",
        "storage_method": "Anaerobic ensiling in polyethylene bags within 5-L water-lock silo; N2 flushed for about 3 min",
        "initial_solids_class": solids_class,
        "prewilting_hours": str(wilting_h),
        "storage_temperature_c": "20",
        "additive": "none",
        "storage_duration_months": str(duration_months),
        "ph": ph,
        "scod_mg_per_g_ts": scod,
        "total_solids_pct": ts,
        "volatile_solids_pct": vs,
        "vs_per_ts_pct": vs_ts,
        "vs_loss_pct": vs_loss,
        "methane_potential_m3_per_kg_vs": methane_potential,
        "methane_potential_sd_m3_per_kg_vs": methane_sd,
        "methane_yield_m3_per_t_current_wet": methane_current_wet,
        "methane_yield_m3_per_t_original_wet": methane_original_wet,
        "source_location": "Table 2, journal p. 7077; values in the original no-additive treatment rows",
        "replication_context": "Storage experiment performed in duplicate; methane assays in triplicate. Table does not report SD for every composition or VS-loss value. Methane-potential SD is retained only where reported.",
        "evidence_class": "B_measured_literature",
        "quality_class": "B",
        "activation_state": "reference_only",
        "applicability_limit": LIMIT,
        "notes": notes or SOURCE_COMMON,
    }


ROWS = [
    _row("PAK08-RG-LOW-0M", "low solids", 0, 0, "6.36", "217", "13.3", "11.7", "88.0", "0", "0.41", "0.02", "47.6", "47.6"),
    _row("PAK08-RG-LOW-2M", "low solids", 0, 2, "4.82", "374", "9.9", "8.4", "84.8", "29.6", "0.47", "0.04", "39.9", "39.1"),
    _row("PAK08-RG-LOW-6M", "low solids", 0, 6, "6.73", "347", "7.6", "5.9", "77.6", "51.8", "0.45", "0.04", "26.7", "25.6"),
    _row("PAK08-RG-HIGH-0M", "high solids", 48, 0, "6.50", "234", "30.4", "26.5", "87.2", "0", "", "", "107.9", "47.6", "The table footnote says the initial CH4 potential was tested only on the low-solids sample without additive; therefore it is left blank for this high-solids baseline."),
    _row("PAK08-RG-HIGH-2M", "high solids", 48, 2, "4.39", "172", "27.2", "23.4", "86.0", "14.2", "0.46", "0.01", "108.3", "46.5"),
    _row("PAK08-RG-HIGH-6M", "high solids", 48, 6, "6.16", "324", "24.4", "20.4", "83.6", "27.0", "0.51", "0.00", "103.9", "43.5"),
]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def _append_once(path: Path, row: dict[str, object], key: str) -> None:
    fields, existing = _read_csv(path)
    matches = [item for item in existing if item.get(key) == str(row.get(key, ""))]
    if matches:
        if len(matches) != 1 or any(matches[0].get(field, "") != str(row.get(field, "")) for field in fields):
            raise ValueError(f"Conflicting registration in {path}: {row.get(key)}")
        return
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    STORAGE.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    retrieved = "2026-11-08"
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:pakarinen-ryegrass-ensiling-2008:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Pakarinen, O., Lehtomäki, A., Rissanen, S., & Rintala, J. (2008). Storing energy crops for methane production: Effects of solids content and biological additive. Bioresource Technology, 99(15), 7074-7082.",
        "publication_year": 2008,
        "doi": DOI,
        "source_url": DOI_URL,
        "accessible_full_text_url": JYX_URL,
        "retrieval_date": retrieved,
        "source_locations": [
            "Table 2, journal p. 7077: laboratory ryegrass storage outcomes, original no-additive treatment rows.",
            "Methods §§2.1-2.2 and 2.4, journal pp. 7075-7076: crop identity, drying, silos, temperature, oxygen purge, and methane-yield basis.",
        ],
        "geography": "Laukaa, Finland",
        "material_scope": "Cultivated Lolium multiflorum-dominant crop; the seed mixture included 17% ryegrass and 83% oat, with oat used as a companion crop; authors state harvested material was mainly ryegrass.",
        "applicable_phases": [2, 5],
        "experimental_conditions": "Laboratory material was chopped to about 5 cm; high-solids treatment was spread thin and dried 48 h at 20 C. No-additive treatment was packed in polyethylene bags in 5-L water-lock silos, flushed with N2 for about 3 min, and stored at 20 C. Storage experiments were performed in duplicate; methane assays were performed in triplicate.",
        "evidence_class": "B_measured_literature_table_extract",
        "quality_class": "B",
        "license": "The article is Elsevier-copyrighted; the accessible University of Jyväskylä thesis reprints it with permission. No open-data reuse license was identified. This repository stores six selected factual observations and attribution only, not the source article or table image. Review rights before redistribution outside this project.",
        "data_availability": "Six selected no-additive rows from Table 2 are transcribed. The full article is accessible as a reprint in the University of Jyväskylä repository; the primary bibliographic identifier is the DOI.",
        "data_structure": "One row per reported crop-solids/storage-duration condition. Source-reported methane yield per current wet tonne and per original wet tonne are kept as separate columns. Missing methane potential for the high-solids initial sample is intentional because the source footnote says initial methane potential was tested only on the low-solids sample.",
        "uncertainty": "Methane-potential standard deviations are transcribed where the table reports them. The source does not give SD for all composition, VS-loss, and methane-yield-per-tonne fields in this table extract.",
        "conversion_or_processing": "Direct transcription of six source table rows. Decimal values and units are retained. No storage kinetics, intermediate values, loss factors, retention ratios, or emissions are inferred. Blank means not reported/not separately tested, not zero.",
        "limitations": [
            "Cultivated Finnish crop, not roadside/VARTA grass; companion-oat seed mixture means the study is not pure ryegrass.",
            "Only anaerobic laboratory ensiling at 20 C is represented; this is not an aerobic-storage dataset.",
            "Selected rows cover low-solids fresh material and high-solids material dried for 48 h; intermediate 24 h treatments and additive treatments are intentionally outside this small extract.",
            "Storage times are 0, 2, and 6 months only. Do not interpolate or fit continuous kinetics from these six points.",
            "Reported methane per original wet tonne incorporates storage VS and mass losses per the methods; it is distinct from methane per current wet tonne and from methane potential per kg VS.",
            "The study does not provide a complete GreenHub-compatible mass, water, nutrient, or greenhouse-gas emission balance.",
        ],
        "runtime_policy": "Reference-only; not mapped to the parameter registry, process calculations, model defaults, seasonal schedule, TEA/LCA, or Pareto inputs.",
        "access_protocol": "HTTPS DOI and University of Jyväskylä repository full-text URL.",
        "fair_metadata": {
            "findable": "Repository-local URN, file checksum, source ID, DOI and repository URL.",
            "accessible": "Machine-readable UTF-8 CSV and JSON sidecar; source access is through HTTPS.",
            "interoperable": "Long-form CSV with explicit units, solids and storage conditions, time, source table, source basis, quality and activation state.",
            "reusable": "Citation, checksum, rights warning, experimental context, missingness, transfer limits and no-runtime-use policy are explicit.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID,
        "source_title": "Storing energy crops for methane production: Effects of solids content and biological additive",
        "authors": "Outi Pakarinen; Annimari Lehtomäki; Sanna Rissanen; Jukka Rintala",
        "year": "2008",
        "source_type": "peer-reviewed primary experimental article; six selected Table 2 observations",
        "doi_or_stable_identifier": DOI,
        "stable_url": DOI_URL,
        "material": "Cultivated ryegrass-dominant crop with companion oat, laboratory anaerobic storage",
        "quality_notes": "Table 2 records storage composition, VS loss, and methane yields at 0, 2, and 6 months for no-additive low- and high-solids conditions. Cultivated Finnish comparator only; limited extract, reuse license not identified, reference-only.",
        "accessed_date": retrieved,
    }
    _append_once(STORAGE / "source_register.csv", local_source, "source_id")
    _append_once(STORAGE / "dataset_manifest.csv", {
        "filename": FILENAME,
        "description": "Six selected Table 2 laboratory ryegrass-dominant crop storage observations; separate current- and original-wet-weight methane yields; no kinetics inferred.",
        "row_count": len(ROWS),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }, "filename")

    relative_path = f"storage/{FILENAME}"
    global_source = {
        "dataset_path": relative_path,
        "dataset_group": "storage",
        "source_id": SOURCE_ID,
        "source_title": local_source["source_title"],
        "authors": local_source["authors"],
        "year": "2008",
        "doi_or_stable_id": DOI,
        "url": JYX_URL,
        "source_type": local_source["source_type"],
        "notes": local_source["quality_notes"],
    }
    _append_once(DATA / "global_audit_package" / "global_source_register.csv", global_source, "dataset_path")
    _append_once(DATA / "global_audit_package" / "global_dataset_manifest.csv", {
        "dataset_path": relative_path,
        "category": "storage",
        "subgroup": "storage",
        "filename": FILENAME,
        "row_count_observed": len(ROWS),
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Six selected Table 2 records; source-located, quality B, comparator only, and not runtime eligible.",
    }, "dataset_path")
    _append_once(DATA / "global_audit_package" / "global_dataset_readiness.csv", {
        "dataset_path": relative_path,
        "category": "storage",
        "subgroup": "storage",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": 6,
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Six selected laboratory observations from Table 2; no inferred kinetics, emissions, or GreenHub activation.",
    }, "dataset_path")

    summary_path = DATA / "global_audit_package" / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(DATA / "global_audit_package" / "global_dataset_manifest.csv")
    _, readiness_rows = _read_csv(DATA / "global_audit_package" / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    counts: dict[str, int] = {}
    for item in readiness_rows:
        readiness = item.get("readiness", "")
        counts[readiness] = counts.get(readiness, 0) + 1
    summary["readiness_counts"] = counts
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": FILENAME, "rows": len(ROWS), "sha256": digest, "source_id": SOURCE_ID}, indent=2))


if __name__ == "__main__":
    main()
