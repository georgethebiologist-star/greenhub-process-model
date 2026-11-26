"""Build a small, traceable extract of GR3 roadside/nature-grass case evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
FILENAME = "gr3_2016_roadside_grass_biogas_cases_reference.csv"
CSV_PATH = GROUP / FILENAME
SOURCE_ID = "SRC-GR3-2016-ROADSIDEBIOMASS-CASES"
URL = "https://izes.eu/wp-content/uploads/GR3_endreport_20160314_HP.pdf"
TITLE = "GR3 Project: Grass to Green Gas — final project report"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "case_id", "case_name", "location", "process_phase",
    "variable", "reported_value", "lower_value", "upper_value", "unit", "basis",
    "observation_status", "source_location", "source_wording", "evidence_class",
    "quality_class", "activation_state", "transferability", "limitations", "retrieval_date",
]

COMMON_LIMITATION = (
    "Historical Belgian case study in a 2016 European project report; not current Dutch roadside supply, "
    "not GreenHub measurements, and not a runtime default. No exact collection year, sampling protocol, "
    "or site-level uncertainty is supplied unless the record explicitly says otherwise."
)

RECORDS = [
    ("NL-ANNUAL-FRESH-GRASS", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "1", "annual_grass_available", "1200", "", "", "t fresh/year", "case estimate; report says calculated using 7 t fresh/ha", "planning_estimate", "printed p. 25, case table", "1.200 ton/year (fresh material); calculated with 7 ton fresh material/ha", "Reported estimate; number format interpreted as 1,200 using the report's European thousands separator.", "B"),
    ("NL-FRESH-YIELD-BASIS", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "1", "availability_yield_basis", "7", "", "", "t fresh/(ha·year)", "calculation basis stated for annual supply estimate", "reported_calculation_basis", "printed p. 25, case table", "calculated with 7 ton fresh material/ha", "The report does not state whether this is a measured site yield or a planning coefficient.", "B"),
    ("NL-GATE-FEE-RANGE", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "1", "current_grass_disposal_rate", "", "0", "35", "EUR/t grass", "rate basis and price year not specified", "reported_current_rate_range", "printed p. 25, case table", "Actual disposal rate: 0–35 €/ton", "Historical local range; not inflation-adjusted and not a GreenHub price assumption.", "B"),
    ("NL-SEASONAL-PILOT", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "2; 5", "spring_autumn_digestibility_observation", "spring_and_autumn_compared", "", "", "qualitative", "grass pilot tests; feed quantity, composition and trial protocol not supplied", "reported_pilot_observation", "printed p. 25, case table", "Spring grass caused no technical problems; fibrous autumn grass caused problems in digestate treatment.", "Qualitative seasonal result; cannot quantify seasonal yield or kinetic response.", "B"),
    ("NL-ENSILING-THRESHOLD", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "2", "ensiling_consideration_threshold", ">5%", "", "", "share of digester daily feedstock", "report's threshold wording; mass/volume basis not specified", "reported_operational_guidance", "printed p. 25, case table", "Consider ensiling when mowing large volumes at once (> 5% of the digester’s daily feedstock).", "Guidance from a project case report, not a measured GreenHub storage threshold.", "B"),
    ("NL-WET-AD-PARTICLE-SIZE", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "3; 5", "recommended_particle_size", "<1", "", "", "mm", "wet digester feed; report states particle size", "reported_operational_guidance", "printed p. 25, case table", "Very important to cut the grass to a size < 1 mm when feeding it to a wet digester.", "Preserved as printed; unusually fine threshold requires checking against the detailed case report before process activation.", "B"),
    ("NL-GRASS-DRY-MATTER", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "1", "grass_dry_matter", "32.2", "", "", "% as received", "grass; source reports approximate value", "reported_case_value_approximate", "printed p. 25, case table", "± 32.2 %", "Sample identity, variability and analytical method are not reported in this summary.", "B"),
    ("NL-BIOGAS-YIELD-RANGE", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "5", "biogas_yield", "", "130", "185", "Nm3 biogas/t fresh grass", "fresh-mowed grass; gas reference conditions and methane fraction not supplied", "reported_case_range_basis_unclear", "printed p. 25, case table", "130–185 Nm³ biogas/ton fresh mowed grass", "Source does not identify the exact measurement method, seasonal allocation, methane content, or standard reference conditions; do not treat as methane yield.", "B"),
    ("NL-GATE-FEE-SCENARIO", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "8", "gate_fee", "20", "", "", "EUR/t grass", "delivered to digester; business-case scenario", "assumption_in_case_evaluation", "printed p. 25, case economics", "With a gate fee of 20 €/ton... assumptions: grass delivered at the digester site + actual disposal at 35 €/ton", "Historical case assumption, not observed price and not a current project price.", "B"),
    ("NL-PROFIT-SCENARIO", "noord_limburg", "Noord Limburg", "Belgium — Limburg", "8", "profit", "approximately 10", "", "", "EUR/t grass", "report's case calculation under the stated gate fee and avoided-disposal assumptions", "reported_case_calculation", "printed p. 25, case economics", "Both partners could make a profit of ± 10 €/ton", "Definition of profit, cost boundary and price year are not stated; not comparable to GreenHub operating profit.", "B"),
    ("BAC-ANNUAL-FRESH-GRASS", "brussels_airport", "Brussels Airport Company / Guilliams Green Power", "Belgium — Zaventem to Boutersem", "1", "annual_grass_available", "1600", "", "", "t fresh/year", "airport maintenance grass; report estimate", "planning_estimate", "printed p. 27, case description", "1.600 ton/year (fresh material)", "Historical case estimate; report does not provide weighing records or moisture basis beyond fresh material.", "B"),
    ("BAC-DISPOSAL-RATE", "brussels_airport", "Brussels Airport Company / Guilliams Green Power", "Belgium — Zaventem to Boutersem", "1", "current_grass_disposal_rate", "50", "", "", "EUR/t grass", "rate basis and price year not specified", "reported_current_rate", "printed p. 27, case description", "Actual disposal rate: 50 €/ton", "Historical rate, not inflation-adjusted and not a GreenHub price assumption.", "B"),
    ("BAC-HARVEST-SEASONALITY", "brussels_airport", "Brussels Airport Company / Guilliams Green Power", "Belgium — Zaventem to Boutersem", "1", "mowing_availability_pattern", "frequent; year-round, mainly summer", "", "", "qualitative schedule", "airport maintenance grass; no monthly tonnage profile", "reported_qualitative_schedule", "printed p. 27, case practical opportunities/issues", "Grass is frequently cut (airport restrictions) so at disposal throughout the year (mainly summer time).", "Qualitative timing only; not a monthly biomass schedule and not GreenHub seasonality.", "B"),
    ("BAC-TRANSPORT-DISTANCE", "brussels_airport", "Brussels Airport Company / Guilliams Green Power", "Belgium — Zaventem to Boutersem", "1", "supplier_to_digester_distance", "30", "", "", "km", "reported route distance; route method unspecified", "reported_case_value", "printed p. 27, case practical opportunities/issues", "Distance between BAC and GGP: 30 km", "Historical route distance; not a GreenHub transport route.", "B"),
    ("BAC-EXISTING-DIGESTER-CAPACITY", "brussels_airport", "Brussels Airport Company / Guilliams Green Power", "Belgium — Boutersem", "5", "existing_digester_capacity", "60000", "", "", "t/year", "existing wet digester", "reported_facility_context", "printed p. 27, case description", "Capacity digester: 60.000 ton/year", "Facility capacity is contextual; no capacity reserved for airport grass is reported.", "B"),
    ("BAC-CHP-CAPACITY", "brussels_airport", "Brussels Airport Company / Guilliams Green Power", "Belgium — Boutersem", "5", "CHP_electrical_capacity", "approximately 1.2", "", "", "MW electrical", "existing facility; report uses approximate value", "reported_facility_context", "printed p. 27, case description", "CHP: ± 1.2 MWe", "Facility-level capacity; not attributable to the grass stream.", "B"),
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def upsert(path: Path, row: dict[str, object], key: str) -> None:
    fields, rows = read_csv(path)
    if not fields:
        raise ValueError(f"Expected CSV headers in {path}")
    normalized = {field: str(row.get(field, "")) for field in fields}
    rows = [item for item in rows if item.get(key) != normalized[key]]
    rows.append(normalized)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    GROUP.mkdir(parents=True, exist_ok=True)
    rows = []
    for (record_id, case_id, case_name, location, phase, variable, value, lower, upper,
         unit, basis, status, page, wording, specific_limit, quality) in RECORDS:
        rows.append({
            "record_id": f"GR3-2016-{record_id}", "source_id": SOURCE_ID,
            "case_id": case_id, "case_name": case_name, "location": location,
            "process_phase": phase, "variable": variable, "reported_value": value,
            "lower_value": lower, "upper_value": upper, "unit": unit, "basis": basis,
            "observation_status": status, "source_location": page,
            "source_wording": wording, "evidence_class": "B_official_project_case_report",
            "quality_class": quality, "activation_state": "reference_only",
            "transferability": "historical_Belgian_case_context_not_GreenHub_site_data",
            "limitations": COMMON_LIMITATION + " " + specific_limit,
            "retrieval_date": RETRIEVED,
        })
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:gr3-2016-belgian-grass-biogas-cases:v1",
        "dataset_version": "1.0.0", "title": "Selected GR3 Belgian roadside/nature-grass case evidence",
        "source_file": FILENAME, "source_file_sha256": digest,
        "source_id": SOURCE_ID, "citation": "Laub, K. et al. (2016). GR3 Project: Grass to Green Gas — final project report. Published 10 March 2016, printed pp. 25 and 27.",
        "source_url": URL, "doi": None, "publication_date": "2016-03-10",
        "authors": "Katharina Laub; Joachim Pertagnol; Lies Bamelis; Lorie Hamilton; Federico Correales; David Bolzonella; Robert Gruwez; Alain de Vocht; Ramon Pasman; Achim Kaiser; Michael Köttner; Erik Meers; Reinhart van Poucke; Willem Boeve; Santino di Beradino",
        "retrieval_date": RETRIEVED, "geography": "Limburg, Belgium (Noord Limburg case) and Zaventem–Boutersem, Belgium (Brussels Airport case)",
        "record_count": len(rows), "process_phases": [1, 2, 3, 5],
        "rights_status": "No explicit open license identified in the report. Only concise reported facts are transcribed with attribution; the report itself is not redistributed.",
        "evidence_class": "B_official_project_case_report", "quality_class": "B",
        "activation_state": "reference_only", "runtime_parameter_mapping": None,
        "extraction_method": "Factual transcription of specified case descriptions and reported case calculations; numeric separators are interpreted as European thousands separators only where noted in row limitations. No unreported conversions or recalculations.",
        "limitations": [COMMON_LIMITATION, "The report summarizes several business cases and pilot observations; not every number is a direct measurement. Per-record observation_status and basis distinguish estimates, case assumptions, contextual capacities, qualitative observations and unclear-basis ranges.", "The reported biogas value is biogas (not methane) per fresh tonne; methane content and gas reference conditions are absent.", "The report's stated wet-digester particle size <1 mm is reproduced verbatim and flagged for checking before any use.", "No source values change GreenHub defaults, calculations, or scenario results."],
        "fair_metadata": {
            "findable": "Versioned local URN, source ID, full citation, report URL, printed page and record IDs are provided.",
            "accessible": "UTF-8 CSV and JSON sidecar are in the project data tree and indexed in the FAIR catalog.",
            "interoperable": "Long-form UTF-8 CSV separates cases, process phase, variable, value/range, units, basis and evidence status.",
            "reusable": "Each row preserves source wording, scope, provenance, limitations and reference-only status; no reuse license is asserted."},
    }
    Path(str(CSV_PATH) + ".source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID, "source_title": TITLE,
        "authors": "Laub et al.; full author list in dataset sidecar", "year": "2016",
        "source_type": "European project final report; regional case summaries and pilot observations",
        "doi_or_stable_identifier": "", "stable_url": URL,
        "material": "Belgian natural-conservancy grass and Brussels Airport maintenance grass case studies",
        "quality_notes": "B-tier reported case evidence; values mix estimates, contextual facility data, qualitative pilot observations and case assumptions. No explicit open license identified. Historical and reference-only; not Dutch GreenHub supply or runtime inputs.",
        "accessed_date": RETRIEVED,
    }
    upsert(GROUP / "source_register.csv", local_source, "source_id")
    upsert(GROUP / "dataset_manifest.csv", {
        "file_name": FILENAME, "description": "Selected GR3 Belgian grass supply, seasonal handling, pretreatment and biogas case records",
        "row_count": len(rows), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_readiness": "traceable_reference_only_not_runtime_eligible",
        "limitations": "Historical report; data basis varies by record and several process/financial values are scenario estimates; not Dutch GreenHub inputs.",
    }, "file_name")

    rel = f"Pre-treatment/Feedstock/{FILENAME}"
    upsert(AUDIT / "global_source_register.csv", {
        "dataset_path": rel, "dataset_group": "Pre-treatment/Feedstock", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": local_source["authors"], "year": "2016",
        "doi_or_stable_id": "", "url": URL, "source_type": local_source["source_type"],
        "notes": local_source["quality_notes"],
    }, "dataset_path")
    upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Belgian roadside/nature grass cases; Phases 1, 2, 3, 5",
        "filename": FILENAME, "row_count_observed": len(rows), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "Case estimates, reported pilot observations and contextual facility data are distinguished row-by-row; no default activation.",
    }, "dataset_path")
    upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": "Belgian roadside/nature grass cases; Phases 1, 2, 3, 5",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": 14,
        "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0, "notes": "Every numeric record links to a printed report page; denominator, uncertainty and measurement status remain incomplete where report does not specify them.",
    }, "dataset_path")
    upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": rel, "sha256": digest, "byte_size": CSV_PATH.stat().st_size,
    }, "dataset_path")
    print(json.dumps({"dataset": rel, "records": len(rows), "sha256": digest, "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
