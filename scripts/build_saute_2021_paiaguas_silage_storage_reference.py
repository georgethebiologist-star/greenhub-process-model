"""Transcribe the published marginal means for Paiaguás grass silage storage.

The study is a tropical cultivated-forage comparator, not a roadside-grass
calibration. Table means remain reference-only and preserve source units/bases.
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
FILENAME = "paiaguas_grass_silage_storage_loss_effluent_saute_2021_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-SAUTE-PAIAGUAS-GRASS-SILAGE-2021"
DOI = "10.1590/1678-4162-12197"
URL = "https://www.scielo.br/j/abmvz/a/dBKkfPD6rTsFHQx6yzP95jG/?lang=en"
DOI_URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_table", "source_location",
    "material", "storage_or_exposure_period", "factor", "factor_level", "factor_unit",
    "metric", "value", "unit", "basis", "sem", "p_particle_size",
    "p_compaction_density", "p_interaction", "significance_group",
    "replication_design", "evidence_class", "quality_class", "activation_state",
    "transferability", "limitations",
]

SOURCE = {
    "source_id": SOURCE_ID,
    "source_title": "Nutritional value, total dry matter losses, effluent production and pollutant potential in Brachiaria brizantha cv. Paiaguás grass",
    "authors": "J. M. Saute; T. T. Tres; M. P. Osmari; S. L. Silva; J. L. P. Daniel; C. C. Jobim",
    "year": "2021",
    "source_type": "peer-reviewed primary experimental article; measured silage and effluent outcomes",
    "doi_or_stable_identifier": DOI,
    "stable_url": URL,
    "material": "Cultivated Brachiaria brizantha cv. Paiaguás grass ensiled in 13 L laboratory silos in Paraná, Brazil",
    "quality_notes": (
        "Tables 2–4 report 90-day storage endpoints and treatment-factor marginal means for particle size and compaction density. "
        "The article also reports the initial forage composition and a bounded 216-hour aerobic-stability observation. "
        "The study is not Dutch roadside/VARTA feed; COD/BOD units are retained exactly as printed and require scale confirmation. "
        "All records are reference-only and are not runtime inputs."
    ),
    "accessed_date": RETRIEVED,
}

MATERIAL = "Cultivated Brachiaria brizantha cv. Paiaguás grass silage"
REP_DESIGN = (
    "3 x 3 factorial split-plot design with four replications; reported values are marginal means by one factor, "
    "not the nine treatment-cell means or replicate-level observations."
)
LIMITATIONS = (
    "Tropical cultivated forage and small laboratory silos are not Dutch roadside/GreenHub feed or storage. "
    "No row is activated as a GreenHub kinetic or loss parameter."
)

# Table values are transcribed as reported. Each metric stores marginal means
# for the three theoretical particle sizes and the three compaction densities.
TABLES = {
    "Table 2": {
        "location": "printed p. 678, Table 2",
        "period": "90 days sealed storage; silo-opening endpoint",
        "metrics": {
            "silage_dry_matter_loss": {
                "unit": "%", "basis": "percent loss of initial silage dry matter; source formula in Methods",
                "sem": "1.167", "p": ("0.3006", "<0.0001", "0.2077"),
                "particle": [("5", "10.66", ""), ("8", "12.36", ""), ("12", "9.56", "")],
                "density": [("550", "3.76", "b"), ("600", "13.55", "a"), ("650", "15.54", "a")],
            },
            "silage_electrical_conductivity": {
                "unit": "µ/cm (as printed)", "basis": "reported silage measurement; conductivity unit is transcribed verbatim",
                "sem": "35.49", "p": ("0.228", "0.0428", "0.6734"),
                "particle": [("5", "1418.34", ""), ("8", "1505.20", ""), ("12", "1376.68", "")],
                "density": [("550", "1437.7", "ab"), ("600", "1533.9", "a"), ("650", "1324.3", "b")],
            },
            "silage_pH": {
                "unit": "pH", "basis": "dimensionless; silage endpoint",
                "sem": "0.07", "p": ("<0.0001", "0.01", "0.59"),
                "particle": [("5", "4.39", "b"), ("8", "4.49", "b"), ("12", "5.07", "a")],
                "density": [("550", "4.5", "b"), ("600", "4.8", "a"), ("650", "4.6", "b")],
            },
        },
    },
    "Table 3": {
        "location": "printed p. 679, Table 3",
        "period": "90 days sealed storage; accumulated effluent and silo-opening endpoint",
        "metrics": {
            "effluent_dry_matter_loss": {
                "unit": "%", "basis": "dry-matter loss via effluent; denominator not further defined in table",
                "sem": "0.92", "p": ("0.003", "<0.0001", "0.03"),
                "particle": [("5", "8.10", "b"), ("8", "11.16", "a"), ("12", "6.86", "b")],
                "density": [("550", "2.9", "b"), ("600", "12.1", "a"), ("650", "11.9", "a")],
            },
            "effluent_production": {
                "unit": "L/t", "basis": "per tonne of ensiled material; wet/dry denominator basis not stated",
                "sem": "1.30", "p": ("<0.0001", "<0.0001", "<0.0001"),
                "particle": [("5", "14.39", "a"), ("8", "15.02", "a"), ("12", "5.60", "b")],
                "density": [("550", "6.50", "b"), ("600", "14.8", "a"), ("650", "14.4", "a")],
            },
            "effluent_COD": {
                "unit": "mg/L (as printed)", "basis": "effluent concentration; do not rescale from the printed unit",
                "sem": "1.10", "p": ("<0.0001", "<0.0001", "<0.0001"),
                "particle": [("5", "18.97", "a"), ("8", "12.09", "b"), ("12", "9.70", "c")],
                "density": [("550", "10.8", "b"), ("600", "14.8", "a"), ("650", "15.1", "a")],
            },
            "effluent_BOD": {
                "unit": "mg/L (as printed)", "basis": "effluent concentration; do not rescale from the printed unit",
                "sem": "0.50", "p": ("<0.0001", "<0.0001", "<0.0001"),
                "particle": [("5", "5.96", "a"), ("8", "4.41", "b"), ("12", "2.08", "c")],
                "density": [("550", "2.7", "b"), ("600", "5.1", "a"), ("650", "4.6", "a")],
            },
            "effluent_pH": {
                "unit": "pH", "basis": "dimensionless; effluent endpoint",
                "sem": "0.14", "p": ("0.2003", "0.19", "0.4541"),
                "particle": [("5", "8.04", ""), ("8", "8.46", ""), ("12", "7.93", "")],
                "density": [("550", "7.8", ""), ("600", "8.3", ""), ("650", "8.3", "")],
            },
        },
    },
    "Table 4": {
        "location": "printed pp. 679–680, Table 4",
        "period": "90 days sealed storage; silage composition at opening",
        "metrics": {
            "silage_dry_matter": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.223", "p": ("0.92", "0.59", "0.84"),
                "particle": [("5", "19.8", ""), ("8", "19.7", ""), ("12", "19.6", "")],
                "density": [("550", "19.9", ""), ("600", "19.4", ""), ("650", "19.8", "")],
            },
            "organic_matter": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.182", "p": ("0.52", "0.13", "0.96"),
                "particle": [("5", "90.7", ""), ("8", "90.7", ""), ("12", "91.2", "")],
                "density": [("550", "91.2", ""), ("600", "90.3", ""), ("650", "91.1", "")],
            },
            "crude_protein": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.140", "p": ("0.43", "0.56", "0.63"),
                "particle": [("5", "9.54", ""), ("8", "10.0", ""), ("12", "9.72", "")],
                "density": [("550", "9.55", ""), ("600", "9.93", ""), ("650", "9.79", "")],
            },
            "NDF": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.362", "p": ("0.15", "0.84", "0.43"),
                "particle": [("5", "64.6", ""), ("8", "64.1", ""), ("12", "65.8", "")],
                "density": [("550", "64.5", ""), ("600", "64.9", ""), ("650", "65.0", "")],
            },
            "ADF": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.409", "p": ("0.08", "0.27", "0.19"),
                "particle": [("5", "47.3", ""), ("8", "46.1", ""), ("12", "48.2", "")],
                "density": [("550", "47.1", ""), ("600", "46.5", ""), ("650", "48.0", "")],
            },
            "hemicellulose": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.355", "p": ("0.67", "0.20", "0.12"),
                "particle": [("5", "17.3", ""), ("8", "18.0", ""), ("12", "17.6", "")],
                "density": [("550", "17.4", ""), ("600", "18.5", ""), ("650", "17.0", "")],
            },
            "cellulose": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.401", "p": ("0.09", "0.19", "0.40"),
                "particle": [("5", "45.4", ""), ("8", "44.5", ""), ("12", "46.7", "")],
                "density": [("550", "45.0", ""), ("600", "44.9", ""), ("650", "46.5", "")],
            },
            "lignin": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.083", "p": ("<0.01", "<0.01", "<0.01"),
                "particle": [("5", "1.98", "a"), ("8", "1.52", "b"), ("12", "1.54", "b")],
                "density": [("550", "2.07", "a"), ("600", "1.49", "b"), ("650", "1.48", "b")],
            },
            "ether_extract": {
                "unit": "%", "basis": "reported percentage; analytical denominator not specified in table",
                "sem": "0.049", "p": ("<0.01", "0.08", "0.47"),
                "particle": [("5", "2.61", "b"), ("8", "2.58", "b"), ("12", "2.98", "a")],
                "density": [("550", "2.63", ""), ("600", "2.84", ""), ("650", "2.69", "")],
            },
            "in_vitro_dry_matter_digestibility": {
                "unit": "%", "basis": "reported percentage; denominator described as in-vitro dry matter digestibility",
                "sem": "0.623", "p": ("<0.01", "0.53", "0.43"),
                "particle": [("5", "57.8", "a"), ("8", "56.6", "a"), ("12", "53.3", "b")],
                "density": [("550", "55.4", ""), ("600", "56.7", ""), ("650", "55.4", "")],
            },
        },
    },
}

INITIAL_COMPOSITION = [
    ("initial_forage_dry_matter", "20.7", "%", "Methods/Results text; exact basis and analytical denominator not further specified"),
    ("initial_forage_crude_protein", "10.2", "%", "Methods/Results text; exact analytical denominator not further specified"),
    ("initial_forage_NDF", "65.8", "%", "Methods/Results text; exact analytical denominator not further specified"),
    ("initial_forage_ether_extract", "1.6", "%", "Methods/Results text; exact analytical denominator not further specified"),
    ("initial_forage_total_carbohydrates", "79.8", "%", "Methods/Results text; exact calculation basis not further specified"),
]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read_csv(path)
    keys = key.split("|")
    index = {tuple(row.get(field, "") for field in keys): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(field, "") for field in keys)
        if identity in index:
            index[identity].update(entry)
        else:
            rows.append(entry)
            index[identity] = rows[-1]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(entries[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _build_row(table: str, metric: str, factor: str, level: str, value: str,
               factor_unit: str, unit: str, basis: str, sem: str,
               p_values: tuple[str, str, str], significance: str = "") -> dict[str, str]:
    source_location = TABLES[table]["location"]
    short_metric = metric.upper().replace(" ", "_")
    return {
        "record_id": f"SAUTE21-{table.replace(' ', '')}-{short_metric}-{factor}-{level.replace('.', '_')}",
        "source_id": SOURCE_ID,
        "phase_relevance": "2",
        "source_table": table,
        "source_location": source_location,
        "material": MATERIAL,
        "storage_or_exposure_period": TABLES[table]["period"],
        "factor": factor,
        "factor_level": level,
        "factor_unit": factor_unit,
        "metric": metric,
        "value": value,
        "unit": unit,
        "basis": basis,
        "sem": sem,
        "p_particle_size": p_values[0],
        "p_compaction_density": p_values[1],
        "p_interaction": p_values[2],
        "significance_group": significance,
        "replication_design": REP_DESIGN,
        "evidence_class": "B_measured_literature",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "Brazilian tropical Brachiaria forage; controlled laboratory silage; not Dutch roadside/VARTA/GreenHub feed.",
        "limitations": LIMITATIONS,
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for table, table_data in TABLES.items():
        for metric, data in table_data["metrics"].items():
            for factor, factor_unit, key in (
                ("theoretical_particle_size", "mm", "particle"),
                ("compaction_density", "kg/m3", "density"),
            ):
                for level, value, group in data[key]:
                    rows.append(_build_row(
                        table, metric, factor, level, value, factor_unit,
                        data["unit"], data["basis"], data["sem"], data["p"], group,
                    ))

    for metric, value, unit, basis in INITIAL_COMPOSITION:
        rows.append({
            "record_id": f"SAUTE21-INITIAL-{metric.upper()}",
            "source_id": SOURCE_ID,
            "phase_relevance": "1;2",
            "source_table": "Methods/Results text",
            "source_location": "printed p. 677, Materials and Methods / Results and Discussion",
            "material": "Cultivated Brachiaria brizantha cv. Paiaguás forage at cutting",
            "storage_or_exposure_period": "pre-ensiling at cut",
            "factor": "initial_forage_state",
            "factor_level": "reported source value",
            "factor_unit": "",
            "metric": metric,
            "value": value,
            "unit": unit,
            "basis": basis,
            "sem": "",
            "p_particle_size": "",
            "p_compaction_density": "",
            "p_interaction": "",
            "significance_group": "",
            "replication_design": "Initial forage composition reported in article text; n and uncertainty not stated for these values.",
            "evidence_class": "B_measured_literature",
            "quality_class": "B",
            "activation_state": "reference_only",
            "transferability": "Brazilian tropical cultivated forage; not Dutch roadside/VARTA/GreenHub feed.",
            "limitations": "Percentage basis is not fully specified in the cited text; do not infer a dry-matter basis or map as a GreenHub feed default.",
        })

    rows.append({
        "record_id": "SAUTE21-AEROBIC-216H-TEMP-RISE-BOUND",
        "source_id": SOURCE_ID,
        "phase_relevance": "2",
        "source_table": "Figure 2 / Results text",
        "source_location": "printed p. 680, Figure 2 and aerobic-stability results",
        "material": MATERIAL,
        "storage_or_exposure_period": "216 h after exposure to oxygen",
        "factor": "treatment_scope",
        "factor_level": "all particle-size and compaction-density treatments",
        "factor_unit": "",
        "metric": "silage_temperature_rise_above_ambient_upper_bound",
        "value": "<2",
        "unit": "°C",
        "basis": "reported upper bound on difference between silage and ambient temperature; not a time-resolved observation series",
        "sem": "0.21",
        "p_particle_size": "",
        "p_compaction_density": "",
        "p_interaction": "<0.01",
        "significance_group": "",
        "replication_design": "3 x 3 factorial split-plot design with four replications; plotted time series not digitized.",
        "evidence_class": "B_measured_literature",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "Brazilian tropical cultivated forage; post-opening laboratory aerobic-stability comparator.",
        "limitations": "Only the paper's stated bound is recorded; Figure 2 points are not digitized and no temperature response curve is inferred.",
    })
    return rows


def _numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _register(rows: list[dict[str, str]]) -> None:
    _upsert(FOLDER / "source_register.csv", "source_id", [SOURCE])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "filename": FILENAME,
        "description": "Tables 2–4 marginal means for 90-day silage dry-matter loss, effluent loss/quantity/quality and silage composition; includes source-reported initial forage values and a bounded 216-hour aerobic observation. Reference-only tropical forage comparator.",
        "row_count": str(len(rows)), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "record_id",
    }])
    rel = f"storage/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel, "dataset_group": "storage", "source_id": SOURCE_ID,
        "source_title": SOURCE["source_title"], "authors": SOURCE["authors"], "year": SOURCE["year"],
        "doi_or_stable_id": DOI, "url": URL, "source_type": SOURCE["source_type"], "notes": SOURCE["quality_notes"],
    }])
    numeric_rows = sum(_numeric(row["value"]) for row in rows)
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "storage", "subgroup": "cultivated-grass silage losses, effluent and composition; Phase 2",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only", "detected_readiness": "D3",
        "notes": "Published marginal means only; 90-day laboratory silos, four replications in a 3 x 3 split-plot design. COD/BOD and several percent bases remain exactly as reported, with no runtime use.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "storage", "subgroup": "cultivated-grass silage losses, effluent and composition; Phase 2",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0", "numeric_rows": str(numeric_rows),
        "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "0", "cross_reference_issues": "0", "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0", "notes": "Every row cites table/page or text/page; units and ambiguous bases are marked as reported rather than inferred. Factor marginal means are not treatment-cell values; no calculation connection.",
    }])
    checksum_rows = [
        {"dataset_path": f"storage/{path.name}", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "byte_size": str(path.stat().st_size)}
        for path in (CSV_PATH, SIDECAR_PATH)
    ]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksum_rows)
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for item in readiness:
        label = item.get("readiness", "")
        counts[label] = counts.get(label, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    ids = {row["record_id"] for row in rows}
    if len(rows) != 114 or len(ids) != len(rows):
        raise ValueError(f"Expected 114 unique source records, got {len(rows)} rows / {len(ids)} IDs")
    _write_csv(CSV_PATH, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:saute-paiaguas-grass-silage-storage-loss-effluent-2021:v1",
        "persistent_identifier_status": "Repository-local URN identifies this transcription; DOI identifies the source article, not this derivative dataset.",
        "dataset_version": "1.0.0",
        "title": "Paiaguás grass silage storage losses, effluent and composition marginal means",
        "source_file": FILENAME,
        "source_id": SOURCE_ID,
        "citation": "Saute, J. M., Tres, T. T., Osmari, M. P., Silva, S. L., Daniel, J. L. P., & Jobim, C. C. (2021). Nutritional value, total dry matter losses, effluent production and pollutant potential in Brachiaria brizantha cv. Paiaguás grass. Arquivo Brasileiro de Medicina Veterinária e Zootecnia, 73(3), 675–683. https://doi.org/10.1590/1678-4162-12197",
        "doi": DOI,
        "source_url": URL,
        "doi_url": DOI_URL,
        "retrieval_date": RETRIEVED,
        "source_locations": [
            "Table 2, printed p. 678: silage dry-matter loss, electrical conductivity and pH",
            "Table 3, printed p. 679: effluent dry-matter loss, production, COD, BOD and pH",
            "Table 4, printed pp. 679–680: silage composition and in-vitro dry-matter digestibility",
            "Methods/Results text, printed p. 677: initial forage composition and DM-loss method",
            "Figure 2 / Results text, printed p. 680: 216-hour aerobic-stability bound",
        ],
        "reference_year": 2021,
        "experiment_period": "2016-12-13 to 2017-05-17; the source reports this overall experimental period.",
        "geography": "Fazenda Experimental de Iguatemi, Universidade Estadual de Maringá, Paraná, Brazil",
        "material_scope": "Cultivated Brachiaria brizantha cv. Paiaguás grass; initial forage DM reported as 20.7%; ensiled in laboratory PVC silos.",
        "experimental_conditions": "Silo volume 0.013 m3; up to 8.45 kg grass; theoretical particle sizes 5, 8, 12 mm; compaction densities 550, 600, 650 kg/m3; sealed and stored covered for 90 days. The factorial design was split-plot 3 x 3 with four replications. Effluent was collected during storage. The article reports aerobic stability observations for 216 h after opening.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0), stated by the journal's official policy.",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "evidence_class": "B_measured",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Transcribes reported Table 2–4 marginal means, SEM, factor p-values, interaction p-values and significance letters; adds five source-reported initial forage values and one stated aerobic-stability upper bound. Decimal commas are represented with decimal points for numeric CSV fields. No interaction-cell values are inferred, no graph points are digitized, and no unit/basis is corrected by assumption.",
        "known_source_ambiguities": [
            "Table 3 COD and BOD are labeled mg/L in the source, with values 2.08–18.97; the published units and numbers are preserved without rescaling, and the concentration scale needs verification before use.",
            "Table 3 reports an overall effluent average of 14.7 L/t in prose, which does not reconcile with the Table 3 marginal means. The prose average is not included as an extra record; table values are retained verbatim pending source clarification.",
            "Table 4 reports percentages but does not state the denominator basis in its heading/footnote; the extract marks this basis unspecified.",
            "The reported effluent production denominator is per tonne of ensiled material; wet/dry basis is not stated.",
            "The Table 2 electrical-conductivity unit is printed as µ/cm; it is transcribed verbatim and not silently changed to µS/cm.",
        ],
        "limitations": [
            "The feed is tropical cultivated Brachiaria, not Dutch roadside, GreenHub, or VARTA material; values are not GreenHub process factors.",
            "Only marginal means by particle-size and compaction-density main effects are published in Tables 2–4. The factorial interaction is significant for several Table 3 and Table 4 outcomes, so no combined 3 x 3 treatment response can be reconstructed from these marginal means.",
            "No raw replicate measurements, mass closure, gas emission flux, or complete component inventory is published in this extract.",
            "Effluent COD/BOD unit scale and several percent/tonne bases are unresolved as stated above; no conversions or runtime mapping are made.",
            "No GreenHub defaults, model equations, scenario IDs, routes, or results are changed.",
        ],
        "fair_metadata": {
            "findable": "Repository-local URN, source DOI, bibliographic citation, source-register entry, table/page locators, and FAIR catalog record are supplied.",
            "accessible": "UTF-8 CSV and JSON sidecar are repository assets; the article is openly available under CC BY 4.0.",
            "interoperable": "Long-form records use source IDs, phase, factor, factor level, metric, value, unit, basis, statistics and source locations.",
            "reusable": "License, transcription policy, experimental context, unclear units/bases, source discrepancies, and transfer limits are recorded.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _register(rows)
    print(json.dumps({"file": str(CSV_PATH), "rows": len(rows), "numeric_rows": sum(_numeric(row["value"]) for row in rows), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
