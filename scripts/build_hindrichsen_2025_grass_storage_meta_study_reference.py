"""Transcribe the grass-silage storage summary in the 2025 ISC proceedings.

The source is a company-authored meta-study abstract, not GreenHub or roadside
grass kinetics. Values are stored as published summaries and remain reference-only.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/storage"
CSV_PATH = FOLDER / "grass_silage_fresh_matter_loss_stability_hindrichsen_2025_reference.csv"
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "HINDRICHSEN2025_META_GRASS"
SOURCE_URL = "https://conference.ifas.ufl.edu/silage/documents/Silage-2025-Abstract-Compilation.pdf"
TITLE = "Meta Study on Preserving Grass Silage During Storage and Feed Out with SiloSolve FC"
AUTHORS = "Ida Hindrichsen; Rafael Camargo do Amaral; Kristian Lybek Witt"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "phase_relevance", "study_title", "material_scope", "storage_stage",
    "condition_group", "treatment", "metric", "statistic", "reported_value", "unit",
    "reported_basis", "source_id", "source_location", "experimental_context",
    "replicate_count", "evidence_class", "quality_class", "activation_state",
    "transferability", "notes",
]


def _record(record_id: str, *, stage: str, group: str, treatment: str, metric: str,
            statistic: str, value: str, unit: str, basis: str, location: str,
            context: str, notes: str = "") -> dict[str, str]:
    return {
        "record_id": record_id,
        "phase_relevance": "2",
        "study_title": TITLE,
        "material_scope": "Grass mixtures without legumes; six harvest times across Denmark, Lithuania and Germany; harvest years 2019–2023",
        "storage_stage": stage,
        "condition_group": group,
        "treatment": treatment,
        "metric": metric,
        "statistic": statistic,
        "reported_value": value,
        "unit": unit,
        "reported_basis": basis,
        "source_id": SOURCE_ID,
        "source_location": location,
        "experimental_context": context,
        "replicate_count": "Not reported for this pooled summary; underlying trials used 3–5 replicates per treatment where stated.",
        "evidence_class": "primary_experimental_meta_study_conference_abstract",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "grass_silage_comparator_not_roadside_or_GreenHub_feed",
        "notes": notes or "Published pooled summary; not raw replicate data and not a fitted loss coefficient.",
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    # Table 1: pooled minima, maxima and averages across the selected grass trials.
    table1_context = (
        "Grass silage from six harvest times; wilting 0–2 d where tested; anaerobic storage 7–90 d; "
        "mini-silos up to 1 kg or big bales over 600 kg. Aerobic challenge was up to 30 d; ambient "
        "challenge temperature 20–25 °C in mini-silos, while one bale trial followed outdoor temperature."
    )
    summaries = [
        ("forage_dry_matter", "all grass forage", "all", "20.8", "Minimum", "%", "Table 1 under the Hindrichsen et al. abstract; page number not verified"),
        ("forage_dry_matter", "all grass forage", "all", "72.6", "Maximum", "%", "Table 1 under the Hindrichsen et al. abstract; page number not verified"),
        ("forage_dry_matter", "all grass forage", "all", "37.2", "Average", "%", "Table 1 under the Hindrichsen et al. abstract; page number not verified"),
        ("crude_protein", "all grass forage", "all", "9.1", "Minimum", "% DM", "Table 1 under the Hindrichsen et al. abstract; page number not verified"),
        ("crude_protein", "all grass forage", "all", "19.7", "Maximum", "% DM", "Table 1 under the Hindrichsen et al. abstract; page number not verified"),
        ("crude_protein", "all grass forage", "all", "14.6", "Average", "% DM", "Table 1 under the Hindrichsen et al. abstract; page number not verified"),
    ]
    for metric, group, treatment, value, statistic, unit, location in summaries:
        rows.append(_record(
            f"HIND25-{metric.upper()}-{statistic.upper()}", stage="forage before ensiling",
            group=group, treatment=treatment, metric=metric, statistic=statistic, value=value,
            unit=unit, basis="as stated in Table 1", location=location,
            context=table1_context,
        ))

    loss_table = [
        ("anaerobic_storage", "control", "minimum", "0.2"),
        ("anaerobic_storage", "control", "maximum", "2.1"),
        ("anaerobic_storage", "control", "average", "1.2"),
        ("anaerobic_storage", "SiloSolve_FC", "minimum", "0.1"),
        ("anaerobic_storage", "SiloSolve_FC", "maximum", "2.1"),
        ("anaerobic_storage", "SiloSolve_FC", "average", "1.2"),
        ("aerobic_challenge", "control", "minimum", "2.2"),
        ("aerobic_challenge", "control", "maximum", "18.4"),
        ("aerobic_challenge", "control", "average", "6.7"),
        ("aerobic_challenge", "SiloSolve_FC", "minimum", "1.6"),
        ("aerobic_challenge", "SiloSolve_FC", "maximum", "9.4"),
        ("aerobic_challenge", "SiloSolve_FC", "average", "3.8"),
    ]
    for stage, treatment, statistic, value in loss_table:
        rows.append(_record(
            f"HIND25-FMLOSS-{stage.upper()}-{treatment.upper()}-{statistic.upper()}",
            stage=stage, group="pooled six-harvest grass-silage meta-study", treatment=treatment,
            metric="fresh_matter_loss", statistic=statistic, value=value, unit="%",
            basis="source-reported fresh-matter loss; exact denominator protocol not specified in abstract table",
            location="Table 1 under the Hindrichsen et al. abstract; page number not verified",
            context=table1_context,
            notes="Fresh-matter loss, not dry-matter loss. Do not convert to DM loss or infer component emissions.",
        ))

    stability = [
        ("control", "minimum", "19"), ("control", "maximum", "679"), ("control", "average", "181"),
        ("SiloSolve_FC", "minimum", "27"), ("SiloSolve_FC", "maximum", "710"), ("SiloSolve_FC", "average", "251"),
    ]
    for treatment, statistic, value in stability:
        rows.append(_record(
            f"HIND25-STABILITY-{treatment.upper()}-{statistic.upper()}",
            stage="aerobic feed-out challenge", group="pooled six-harvest grass-silage meta-study",
            treatment=treatment, metric="aerobic_stability", statistic=statistic, value=value,
            unit="h", basis="time until silage temperature reached 3 °C above ambient",
            location="Table 1 under the Hindrichsen et al. abstract; page number not verified",
            context="Aerobic challenge lasted up to 30 d; ambient temperature 20–25 °C in mini-silos, while one bale trial followed outdoor temperature.",
        ))

    # A separate single-study comparison explicitly described in the abstract.
    paired_context = "After 2 d wilting, 70 d anaerobic storage, then 30 d aerobic challenge; same reported study context, control versus inoculated treatment."
    for treatment, value in (("control", "18.4"), ("SiloSolve_FC", "4.2")):
        rows.append(_record(
            f"HIND25-FMLOSS-70D-2DWILT-30DAIR-{treatment.upper()}",
            stage="aerobic challenge after anaerobic storage", group="one explicitly conditioned comparison",
            treatment=treatment, metric="fresh_matter_loss", statistic="reported value", value=value,
            unit="%", basis="source-reported fresh-matter loss; exact denominator protocol not specified in abstract",
            location="Results paragraph immediately before Table 1 under the Hindrichsen et al. abstract; page number not verified",
            context=paired_context,
            notes="Single specific comparison, not a pooled treatment mean; does not establish a general inoculant effect for roadside or GreenHub feed.",
        ))
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _update_register() -> None:
    path = FOLDER / "source_register.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    source = {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2025",
        "source_type": "International Silage Conference 2025 abstract compilation; company-authored meta-study",
        "doi_or_stable_identifier": "No DOI identified",
        "stable_url": SOURCE_URL,
        "material": "Grass silage from six harvest times at three sites in Denmark, Lithuania and Germany, harvest years 2019–2023",
        "quality_notes": "Summary minima/maxima/averages and one conditioned fresh-matter-loss comparison transcribed from abstract Table 1/results. Inoculant supplier is the author affiliation. No pooled n, raw data, full condition-level values or explicit reuse license identified. Reference-only; fresh-matter losses must not be confused with DM losses.",
        "accessed_date": RETRIEVED,
    }
    existing = next((row for row in rows if row.get("source_id") == SOURCE_ID), None)
    if existing is None:
        rows.append(source)
    else:
        existing.update(source)
    _write_csv(path, rows, fields)


def _update_manifest(count: int) -> None:
    path = FOLDER / "dataset_manifest.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    entry = {
        "filename": CSV_PATH.name,
        "description": "Pooled grass-silage fresh-matter losses, forage composition and aerobic stability from an industry-authored 2025 conference meta-study; reference-only.",
        "row_count": str(count),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }
    existing = next((row for row in rows if row.get("filename") == CSV_PATH.name), None)
    if existing is None:
        rows.append(entry)
    else:
        existing.update(entry)
    _write_csv(path, rows, fields)


def main() -> None:
    rows = build_rows()
    _write_csv(CSV_PATH, rows, FIELDS)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:storage:hindrichsen-2025-grass-silage-storage-meta-study:v1",
        "title": TITLE,
        "source_id": SOURCE_ID,
        "authors": AUTHORS.split("; "),
        "publication_year": 2025,
        "doi": None,
        "source_url": SOURCE_URL,
        "geography": "Three sites in Denmark, Lithuania and Germany",
        "harvest_years": "2019–2023",
        "retrieval_date": RETRIEVED,
        "source_location": "International Silage Conference 2025 Abstract Compilation, Hindrichsen et al. abstract Table 1 and preceding Results paragraph; page number not verified.",
        "methods_summary": "Six harvest times; grass mixtures without legumes; 0–2 d wilting where tested; 7–90 d anaerobic storage; mini-silos up to 1 kg or bales >600 kg; 3–5 replicates per treatment where stated; aerobic challenge up to 30 d.",
        "license_or_rights": "No explicit reuse license identified in the conference abstract compilation. Only concise factual summaries are transcribed; review rights before external redistribution.",
        "evidence_class": "B-tier published experimental meta-study summary",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Transcribed published summary values and specified conditions only. Range/average summaries remain separate; no raw samples, intermediate time points, curve fits, unit conversions or modeled loss coefficients are inferred.",
        "limitations": [
            "This is grass silage, not roadside grass or GreenHub feed; vegetation, harvest maturity, site, storage package and inoculant use differ.",
            "The abstract does not report the pooled n or the distribution of storage duration, dry matter and replicate counts behind each minimum/maximum/average.",
            "Although the Table 1 caption mentions dry-matter loss, the corresponding storage/challenge rows are explicitly labeled fresh-matter loss; this extract follows the row labels and does not reinterpret them.",
            "Table 1 reports fresh-matter loss; it is not dry-matter loss and must not be treated as an emissions or component-degradation fraction.",
            "The meta-study is affiliated with the commercial inoculant supplier; intervention and sponsorship context are disclosed for interpretation.",
            "No kinetic rate, time interpolation, inoculant benefit or GreenHub storage default is inferred. These observations do not clear the project-specific storage evidence gate.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_register()
    _update_manifest(len(rows))
    print(f"wrote {len(rows)} storage reference observations; sha256={digest}")


if __name__ == "__main__":
    main()
