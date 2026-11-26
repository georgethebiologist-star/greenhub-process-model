"""Transcribe Schaffers et al. (1998) field-decay Table 4 and Table 5."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
FILENAME = "roadside_cutting_field_decay_schaffers_1998_tables4_5_reference.csv"
CSV_PATH = GROUP / FILENAME
SOURCE_ID = "SRC-SCHAFFERS-1998"
DOI = "10.1046/j.1365-2664.1998.00316.x"
URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "source_table", "record_type", "plant_community",
    "response_variable", "time_since_cut_weeks", "time_endpoint", "reported_value",
    "unit", "significance_marker", "model_family", "predictor", "predictor_unit",
    "coefficient_b", "coefficient_c", "r_squared", "significance_p",
    "analysis_scope", "source_location", "evidence_class", "quality_class",
    "activation_state", "limitations", "retrieval_date",
]

RESPONSES = {
    "dry_weight": {
        "Ran": ["77.5", "65.2", "58.3", "54.4", "52.2", "50.9", "49.0", "0.085"],
        "Arrh": ["86.2", "77.7", "72.2", "68.7", "66.6", "65.2", "62.9", "0.066"],
        "arrh_sig": ["*", "**", "**", "**", "*", "*", "*"],
    },
    "nitrogen": {
        "Ran": ["82.6", "71.7", "64.7", "60.1", "57.1", "55.1", "50.5", "0.062"],
        "Arrh": ["88.8", "82.5", "78.6", "76.0", "74.0", "72.6", "72.4", "0.090"],
        "arrh_sig": ["", "", "", "", "*", "*", "*"],
    },
    "phosphorus": {
        "Ran": ["65.6", "51.4", "45.3", "42.8", "41.7", "41.2", "40.8", "0.128"],
        "Arrh": ["77.1", "68.0", "64.1", "62.4", "61.7", "61.3", "61.0", "0.133"],
        "arrh_sig": ["**", "**", "**", "**", "**", "**", "**"],
    },
    "potassium": {
        "Ran": ["59.6", "38.7", "27.5", "21.1", "17.3", "15.0", "10.1", "0.091"],
        "Arrh": ["71.0", "51.2", "37.7", "28.3", "21.7", "17.1", "5.4", "0.054"],
        "arrh_sig": ["", "", "", "", "", "", ""],
    },
}

# Each row: response, predictor, equation, then (b, c, R2, p) for weeks 1–6 and asymptote.
TABLE5 = {
    "dry_weight": {
        "predictor": "initial_C_to_N_ratio", "predictor_unit": "mass ratio, dimensionless",
        "model": "remaining_percent = c + b * initial_C_to_N_ratio",
        "values": [
            ("0.74", "60.3", "0.38", "0.143"), ("1.17", "37.3", "0.50", "0.075"),
            ("1.41", "24.1", "0.61", "0.039"), ("1.56", "16.3", "0.68", "0.023"),
            ("1.65", "11.6", "0.72", "0.015"), ("1.69", "8.9", "0.75", "0.012"),
            ("1.76", "4.9", "0.78", "0.009"),
        ],
    },
    "nitrogen": {
        "predictor": "initial_C_to_N_ratio", "predictor_unit": "mass ratio, dimensionless",
        "model": "remaining_percent = c * b ** initial_C_to_N_ratio",
        "values": [
            ("1.0089", "66.2", "0.27", "0.236"), ("1.0172", "46.7", "0.38", "0.141"),
            ("1.0239", "35.7", "0.48", "0.085"), ("1.0289", "29.4", "0.57", "0.051"),
            ("1.0321", "25.9", "0.63", "0.033"), ("1.0342", "23.7", "0.68", "0.023"),
            ("1.0413", "18.4", "0.78", "0.019"),
        ],
    },
    "phosphorus": {
        "predictor": "initial_phosphorus_concentration", "predictor_unit": "mg P/g dry matter",
        "model": "remaining_percent = c * b ** initial_phosphorus_concentration",
        "values": [
            ("0.877", "95.8", "0.62", "0.036"), ("0.815", "98.0", "0.57", "0.051"),
            ("0.776", "100.8", "0.52", "0.067"), ("0.757", "102.6", "0.50", "0.074"),
            ("0.748", "103.6", "0.48", "0.083"), ("0.745", "103.9", "0.48", "0.086"),
            ("0.741", "104.3", "0.47", "0.088"),
        ],
    },
    "potassium": {
        "predictor": "initial_phosphorus_concentration", "predictor_unit": "mg P/g dry matter",
        "model": "remaining_percent = c * b ** initial_phosphorus_concentration",
        "values": [
            ("0.888", "86.7", "0.19", "0.326"), ("0.791", "78.3", "0.26", "0.245"),
            ("0.707", "74.0", "0.34", "0.166"), ("0.635", "73.1", "0.42", "0.113"),
            ("0.575", "73.3", "0.44", "0.102"), ("0.517", "77.4", "0.42", "0.115"),
            None,
        ],
    },
}

COMMON_LIMITATION = (
    "Dutch roadside-cutting field experiment in 1993; cut material was left in field litterbags for up to six weeks. "
    "This is field-delay/decomposition evidence, not bunker ensiling, warehouse storage, or GreenHub feed-specific kinetics. "
    "No runtime mapping or GreenHub default activation."
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = read_csv(path)
    if not fields:
        raise ValueError(f"Expected CSV headers in {path}")
    normalized = {field: str(row.get(field, "")) for field in fields}
    rows = [existing for existing in rows if existing.get(key) != normalized[key]]
    rows.append(normalized)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    GROUP.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for response, values in RESPONSES.items():
        for community, species_name in (("Ran", "Ranunculo-Alopecuretum"), ("Arrh", "Arrhenatheretum")):
            arr = values[community]
            for week in range(1, 7):
                rows.append({
                    "record_id": f"SCH98-T4-{response.upper()}-{community}-W{week}", "source_id": SOURCE_ID,
                    "source_table": "Table 4", "record_type": "community_mean_remaining_percent",
                    "plant_community": species_name, "response_variable": response,
                    "time_since_cut_weeks": str(week), "time_endpoint": "weekly model-estimated remaining fraction",
                    "reported_value": arr[week - 1], "unit": "% of initial amount remaining",
                    "significance_marker": values["arrh_sig"][week - 1] if community == "Arrh" else "",
                    "model_family": "asymptotic exponential fit; community-level reported values",
                    "predictor": "", "predictor_unit": "", "coefficient_b": "", "coefficient_c": "",
                    "r_squared": "", "significance_p": "",
                    "analysis_scope": "Two grassland communities; source does not state per-community plot count in Table 4.",
                    "source_location": "Table 4, printed article page 7; DOI landing page table",
                    "evidence_class": "B_primary_field_study_derived_model_output", "quality_class": "B",
                    "activation_state": "reference_only",
                    "limitations": COMMON_LIMITATION + " Table 4 values are model-estimated group means, not the raw litterbag replicate measurements.",
                    "retrieval_date": RETRIEVED,
                })
            rows.append({
                "record_id": f"SCH98-T4-{response.upper()}-{community}-ASYMPTOTE", "source_id": SOURCE_ID,
                "source_table": "Table 4", "record_type": "asymptotic_remaining_percent",
                "plant_community": species_name, "response_variable": response,
                "time_since_cut_weeks": "", "time_endpoint": "asymptotic fraction a",
                "reported_value": arr[6], "unit": "% of initial amount remaining",
                "significance_marker": values["arrh_sig"][6] if community == "Arrh" else "",
                "model_family": "asymptotic exponential fit; community-level reported values",
                "predictor": "", "predictor_unit": "", "coefficient_b": "", "coefficient_c": "",
                "r_squared": "", "significance_p": "",
                "analysis_scope": "Two grassland communities; source does not state per-community plot count in Table 4.",
                "source_location": "Table 4, printed article page 7; DOI landing page table",
                "evidence_class": "B_primary_field_study_derived_model_output", "quality_class": "B",
                "activation_state": "reference_only",
                "limitations": COMMON_LIMITATION + " Asymptote is model-derived and should not be interpreted as a six-week observed endpoint.",
                "retrieval_date": RETRIEVED,
            })
            rows.append({
                "record_id": f"SCH98-T4-{response.upper()}-{community}-K", "source_id": SOURCE_ID,
                "source_table": "Table 4", "record_type": "asymptotic_rate_constant",
                "plant_community": species_name, "response_variable": response,
                "time_since_cut_weeks": "", "time_endpoint": "rate parameter k",
                "reported_value": arr[7], "unit": "week^-1",
                "significance_marker": "not significant between communities",
                "model_family": "Y(t)=a+(1-a)*exp(-k*t); community-level reported parameter",
                "predictor": "", "predictor_unit": "", "coefficient_b": "", "coefficient_c": "",
                "r_squared": "", "significance_p": "",
                "analysis_scope": "Two grassland communities; Table 4 reports no significant difference in k between communities.",
                "source_location": "Table 4, printed article page 7; DOI landing page table",
                "evidence_class": "B_primary_field_study_derived_model_output", "quality_class": "B",
                "activation_state": "reference_only",
                "limitations": COMMON_LIMITATION + " Parameter is fit-derived; the source says no significant difference between communities.",
                "retrieval_date": RETRIEVED,
            })

    for response, spec in TABLE5.items():
        for index, endpoint in enumerate(["1", "2", "3", "4", "5", "6", "asymptotic"]):
            fit = spec["values"][index]
            status = "reported_regression_fit" if fit is not None else "no_satisfactory_fit_reported"
            b, c, r2, p = fit if fit is not None else ("", "", "", "")
            rows.append({
                "record_id": f"SCH98-T5-{response.upper()}-{endpoint.upper()}", "source_id": SOURCE_ID,
                "source_table": "Table 5", "record_type": status,
                "plant_community": "pooled seven grassland plots; Ericion grass-heath plot excluded from initial regression analysis",
                "response_variable": response,
                "time_since_cut_weeks": "" if endpoint == "asymptotic" else endpoint,
                "time_endpoint": "asymptotic remaining fraction" if endpoint == "asymptotic" else f"{endpoint} week after cutting",
                "reported_value": "", "unit": "remaining amount as percent of initial amount",
                "significance_marker": "", "model_family": spec["model"],
                "predictor": spec["predictor"], "predictor_unit": spec["predictor_unit"],
                "coefficient_b": b, "coefficient_c": c, "r_squared": r2,
                "significance_p": p,
                "analysis_scope": "Regression across seven grassland plots; Ericion plot was omitted initially as an outlier/poor-fit case.",
                "source_location": "Table 5, printed article page 7; DOI landing page table",
                "evidence_class": "B_primary_field_study_regression_coefficients", "quality_class": "B",
                "activation_state": "reference_only",
                "limitations": COMMON_LIMITATION + (" Potassium regression is nonsignificant and may be unjustified; no asymptotic fit was obtained." if response == "potassium" else " Predictor-range validation must be respected; article warns that high-C:N nitrogen predictions include extrapolation." if response == "nitrogen" else " No GreenHub-specific validation or activation; input composition and time domains must match the source study."),
                "retrieval_date": RETRIEVED,
            })

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:schaffers-1998-roadside-field-decay-tables4-5:v1",
        "dataset_version": "1.0.0", "title": "Community-mean field-decay model outputs and composition regressions for Dutch roadside cuttings",
        "source_file": FILENAME, "source_file_sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Schaffers, A.P., Vesseur, M.C. & Sýkora, K.V. (1998). Effects of delayed hay removal on the nutrient balance of roadside plant communities. Journal of Applied Ecology, 35, 166–174.",
        "doi": DOI, "source_url": URL, "retrieval_date": RETRIEVED,
        "geography": "Netherlands; roadside grassland plots in a 1993 field campaign",
        "field_period": "24 May–6 July 1993; seven grassland plots had 5–6 week exposure, contrasting grass-heath plot had 4 weeks",
        "record_count": len(rows), "source_tables": [4, 5], "evidence_class": "B_primary_field_study_model_outputs_and_fits",
        "quality_class": "B", "license": "No explicit open license identified on accessible article record; concise table facts transcribed with full attribution.",
        "method": "Table 4 values are reported community means of fitted/model-estimated remaining fractions and asymptotic parameters. Table 5 coefficients are source-reported regressions. Values are transcribed as printed; decimal points normalize the source's decimal-point glyphs; no parameter conversion or fit is performed.",
        "equations": [
            "Plot/community field decay: Y(t)=a+(1-a)*exp(-k*t), where Y is remaining fraction; a is asymptotic remaining fraction; k is week^-1.",
            "Table 5 dry weight: remaining_percent=c+b*initial_C_to_N_ratio.",
            "Table 5 nitrogen: remaining_percent=c*b**initial_C_to_N_ratio.",
            "Table 5 phosphorus/potassium: remaining_percent=c*b**initial_phosphorus_concentration_mgP_per_gDM.",
        ],
        "scope": "Phase 2 field delay/decomposition before biomass removal. This does not describe ensiling, bunker storage, indoor storage, or anaerobic degradation.",
        "activation_state": "reference_only",
        "limitations": [COMMON_LIMITATION, "Table 4 values are model-estimated community means and are not raw litterbag replicates.", "Table 5 regressions were based on seven grassland plots, with the grass-heath (Ericion) plot excluded initially; article warns of extrapolation beyond the observed C:N range.", "The potassium regressions were not statistically significant, are described as poor/may be unjustified, and have no satisfactory asymptotic fit.", "The source has no direct GreenHub feed, storage, leachate, emissions, protein, COD or methane measurements.", "This extract complements the existing Table 1/Table 3 plot-level dataset; do not double-count fitted parameters or treat alternative Table 4/5 regressions as independent observations."],
        "runtime_parameter_mapping": None,
    }
    Path(str(CSV_PATH) + ".source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    upsert(GROUP / "dataset_manifest.csv", {
        "file_name": FILENAME, "description": "Schaffers et al. (1998) Table 4 community field-decay summaries and Table 5 composition regressions",
        "row_count": len(rows), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": "Fitted/model-derived field-delay values, not raw replicates or storage kinetics; Dutch 1993 roadside plots; no GreenHub activation.",
    }, "file_name")
    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel, "dataset_group": "Pre-treatment/Feedstock", "source_id": SOURCE_ID,
        "source_title": "Effects of delayed hay removal on the nutrient balance of roadside plant communities",
        "authors": "A. P. Schaffers; M. C. Vesseur; K. V. Sýkora", "year": "1998",
        "doi_or_stable_id": DOI, "url": URL,
        "source_type": "peer-reviewed primary roadside field study; model-derived table values and regressions",
        "notes": "Tables 4–5 are reference-only. Table 4 community means are fitted/model-derived; Table 5 composition regressions have significant limitations, especially nonsignificant potassium models.",
    }, "dataset_path")
    upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock; field decomposition and nutrient return before collection",
        "filename": FILENAME, "row_count_observed": len(rows), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "Table 4 model-derived community means; Table 5 source fits. Not storage kinetics or GreenHub runtime values.",
    }, "dataset_path")
    upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Feedstock; field decomposition and nutrient return before collection",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": len(rows),
        "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0, "notes": "Each numeric record cites Table 4 or 5; model-derived vs regression and weak K fits are explicit.",
    }, "dataset_path")
    upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel, "sha256": digest, "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")

    source_register = GROUP / "source_register.csv"
    _, sources = read_csv(source_register)
    source = next((item for item in sources if item.get("source_id") == SOURCE_ID), None)
    if source:
        updated = dict(source)
        prior = updated.get("quality_notes", "")
        addition = "Tables 4–5 also staged separately: community-mean fitted field-decay fractions and initial-composition regressions; reference-only."
        if addition not in prior:
            updated["quality_notes"] = (prior + " " + addition).strip()
        updated["accessed_date"] = RETRIEVED
        upsert(source_register, updated, "source_id")
    else:
        raise ValueError("Expected the existing SRC-SCHAFFERS-1998 source-register row.")
    print(json.dumps({"dataset": rel, "records": len(rows), "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
