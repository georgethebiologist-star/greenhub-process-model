from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Greenhub" / "data" / "storage"
CSV_PATH = OUT / "roadside_grass_silage_duration_codigestion_homeky_2016_abstract_reference.csv"

FIELDS = [
    "observation_id",
    "source_id",
    "evidence_class",
    "activation_state",
    "feedstock",
    "co_feedstock",
    "storage_duration_weeks",
    "storage_duration_days",
    "outcome",
    "reported_direction_and_magnitude",
    "relative_change_percent_vs_slurry_only_control",
    "reported_yield_unit",
    "yield_basis",
    "test_type",
    "replicate_count",
    "additional_inoculum",
    "silage_additives",
    "geography",
    "source_location",
    "uncertainty",
    "transfer_and_scope_note",
]


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_id = "SRC-HOMEKY-ROADSIDE-ENSILING-DURATION-2016"
    values = [
        (3, "decreased by 14%", -14),
        (8, "decreased by 5%", -5),
        (36, "increased by 15%", 15),
    ]
    note = (
        "Abstract-level co-digestion comparison only; not an isolated storage effect, "
        "not a grass-only methane yield, and not a storage mass-loss measurement. "
        "Roadside-grass source is relevant, but grass species, site, slurry:grass ratio, "
        "storage temperature, absolute yields, and full batch protocol are not reported "
        "in the accessible abstract. Do not calibrate GreenHub storage or AD parameters."
    )
    rows = []
    for weeks, phrase, signed_change in values:
        rows.append(
            {
                "observation_id": f"HOMEKY16-ROAD-GRASS-{weeks}W",
                "source_id": source_id,
                "evidence_class": "B_abstract_only_primary_literature",
                "activation_state": "reference_only",
                "feedstock": "roadside grass silage",
                "co_feedstock": "cow slurry",
                "storage_duration_weeks": weeks,
                "storage_duration_days": weeks * 7,
                "outcome": "relative methane-yield change for grass-silage/cow-slurry mixture",
                "reported_direction_and_magnitude": phrase,
                "relative_change_percent_vs_slurry_only_control": signed_change,
                "reported_yield_unit": "L CH4/kg VS added",
                "yield_basis": "VS added to batch test; abstract does not clarify component allocation",
                "test_type": "anaerobic batch co-digestion; slurry-only control",
                "replicate_count": 2,
                "additional_inoculum": "none",
                "silage_additives": "none",
                "geography": "not reported in abstract",
                "source_location": "publisher abstract",
                "uncertainty": "No SD, confidence interval, or absolute methane yield reported in abstract",
                "transfer_and_scope_note": note,
            }
        )

    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:homeky-roadside-grass-silage-duration-2016-abstract:v1",
        "persistent_identifier_status": "Repository-local stable dataset identifier; the DOI identifies the cited article, not this transcription.",
        "dataset_version": "1.0.0",
        "source_file": CSV_PATH.name,
        "title": "Roadside-grass silage duration and relative co-digestion methane-yield response",
        "citation": "Homeky, B. O., Adouani, N., Potier, O., & Pons, M.-N. (2016). Anaerobic codigestion of cow slurry with grass silage: Effect of silage duration. Environmental Progress & Sustainable Energy, 35(5), 1374–1380. https://doi.org/10.1002/ep.12361",
        "persistent_identifier": "doi:10.1002/ep.12361",
        "source_url": "https://doi.org/10.1002/ep.12361",
        "full_text_url": None,
        "source_locations": ["Publisher abstract: tested silage durations, batch replication, control comparison and relative methane-yield changes"],
        "retrieval_date": "2026-11-08",
        "reference_year": 2016,
        "experiment_year": None,
        "geography": "Not reported in the accessible abstract; author affiliation is not treated as experimental location.",
        "evidence_class": "B_measured_literature_abstract_only",
        "license": "Publisher copyright; no open reuse license identified. The extract preserves a small set of abstract-level factual values with attribution; review publisher terms before external redistribution.",
        "material_scope": "Roadside grass ensiled without additives and co-digested with cow slurry; three storage durations.",
        "experimental_conditions": "Anaerobic batch tests of cow-slurry/grass-silage mixtures after 3, 8 and 36 weeks of ensiling. Each mixture was tested twice, with no additional inoculum. The abstract does not report the grass-to-slurry ratio, exact storage conditions, batch duration, temperature, or absolute methane yields.",
        "data_scope": "Three abstract-reported relative methane-yield changes versus slurry-only controls. Storage durations in days are transparent unit conversions from reported weeks (7 days/week). Directional language is preserved alongside signed percentage change.",
        "limitations": [
            "Reference-only: no runtime, default, parameter registry, or calculation consumes these values.",
            "The values compare co-digestion mixtures with slurry-only controls and do not isolate the causal effect of storage on grass methane potential.",
            "Absolute methane yields, exact slurry-to-grass ratio, storage temperature, grass species/site, test duration, and uncertainty intervals are not available in the accessible abstract.",
            "Two batch repetitions per mixture provide limited replication; no SD or statistical test is reported in the abstract.",
            "The abstract's methane-yield denominator is VS added to the test, but it does not state how added VS is apportioned between grass and slurry.",
            "Do not infer storage dry-matter loss, per-tonne-harvested methane yield, methane kinetics, or a minimum GreenHub storage duration from these results.",
            "The study is roadside-grass relevant but not demonstrated to represent Dutch VARTA feed or GreenHub processing conditions."
        ],
        "conversion_or_processing": "Direct transcription of three abstract-reported relative changes. Verbal decrease/increase was mapped to signed percent values; weeks were converted to days using 7 days/week. No absolute yield, uncertainty, or kinetic value was inferred.",
        "uncertainty": "The abstract states each mixture was tested twice but gives no variability statistic, absolute yield, or test-level observations.",
        "activation_state": "reference_only",
        "phase_tags": ["Phase 2: storage", "Phase 5: anaerobic digestion"],
        "fair_metadata": {
            "findable": "Stable repository-local dataset ID, descriptive title, DOI, and source location are recorded; the DOI identifies the article.",
            "accessible": "CSV and JSON sidecar are included in the repository; the publisher abstract is accessible, full text was not available in this collection pass.",
            "interoperable": "UTF-8 CSV with explicit storage duration, comparison basis, reported unit, replication, and missingness fields.",
            "reusable": "Citation, conversions, evidence class, scope, limitations, uncertainty and licensing caveat are recorded."
        }
    }
    CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").write_text(
        json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
