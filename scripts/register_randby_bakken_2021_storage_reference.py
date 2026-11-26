"""Register low-dry-matter grass silage outcomes from Randby & Bakken (2021).

This source is a Norwegian cultivated grass-clover storage comparator. The
extract is reference-only and must not activate GreenHub storage defaults.
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
FILENAME = "grass_silage_storage_system_losses_randby_bakken_2021_reference.csv"
CSV_PATH = FOLDER / FILENAME
SOURCE_ID = "SRC-RANDBY-BAKKEN-GRASS-SILAGE-2021"
TITLE = "Bunkers or round bales: Losses and silage quality with or without acid treatment of low dry matter grass crops"
AUTHORS = "Å.T. Randby; A.K. Bakken"
DOI = "10.1016/j.anifeedsci.2021.114868"
URL = f"https://doi.org/{DOI}"
FULL_TEXT_URL = (
    "https://www.researchgate.net/publication/349116084_"
    "Bunkers_or_round_bales_Losses_and_silage_quality_with_or_without_acid_treatment_of_low_dry_matter_grass_crops"
)
RETRIEVED = "2026-11-08"

FIELDS = [
    "observation_id", "source_id", "table", "aggregation", "harvest",
    "silo_type", "additive", "sealing", "additive_target_l_per_t",
    "replicate_count", "storage_duration_days", "measurement", "value",
    "standard_error", "uncertainty_statistic", "unit", "basis",
    "source_location", "evidence_class", "quality_class", "activation_state",
    "limitations",
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
    key_columns = key.split("|")
    indexed = {tuple(row.get(column, "") for column in key_columns): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(column, "") for column in key_columns)
        if identity in indexed:
            indexed[identity].update(entry)
        else:
            rows.append(entry)
            indexed[identity] = rows[-1]
    _write(path, fields or list(entries[0]), rows)
    return rows


def _table3_records() -> list[dict[str, str]]:
    # Table 3 reports treatment means pooled over three 2017 harvests. The
    # order of each tuple is offered, wasted, and invisible loss, first per kg
    # fresh crop and then per kg crop DM. SEMs are group-level values printed
    # below the table, applied consistently to rows in that silo group.
    treatments = [
        ("BUNKER-C", "bunker", "untreated", "not_applicable", 3,
         (852, 25.8, 122), (829, 25.0, 146), "bunker"),
        ("BUNKER-A", "bunker", "acid_treated", "not_applicable", 3,
         (814, 26.0, 160), (837, 26.9, 136), "bunker"),
        ("BALE-C-IMM", "round_bale", "untreated", "immediate", 9,
         (918, 0.2, 82.0), (931, 0.2, 68.6), "bale"),
        ("BALE-C-DEL", "round_bale", "untreated", "delayed", 9,
         (914, 2.0, 84.4), (916, 2.0, 82.0), "bale"),
        ("BALE-A-IMM", "round_bale", "acid_treated", "immediate", 9,
         (898, 0.2, 102), (939, 0.3, 61.1), "bale"),
        ("BALE-A-DEL", "round_bale", "acid_treated", "delayed", 9,
         (892, 0.0, 108), (923, 0.0, 76.9), "bale"),
        ("LAB-C-IMM", "laboratory_silo", "untreated", "immediate", 9,
         (992, 0, 8.2), (934, 0, 65.9), "lab"),
        ("LAB-C-DEL", "laboratory_silo", "untreated", "delayed", 9,
         (988, 0, 12.0), (913, 0, 87.3), "lab"),
        ("LAB-A-IMM", "laboratory_silo", "acid_treated", "immediate", 9,
         (994, 0, 6.4), (937, 0, 62.8), "lab"),
        ("LAB-A-DEL", "laboratory_silo", "acid_treated", "delayed", 9,
         (991, 0, 9.5), (941, 0, 59.5), "lab"),
    ]
    measurements = ("offered_silage", "wasted_silage", "invisible_losses")
    sems = {
        "bunker": ((29.6, 1.63, 29.8), (27.3, 1.56, 27.3)),
        "bale": ((17.1, 0.94, 17.2), (15.8, 0.90, 15.8)),
        "lab": ((17.1, 0.94, 17.2), (15.8, 0.90, 15.8)),
    }
    rows: list[dict[str, str]] = []
    for treatment_id, silo, additive, sealing, n, fresh, dry, sem_group in treatments:
        for basis_id, values, sem_values, unit, basis in (
            ("FW", fresh, sems[sem_group][0], "g/kg crop", "initial_crop_fresh_mass"),
            ("DM", dry, sems[sem_group][1], "g/kg crop DM", "initial_crop_dry_matter"),
        ):
            for metric, value, sem in zip(measurements, values, sem_values, strict=True):
                rows.append({
                    "observation_id": f"RB21-T3-{treatment_id}-{metric.upper()}-{basis_id}",
                    "source_id": SOURCE_ID,
                    "table": "3",
                    "aggregation": "treatment_mean_pooled_over_three_harvests",
                    "harvest": "all_three_2017_harvests",
                    "silo_type": silo,
                    "additive": additive,
                    "sealing": sealing,
                    "additive_target_l_per_t": "4" if additive == "acid_treated" else "0",
                    "replicate_count": str(n),
                    "storage_duration_days": "",
                    "measurement": metric,
                    "value": str(value),
                    "standard_error": str(sem),
                    "uncertainty_statistic": "SEM_group_level_as_reported",
                    "unit": unit,
                    "basis": basis,
                    "source_location": "Table 3, printed page 6; Table 3 note 3 for bale effluent correction; Methods §2.3 for additive application",
                    "evidence_class": "B_measured_literature",
                    "quality_class": "B",
                    "activation_state": "reference_only",
                    "limitations": (
                        "Cultivated Norwegian grass-clover, not roadside/VARTA grass. Three harvests in 2017; storage opening duration is not reported as a common numeric value. "
                        "Invisible losses combine respiration, effluent, fermentation, aerobic deterioration and gaseous losses; component pathways are not separated. "
                        "Round-bale values use an estimated effluent correction; exact additive dose differed among bale harvests. Not a GreenHub default or runtime calibration."
                    ),
                })
    return rows


def _extra_records() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for harvest, value in ((1, 194), (2, 186), (3, 213)):
        rows.append({
            "observation_id": f"RB21-ABSTRACT-H{harvest}-LOW-CROP-DM",
            "source_id": SOURCE_ID, "table": "Abstract", "aggregation": "reported_low_crop_DM_for_harvest",
            "harvest": f"H{harvest}_2017", "silo_type": "all", "additive": "not_stratified",
            "sealing": "not_applicable", "additive_target_l_per_t": "", "replicate_count": "",
            "storage_duration_days": "", "measurement": "crop_dry_matter_low_observation",
            "value": str(value), "standard_error": "", "uncertainty_statistic": "not_reported",
            "unit": "g DM/kg fresh crop", "basis": "fresh_crop_mass",
            "source_location": "Abstract; also Methods §2.1 for three 2017 harvest dates",
            "evidence_class": "B_measured_literature", "quality_class": "B", "activation_state": "reference_only",
            "limitations": "Source wording is 'crop DM as low as'; retain as a reported low observation, not a harvest mean or a GreenHub seasonal-feed value.",
        })
    for silo, wet_density, dm_density in (
        ("round_bale", 531, 111), ("bunker", 833, 164),
    ):
        for measurement, value, unit, basis in (
            ("silage_density_wet_mass", wet_density, "kg/m3", "silage_wet_volume"),
            ("silage_density_dry_matter", dm_density, "kg DM/m3", "silage_volume"),
        ):
            rows.append({
                "observation_id": f"RB21-ABSTRACT-{silo.upper()}-{measurement.upper()}",
                "source_id": SOURCE_ID, "table": "Abstract", "aggregation": "reported_silo_type_comparison",
                "harvest": "pooled_or_averaged_as_reported", "silo_type": silo,
                "additive": "not_stratified", "sealing": "not_stratified",
                "additive_target_l_per_t": "", "replicate_count": "", "storage_duration_days": "",
                "measurement": measurement, "value": str(value), "standard_error": "",
                "uncertainty_statistic": "not_reported", "unit": unit, "basis": basis,
                "source_location": "Abstract",
                "evidence_class": "B_measured_literature", "quality_class": "B", "activation_state": "reference_only",
                "limitations": "Source abstract reports the bunker-versus-bale comparison but not uncertainty or the exact pooled strata; do not interpret as a GreenHub storage design value.",
            })
    return rows


def main() -> None:
    records = _extra_records() + _table3_records()
    if CSV_PATH.exists():
        _, existing = _read(CSV_PATH)
    else:
        existing = []
    known = {row.get("observation_id", "") for row in existing}
    existing.extend(row for row in records if row["observation_id"] not in known)
    _write(CSV_PATH, FIELDS, existing)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()

    metadata = {
        "dataset_id": "urn:greenhub:dataset:storage:randby-bakken-low-dm-grass-silage-storage-2021:v1",
        "persistent_identifier_status": "Repository-local stable identifier for this CSV transcription; the cited article has DOI 10.1016/j.anifeedsci.2021.114868.",
        "dataset_version": "1.0.0",
        "source_file": FILENAME,
        "title": "Low-dry-matter grass-clover silage storage losses, density and crop DM reference observations",
        "citation": "Randby, Å.T., & Bakken, A.K. (2021). Bunkers or round bales: Losses and silage quality with or without acid treatment of low dry matter grass crops. Animal Feed Science and Technology, 275, 114868. https://doi.org/10.1016/j.anifeedsci.2021.114868",
        "persistent_identifier": f"doi:{DOI}",
        "source_url": URL,
        "full_text_url": FULL_TEXT_URL,
        "source_locations": ["Abstract: crop dry matter, density and pooled loss comparisons", "Table 3, printed page 6: treatment-level offered/wasted/invisible loss means and group SEM", "Methods §§2.1–2.3: site, harvests, additive and sealing conditions"],
        "retrieval_date": RETRIEVED,
        "reference_year": 2021,
        "experiment_year": 2017,
        "geography": "Animal Production Experimental Centre, Ås, Norway (59°40′N, 10°47′E).",
        "evidence_class": "B_measured_literature",
        "license": "The open-access article states it is distributed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Attribution retained; this extract is limited to source-reported factual data.",
        "material_scope": "Cultivated grass-clover crops harvested in three 2017 harvests; bunker silos, round bales and laboratory-scale silos. Not Dutch roadside grass or GreenHub/VARTA feed.",
        "experimental_conditions": "Crop DM lows reported for H1/H2/H3 were 194/186/213 g DM/kg fresh crop. The study used a formic- and propionic-acid-based additive at a 4 L/t target. Bales were wrapped immediately or after delays; delayed bales had harvest-average delays of 16.7, 8.3 and 18.2 h (H1–H3), with individual delays from 3.5 to 25.9 h. Table 3 treatment means are pooled over harvests; N=3 for bunker observations and N=9 for bale/laboratory-silo observations. Table-reported SEM values are group-level. Bale mass-loss calculations include the paper's estimated effluent correction.",
        "data_scope": f"{len(existing)} long-form records: abstract-reported crop-DM lows, wet and DM density comparisons by silo type, and Table 3 offered silage, wasted silage and invisible loss means for 10 silo/additive/sealing treatments on fresh-crop and initial-crop-DM bases.",
        "limitations": [
            "Reference-only literature comparator; not a GreenHub default, roadside-grass calibration or runtime input.",
            "Cultivated Norwegian grass-clover and farm/pilot storage equipment differ from Dutch roadside/VARTA material and GreenHub storage configurations.",
            "The abstract crop-DM figures are described as low observations, not harvest means; uncertainty is not reported for these values.",
            "Table 3 treatment means are pooled over three harvests. The paper does not provide one common numeric storage duration for the pooled observations; no storage-day kinetics are inferred.",
            "Invisible losses combine respiration, effluent, fermentation, aerobic deterioration and gaseous losses; the source does not partition these components.",
            "Round-bale losses use an estimated correction for unmeasured effluent. This estimate can overstate losses according to the authors.",
            "The 4 L/t additive value is a target. Actual bale dosage varied by harvest (5.0, 4.3 and 3.1 L/t). No chemical demand is inferred for GreenHub.",
            "Abstract density comparisons lack uncertainty and do not expose all pooling strata.",
        ],
        "conversion_or_processing": "Direct transcription of source-reported values and units. No conversion, interpolation, component-loss allocation, kinetic fitting or imputation. Table 3 group-level SEMs are retained as printed.",
        "uncertainty": "Table 3 SEMs are recorded for each outcome using the source's bunker versus bale/laboratory group SEM. Exact uncertainty for abstract-level crop-DM lows and density contrasts is not reported.",
        "activation_state": "reference_only",
        "fair_metadata": {
            "findable": "Local versioned URN, article DOI, citation, source and table locations recorded.",
            "accessible": "Publisher DOI landing page and author-posted full text linked; retrieval date recorded.",
            "interoperable": "UTF-8 long-form CSV with explicit silo type, additive, sealing, measurement, unit and mass basis fields.",
            "reusable": "Article CC BY 4.0 status, attribution, extraction method, uncertainty and transferability limits recorded.",
        },
    }
    sidecar_path = CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json")
    sidecar_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source_path = FOLDER / "source_register.csv"
    source_rows = _upsert(source_path, "source_id", [{
        "source_id": SOURCE_ID, "source_title": TITLE, "authors": AUTHORS, "year": "2021",
        "source_type": "peer-reviewed open-access primary experimental article",
        "doi_or_stable_identifier": DOI, "stable_url": URL,
        "material": "Cultivated grass-clover ensiled in bunkers, round bales and laboratory silos; Ås, Norway; 2017",
        "quality_notes": "Table 3 reports fresh-crop and initial-DM-based offered silage, wasted silage and invisible storage-loss means for 10 treatment configurations, plus group SEMs. Abstract reports low crop-DM values and silo density comparisons. CC BY 4.0. Bale values include an estimated effluent correction. Reference-only; not roadside/VARTA or GreenHub calibration.",
        "accessed_date": RETRIEVED,
    }])
    source_fields, _ = _read(source_path)
    source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [
        {"filename": FILENAME,
         "description": "Randby & Bakken (2021) abstract and Table 3 storage outcomes for low-DM cultivated grass-clover across bunker, bale and laboratory silos; reference-only.",
         "row_count": str(len(existing)), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
         "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "observation_id"},
        {"filename": "source_register.csv",
         "description": "Local bibliographic and dataset provenance register for staged Phase 1–7 evidence.",
         "row_count": str(len(source_rows)), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
         "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "source_id"},
    ])

    rel = f"storage/{FILENAME}"
    source_rel = "storage/source_register.csv"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": source_rel, "dataset_group": "storage", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": AUTHORS, "year": "2021",
        "doi_or_stable_id": DOI, "url": URL,
        "source_type": "peer-reviewed open-access primary experimental article",
        "notes": "CC BY 4.0. Table 3 storage-loss means and SEMs; cultivated Norwegian grass-clover comparator, not roadside/VARTA calibration. Bale loss includes estimated effluent correction. Reference-only.",
    }])
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [
        {"dataset_path": rel, "category": "storage", "subgroup": "storage",
         "filename": FILENAME, "row_count_observed": str(len(existing)), "header_count": str(len(FIELDS)),
         "headers": "; ".join(FIELDS), "standardized_status_values": "reported; reference_only",
         "detected_readiness": "D3",
         "notes": "Source-linked, units/bases recorded, but reference-only due material/system transferability and lack of GreenHub calibration."},
        {"dataset_path": source_rel, "category": "storage", "subgroup": "storage",
         "filename": "source_register.csv", "row_count_observed": str(len(source_rows)),
         "header_count": str(len(source_fields)), "headers": "; ".join(source_fields),
         "detected_readiness": "D3", "notes": "Bibliographic metadata index; evidence remains reference-only unless separately activated after validation."},
    ])
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", [
        {"dataset_path": rel, "sha256": digest, "byte_size": str(CSV_PATH.stat().st_size)},
        {"dataset_path": source_rel, "sha256": source_digest, "byte_size": str(source_path.stat().st_size)},
    ])
    _upsert(AUDIT / "dataset_activation_matrix.csv", "dataset_path", [{
        "dataset_path": rel, "category": "storage", "subgroup": "Phase 2 storage",
        "audit_readiness": "D3", "integration_eligibility": "reference_only",
        "default_eligibility": "False", "calculation_connected": "False", "active": "False",
        "source_issue_count": "0", "quarantine_row_count": "0", "issue_types": "none",
        "cost_pathway_status": "not_applicable",
        "selection_reason": "Traceable measured literature comparator, but not matched to Dutch roadside grass or GreenHub storage conditions.",
        "required_action": "Obtain paired GreenHub storage inventory and composition/emission measurements before parameter activation.",
        "source_checksum_sha256": digest,
    }, {
        "dataset_path": source_rel, "source_checksum_sha256": source_digest,
    }])

    print(f"rows={len(existing)} registered={len(records)} sha256={digest}")


if __name__ == "__main__":
    main()
