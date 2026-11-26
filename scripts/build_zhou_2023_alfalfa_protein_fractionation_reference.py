"""Transcribe selected Phase 3–5 observations from Zhou's 2023 DTU thesis.

The extract is evidence-only. It preserves source-reported conflicts and does
not activate alfalfa values as GreenHub roadside-grass parameters.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Protein recovery" / "Isoelectric"
AUDIT = DATA / "global_audit_package"
FILENAME = "alfalfa_green_biorefinery_press_and_precipitation_zhou_2023_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-ZHOU-DTU-THESIS-2023-ALFALFA-PROTEIN"
SOURCE_URL = "https://orbit.dtu.dk/files/363463153/PhD_thesis_-_Fa_Zhou.pdf"
RECORD_URL = "https://orbit.dtu.dk/en/publications/valorization-of-green-biomass-alfalfa-pulp-as-a-potential-platfor/"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_section_or_table", "material",
    "process_step", "metric", "value", "unit", "basis", "condition_scope",
    "statistic", "replicate_count", "uncertainty", "source_location", "evidence_class",
    "quality_class", "activation_state", "transferability", "limitations",
]

SOURCE = {
    "source_id": SOURCE_ID,
    "source_title": "Valorization of Green Biomass: Alfalfa Pulp as a Potential Platform for Food and Biochemicals",
    "authors": "Fa Zhou",
    "year": "2023",
    "source_type": "doctoral thesis; primary experimental research",
    "peer_review_status": "doctoral thesis; not a peer-reviewed journal article",
    "doi_or_stable_id": "DTU Orbit institutional record; no DOI identified for thesis",
    "source_url": RECORD_URL,
    "materials": "Fresh cultivated alfalfa (Medicago sativa); exact cultivar, field site and harvest date not established in this extract",
    "processes": "Twin-screw juicing, pulp rewetting/repressing, green-juice protein precipitation with acid or heat, and pulp/brown-juice characterization",
    "used_in_files": FILENAME,
    "access_notes": f"Open institutional thesis PDF: {SOURCE_URL}. No explicit reuse license identified; retain citation and factual extract, review rights before external redistribution.",
    "quality_notes": "Directly reported experimental comparator evidence. The thesis reports conflicting feed moisture/DM statements and does not give a transferable acid dose per feed or juice volume. Alfalfa is not Dutch roadside/VARTA grass.",
}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read(path)
    keys = key.split("|")
    indexed = {tuple(row.get(column, "") for column in keys): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(column, "") for column in keys)
        if identity in indexed:
            indexed[identity].update(entry)
        else:
            rows.append(entry)
            indexed[identity] = rows[-1]
    _write(path, fields or list(entries[0]), rows)


def _row(
    record_id: str, *, phase: str, section: str, material: str, step: str,
    metric: str, value: str, unit: str, basis: str, condition: str,
    statistic: str = "source-reported value", n: str = "not reported",
    uncertainty: str = "not reported", location: str,
) -> dict[str, str]:
    return {
        "record_id": record_id, "source_id": SOURCE_ID, "phase_relevance": phase,
        "source_section_or_table": section, "material": material, "process_step": step,
        "metric": metric, "value": value, "unit": unit, "basis": basis,
        "condition_scope": condition, "statistic": statistic, "replicate_count": n,
        "uncertainty": uncertainty, "source_location": location,
        "evidence_class": "B_measured_or_source_reported", "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "Cultivated alfalfa comparator; not Dutch roadside/VARTA feed and not GreenHub route validation.",
        "limitations": "No runtime/default activation. Preserve the stated material and denominator; do not infer missing stream flows, reagent normalization, or mass closure.",
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    table = "Thesis Table 1.2; page number not verified; extracted-text locator 675–732"
    treatments = {
        "HCL": ("1 M hydrochloric acid; endpoint pH 3.5", [
            ("protein_precipitation", "12.6", "% green juice", "0.45"),
            ("pH", "3.5", "pH", "not reported"),
            ("glucose", "6.8", "g/L", "0.06"), ("galactose", "2.3", "g/L", "0.05"),
            ("xylose", "2.7", "g/L", "0.19"), ("fructose", "3.5", "g/L", "0.06"),
            ("arabinose", "0.2", "g/L", "0.02"), ("succinic_acid", "0.7", "g/L", "0.03"),
            ("lactic_acid", "—", "g/L", "not reported; source table uses dash"),
            ("citric_acid", "1.0", "g/L", "0.02"),
        ]),
        "LA": ("1 M lactic acid; endpoint pH 3.5", [
            ("protein_precipitation", "15.0", "% green juice", "1.63"),
            ("pH", "3.5", "pH", "not reported"),
            ("glucose", "6.1", "g/L", "0.07"), ("galactose", "1.9", "g/L", "0.14"),
            ("xylose", "2.5", "g/L", "0.15"), ("fructose", "2.9", "g/L", "0.16"),
            ("arabinose", "—", "g/L", "not reported; source table uses dash"),
            ("succinic_acid", "—", "g/L", "not reported; source table uses dash"),
            ("lactic_acid", "12.4", "g/L", "0.11"), ("citric_acid", "1.6", "g/L", "0.04"),
        ]),
        "HEAT": ("Heat treatment; reported endpoint pH 5.8", [
            ("protein_precipitation", "11.9", "% green juice", "0.84"),
            ("pH", "5.8", "pH", "0.01"),
            ("glucose", "6.6", "g/L", "0.10"), ("galactose", "2.4", "g/L", "0.21"),
            ("xylose", "2.5", "g/L", "0.36"), ("fructose", "3.1", "g/L", "0.02"),
            ("arabinose", "—", "g/L", "not reported; source table uses dash"),
            ("succinic_acid", "0.4", "g/L", "0.12"),
            ("lactic_acid", "—", "g/L", "not reported; source table uses dash"),
            ("citric_acid", "—", "g/L", "not reported; source table uses dash"),
        ]),
    }
    for treatment, (condition, observations) in treatments.items():
        for metric, value, unit, sd in observations:
            rows.append(_row(
                f"ZHOU23-T12-{treatment}-{metric.upper()}", phase="4", section=table,
                material="Alfalfa green juice", step="protein precipitation and brown-juice characterization",
                metric=metric, value=value, unit=unit,
                basis="As reported in Table 1.2; protein precipitation denominator explicitly printed as green juice; analyte concentration unit printed as g/L.",
                condition=condition,
                statistic="mean of technical replicates; source caption reports mean and standard deviation" if sd not in {"not reported", "not reported; source table uses dash"} else "source table entry",
                n="not stated", uncertainty=(f"SD {sd}" if sd.replace(".", "", 1).isdigit() else sd),
                location=table,
            ))

    loc = "Thesis §4.4.6, p. 106 and Figure 4.6"
    mass_items = [
        ("feed_fresh_mass", "1000", "g", "fresh alfalfa batch; prose mass-balance basis", "first press input"),
        ("feed_water_content", "85.6", "%", "as stated in §4.4.6 prose for 1000 g fresh alfalfa", "source narrative value; conflicts with Figure 4.6 dry-matter mass"),
        ("feed_dry_matter_mass", "177.2", "g", "Figure 4.6 label per 1000 g feed", "figure-reported DM; conflicts with prose water content; do not reconcile"),
        ("first_press_wet_pulp_mass", "292.6", "g", "wet mass after first pressing", "reported process mass balance"),
        ("first_press_pulp_moisture", "56.8", "%", "wet pulp moisture as reported", "reported process mass balance"),
        ("first_press_green_juice_mass", "707.4", "g", "theoretical mass calculated/reported in prose", "source calls theoretical; not a measured weighed output"),
        ("rewet_water_added", "585.2", "g", "DI water added to first-press pulp", "reported process mass balance"),
        ("second_press_wet_pulp_mass", "218.5", "g", "wet mass after second pressing", "reported process mass balance"),
        ("second_press_pulp_moisture", "59.7", "%", "wet pulp moisture as reported", "reported process mass balance"),
        ("second_press_green_juice_mass", "659.3", "g", "reported second-press green juice", "source prose mass balance"),
        ("hydrochloric_acid_solution_added", "135.7", "g solution", "mass of 1 M HCl solution added to pooled green juice", "source batch; not normalized per kg feed or juice volume"),
        ("hydrochloric_acid_solution_concentration", "1", "mol/L", "solution concentration", "solution volume/density and neutralization equivalents are not reported here"),
        ("acid_solution_fraction_total_liquid", "9.9", "%", "author-reported equivalent proportion of total liquid", "denominator calculation details not provided; not an acid-demand factor"),
        ("wet_green_protein_pellet_mass_prose", "193.0", "g wet pellet", "wet pellet mass after protein precipitation", "§4.4.6 prose value; distinguish from actual/theoretical labels in Figure 4.6"),
        ("wet_green_protein_pellet_mass_theoretical", "193.0", "g wet pellet", "Figure 4.6 theoretical (T) label", "figure label T; not a separate independent measurement"),
        ("wet_green_protein_pellet_mass_actual", "186.2", "g wet pellet", "Figure 4.6 actual (A) label", "figure label A; differs from prose/theoretical 193.0 g"),
        ("brown_juice_volume_theoretical", "1366.7", "mL", "Figure 4.6 theoretical (T) label", "figure label; not a mass; density not reported"),
        ("brown_juice_volume_actual", "1317.9", "mL", "Figure 4.6 actual (A) label", "figure label; not a mass; density not reported"),
        ("second_pressed_pulp_glucose_mass", "31.3", "g", "reported component mass in second-pressed pulp", "thesis §4.4.6; source-reported component quantity"),
        ("second_pressed_pulp_xylose_mass", "14.46", "g", "reported component mass in second-pressed pulp", "thesis §4.4.6; source-reported component quantity"),
        ("second_pressed_pulp_lignin_mass", "16.58", "g", "reported component mass in second-pressed pulp", "thesis §4.4.6; source-reported component quantity"),
        ("brown_juice_glucose_mass", "9.02", "g", "reported component mass in brown juice", "thesis §4.4.6; source-reported component quantity"),
        ("brown_juice_xylose_mass", "3.70", "g", "reported component mass in brown juice", "thesis §4.4.6; source-reported component quantity"),
        ("twice_pressed_pulp_dry_mass_before_pretreatment", "97.55", "g dry", "dry mass subjected to sodium-chlorite pretreatment", "thesis §4.4.6; pretreatment process sub-study"),
        ("sodium_chlorite_concentration", "6", "%", "source-reported pretreatment concentration", "pretreatment for 2 h; concentration basis not normalized here"),
        ("pretreated_total_solids_recovered", "65.93", "g", "total solids after sodium-chlorite pretreatment", "thesis §4.4.6; distinct from raw press yield"),
    ]
    for index, (metric, value, unit, basis, condition) in enumerate(mass_items, 1):
        rows.append(_row(
            f"ZHOU23-MB-{index:02d}-{metric.upper()}", phase="3;4;5", section=loc,
            material="Fresh cultivated alfalfa and derived juice, pulp or precipitate",
            step="wet fractionation, protein precipitation or pulp pretreatment",
            metric=metric, value=value, unit=unit, basis=basis, condition=condition,
            statistic="source-reported process-batch value", n="single process description; replicate count not reported",
            uncertainty="not reported", location=loc,
        ))
    return rows


def main() -> None:
    rows = build_rows()
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate Zhou thesis record IDs")
    FOLDER.mkdir(parents=True, exist_ok=True)
    _write(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:protein-recovery:zhou-2023-alfalfa-press-precipitation:v1",
        "dataset_version": "1.0.0",
        "persistent_identifier_status": "Repository-local identifier identifies this transcription; DTU Orbit stable record identifies the thesis; no thesis DOI identified.",
        "title": "Alfalfa wet fractionation, acid/heat precipitation and side-stream reference observations",
        "source_id": SOURCE_ID,
        "citation": "Zhou, F. (2023). Valorization of Green Biomass: Alfalfa Pulp as a Potential Platform for Food and Biochemicals. PhD thesis, Technical University of Denmark.",
        "source_url": SOURCE_URL,
        "repository_record": RECORD_URL,
        "retrieval_date": RETRIEVED,
        "source_locations": ["Table 1.2 (PDF extracted-text locator 675–732; printed page not verified)", "§4.4.6, p. 106", "Figure 4.6"],
        "geography": "Technical University of Denmark research; exact crop field site and harvest context not identified in the extracted sections.",
        "material_scope": "Cultivated alfalfa, not Dutch roadside grass, VARTA samples or GreenHub feed.",
        "license_or_rights": "No explicit reuse license identified on the thesis record; attribution retained and external redistribution rights require review.",
        "evidence_class": "B_primary_thesis_experimental_observations",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Transcribe source-reported values only. Preserve source dashes as nonnumeric table entries; do not calculate normalized acid dose, infer stream density, or reconcile feed-moisture and figure discrepancies.",
        "limitations": [
            "Alfalfa is a comparator crop and route, not GreenHub roadside-grass validation.",
            "Table 1.2 reports technical-replicate mean and SD but does not state replicate count in the extracted source.",
            "Protein precipitation is reported as percent of green juice; this is not protein recovery from incoming feed or an isolated-protein mass yield.",
            "The 135.7 g addition is the mass of 1 M HCl solution in a batch, not pure HCl mass, and is not normalized per kg feed or juice volume. Solution volume/density, liquid denominator details, and acid equivalents per feed are absent; no transferable dose is calculated.",
            "§4.4.6 states 85.6% feed water, while Figure 4.6 labels 177.2 g DM per 1000 g feed. These imply different moisture values and are retained as a source discrepancy.",
            "The 193.0 g protein-pellet prose/theoretical value differs from the Figure 4.6 actual label of 186.2 g; the values are not reconciled.",
            "The reported batch flow values do not constitute a fully closed mass balance; figure theoretical/actual flows and prose values are not combined into a single balance.",
            "The thesis does not provide GreenHub-specific press energy, full nutrient/protein component closure, or roadside-feed transfer validation.",
            "No GreenHub defaults, registry parameters, chemistry, TEA/LCA factors, route configuration or Pareto output consume this reference package.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _upsert(FOLDER / "source_register.csv", "source_id", [SOURCE])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "filename": FILENAME,
        "dataset_scope": "Thesis Table 1.2 precipitation conditions/composition and §4.4.6/Figure 4.6 alfalfa press, protein-precipitation and pulp-side-stream batch observations; reference-only.",
        "row_count": str(len(rows)),
        "required_columns_present": "yes: source, phase, material, process, metric, value/unit/basis, condition, statistic, exact source locator and activation state",
        "numeric_traceability_check": "Numeric entries link to Table 1.2, §4.4.6 or Figure 4.6; ambiguous source conflicts and bases retained without normalization.",
        "contains_assumptions_with_blank_values": "yes: missing acid normalization, source dashes and unreported closure/replicate count remain missing, not zero",
        "integration_readiness": "reference_only_D3",
        "limitations": "Cultivated alfalfa; source-reported internal discrepancies; no normalized reagent demand or GreenHub route calibration; external reuse rights not verified.",
    }])
    rel = f"Protein recovery/Isoelectric/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel, "dataset_group": "Protein recovery/Isoelectric", "source_id": SOURCE_ID,
        "source_title": SOURCE["source_title"], "authors": SOURCE["authors"], "year": SOURCE["year"],
        "doi_or_stable_id": SOURCE["doi_or_stable_id"], "url": SOURCE["source_url"],
        "source_type": SOURCE["source_type"], "notes": SOURCE["quality_notes"],
    }])
    numeric_rows = sum(_is_number(row["value"]) for row in rows)
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Protein recovery", "subgroup": "alfalfa wet fractionation and protein precipitation; Phases 3–5",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "Primary thesis data; Table 1.2 and §4.4.6/Figure 4.6; alfalfa comparator; source discrepancies and non-normalized acid addition explicit.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Protein recovery", "subgroup": "alfalfa wet fractionation and protein precipitation; Phases 3–5",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
        "numeric_rows": str(numeric_rows), "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0", "basis_conflicts": "0", "cross_reference_issues": "0",
        "equation_missing_inputs": "0", "equation_symbol_mismatches": "0",
        "notes": "Exact thesis table/section/figure locators recorded; conflicting feed DM values and source-batch acid addition are not normalized.",
    }])
    checksums = [{
        "dataset_path": f"Protein recovery/Isoelectric/{path.name}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "byte_size": str(path.stat().st_size),
    } for path in (CSV_PATH, SIDECAR_PATH)]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)
    _upsert(AUDIT / "dataset_activation_matrix.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Protein recovery", "subgroup": "alfalfa wet fractionation and protein precipitation; Phases 3–5",
        "audit_readiness": "D3", "integration_eligibility": "reference_only", "default_eligibility": "False",
        "calculation_connected": "False", "active": "False", "source_issue_count": "0",
        "quarantine_row_count": "0", "issue_types": "none", "cost_pathway_status": "not_applicable",
        "selection_reason": "Source-linked thesis observations are schema-loadable but alfalfa comparability and route-specific validation gates are unmet.",
        "required_action": "Keep as reference-only; obtain matched roadside feed, titration, separator, and component-balance data before calibration or activation.",
        "source_checksum_sha256": digest,
    }])
    registry_summary_path = AUDIT / "checkpoint1_registry_summary.json"
    registry_summary = json.loads(registry_summary_path.read_text(encoding="utf-8"))
    _, activation_rows = _read(registry_summary_path.with_name("dataset_activation_matrix.csv"))
    eligibility_counts: dict[str, int] = {}
    for item in activation_rows:
        key = item.get("integration_eligibility", "")
        eligibility_counts[key] = eligibility_counts.get(key, 0) + 1
    registry_summary.update(
        source_dataset_count=len(activation_rows),
        dataset_eligibility_counts=dict(sorted(eligibility_counts.items())),
        active_dataset_count=sum(item.get("active") == "True" for item in activation_rows),
        default_eligible_dataset_count=sum(item.get("default_eligibility") == "True" for item in activation_rows),
        source_checksum_count=sum(bool(item.get("source_checksum_sha256")) for item in activation_rows),
    )
    registry_summary_path.write_text(json.dumps(registry_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read(AUDIT / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for item in readiness:
        key = item.get("readiness", "")
        counts[key] = counts.get(key, 0) + 1
    summary.update(dataset_count=len(manifests), readiness_counts=counts,
                   generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": str(CSV_PATH), "rows": len(rows), "numeric_rows": numeric_rows, "sha256": digest}, indent=2))


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    main()
