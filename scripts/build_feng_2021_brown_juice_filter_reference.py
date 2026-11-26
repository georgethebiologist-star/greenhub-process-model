"""Build a traceable, reference-only extract of Feng et al. (2021) abstract results."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Bigas production + upgrade" / "AD reactor"
AUDIT = DATA / "global_audit_package"
FILENAME = "feng_2021_brown_juice_anaerobic_filter_abstract_reference.csv"
SOURCE_ID = "SRC013"
DOI = "10.1016/j.psep.2020.12.026"
DOI_URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "phase", "material", "geography", "trial_scale",
    "reactor_configuration", "co_substrate", "feed_temperature_c",
    "operating_condition", "metric", "reported_value", "numeric_value", "unit",
    "basis", "source_location", "evidence_class", "quality_class",
    "activation_state", "applicability", "limitations",
]

ROWS = [
    {
        "record_id": "FENG2021-AF-COD-REMOVAL",
        "source_id": SOURCE_ID,
        "phase": "5",
        "material": "Brown juice after grass-protein extraction; harvested input grass-clover mixture reported as 60% ryegrass and 40% clover",
        "geography": "Aarhus University Foulum, Denmark",
        "trial_scale": "pilot",
        "reactor_configuration": "anaerobic filter; reactor unheated and insulated; feed pre-warmed",
        "co_substrate": "none; brown juice was the sole substrate",
        "feed_temperature_c": "55-60",
        "operating_condition": "HRT 5.5 days; source reports up to 80% influent COD removal",
        "metric": "influent_COD_removed",
        "reported_value": "up to 80",
        "numeric_value": "80",
        "unit": "%",
        "basis": "fraction of influent COD; source-reported maximum, not a mean",
        "source_location": "Abstract",
        "evidence_class": "B_primary_literature_measurement_abstract",
        "quality_class": "B",
        "activation_state": "reference_only",
        "applicability": "Pilot brown-juice anaerobic-filter comparator for Phase 5; feed is cultivated grass-clover, not GreenHub roadside-grass residual.",
        "limitations": "Abstract-level result; replicate count, uncertainty, period-specific values, reactor gas flow, methane fraction, and full operating table are unavailable here. Do not treat the maximum as a general removal factor or runtime default.",
    },
    {
        "record_id": "FENG2021-AF-SPECIFIC-CH-PRODUCTION",
        "source_id": SOURCE_ID,
        "phase": "5",
        "material": "Brown juice after grass-protein extraction; harvested input grass-clover mixture reported as 60% ryegrass and 40% clover",
        "geography": "Aarhus University Foulum, Denmark",
        "trial_scale": "pilot",
        "reactor_configuration": "anaerobic filter; reactor unheated and insulated; feed pre-warmed",
        "co_substrate": "none; brown juice was the sole substrate",
        "feed_temperature_c": "55-60",
        "operating_condition": "The abstract does not pair this reported metric with a specific HRT or feeding frequency.",
        "metric": "specific_CH_production_as_reported",
        "reported_value": "230 mL gCOD^-1 d^-1 (publisher abstract notation)",
        "numeric_value": "230",
        "unit": "mL gCOD^-1 d^-1; dimensional interpretation unresolved",
        "basis": "Abstract-level wording: ‘specific CH production’; gas species rendering and time-normalization are not resolved from the abstract.",
        "source_location": "Abstract",
        "evidence_class": "B_primary_literature_measurement_abstract",
        "quality_class": "B",
        "activation_state": "reference_only",
        "applicability": "Preserved as source-reported text for Phase 5 evidence review only; no calculation or normalization use.",
        "limitations": "Do not interpret as mL CH4/g COD, a methane yield, or volumetric productivity; no normalized value is supplied. Full-text table and definition are needed to resolve the dimensional expression.",
    },
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_once(path: Path, row: dict[str, str], key: str) -> None:
    fields, rows = read_csv(path)
    if key not in fields:
        raise ValueError(f"{key} is not a field in {path}")
    existing = [item for item in rows if item.get(key) == row.get(key)]
    if existing:
        if len(existing) != 1 or any(existing[0].get(k, "") != v for k, v in row.items()):
            raise ValueError(f"Conflicting pre-existing {key}={row.get(key)!r} in {path}")
        return
    write_csv(path, fields, [*rows, row])


def main() -> None:
    csv_path = GROUP / FILENAME
    write_csv(csv_path, FIELDS, ROWS)
    checksum = hashlib.sha256(csv_path.read_bytes()).hexdigest()

    source_title = (
        "Pilot-scale anaerobic digestion of by-product liquid (brown juice) from "
        "grass protein extraction using an un-heated anaerobic filter"
    )
    authors = "Lu Feng; Alastair James Ward; Morten Ambye-Jensen; Henrik Bjarne Møller"
    source_url = "https://www.sciencedirect.com/science/article/abs/pii/S0957582020319534"
    sidecar = {
        "dataset_title": "Feng et al. pilot brown-juice anaerobic-filter abstract observations",
        "dataset_identifier": "greenhub:ad-reactor:feng-2021-brown-juice-filter-abstract:v1",
        "source_file": FILENAME,
        "source_file_sha256": checksum,
        "source_id": SOURCE_ID,
        "source_title": source_title,
        "authors": authors,
        "reference_year": 2021,
        "doi": DOI,
        "source_url": DOI_URL,
        "publisher_record_url": source_url,
        "institutional_record_url": "https://pure.au.dk/portal/en/publications/pilot-scale-anaerobic-digestion-of-by-product-liquid-brown-juicef/",
        "retrieval_date": RETRIEVED,
        "source_location": "Publisher and Aarhus University records, Abstract; publisher-rendered Substrates and inoculum section snippet for crop composition and collection context.",
        "document_type": "peer-reviewed primary experimental article; abstract-level extract",
        "evidence_class": "B_primary_literature_measurement_abstract",
        "license": "No explicit open reuse license was identified for the article. Only short factual abstract results are transcribed; the article text/PDF is not redistributed.",
        "rows": len(ROWS),
        "data_basis": "Pilot anaerobic filtration of brown juice as sole substrate. COD removal and the abstract's specific-CH expression are separate records; no unreported pairing or normalized yield is inferred.",
        "experimental_context": {
            "location": "Aarhus University Foulum research centre, Denmark",
            "input_crop": "60% ryegrass and 40% clover, harvested September 2019, as reported in the publisher-rendered source section",
            "reactor": "Pilot anaerobic filter; no co-digestion substrate; insulated reactor without an installed continuous heating device",
            "feed_heating": "Brown juice was warmed to 55-60 °C before feeding to maintain digestion temperature; this is feed temperature, not a measured reactor setpoint.",
        },
        "interpretation_and_limits": [
            "The abstract reports up to 80% influent COD removal at 5.5 d HRT; ‘up to’ is retained and is not represented as a mean or universal removal fraction.",
            "The abstract's 230 mL gCOD^-1 d^-1 ‘specific CH production’ expression is stored verbatim. The gas-species rendering and dimensional/time interpretation are unresolved; normalized value is intentionally absent.",
            "A secondary review table attributes 409.6 L CH4/kg VS to Feng et al. as continuous at 5.5 d, while a separately staged Green Valleys report assigns 409.6 NmL CH4/g VS to a 90-day batch BMP. The Feng abstract does not substantiate that VS-normalized continuous figure; it is excluded pending primary full-text reconciliation.",
            "No replicates, uncertainty, period-specific feed/gas flows, gas composition, energy use, or digestate measurements are extracted from the abstract.",
            "Cultivated grass-clover brown juice is a comparator, not GreenHub roadside feed or an isoelectric-precipitation supernatant measurement.",
        ],
        "normalization": "No conversions. Numeric fields preserve the abstract values; the ambiguous specific-CH metric has no normalized value.",
        "runtime_policy": "Reference-only; not linked to parameters, equations, defaults, TEA/LCA calculations, or Pareto inputs.",
        "fair_metadata": {
            "findable": "Repository-local persistent identifier, source ID, article DOI, URLs, and SHA-256 are recorded.",
            "accessible": "UTF-8 CSV and JSON metadata sidecar; source records are linked over HTTPS.",
            "interoperable": "Long-form CSV gives explicit source, phase, metric, value, unit, basis, operating condition, and activation state.",
            "reusable": "Source locations, license uncertainty, experimental context, unresolved unit, non-activation, and transfer limits are stated.",
        },
    }
    (GROUP / FILENAME.replace(".csv", ".source.json")).write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    append_once(GROUP / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": source_title,
        "authors_or_organization": authors,
        "year": "2021",
        "doi_or_stable_id": DOI,
        "source_url": DOI_URL,
    }, "source_id")
    append_once(GROUP / "dataset_manifest.csv", {
        "filename": FILENAME,
        "row_count": str(len(ROWS)),
        "encoding": "UTF-8 with BOM",
        "delimiter": ",",
        "integration_status": "reference_only_abstract_measurements_not_runtime_eligible",
    }, "filename")

    relative_path = f"Bigas production + upgrade/AD reactor/{FILENAME}"
    append_once(AUDIT / "global_source_register.csv", {
        "dataset_path": relative_path,
        "dataset_group": "AD reactor",
        "source_id": SOURCE_ID,
        "source_title": source_title,
        "authors": authors,
        "year": "2021",
        "doi_or_stable_id": DOI,
        "url": DOI_URL,
        "source_type": "peer-reviewed primary experimental article; abstract-level measurements",
        "notes": "Phase 5 pilot brown-juice anaerobic-filter comparator. One COD-removal maximum and one unit-ambiguous abstract metric; reference-only, not runtime eligible.",
    }, "dataset_path")
    append_once(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": relative_path,
        "category": "Bigas production + upgrade",
        "subgroup": "AD reactor",
        "filename": FILENAME,
        "row_count_observed": str(len(ROWS)),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Abstract-only pilot observations; COD removal retained as an upper result and the specific-CH unit remains unresolved. No runtime connection.",
    }, "dataset_path")
    append_once(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": relative_path,
        "category": "Bigas production + upgrade",
        "subgroup": "AD reactor",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": "2",
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "1",
        "basis_conflicts": "0",
        "cross_reference_issues": "1",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "Both values cite the primary abstract; one specific-CH unit is unresolved and a secondary VS-yield attribution conflicts with the separate staged 90-day batch BMP. Explicitly reference-only.",
    }, "dataset_path")

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = read_csv(AUDIT / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    counts: dict[str, int] = {}
    for row in readiness:
        readiness_value = row.get("readiness", "")
        counts[readiness_value] = counts.get(readiness_value, 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = "2026-11-08T00:00:00Z"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": relative_path, "rows": len(ROWS), "sha256": checksum}, indent=2))


if __name__ == "__main__":
    main()
