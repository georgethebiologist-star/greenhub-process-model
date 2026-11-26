"""Transcribe incremental Czubaszek et al. (2023) Tables 3 and 4.

Table 1/2/5 and BMP observations from this paper are already represented in
GreenHub. This extract adds only the missing fresh-grass Table 3 analytes
(excluding ash and sulfur already staged) and Table 4 metals. Five summer
Table 4 potentially-toxic-element observations are connected through a
separate C-class GreenHub profile proxy; all other rows remain reference-only.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Pre-treatment/Feedstock"
CSV_PATH = FOLDER / "czubaszek_2023_fresh_grass_ultimate_and_metals_reference.csv"
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-CZUBASZEK-2023"
DOI = "10.3390/en16114488"
TITLE = "Grass from Road Verges as a Substrate for Biogas Production"
AUTHORS = "R. Czubaszek; A. Wysocka-Czubaszek; G. Zając; et al."
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "phase_relevance", "material", "harvest_season", "metric",
    "reported_mean", "reported_sd", "source_reported_text", "unit", "basis",
    "statistical_group", "observation_status", "analytical_replicates",
    "field_replicates", "source_id", "source_title", "authors", "publication_year",
    "doi", "source_location", "method_context", "evidence_class", "quality_class",
    "activation_state", "transferability", "notes",
]


def _make_row(*, table: int, season: str, metric: str, mean: str = "", sd: str = "",
              unit: str, basis: str, group: str = "", status: str = "reported",
              literal: str = "") -> dict[str, str]:
    season_label = {"spring": "spring", "summer": "summer", "autumn": "autumn"}[season]
    fresh = f"Fresh, non-ensiled urban roadside/verge grass, {season_label} 2019 cutting"
    is_metal = table == 4
    source_location = f"Table {table}, p.{'7' if table == 3 else '8'}"
    if is_metal:
        source_location += "; Table 4 footnote defines n.d. as not detected"
    source_text = literal or (f"{mean} ± {sd}" + (f" {group}" if group else ""))
    return {
        "record_id": f"CZ2023-T{table}-{season[:2].upper()}-{metric.upper()}",
        "phase_relevance": "1;3" if not is_metal else "1;7",
        "material": fresh,
        "harvest_season": season,
        "metric": metric,
        "reported_mean": mean,
        "reported_sd": sd,
        "source_reported_text": source_text,
        "unit": unit,
        "basis": basis,
        "statistical_group": group,
        "observation_status": status,
        "analytical_replicates": "3 (all analyses run in triplicate)",
        "field_replicates": "not reported; do not interpret analytical triplicates as independent sites",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "publication_year": "2023",
        "doi": DOI,
        "source_location": source_location,
        "method_context": (
            "Grass collected during municipal green-area maintenance; brought to the laboratory, air-dried "
            "24 h at room temperature, then cut to 2–4 cm. Fresh denotes not ensiled, not as-received wet feed. "
            "Analytical results are reported on a dry-weight basis."
        ),
        "evidence_class": "primary_experimental_table_transcription",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "Bialystok_Poland_roadside_grass_comparator_not_Dutch_or_GreenHub_calibration",
        "notes": (
            "Source summary statistic only; not raw replicate data. No field-site replication is stated. "
            "Do not infer protein from elemental nitrogen or infer GreenHub contaminant compliance."
        ),
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    # Table 3: sulfur and ash are excluded because they are already represented
    # in the existing feed-characterization package. The remaining analytes are
    # direct transcriptions; no mass closure or protein conversion is applied.
    table3 = {
        "spring": {
            "volatile_matter": ("62.15", "0.18", "a"),
            "fixed_carbon": ("15.01", "0.08", "a"),
            "elemental_carbon": ("38.31", "0.28", "a"),
            "elemental_hydrogen": ("7.23", "0.04", "a"),
            "elemental_nitrogen": ("2.10", "0.00", "a"),
        },
        "summer": {
            "volatile_matter": ("66.27", "0.52", "b"),
            "fixed_carbon": ("14.89", "0.48", "a"),
            "elemental_carbon": ("40.60", "0.23", "b"),
            "elemental_hydrogen": ("7.61", "0.04", "b"),
            "elemental_nitrogen": ("2.49", "0.00", "b"),
        },
        "autumn": {
            "volatile_matter": ("67.84", "0.10", "c"),
            "fixed_carbon": ("14.98", "0.07", "a"),
            "elemental_carbon": ("41.91", "0.03", "c"),
            "elemental_hydrogen": ("7.73", "0.02", "c"),
            "elemental_nitrogen": ("2.62", "0.01", "c"),
        },
    }
    for season, analytes in table3.items():
        for metric, (mean, sd, group) in analytes.items():
            rows.append(_make_row(
                table=3, season=season, metric=metric, mean=mean, sd=sd,
                unit="%", basis="dry weight basis (methods; Table 3 reports %)", group=group,
            ))

    # Table 4: preserve the source's non-detects as censored qualitative data,
    # never as zero. Metal values are on the explicitly printed dry-matter basis.
    metals = {
        "chromium": {"spring": ("14.43", "2.94", "a"), "summer": ("7.54", "3.49", "ab"), "autumn": ("2.67", "0.20", "b")},
        "manganese": {"spring": ("175.24", "11.92", "a"), "summer": ("116.98", "3.17", "ab"), "autumn": ("34.87", "3.85", "b")},
        "iron": {"spring": ("3970.23", "635.23", "a"), "summer": ("977.88", "416.44", "ab"), "autumn": ("295.52", "6.00", "b")},
        "nickel": {"spring": ("3.37", "0.77", "a"), "summer": ("0.78", "0.59", "b"), "autumn": ("1.45", "0.01", "ab")},
        "copper": {"spring": None, "summer": None, "autumn": ("19.53", "2.75", "")},
        "zinc": {"spring": ("80.16", "34.09", "a"), "summer": ("31.04", "8.37", "ab"), "autumn": ("1.73", "0.68", "b")},
        "cadmium": {"spring": ("0.26", "0.09", "a"), "summer": ("0.27", "0.03", "a"), "autumn": ("0.07", "0.02", "b")},
        "mercury": {"spring": None, "summer": ("1.93", "0.11", "a"), "autumn": ("1.41", "0.31", "b")},
        "lead": {"spring": ("8.79", "2.58", "a"), "summer": ("2.45", "1.52", "b"), "autumn": ("1.61", "0.16", "b")},
    }
    for metric, by_season in metals.items():
        for season, values in by_season.items():
            if values is None:
                rows.append(_make_row(
                    table=4, season=season, metric=metric, unit="mg/kg DM",
                    basis="dry matter, as printed", status="not_detected",
                    literal="n.d. (not detected)",
                ))
            else:
                mean, sd, group = values
                rows.append(_make_row(
                    table=4, season=season, metric=metric, mean=mean, sd=sd,
                    unit="mg/kg DM", basis="dry matter, as printed", group=group,
                ))
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _update_manifest(row_count: int) -> None:
    path = FOLDER / "dataset_manifest.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    entry = {
        "file_name": CSV_PATH.name,
        "description": "Incremental fresh roadside-grass proximate/ultimate composition and seasonal metal-screen extract from Czubaszek et al. Tables 3–4; ash and sulfur are already present in the package.",
        "row_count": str(row_count),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_readiness": "D4_partial_calculation_connected_C_class_profile_proxy",
        "limitations": "Only the five detected summer Table 4 Cr/Ni/Cd/Hg/Pb means are connected as a C-class proxy, scaled by the VARTA sample dry matter; all other rows remain reference-only. Polish roadside-grass comparator; analytical triplicates are not field replicates; Table 4 non-detects remain censored; no compliance inference.",
    }
    existing = next((row for row in rows if row.get("file_name") == CSV_PATH.name), None)
    if existing is None:
        rows.append(entry)
    else:
        existing.update(entry)
    _write_csv(path, rows, fields)


def _update_source_register() -> None:
    path = FOLDER / "source_register.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    source = next(row for row in rows if row.get("source_id") == SOURCE_ID)
    note = (
        "Tables 3–4 additionally transcribed as an incremental reference extract: fresh-grass proximate/ultimate "
        "composition and seasonal metal-screen results; Table 3 ash/sulfur omitted from that supplemental file "
        "because already staged elsewhere. The five detected summer Table 4 Cr/Ni/Cd/Hg/Pb means feed a C-class "
        "profile proxy scaled by VARTA dry matter; remaining records are reference-only. All analyses triplicate; "
        "do not treat as field-site replication or infer compliance."
    )
    old = source.get("quality_notes", "")
    if note not in old:
        source["quality_notes"] = (old.rstrip("; ") + "; " + note).strip("; ")
    _write_csv(path, rows, fields)


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    _write_csv(CSV_PATH, rows, FIELDS)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:feedstock:czubaszek-2023-proximate-ultimate-metals:v1",
        "title": "Fresh roadside-grass proximate, ultimate and metals reference observations",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": ["Robert Czubaszek", "Agnieszka Wysocka-Czubaszek", "Grzegorz Zając", "et al."],
        "publication_year": 2023,
        "doi": DOI,
        "doi_url": f"https://doi.org/{DOI}",
        "transcription_source_url": "https://dspace.library.uu.nl/bitstream/handle/1874/428724/energies_16_04488.pdf?sequence=1",
        "geography": "Urban road verges and median strips, Białystok, northeastern Poland",
        "sample_collection_year": 2019,
        "retrieval_date": RETRIEVED,
        "source_tables": {
            "Table 3": "p. 7; proximate and ultimate analysis of fresh grass from spring, summer and autumn cuttings; source units %",
            "Table 4": "p. 8; metals in fresh grass from three cuttings; source unit mg kgDM-1; n.d. means not detected",
        },
        "license": "CC BY 4.0 as stated by the article; transcribed values and source citation are retained.",
        "data_availability": "The article states no separate underlying dataset is available; this extract reproduces only the published table summaries.",
        "evidence_class": "B-tier measured literature comparator",
        "quality_class": "B",
        "activation_state": "partially_calculation_connected_profile_default_proxy",
        "calculation_connected": True,
        "connected_records": [
            "CZ2023-T4-SU-CHROMIUM",
            "CZ2023-T4-SU-NICKEL",
            "CZ2023-T4-SU-CADMIUM",
            "CZ2023-T4-SU-MERCURY",
            "CZ2023-T4-SU-LEAD",
        ],
        "connected_profile_component": "Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json#compounds.HeavyMetals",
        "connected_calculation": "sum(summer Cr, Ni, Cd, Hg, Pb in mg/kg DM) × VARTA measured kg DM/kg wet × 1e-6 kg/mg",
        "connected_output_use": "Shared UI/backend feed composition and downstream contaminant tracking; this is not a compliance result.",
        "rows": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Literal transcription of reported means, standard deviations, table significance letters and non-detect labels. The connected profile aggregate and wet-basis conversion are recorded separately in connected_calculation; they do not alter the source observations or establish GreenHub compliance.",
        "limitations": [
            "The material is from Białystok, Poland, collected in 2019 during municipal verge maintenance; it is not a Dutch VARTA sample or GreenHub feed calibration.",
            "Fresh means not ensiled in the study. Grass was brought to the laboratory, air-dried 24 h at room temperature and cut to 2–4 cm before preparation/analysis; it is not an as-received wet-feed dataset.",
            "The source states analyses were run in triplicate, but does not establish that these are independent field sites. Analytical n must not be interpreted as spatial replication.",
            "Elemental nitrogen is not crude protein and is not converted to protein. The reported proximate components are not forced to close to 100%.",
            "Metal non-detects are censored observations, not zero; the values do not establish regulatory compliance or contaminant removal in downstream products.",
            "Table 3 ash and sulfur are excluded from this supplemental file because the same source values are already present in the existing feedstock package. Existing Table 1/2/5 and methane-potential extracts are not duplicated.",
            "Only the explicitly listed summer potentially-toxic-element rows contribute to one GreenHub profile proxy. Remaining records are not activated; this proxy does not establish Dutch compliance, chemical speciation, or product quality.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_source_register()
    _update_manifest(len(rows))
    print(f"wrote {len(rows)} reference observations; sha256={digest}")


if __name__ == "__main__":
    main()
