"""Register concise storage observations for wet green-protein pastes.

The sources concern cultivated forage protein paste, not roadside grass or
GreenHub production. Extracted observations remain reference-only and do not
activate storage kinetics, product quality limits, or runtime defaults.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
AUDIT = DATA / "global_audit_package"
FILENAME = "wet_green_protein_paste_storage_santamaria_stodkilde_2019_2021_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
RETRIEVED = "2026-11-08"
REPORT_ID = "SRC-SANTAMARIA-STODKILDE-WET-PASTE-2019"
ABSTRACT_ID = "SRC-OKNET-ECOFEED-WET-PROTEIN-SHELF-LIFE-2021"
REPORT_URL = "https://orgprints.org/36872/1/D1.4%20Research%20report_Shelf%20life%20of%20wet%20protein%20pastes.pdf"
ABSTRACT_URL = "https://orgprints.org/id/eprint/39520/1/PA-AU-green-protein-testing-layers-final.pdf"

FIELDS = [
    "record_id", "phase_relevance", "source_id", "material", "species_or_blend",
    "storage_stage", "condition", "storage_temperature_C", "storage_time_month",
    "metric", "statistic", "value", "unit", "basis", "source_location",
    "experimental_context", "evidence_class", "quality_class", "activation_state",
    "transferability", "limitations",
]

SOURCES = [
    {
        "source_id": REPORT_ID,
        "source_title": "Shelf life of the wet protein pastes upon storage",
        "authors": "Maria Santamaria Fernandez; Lene Stødkilde",
        "year": "2019",
        "source_type": "Aarhus University project research report; primary experimental results",
        "doi_or_stable_identifier": "Organic Eprints record 36872; no DOI identified",
        "stable_url": REPORT_URL,
        "material": "Wet protein pastes prepared from alfalfa, red clover and ryegrass at Aarhus University Foulum in summer 2017",
        "quality_notes": (
            "Reports initial paste DM/OM and storage observations for vacuum-packed samples at room temperature and approximately 4 °C. "
            "No explicit data-reuse license was identified; only a concise factual extract is included, and rights review is required before external redistribution. "
            "The report's bag-count statement does not reconcile arithmetically with its stated four bags per crop/condition/time combination; replicate counts are not used here."
        ),
        "accessed_date": RETRIEVED,
    },
    {
        "source_id": ABSTRACT_ID,
        "source_title": "Clover-grass protein by bio-refining: nutrient composition and shelf life",
        "authors": "Sanna Steenfeldt; Ricarda Engberg; Morten Ambye-Jensen",
        "year": "2021",
        "source_type": "OK-Net EcoFeed practice abstract summarizing a storage trial",
        "doi_or_stable_identifier": "Organic Eprints record 39520; no DOI identified",
        "stable_url": ABSTRACT_URL,
        "material": "Clover-grass green protein concentrate; anaerobically stored at 4 °C or 24 °C with/without added lactic acid bacteria",
        "quality_notes": (
            "Compact abstract-level values and author-reported maximum stable durations are transcribed; plotted time-series points are not digitized. "
            "Stability criterion and full experimental dataset are not supplied in the abstract. No explicit data-reuse license was identified; rights review is required before external redistribution."
        ),
        "accessed_date": RETRIEVED,
    },
]


def _row(
    record_id: str, source_id: str, *, species: str, metric: str, value: str,
    unit: str, basis: str, location: str, stage: str = "wet_protein_paste_storage",
    condition: str = "", temperature: str = "", time: str = "",
    statistic: str = "reported value", context: str = "", limitation: str = "",
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "phase_relevance": "2;4",
        "source_id": source_id,
        "material": "wet green-biorefinery protein paste/concentrate",
        "species_or_blend": species,
        "storage_stage": stage,
        "condition": condition,
        "storage_temperature_C": temperature,
        "storage_time_month": time,
        "metric": metric,
        "statistic": statistic,
        "value": value,
        "unit": unit,
        "basis": basis,
        "source_location": location,
        "experimental_context": context,
        "evidence_class": (
            "primary_project_experiment_report_summary" if source_id == REPORT_ID
            else "project_practice_abstract_summary_of_experiment"
        ),
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "cultivated forage protein paste; not roadside grass, VARTA feed, or GreenHub protein product",
        "limitations": limitation or (
            "Storage of an extracted protein paste is not raw-feed storage. Do not infer grass-feed degradation, mass loss, emissions, or a kinetic rate."
        ),
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    report_context = (
        "Pilot protein biorefinery at Aarhus University Foulum; forage pressed, green juice fermented, protein precipitated and decanter-centrifuged; "
        "paste vacuum-packed. Storage at room temperature (actual temperature not reported) or approximately 4 °C; reported monitoring through 12 months."
    )
    for species, dm, om in (
        ("alfalfa", "31", "27"),
        ("red clover", "29", "19"),
        ("ryegrass", "28", "21"),
    ):
        key = species.upper().replace(" ", "-")
        rows.append(_row(
            f"SST19-{key}-DM-T0", REPORT_ID, species=species,
            metric="dry_matter_content", value=dm, unit="% wet paste",
            basis="wet sample basis; source-reported percentage",
            location="Report section 'Dry matter and organic matter in the wet protein pastes', printed p. 2",
            stage="newly_produced_paste", time="0", statistic="reported mean/summary",
            context=report_context,
            limitation="The report does not state a numeric SD alongside this prose value; do not add one.",
        ))
        rows.append(_row(
            f"SST19-{key}-OM-T0", REPORT_ID, species=species,
            metric="organic_matter_content", value=om, unit="% wet paste",
            basis="wet sample basis; source-reported percentage",
            location="Report section 'Dry matter and organic matter in the wet protein pastes', printed p. 2",
            stage="newly_produced_paste", time="0", statistic="reported mean/summary",
            context=report_context,
            limitation="Organic matter is not crude protein or volatile solids; the report attributes high inorganic matter partly to possible soil contamination.",
        ))

    rows.extend([
        _row(
            "SST19-RED-CLOVER-PH-RT-12M", REPORT_ID, species="red clover",
            metric="pH", value="5.5", unit="pH", basis="as measured",
            location="Report pH-storage results paragraph immediately before Figure 2",
            condition="vacuum-packed; room temperature (actual temperature not reported)",
            time="12", temperature="", statistic="reported endpoint",
            context=report_context,
            limitation="One reported endpoint; not a pH time series, buffer capacity, or acid-demand measurement.",
        ),
        _row(
            "SST19-RYEGRASS-PH-4C-12M", REPORT_ID, species="ryegrass",
            metric="pH", value="3.8", unit="pH", basis="as measured",
            location="Report pH-storage results paragraph immediately before Figure 2",
            condition="vacuum-packed; fridge, approximately 4 °C", temperature="4",
            time="12", statistic="reported endpoint",
            context=report_context,
            limitation="One reported endpoint; not a pH time series, buffer capacity, or acid-demand measurement.",
        ),
        _row(
            "SST19-DM-OM-12M-QUAL", REPORT_ID, species="alfalfa; red clover; ryegrass",
            metric="dry_matter_and_organic_matter_storage_change", value="no change reported",
            unit="qualitative", basis="source conclusion; no numeric endpoint table values transcribed",
            location="Report section 'Dry matter and organic matter in the wet protein pastes', printed p. 2",
            condition="vacuum-packed; room temperature and approximately 4 °C", time="12",
            statistic="qualitative reported conclusion", context=report_context,
            limitation="This is the report's qualitative conclusion, not evidence of zero loss or a transferable retention coefficient.",
        ),
    ])

    abstract_context = (
        "Clover-grass protein concentrate; anaerobic storage; tested 0, 0.5, 1, 2, 3, 4, 5 and 6 months; "
        "treatments at 24 °C and 4 °C, each with or without added lactic acid bacteria (LAB)."
    )
    abstract_rows = [
        ("SST21-CG-DM-T0", "dry_matter_content", "44", "% wet paste", "wet sample basis", "day of harvest/production", "0"),
        ("SST21-CG-CP-T0", "crude_protein_content", "48.5", "% DM", "dry matter basis; protein = nitrogen × 6.25 in the abstract context", "day of harvest/production", "0"),
        ("SST21-CG-MET-T0", "methionine_content", "10.8", "g/kg DM", "dry matter basis", "day of harvest/production", "0"),
        ("SST21-CG-LYS-T0", "lysine_content", "31.4", "g/kg DM", "dry matter basis", "day of harvest/production", "0"),
    ]
    for record_id, metric, value, unit, basis, time_label, time in abstract_rows:
        rows.append(_row(
            record_id, ABSTRACT_ID, species="clover-grass blend", metric=metric,
            value=value, unit=unit, basis=basis,
            location="Practice abstract, 'Practical recommendation' section, printed p. 1",
            stage="newly_produced_paste", time=time,
            statistic="reported value", context=abstract_context,
            limitation=f"The abstract does not report replicate count or uncertainty for this value; time label is {time_label}.",
        ))
    for temp, stable_months in (("24", "2"), ("4", "3")):
        rows.append(_row(
            f"SST21-CG-STABLE-{temp}C", ABSTRACT_ID,
            species="clover-grass blend", metric="author_reported_maximum_stable_anaerobic_storage_duration",
            value=stable_months, unit="month", basis="author-reported maximum under the tested conditions",
            location="Practice abstract, 'Practical recommendation' section, printed p. 1",
            condition="anaerobic; with/without LAB treatments were tested",
            temperature=temp, time=stable_months,
            statistic="reported maximum stable duration", context=abstract_context,
            limitation="The abstract does not define the stability criterion or provide a numerical acceptance threshold; not a kinetic cutoff or regulatory shelf-life guarantee.",
        ))
    rows.append(_row(
        "SST21-CG-TESTED-STORAGE-DESIGN", ABSTRACT_ID,
        species="clover-grass blend", metric="tested_storage_timepoints",
        value="0;0.5;1;2;3;4;5;6", unit="month",
        basis="timepoints listed in the practice abstract",
        location="Practice abstract, 'Solution' section, printed p. 1",
        condition="anaerobic; 4 °C or 24 °C; with or without LAB",
        statistic="experimental design", context=abstract_context,
        limitation="The abstract gives design timepoints, not the corresponding numerical time series; no unreported values were digitized from plots.",
    ))
    rows.append(_row(
        "SST21-CG-LAB-QUAL", ABSTRACT_ID,
        species="clover-grass blend", metric="relative_temperature_and_LAB_effect",
        value="temperature reported as the main shelf-life determinant; LAB addition reported to have minimal effect",
        unit="qualitative", basis="author interpretation",
        location="Practice abstract, 'Practical recommendation' section, printed p. 1",
        condition="anaerobic; 4 °C and 24 °C",
        statistic="qualitative conclusion", context=abstract_context,
        limitation="No effect size or statistical test is reported in the abstract; do not quantify a treatment response.",
    ))
    return rows


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read_csv(path)
    if not fields:
        fields = list(entries[0])
    key_columns = key.split("|")
    identity = lambda row: tuple(row.get(column, "") for column in key_columns)
    index = {identity(row): row for row in rows}
    for entry in entries:
        row_identity = identity(entry)
        if row_identity in index:
            index[row_identity].update(entry)
        else:
            rows.append(entry)
            index[row_identity] = rows[-1]
    _write_csv(path, fields, rows)


def _register() -> None:
    _upsert(FOLDER / "source_register.csv", "source_id", SOURCES)
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "filename": FILENAME,
        "description": "Concise measured and author-reported wet green-protein paste storage observations from Aarhus pilot and OK-Net EcoFeed summary; reference-only and not a GreenHub raw-feed storage model.",
        "row_count": str(len(build_rows())),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }])

    rel = f"storage/{FILENAME}"
    audit_sources = [
        {
            "dataset_path": rel, "dataset_group": "storage", "source_id": src["source_id"],
            "source_title": src["source_title"], "authors": src["authors"], "year": src["year"],
            "doi_or_stable_id": src["doi_or_stable_identifier"], "url": src["stable_url"],
            "source_type": src["source_type"], "notes": src["quality_notes"],
        } for src in SOURCES
    ]
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", audit_sources)

    count = len(build_rows())
    numbers = 0
    for row in build_rows():
        try:
            float(row["value"])
        except ValueError:
            continue
        numbers += 1
    dataset_path = {
        "dataset_path": rel, "category": "storage", "subgroup": "protein-paste storage; Phases 2 and 4",
        "filename": FILENAME, "row_count_observed": str(count), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Concise source-located pilot/abstract results; extracted-protein paste only. Abstract plots not digitized; no rights license identified; no runtime mapping.",
    }
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [dataset_path])
    readiness = {
        "dataset_path": rel, "category": "storage", "subgroup": "protein-paste storage; Phases 2 and 4",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
        "numeric_rows": str(numbers), "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "0", "cross_reference_issues": "0",
        "equation_missing_inputs": "0", "equation_symbol_mismatches": "0",
        "notes": "Source-located reference evidence; not raw feed storage, not roadside/GreenHub-specific, not calculation-connected.",
    }
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [readiness])

    checksums = []
    for path in (CSV_PATH, SIDECAR_PATH):
        checksums.append({
            "dataset_path": f"storage/{path.name}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "byte_size": str(path.stat().st_size),
        })
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, global_manifest = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness_rows = _read_csv(AUDIT / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(global_manifest)
    counts: dict[str, int] = {}
    for item in readiness_rows:
        value = item.get("readiness", "")
        counts[value] = counts.get(value, 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate record IDs in storage package")
    _write_csv(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:wet-green-protein-paste-storage-santamaria-stodkilde:v1",
        "title": "Wet green-protein paste storage observations and author-reported limits",
        "dataset_version": "1.0",
        "source_ids": [REPORT_ID, ABSTRACT_ID],
        "sources": [
            {"source_id": REPORT_ID, "title": SOURCES[0]["source_title"], "authors": SOURCES[0]["authors"].split("; "),
             "year": 2019, "doi": None, "stable_identifier": "Organic Eprints 36872", "url": REPORT_URL,
             "source_locations": "Report methods and results; printed pp. 1–2; pH-storage results paragraph before Figure 2.",
             "data_collection_year_or_period": "Summer 2017; storage through 12 months", "retrieval_date": RETRIEVED},
            {"source_id": ABSTRACT_ID, "title": SOURCES[1]["source_title"], "authors": SOURCES[1]["authors"].split("; "),
             "year": 2021, "doi": None, "stable_identifier": "Organic Eprints 39520", "url": ABSTRACT_URL,
             "source_locations": "Practice abstract, Solution and Practical recommendation sections; printed p. 1.",
             "data_collection_year_or_period": "Not stated in the abstract; storage trial observed through six months", "retrieval_date": RETRIEVED},
        ],
        "geography": "Aarhus University Foulum, Denmark for the 2017 pilot report; practice abstract does not identify its experimental site in the extract.",
        "material_scope": "Cultivated forage protein paste/concentrate from alfalfa, red clover, ryegrass, and a clover-grass blend; not roadside grass.",
        "methods_summary": "Report: screw press, lactic-acid fermentation (pure L. salivarius or natural epiphytic fermentation), protein precipitation and decanter centrifugation; vacuum-packed paste; room temperature or approximately 4 C. Abstract: anaerobic clover-grass protein concentrate stored at 24 C or 4 C, with and without LAB; listed monthly sampling schedule.",
        "license_or_rights": "No explicit open data-reuse license identified for either cited record. Only a concise factual extract is stored; the source documents are not redistributed. Review rights before external redistribution.",
        "evidence_class": "B-tier primary pilot experiment as reported in project report and practice-abstract summary; exact data provenance is recorded per row.",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Transcribe only values stated in prose and exact study design. Do not digitize plots, reconstruct missing time series, infer shelf-life criteria, or fit rates.",
        "limitations": [
            "Extracted protein-paste storage does not establish raw grass storage or feedstock degradation kinetics.",
            "Cultivated forage material is not roadside/VARTA/GreenHub material, and process route and storage packaging differ.",
            "The practice abstract does not define the acceptance criterion for its stated maximum stable storage durations, or report sample sizes/uncertainty.",
            "The 2017 report's stated bag total does not reconcile arithmetically with its stated four bags per crop/condition/time; replicate count is not encoded as a numeric datum.",
            "No mass-loss, storage-gas, leachate, emissions, protein-recovery, or GreenHub-specific shelf-life factors are inferred.",
            "No plotted time-series points were digitized; omitted values remain unreported in this extract.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _register()
    print(json.dumps({"file": str(CSV_PATH), "rows": len(rows), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
