"""Register pilot grass-silage storage-loss measurements from Kristensen et al. (2016).

The Danish wet-lowland grass experiment is a literature comparator only. It is
not a GreenHub roadside-grass measurement and must not activate model defaults.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
AUDIT = DATA / "global_audit_package"
FILENAME = "wet_lowland_grass_silage_storage_losses_kristensen_feng_moller_2016_reference.csv"
CSV_PATH = FOLDER / FILENAME
SOURCE_ID = "SRC-KRISTENSEN-FENG-MOLLER-WET-LOWLAND-GRASS-STORAGE-2016"
TITLE = "Storage and pretreatment of grass for from extensive lowland areas used in a biogas plant"
AUTHORS = "Erik Fløjgaard Kristensen; Lu Feng; Henrik B. Møller"
SOURCE_URL = "https://pure.au.dk/portal/en/publications/storage-and-pretreatment-of-grass-for-from-extensive-lowland-area"
FULL_TEXT_URL = "https://conferences.au.dk/uploads/tx_powermail/energy_production_of_biomass__cigr_ageng_full_paper.pdf"
RETRIEVED = "2026-11-08"

FIELDS = [
    "observation_id", "source_id", "source_table", "record_scope", "grass_species",
    "additive_treatment", "harvest_date_as_reported", "sampling_date_as_reported",
    "storage_duration_days", "initial_moisture_pct_as_reported", "measurement",
    "value", "unit", "basis", "replicate_count", "aggregation", "uncertainty",
    "source_location", "evidence_class", "quality_class", "activation_state",
    "limitations",
]

SPECIES = (
    ("Tall fescue", 69.7),
    ("Festulolium", 69.6),
    ("Reed canary grass", 59.9),
)

# For each table, each treatment has three species-specific (mass-loss %,
# dry-matter-loss %) pairs followed by the source's reported cross-species
# average. Values, including negative mass-loss observations, are transcribed.
TABLES = [
    {
        "table": "1", "days": 144, "sampling": "October 2015", "printed_page": "3",
        "treatments": [
            ("No additive", [(1.9, 7.1), (1.4, 8.2), (0.0, 4.1)], (1.1, 6.5)),
            ("Sill-All Fireguard", [(1.0, 5.6), (1.4, 7.2), (1.2, 2.2)], (1.2, 5.0)),
            ("Biotal Axcool Gold", [(0.7, 2.1), (0.7, 7.9), (0.9, 6.8)], (0.8, 5.6)),
        ],
    },
    {
        "table": "2", "days": 223, "sampling": "January 2016", "printed_page": "3–4",
        "treatments": [
            ("No additive", [(-0.2, 2.7), (-2.2, 7.9), (-0.2, 2.7)], (-0.9, 4.5)),
            ("Sill-All Fireguard", [(-0.9, 1.4), (0.6, 6.4), (-1.4, -0.9)], (-0.6, 2.3)),
            ("Biotal Axcool Gold", [(0.2, 6.1), (0.0, 8.2), (-3.4, 2.2)], (-1.0, 5.5)),
        ],
    },
    {
        "table": "3", "days": 304, "sampling": "April 2016", "printed_page": "4",
        "treatments": [
            ("No additive", [(0.0, 3.4), (-0.2, 6.8), (0.9, 0.2)], (0.2, 3.5)),
            ("Sill-All Fireguard", [(0.4, 2.9), (-0.2, 5.7), (0.0, -1.9)], (0.1, 2.3)),
            ("Biotal Axcool Gold", [(0.0, -0.3), (0.2, 7.0), (0.2, 4.0)], (0.2, 3.6)),
        ],
    },
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> list[dict[str, str]]:
    fields, rows = _read(path)
    columns = key.split("|")
    indexed = {tuple(row.get(column, "") for column in columns): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(column, "") for column in columns)
        if identity in indexed:
            indexed[identity].update(entry)
        else:
            rows.append(entry)
            indexed[identity] = rows[-1]
    _write(path, fields or list(entries[0]), rows)
    return rows


def _records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for table in TABLES:
        for treatment, species_values, reported_average in table["treatments"]:
            scopes = [
                (species, moisture, values, "species_specific", "3 pilot barrels per species-treatment-duration")
                for (species, moisture), values in zip(SPECIES, species_values, strict=True)
            ]
            scopes.append((
                "Source-reported average across three grass species", "", reported_average,
                "source_reported_species_average", "Mean across three reported species values; not a pooled barrel-level estimate",
            ))
            for species, moisture, values, scope, aggregation in scopes:
                for metric, value, basis in (
                    ("wet_mass_loss", values[0], "Source table reports mass loss (%); calculation and denominator are not stated."),
                    ("dry_matter_loss", values[1], "Source table reports dry matter loss (%); calculation and denominator are not stated."),
                ):
                    identity = f"KFM16-T{table['table']}-{table['days']}D-{treatment}-{species}-{metric}"
                    records.append({
                        "observation_id": identity.upper().replace(" ", "-").replace("/", "-"),
                        "source_id": SOURCE_ID,
                        "source_table": table["table"],
                        "record_scope": scope,
                        "grass_species": species,
                        "additive_treatment": treatment,
                        "harvest_date_as_reported": "June 2015 (first cut)",
                        "sampling_date_as_reported": table["sampling"],
                        "storage_duration_days": str(table["days"]),
                        "initial_moisture_pct_as_reported": str(moisture),
                        "measurement": metric,
                        "value": str(value),
                        "unit": "%",
                        "basis": basis,
                        "replicate_count": "3" if scope == "species_specific" else "",
                        "aggregation": aggregation,
                        "uncertainty": "Not reported in Tables 1–3; do not infer zero variability.",
                        "source_location": f"Table {table['table']}, printed page {table['printed_page']}; Methods §2.2 for triplicate storage barrels",
                        "evidence_class": "B_measured_literature",
                        "quality_class": "B",
                        "activation_state": "reference_only",
                        "limitations": (
                            "Danish wet-lowland cultivated meadow grasses, not Dutch roadside/VARTA or GreenHub feed. "
                            "Grass from three field plots was mixed before ensiling; no field-level variation is represented. "
                            "Pilot-scale 60 L barrels, manually compressed and closed airtight; additives used manufacturer standard dose, "
                            "but dose is not reported. Negative mass-loss values are retained as printed; authors attribute small mass "
                            "differences to measurement variation/weighing accuracy and report moisture increases of 0.2–2.9 percentage points. "
                            "Table percentages do not define their calculation denominator; no kinetics, emissions, or GreenHub parameter is inferred."
                        ),
                    })
    return records


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    records = _records()
    if CSV_PATH.exists():
        _, existing = _read(CSV_PATH)
    else:
        existing = []
    indexed = {row.get("observation_id", ""): row for row in existing}
    for record in records:
        indexed.setdefault(record["observation_id"], record)
    existing = list(indexed.values())
    _write(CSV_PATH, FIELDS, existing)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()

    metadata = {
        "dataset_id": "urn:greenhub:dataset:storage:kristensen-feng-moller-wet-lowland-grass-silage-storage-losses-2016:v1",
        "persistent_identifier_status": "Repository-local versioned URN for this transcription; the source has a stable Aarhus University research portal record but no DOI was identified.",
        "dataset_version": "1.0.0",
        "source_file": FILENAME,
        "title": "Pilot wet-lowland grass silage mass-loss and dry-matter-loss observations at 144, 223 and 304 days",
        "citation": "Kristensen, E.F., Feng, L., & Møller, H.B. (2016). Storage and pretreatment of grass for from extensive lowland areas used in a biogas plant. Paper presented at the International Conference on Agricultural Engineering 2016, Aarhus, Denmark, 26–29 June 2016.",
        "persistent_identifier": "urn:greenhub:source:storage:kristensen-feng-moller-2016",
        "source_url": SOURCE_URL,
        "full_text_url": FULL_TEXT_URL,
        "source_locations": [
            "Tables 1–3, printed pages 3–4: species/treatment mass loss and dry-matter loss at 144, 223 and 304 days.",
            "Methods §2.1: field location, species, harvest, and mixing of field-plot grass.",
            "Methods §2.2: 60 L airtight barrels, sample weighing, storage periods, and triplicate setup.",
            "Results preceding Table 1: initial moisture by grass species.",
            "Discussion following Table 3: weighing variability, moisture increases, and interpretation of observed losses.",
        ],
        "retrieval_date": RETRIEVED,
        "reference_year": 2016,
        "experiment_year": 2015,
        "geography": "Nørreådalen near Viborg, Denmark; very moist but drained peat land near a stream.",
        "evidence_class": "B_measured_literature",
        "license": "No explicit reuse license identified in the official Aarhus University record or paper. The source paper is linked, not redistributed. Reuse rights for broader redistribution remain unverified.",
        "material_scope": "Tall fescue, Festulolium, and reed canary grass cultivated on wet lowland peat; first-cut material harvested June 2015 and stored as airtight pilot-scale silage.",
        "experimental_conditions": "Grass was chopped at a theoretical 10 mm length, put in manually compressed 60 L barrels, and closed airtight. Triplicates were made for each species, storage period, harvest date, and additive. Manufacturer standard additive doses were used but not quantified in the paper. Initial moisture was reported as 69.7% for tall fescue, 69.6% for Festulolium, and 59.9% for reed canary grass. Storage endpoints were 144, 223, and 304 days.",
        "data_scope": f"{len(existing)} long-form records from Tables 1–3: wet-mass loss and dry-matter loss for three species under no-additive, Sill-All Fireguard, and Biotal Axcool Gold treatments, plus source-reported across-species averages at each duration.",
        "limitations": [
            "Comparator evidence only; this is not Dutch roadside grass, VARTA feed, or a GreenHub storage trial.",
            "Grass from three field plots was mixed before ensiling, so the field plot replicates do not quantify field-level variation.",
            "The experiment used pilot-scale 60 L barrels rather than commercial piles, bunkers, or GreenHub storage equipment.",
            "The paper does not state the equations/denominators for its table percentages and reports no SD, SEM, confidence interval, or row-level measurements.",
            "Negative reported mass-loss values are preserved literally. The authors discuss weighing accuracy and storage moisture increases; these are not evidence of biomass creation.",
            "The additive dose is described as manufacturer-standard but is not quantified, and additive treatment differences are not statistically established in the paper.",
            "No storage gas, leachate, protein-quality, or component-specific loss measurements are included in this extract.",
            "No kinetic fit, interpolation between storage durations, GreenHub default, or runtime parameter is inferred.",
            "The source is publicly accessible but no explicit license was identified; external redistribution rights remain to be checked.",
        ],
        "conversion_or_processing": "Direct transcription of Tables 1–3. No unit conversion, clamping, interpolation, averaging beyond source-reported averages, or imputation. Percent denominators are left as the paper defines them (not further specified).",
        "uncertainty": "Triplicate barrels are described in Methods §2.2. Tables 1–3 do not report replicate dispersion or table-level uncertainty. Group averages are retained as printed and not assigned additional n.",
        "activation_state": "reference_only",
        "fair_metadata": {
            "findable": "Stable local versioned URN, source identifier, full citation, official institutional record, and table/method locations recorded.",
            "accessible": "Official Aarhus University record and public conference-paper URL linked; retrieval date recorded.",
            "interoperable": "UTF-8 long-form CSV with explicit durations, treatments, measurements, units, species, and reported-versus-missing uncertainty.",
            "reusable": "Direct transcription and limitations are documented; no explicit source reuse license was found, so external redistribution rights remain unresolved.",
        },
        "sha256": digest,
    }
    sidecar_path = CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json")
    sidecar_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source_path = FOLDER / "source_register.csv"
    local_sources = _upsert(local_source_path, "source_id", [{
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2016",
        "source_type": "peer-reviewed conference paper; pilot experimental storage results",
        "doi_or_stable_identifier": "Aarhus University research portal record; no DOI identified",
        "stable_url": SOURCE_URL,
        "material": "First-cut tall fescue, Festulolium and reed canary grass stored airtight at pilot scale; Nørreådalen near Viborg, Denmark; harvested June 2015",
        "quality_notes": "Tables 1–3 report wet-mass and dry-matter losses after 144, 223 and 304 days for three species and three additive treatments, plus source-reported averages. Triplicate 60 L barrels are described; no dispersion statistics. Negative mass-loss values retained as printed. Percent denominator is not defined. No explicit reuse license identified. Reference-only; not GreenHub roadside grass.",
        "accessed_date": RETRIEVED,
    }])
    local_source_digest = hashlib.sha256(local_source_path.read_bytes()).hexdigest()
    local_source_fields, _ = _read(local_source_path)
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [
        {
            "filename": FILENAME,
            "description": "Kristensen et al. (2016) Tables 1–3: mass-loss and dry-matter-loss values for pilot airtight silage of three wet-lowland grass species at 144, 223 and 304 days; reference-only.",
            "row_count": str(len(existing)), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
            "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "observation_id",
        },
        {
            "filename": "source_register.csv",
            "description": "Local bibliographic and dataset provenance register for staged Phase 1–7 evidence.",
            "row_count": str(len(local_sources)), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
            "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "source_id",
        },
    ])

    rel = f"storage/{FILENAME}"
    source_rel = "storage/source_register.csv"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": source_rel,
        "dataset_group": "storage",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2016",
        "doi_or_stable_id": "Aarhus University research portal record; no DOI identified",
        "url": FULL_TEXT_URL,
        "source_type": "peer-reviewed conference paper; pilot experimental storage results",
        "notes": "Tables 1–3; pilot airtight silage of Danish wet-lowland cultivated grasses. Triplicate barrels described; no dispersion reported. Negative mass-loss values preserved. Denominator unspecified. Rights status unresolved. B-tier reference-only.",
    }])
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [
        {
            "dataset_path": rel, "category": "storage", "subgroup": "storage",
            "filename": FILENAME, "row_count_observed": str(len(existing)), "header_count": str(len(FIELDS)),
            "headers": "; ".join(FIELDS), "standardized_status_values": "reported; reference_only",
            "detected_readiness": "D3",
            "notes": "B-tier measured literature comparator; direct transcription with reported uncertainty limitations. Not matched to roadside/VARTA material; no runtime mapping.",
        },
        {
            "dataset_path": source_rel, "category": "storage", "subgroup": "storage",
            "filename": "source_register.csv", "row_count_observed": str(len(local_sources)),
            "header_count": str(len(local_source_fields)), "headers": "; ".join(local_source_fields),
            "detected_readiness": "D3", "notes": "Bibliographic metadata index; evidence remains reference-only unless separately validated and activated.",
        },
    ])
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", [
        {"dataset_path": rel, "sha256": digest, "byte_size": str(CSV_PATH.stat().st_size)},
        {"dataset_path": source_rel, "sha256": local_source_digest, "byte_size": str(local_source_path.stat().st_size)},
    ])
    _upsert(AUDIT / "dataset_activation_matrix.csv", "dataset_path", [{
        "dataset_path": rel,
        "category": "storage",
        "subgroup": "Phase 2 storage",
        "audit_readiness": "D3",
        "integration_eligibility": "reference_only",
        "default_eligibility": "False",
        "calculation_connected": "False",
        "active": "False",
        "source_issue_count": "0",
        "quarantine_row_count": "0",
        "issue_types": "none",
        "cost_pathway_status": "not_applicable",
        "selection_reason": "Traceable pilot storage-loss measurements across three durations and additive treatments, but cultivated Danish wet-lowland species, pilot barrels, undefined percentage denominator, absent dispersion, and unresolved reuse license prevent transfer to GreenHub runtime.",
        "required_action": "Collect matched GreenHub storage inventory and component/emission measurements; resolve source reuse rights before broader redistribution.",
        "source_checksum_sha256": digest,
    }, {
        "dataset_path": source_rel,
        "source_checksum_sha256": local_source_digest,
    }])

    print(f"records={len(existing)} new_records={len(records)} bytes={CSV_PATH.stat().st_size} sha256={digest}")


if __name__ == "__main__":
    main()
