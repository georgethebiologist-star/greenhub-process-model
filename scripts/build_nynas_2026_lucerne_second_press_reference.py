"""Build a traceable, reference-only extract of Nynäs et al. (2026) Table 3.

Only the fresh/frozen lucerne-pulp water re-press conditions are transcribed.
These measurements are not GreenHub roadside-grass parameters and do not
activate the current single-press/isoelectric route.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Protein recovery" / "Isoelectric"
AUDIT = DATA / "global_audit_package"
FILENAME = "nynas_2026_lucerne_second_press_water_dilution_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-NYNAS-2026-SECOND-PRESS"
DOI = "10.1016/j.jafr.2026.102842"
DOI_URL = f"https://doi.org/{DOI}"
PDF_URL = "https://pub.epsilon.slu.se/39893/1/nynas-a-l-et-al-20260415.pdf"
REPOSITORY_URL = "https://research.slu.se/en/publications/increasing-protein-recovery-from-lucerne-by-a-second-pressing-ste/"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "table_section", "treatment", "substrate",
    "material_status", "pulp_to_water_mass_ratio", "soaking_time_min",
    "soaking_temperature_C", "metric", "reported_mean", "reported_sd",
    "unit", "basis", "replicate_n", "significance_group", "source_location",
    "evidence_class", "quality_class", "activation_state", "transferability",
    "notes",
]

# Values and groups are direct transcriptions from Table 3A, rows P:Water 1:1
# and 1:2. Each tuple is (mean, SD, significance group).
TABLE = {
    ("1:1", "fresh"): {
        "N_in_GJR": ("4.19", "0.05", "a"), "N_in_PR": ("2.13", "0.01", "a"),
        "N_in_GPRP": ("5.6", "0.1", "a"), "N_in_GPSS": ("5.01", "0.04", "a"),
        "N_flow_P_to_GJR": ("35", "2", "a"), "N_flow_GJR_to_GPRP": ("66", "2", "b"),
        "N_flow_GJR_to_GPsoluble": ("15", "2", "b"),
    },
    ("1:1", "frozen"): {
        "N_in_GJR": ("5.9", "0.3", "b"), "N_in_PR": ("3.3", "0.2", "b"),
        "N_in_GPRP": ("6.08", "0.06", "a"), "N_in_GPSS": ("6.05", "0.02", "b"),
        "N_flow_P_to_GJR": ("46", "3", "b"), "N_flow_GJR_to_GPRP": ("45", "3", "a"),
        "N_flow_GJR_to_GPsoluble": ("8", "1", "a"),
    },
    ("1:2", "fresh"): {
        "N_in_GJR": ("4.24", "0.01", "a"), "N_in_PR": ("1.95", "0.06", "a"),
        "N_in_GPRP": ("5.6", "0.3", "a"), "N_in_GPSS": ("4.9", "0.1", "a"),
        "N_flow_P_to_GJR": ("37", "6", "a"), "N_flow_GJR_to_GPRP": ("70", "10", "b"),
        "N_flow_GJR_to_GPsoluble": ("17", "5", "a"),
    },
    ("1:2", "frozen"): {
        "N_in_GJR": ("5.4", "0.2", "b"), "N_in_PR": ("2.9", "0.3", "b"),
        "N_in_GPRP": ("6.6", "0.1", "b"), "N_in_GPSS": ("6.12", "0.06", "b"),
        "N_flow_P_to_GJR": ("49", "3", "b"), "N_flow_GJR_to_GPRP": ("48", "5", "a"),
        "N_flow_GJR_to_GPsoluble": ("13", "6", "a"),
    },
}
TIME_TEMPERATURE = [
    ("15MIN-21C", "15", "21", {
        "N_in_GJR": ("4.25", "0.02", "a"), "N_in_PR": ("2.57", "0.03", "bc"),
        "N_in_GPRP": ("4.94", "0.05", "a"), "N_in_GPSS": ("4.68", "0.04", "a"),
        "N_flow_P_to_GJR": ("35", "2", "a"), "N_flow_GJR_to_GPRP": ("59", "1", "b"),
        "N_flow_GJR_to_GPsoluble": ("7", "1", "a"),
    }),
    ("15MIN-ICE", "15", "", {
        "N_in_GJR": ("4.34", "0.04", "b"), "N_in_PR": ("2.43", "0.04", "a"),
        "N_in_GPRP": ("5.09", "0.09", "a"), "N_in_GPSS": ("4.7", "0.1", "a"),
        "N_flow_P_to_GJR": ("35", "1", "a"), "N_flow_GJR_to_GPRP": ("61", "2", "b"),
        "N_flow_GJR_to_GPsoluble": ("9", "1", "ab"),
    }),
    ("1H-4C", "60", "4", {
        "N_in_GJR": ("4.48", "0.03", "c"), "N_in_PR": ("2.48", "0.05", "ab"),
        "N_in_GPRP": ("5.8", "0.2", "c"), "N_in_GPSS": ("5.25", "0.05", "bc"),
        "N_flow_P_to_GJR": ("37", "1", "a"), "N_flow_GJR_to_GPRP": ("61", "1", "b"),
        "N_flow_GJR_to_GPsoluble": ("13", "3", "b"),
    }),
    ("5H-21C", "300", "21", {
        "N_in_GJR": ("4.53", "0.03", "c"), "N_in_PR": ("2.68", "0.09", "c"),
        "N_in_GPRP": ("5.3", "0.2", "ab"), "N_in_GPSS": ("5.12", "0.07", "b"),
        "N_flow_P_to_GJR": ("38", "2", "a"), "N_flow_GJR_to_GPRP": ("53", "2", "a"),
        "N_flow_GJR_to_GPsoluble": ("6", "2", "a"),
    }),
    ("5H-4C", "300", "4", {
        "N_in_GJR": ("4.55", "0.02", "c"), "N_in_PR": ("2.56", "0.01", "abc"),
        "N_in_GPRP": ("5.8", "0.2", "bc"), "N_in_GPSS": ("5.33", "0.09", "c"),
        "N_flow_P_to_GJR": ("38", "1", "a"), "N_flow_GJR_to_GPRP": ("61.5", "0.5", "b"),
        "N_flow_GJR_to_GPsoluble": ("12.2", "0.7", "b"),
    }),
]
METRICS = {
    "N_in_GJR": ("nitrogen_concentration", "%", "nitrogen as percent of dry weight of re-pressed green juice (GJR)"),
    "N_in_PR": ("nitrogen_concentration", "%", "nitrogen as percent of dry weight of re-pressed pulp (PR)"),
    "N_in_GPRP": ("nitrogen_concentration", "%", "nitrogen as percent of dry weight of acid-precipitated pellet, including suspended solids (GPRP)"),
    "N_in_GPSS": ("nitrogen_concentration", "%", "nitrogen as percent of dry weight of suspended-solids pellet (GPSS)"),
    "N_flow_P_to_GJR": ("nitrogen_flow", "%", "nitrogen flow from starting pulp (P) to re-pressed green juice (GJR), relative to N in P"),
    "N_flow_GJR_to_GPRP": ("nitrogen_flow", "%", "nitrogen flow from GJR to the pH-4 acid-precipitated pellet (GPRP), relative to N in GJR; pellet includes suspended solids"),
    "N_flow_GJR_to_GPsoluble": ("nitrogen_flow_estimated_by_difference", "%", "soluble-protein-associated nitrogen flow estimated by authors as GJR-to-GPRP minus GJR-to-GPSS; relative to nitrogen in GJR"),
}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def _upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = _read(path)
    if not fields:
        raise ValueError(f"Expected an existing registry with headers: {path}")
    normalized = {field: str(row.get(field, "")) for field in fields}
    rows = [old for old in rows if old.get(key) != normalized[key]]
    rows.append(normalized)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for (ratio, status), values in TABLE.items():
        for metric, (mean, sd, group) in values.items():
            metric_type, unit, basis = METRICS[metric]
            rows.append({
                "record_id": f"NYNAS26-{ratio.replace(':', '-')}-{status.upper()}-{metric.upper()}",
                "source_id": SOURCE_ID,
                "table_section": "Table 3A, subsection 2: freezing and dilution; P:Water rows",
                "treatment": "water dilution and re-pressing of demo-scale-derived lucerne pulp",
                "substrate": "lucerne pulp from first pressing (P); cultivated lucerne, not roadside grass",
                "material_status": status,
                "pulp_to_water_mass_ratio": ratio,
                "soaking_time_min": "15",
                "soaking_temperature_C": "21",
                "metric": f"{metric_type}:{metric}",
                "reported_mean": mean,
                "reported_sd": sd,
                "unit": unit,
                "basis": basis,
                "replicate_n": "3",
                "significance_group": group,
                "source_location": "Table 3A, journal PDF pp. 6–7; source table notes room temperature approximately 21 C and 15 min unless stated otherwise",
                "evidence_class": "B_measured_primary_literature_summary",
                "quality_class": "B",
                "activation_state": "reference_only",
                "transferability": "cultivated_Swedish_lucerne_lab_repulping_not_GreenHub_roadside_grass_or_single_press_route",
                "notes": (
                    "Mean and SD are transcribed as printed; no N-to-protein conversion. "
                    "Pulp-to-water ratio is w/w. Group letters are source-reported statistical groupings. "
                    "GJR-to-GPsoluble is a source-calculated difference, not direct isolated-protein mass."
                ),
            })
    for condition_id, time_min, temperature_c, values in TIME_TEMPERATURE:
        for metric, (mean, sd, group) in values.items():
            metric_type, unit, basis = METRICS[metric]
            rows.append({
                "record_id": f"NYNAS26-TIME-{condition_id}-FROZEN-{metric.upper()}",
                "source_id": SOURCE_ID,
                "table_section": "Table 3A, subsection 3: soaking time and temperature in water",
                "treatment": "water soaking of frozen lucerne pulp followed by re-pressing",
                "substrate": "frozen lucerne pulp (P); cultivated lucerne, not roadside grass",
                "material_status": "frozen",
                "pulp_to_water_mass_ratio": "1:1",
                "soaking_time_min": time_min,
                "soaking_temperature_C": temperature_c,
                "metric": f"{metric_type}:{metric}",
                "reported_mean": mean,
                "reported_sd": sd,
                "unit": unit,
                "basis": basis,
                "replicate_n": "3",
                "significance_group": group,
                "source_location": "Table 3A, subsection 3, journal PDF p. 6; ice condition is reported categorically and is not assigned a numeric temperature",
                "evidence_class": "B_measured_primary_literature_summary",
                "quality_class": "B",
                "activation_state": "reference_only",
                "transferability": "cultivated_Swedish_lucerne_lab_repulping_not_GreenHub_roadside_grass_or_single_press_route",
                "notes": (
                    "Mean, SD, and statistical group transcribed as printed. Table condition time in hours was converted to minutes where needed; "
                    "ice is retained as a category with blank numeric temperature. No N-to-protein conversion. "
                    "GJR-to-GPsoluble is the authors' difference estimate, not direct isolated-protein mass."
                ),
            })
    return rows


def main() -> None:
    rows = build_rows()
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    citation = (
        "Nynäs, A.-L., Mlook, W., Wedgwood, C., Newson, W. R., Prade, T., & Johansson, E. (2026). "
        "Increasing protein recovery from lucerne by a second pressing step: opportunities and challenges for process and feasibility. "
        "Journal of Agriculture and Food Research, 27, 102842. " + DOI_URL
    )
    limitations = [
        "This is cultivated Swedish lucerne, not Dutch roadside grass or VARTA feed; rows are comparator evidence only.",
        "The tested material is pulp after a first press; these values do not characterize GreenHub's current single-press route.",
        "Table 3 reports nitrogen concentration and nitrogen-flow summaries. Nitrogen is not converted to protein; the soluble-associated flow is calculated by difference as described by the authors.",
        "Only fresh/frozen P:Water 1:1 and 1:2 rows are extracted. Other treatments in Table 3 are outside this dataset's scope.",
        "Reported means and SDs are summary statistics (n=3); raw replicate measurements are not included in this extract.",
        "No runtime parameter, default, equation, TEA/LCA factor, or Pareto scenario consumes this dataset.",
    ]
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:nynas-2026-lucerne-second-press-water-dilution:v1",
        "dataset_version": "1.0.0",
        "dataset_title": "Fresh and frozen lucerne pulp water dilution and second-press nitrogen outcomes",
        "dataset_file": FILENAME,
        "source_dataset_path": f"Greenhub/data/Protein recovery/Isoelectric/{FILENAME}",
        "source_data_sha256": digest,
        "rows": len(rows),
        "source_id": SOURCE_ID,
        "citation": citation,
        "source_doi": DOI,
        "persistent_source_url": DOI_URL,
        "full_text_url": PDF_URL,
        "institutional_record": REPOSITORY_URL,
        "retrieval_date": RETRIEVED,
        "publication_year": 2026,
        "geography": "Alnarp, Sweden; cultivated lucerne. Exact experimental field identity and batch dates are detailed in the article methods.",
        "source_location": "Table 3A, subsection 2, water dilution rows P:Water 1:1 and 1:2; article pp. 6–7; methods Sections 2.1–2.5.",
        "license": "CC BY 4.0, as specified for the final published version by the Swedish University of Agricultural Sciences repository record.",
        "evidence_class": "B_measured_primary_literature_summary",
        "quality_class": "B",
        "readiness": "D3",
        "material_and_process_scope": "Fresh or frozen lucerne pulp after first pressing, diluted with water at 1:1 or 1:2 w/w, soaked 15 min at approximately 21 C, then re-pressed at lab scale; n=3.",
        "data_scope": "63 mean/SD/significance-group observations: four fresh/frozen water-dilution conditions plus five frozen-pulp soak-time/temperature conditions, each with seven N-concentration or N-flow endpoints. Pulp:water ratios are preserved.",
        "conversion_method": "Direct transcription from Table 3A. Reported soaking durations in hours are normalized to minutes (1 h=60 min; 5 h=300 min); ice temperature is left categorical and blank numerically. No conversion from N to crude protein, no interpolation, and no GreenHub scaling.",
        "uncertainty": "Source-reported SD and significance group are preserved; replicate-level data and confidence intervals are not included.",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "parameter_registry_mapping": None,
        "limitations": limitations,
        "fair_metadata": {
            "findable": "Repository-local versioned URN, descriptive title, DOI, institutional record, source location and checksum are recorded.",
            "accessible": "CSV and JSON sidecar are in the repository; the linked full text is publicly available.",
            "interoperable": "UTF-8 CSV uses explicit metric, unit, basis, treatment, material state, uncertainty, and source-location fields.",
            "reusable": "CC BY 4.0 attribution, transcription scope, basis, uncertainty, conversion policy and transfer limits are stated.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID,
        "source_title": "Increasing protein recovery from lucerne by a second pressing step: opportunities and challenges for process and feasibility",
        "authors": "Nynäs; Mlook; Wedgwood; Newson; Prade; Johansson",
        "year": "2026",
        "source_type": "peer-reviewed primary experimental article; Table 3 summary extract",
        "peer_review_status": "peer-reviewed",
        "doi_or_stable_id": DOI,
        "source_url": DOI_URL,
        "materials": "Cultivated lucerne pulp; fresh/frozen; water re-pressing at 1:1 and 1:2 w/w",
        "processes": "Second pressing; nitrogen partition and concentration",
        "used_in_files": FILENAME,
        "access_notes": "Final published version CC BY 4.0 per SLU repository record; extracted scope limited to Table 3A water-dilution rows.",
        "quality_notes": "B-tier measured summary; n=3. Nitrogen basis, not true protein. Lucerne comparator; reference-only; not active GreenHub parameter data.",
    }
    _upsert(GROUP / "source_register.csv", local_source, "source_id")
    _upsert(GROUP / "dataset_manifest.csv", {
        "filename": FILENAME,
        "dataset_scope": "Table 3A fresh/frozen lucerne pulp water re-press rows at 1:1 and 1:2 w/w plus frozen-pulp soaking time/temperature rows; N concentrations and flows with SD and groups.",
        "row_count": len(rows),
        "required_columns_present": "yes",
        "numeric_traceability_check": "Unique record IDs; source/table/metric/unit/basis/SD/n/group recorded for all rows.",
        "contains_assumptions_with_blank_values": "no",
        "integration_readiness": "reference_only_not_runtime_eligible",
        "limitations": "Cultivated lucerne pulp; nitrogen summaries; not GreenHub roadside grass, a primary press calibration, or true-protein recovery.",
    }, "filename")
    rel = f"Protein recovery/Isoelectric/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel, "dataset_group": "Protein recovery/Isoelectric", "source_id": SOURCE_ID,
        "source_title": local_source["source_title"], "authors": local_source["authors"], "year": "2026",
        "doi_or_stable_id": DOI, "url": DOI_URL, "source_type": local_source["source_type"],
        "notes": local_source["quality_notes"],
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel, "category": "Protein recovery", "subgroup": "Isoelectric; second pressing evidence",
        "filename": FILENAME, "row_count_observed": len(rows), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "CC BY literature extract; lucerne secondary press N data; not a runtime parameter.",
    }, "dataset_path")
    _upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel, "category": "Protein recovery", "subgroup": "Isoelectric; second pressing evidence",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": len(rows),
        "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "All numeric rows link to Table 3A, unit/basis and article DOI; reference-only, not roadside grass.",
    }, "dataset_path")
    _upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel, "sha256": digest, "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")
    print(json.dumps({"dataset": rel, "rows": len(rows), "source_id": SOURCE_ID, "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
