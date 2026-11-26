"""Stage reference-only feed and pilot-AD observations from Guanlao (2019).

The thesis includes a roadside-grass batch, a different managed-grass batch,
pilot CSTR runs, and a commercial bird-seed sanitation proxy. Records preserve
these distinct study materials and reported bases; they are not model inputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Bigas production + upgrade/AD reactor"
CSV_PATH = FOLDER / "guanlao_2019_roadside_grass_thermophilic_ad_reference.csv"
SOURCE_ID = "SRC-GUANLAO-2019-ROADSIDE-GRASS-AD"
TITLE = "Anaerobic digestion and sanitation of grass clippings from roadside and grassland"
AUTHOR = "Anjelika Mae S. Guanlao"
SOURCE_URL = "https://libstore.ugent.be/fulltxt/RUG01/002/791/211/RUG01-002791211_2019_0001_AC.pdf"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "phase_relevance", "record_type", "material_batch", "material_origin",
    "process_unit", "metric", "reported_value", "unit", "basis", "condition_scope",
    "source_location", "source_id", "evidence_class", "quality_class",
    "activation_state", "transferability", "limitations",
]

ROWS: list[dict[str, str]] = []


def add(
    record_id: str,
    phases: str,
    record_type: str,
    batch: str,
    origin: str,
    process: str,
    metric: str,
    value: str,
    unit: str,
    basis: str,
    conditions: str,
    location: str,
    limitation: str = "",
    evidence: str = "B_primary_thesis_reported",
    transfer: str = "Belgian_study_material_not_Dutch_VARTA_or_GreenHub_calibration",
) -> None:
    ROWS.append({
        "record_id": record_id,
        "phase_relevance": phases,
        "record_type": record_type,
        "material_batch": batch,
        "material_origin": origin,
        "process_unit": process,
        "metric": metric,
        "reported_value": value,
        "unit": unit,
        "basis": basis,
        "condition_scope": conditions,
        "source_location": location,
        "source_id": SOURCE_ID,
        "evidence_class": evidence,
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": transfer,
        "limitations": limitation,
    })


ROAD = "Batch 1; roadside verge at Zele, Belgium; harvested autumn 2018, dried and ensiled; delivered November 2018"
FIELD = "Batch 2; managed grassland at Quevy-le-Grand, Belgium; harvested December 2018 as fresh wet grass and ensiled without drying"
FEED_ANALYSIS = "Table 9; as reported for ensiled feed; no sample-level uncertainty reported"
COMPOSITION_LIMIT = "Cultivated/managed Belgian comparator, not Dutch roadside or VARTA grass; one batch per material and no reported uncertainty."

for batch, origin, values in [
    ("Batch 1", ROAD, {
        "dry_matter_content": ("57.3", "% as received", "mass DM per mass ensiled feed"),
        "dry_organic_matter_content": ("65.8", "% DM", "DOM as percent of DM"),
        "crude_fat": ("19.1", "kg/tonne DOM", "mass per tonne DOM"),
        "carbohydrates": ("336", "kg/tonne DOM", "mass per tonne DOM"),
        "calculated_methane_potential": ("146", "m3 CH4/tonne DOM", "Thesis-defined EPi-test estimate; not an independently run standardized BMP assay"),
        "expected_methane_content": ("52", "% CH4", "EPi-test expected methane content, not measured reactor-gas composition"),
    }),
    ("Batch 2", FIELD, {
        "dry_matter_content": ("16.3", "% as received", "mass DM per mass ensiled feed"),
        "dry_organic_matter_content": ("85.2", "% DM", "DOM as percent of DM"),
        "crude_fat": ("24.8", "kg/tonne DOM", "mass per tonne DOM"),
        "carbohydrates": ("485", "kg/tonne DOM", "mass per tonne DOM"),
        "calculated_methane_potential": ("252", "m3 CH4/tonne DOM", "Thesis-defined EPi-test estimate; not an independently run standardized BMP assay"),
        "expected_methane_content": ("54", "% CH4", "EPi-test expected methane content, not measured reactor-gas composition"),
    }),
]:
    for metric, (value, unit, basis) in values.items():
        add(
            f"GUA19-{batch.upper().replace(' ', '-')}-FEED-{metric.upper()}", "1;2;5",
            "feed_characterization", batch, origin, "ensiled grass feed", metric, value, unit,
            basis, "Table 9 feed analysis", "Table 9, printed p. 22", COMPOSITION_LIMIT,
            evidence="B_primary_thesis_measured_or_source_calculated",
            transfer="Belgian_roadside_mixed_verge_batch" if batch == "Batch 1" else "Belgian_managed_grassland_comparator",
        )

# Feedstock provenance and preparation are reported as text, not as measured
# supply quantities or a controlled seasonal comparison.
add("GUA19-BATCH1-ORIGIN", "1;2", "feedstock_provenance", "Batch 1", ROAD,
    "collection and storage", "feedstock_preparation", ROAD, "description",
    "Study narrative; batch source and preparation", "Autumn 2018 roadside batch",
    "Section 2.2, printed p. 18", "Harvest mass, field area, mowing regime, dry-down duration and ensiling duration are not given.", transfer="Belgian_roadside_mixed_verge_batch")
add("GUA19-BATCH2-ORIGIN", "1;2", "feedstock_provenance", "Batch 2", FIELD,
    "collection and storage", "feedstock_preparation", FIELD, "description",
    "Study narrative; batch source and preparation", "December 2018 grassland batch",
    "Section 2.2, printed p. 18", "Managed grassland batch, not roadside; harvest mass, field area, storage duration and harvest maturity are not given.", transfer="Belgian_managed_grassland_comparator")

# Reactor configuration, inoculum, mixing and the nominal operating table.
for digester, volume, orientation, hrt_untreated, hrt_treated, olr_treated in [
    ("Digester 1", "33", "horizontal CSTR", "45", "15", "1.00"),
    ("Digester 2", "72", "vertical CSTR", "40", "15", "1.20"),
]:
    safe = digester.upper().replace(" ", "-")
    for metric, value, unit, basis in [
        ("reactor_working_volume", volume, "L", "Reactor volume as stated; effective working volume not distinguished."),
        ("reactor_configuration", orientation, "description", "Pilot-scale CSTR type."),
        ("digestion_temperature_setpoint_untreated", "51", "degC", "Table 6 nominal setpoint for untreated feed."),
        ("digestion_temperature_setpoint_pretreated", "51", "degC", "Table 6 nominal setpoint for pretreated feed."),
        ("organic_loading_rate_untreated", "2.30", "kg DOM/m3/day", "Table 6 nominal operating value; distinct from later reported average OLR."),
        ("organic_loading_rate_pretreated", olr_treated, "kg DOM/m3/day", "Table 6 nominal operating value; distinct from later reported average OLR."),
        ("hydraulic_retention_time_untreated", hrt_untreated, "day", "Table 6 nominal operating value; distinct from later reported average HRT."),
        ("hydraulic_retention_time_pretreated", hrt_treated, "day", "Table 6 nominal operating value; distinct from later reported average HRT."),
    ]:
        add(f"GUA19-{safe}-{metric.upper()}", "5", "reactor_configuration_or_setting",
            "Both feed batches; table applies to both", "Belgium; pilot laboratory facility",
            digester, metric, value, unit, basis,
            "Table 6; nominal conditions unless noted", "Table 6, printed p. 19",
            "Small pilot reactor; no GreenHub scale-up. Table 6 nominal values differ from some average operating results in Tables 13 and 15.")

for metric, value, unit, basis, conditions in [
    ("seed_sludge_fraction", "50", "% v/v", "Seed sludge volume per reactor volume", "Seed sludge from an operating thermophilic digester treating mixed vegetable organics."),
    ("mixing_on_time", "90", "s", "Mixing cycle on-time", "Both pilot digesters."),
    ("mixing_cycle_period", "480", "s", "Reported period for the mixing cycle; source wording: 90 s every 480 s", "Both pilot digesters."),
    ("acclimatization_duration", "20", "day", "Duration of acclimatization phase", "Both pilot digesters; before untreated grass feeding."),
    ("acclimatization_OLR_lower", "0.6", "kg DOM/m3/day", "Lower endpoint of stated acclimatization OLR range", "Thesis reports a reduced OLR between 1.2 and 0.6 for 20 days."),
    ("acclimatization_OLR_upper", "1.2", "kg DOM/m3/day", "Upper endpoint of stated acclimatization OLR range", "Thesis reports a reduced OLR between 1.2 and 0.6 for 20 days."),
    ("observed_system_upset_OLR_lower", "6.30", "kg DOM/m3/day", "Lower endpoint of OLR at which high propionate/acetate ratio and upset were discussed", "A range of 6.30–6.50 is stated; not a universally safe/unsafe threshold."),
    ("observed_system_upset_OLR_upper", "6.50", "kg DOM/m3/day", "Upper endpoint of OLR at which high propionate/acetate ratio and upset were discussed", "A range of 6.30–6.50 is stated; reactor performance and feed are study-specific."),
]:
    add(f"GUA19-AD-{metric.upper()}", "5", "reactor_operation", "Pilot digesters", "Belgium; pilot laboratory facility",
        "thermophilic anaerobic digestion", metric, value, unit, basis, conditions,
        "Sections 2.3 and 3.2, printed pp. 19, 23–25",
        "One thesis experiment; settings and failure behavior are not general design limits.")

# Table 7 enzyme hydrolysis conditions, performed on Batch 2 managed grass.
for enzyme, digester in [("Enhanced cellulase A", "Digester 1"), ("Enhanced cellulase B", "Digester 2")]:
    safe = enzyme.upper().replace(" ", "-")
    for metric, value, unit, basis in [
        ("enzyme_preparation_concentration", "250", "mg/L", "Concentration of enzyme preparation as printed; source does not normalize to kg enzyme/kg DM."),
        ("hydrolysis_temperature", "50", "degC", "Pretreatment temperature."),
        ("hydrolysis_duration_lower", "36", "hour", "Lower endpoint of stated treatment time."),
        ("hydrolysis_duration_upper", "48", "hour", "Upper endpoint of stated treatment time."),
        ("substrate_preparation_solids", "15", "g DM/L", "Feed preparation solids concentration before enzymatic treatment."),
    ]:
        add(f"GUA19-{safe}-{metric.upper()}", "3;5", "pretreatment_condition", "Batch 2; managed grassland",
            FIELD, "enzymatic hydrolysis before digestion", metric, value, unit, basis,
            f"{digester}; Batch 2 silage was milled; {enzyme}", "Table 7, printed p. 20",
            "Enzyme activity units, enzyme mass per substrate DM, mixing power and water balance are not reported in the table.",
            transfer="Belgian_managed_grassland_comparator")

# Table 11 measured/averaged methane productivity by digester and feed batch.
for digester, batch, value in [
    ("Digester 1", "Batch 1 roadside", "188.19"),
    ("Digester 1", "Batch 2 grassland", "188.34"),
    ("Digester 2", "Batch 1 roadside", "237.19"),
    ("Digester 2", "Batch 2 grassland", "189.13"),
]:
    add(f"GUA19-{digester.upper().replace(' ', '-')}-{batch.upper().replace(' ', '-')}-ACTUAL-CH4",
        "5", "reported_digester_performance", batch,
        ROAD if batch.startswith("Batch 1") else FIELD, digester,
        "actual_methane_productivity", value, "m3 CH4/tonne DOM",
        "Table 11 source-reported actual methane productivity per tonne DOM; gas standard conditions not stated.",
        "Untreated feed; Table 11 comparison by reactor and feed batch.", "Table 11, printed p. 27",
        "No replicate count or uncertainty reported; the batch-specific Table 11 values are distinct from summary values elsewhere in the thesis.",
        evidence="B_primary_thesis_reported_pilot_average",
        transfer="Belgian_roadside_mixed_verge_batch" if batch.startswith("Batch 1") else "Belgian_managed_grassland_comparator")

# Feed characterization before/after the separate Cellulase A and B treatments.
for digester, treatment, treated in [
    ("Digester 1", "Enhanced cellulase A", {
        "dry_matter_content": ("1.62", "% as received", "mass DM per mass feed"),
        "dry_organic_matter_content": ("81.81", "% DM", "DOM as percent of DM"),
        "crude_fat": ("14.11", "kg/tonne DOM", "mass per tonne DOM"),
        "protein": ("257.23", "kg/tonne DOM", "mass per tonne DOM; source labels the analyte protein"),
        "carbohydrates": ("308.29", "kg/tonne DOM", "mass per tonne DOM"),
        "calculated_methane_potential": ("281.47", "m3 CH4/tonne DOM", "Thesis-defined EPi-test estimate; not a standardized BMP assay"),
        "expected_methane_content": ("59.5", "% CH4", "EPi-test expected content, not reactor-gas measurement"),
    }),
    ("Digester 2", "Enhanced cellulase B", {
        "dry_matter_content": ("2.27", "% as received", "mass DM per mass feed"),
        "dry_organic_matter_content": ("82.0", "% DM", "DOM as percent of DM"),
        "crude_fat": ("25.5", "kg/tonne DOM", "mass per tonne DOM"),
        "protein": ("105.29", "kg/tonne DOM", "mass per tonne DOM; source labels the analyte protein"),
        "carbohydrates": ("387", "kg/tonne DOM", "mass per tonne DOM"),
        "calculated_methane_potential": ("187", "m3 CH4/tonne DOM", "Thesis Table 14 rounded EPi-test estimate; separate Table 16 reports 187.38"),
        "expected_methane_content": ("55", "% CH4", "EPi-test expected content, not reactor-gas measurement"),
    }),
]:
    source_table = "Table 12, printed p. 28" if "A" in treatment else "Table 14, printed p. 31"
    untreated = {
        "dry_matter_content": ("16.3", "% as received", "mass DM per mass feed"),
        "dry_organic_matter_content": ("85.2", "% DM", "DOM as percent of DM"),
        "crude_fat": ("24.82" if "A" in treatment else "24.8", "kg/tonne DOM", "mass per tonne DOM"),
        "protein": ("135.55" if "A" in treatment else "135", "kg/tonne DOM", "mass per tonne DOM; source labels the analyte protein"),
        "carbohydrates": ("485.23" if "A" in treatment else "485", "kg/tonne DOM", "mass per tonne DOM"),
        "calculated_methane_potential": ("252.03" if "A" in treatment else "252", "m3 CH4/tonne DOM", "Thesis-defined EPi-test estimate; separate tables use different rounding"),
        "expected_methane_content": ("54", "% CH4", "EPi-test expected content, not reactor-gas measurement"),
    }
    for state, measures in [("untreated", untreated), ("enzyme-treated", treated)]:
        for metric, (value, unit, basis) in measures.items():
            add(f"GUA19-{digester.upper().replace(' ', '-')}-{state.upper()}-{metric.upper()}",
                "3;5", "feed_characterization_before_digestion", "Batch 2; managed grassland",
                FIELD, f"{treatment} hydrolysis; feed to {digester}", metric, value, unit, basis,
                f"{state}; Table 12/14 pair; enzyme treatment conducted on Batch 2 silage", source_table,
                "Single study material; reported as treatment-specific feed characterization. These are not roadside Batch 1 values; mass-balance closure and analytical uncertainty are not reported.",
                evidence="B_primary_thesis_measured_or_source_calculated",
                transfer="Belgian_managed_grassland_comparator")

# Average operating outcomes in Tables 13 and 15; keep nominal Table 6
# settings and the later averaged values as separate records.
for digester, treatment, values, table in [
    ("Digester 1", "Enhanced cellulase A", {
        "untreated_OLR": ("2.43", "kg DOM/m3/day", "Average operating parameter in Table 13"),
        "treated_OLR": ("0.99", "kg DOM/m3/day", "Average operating parameter in Table 13"),
        "untreated_HRT": ("34.90", "day", "Average operating parameter in Table 13"),
        "treated_HRT": ("14.50", "day", "Average operating parameter in Table 13"),
        "untreated_feed_DM": ("10.00", "%", "Table 13; distinct from Table 12 feed characterization value"),
        "treated_feed_DM": ("1.62", "%", "Table 13; treated feed concentration"),
        "untreated_actual_methane_productivity": ("188.34", "m3 CH4/tonne DOM", "Average specific productivity in Table 13"),
        "treated_actual_methane_productivity": ("228.53", "m3 CH4/tonne DOM", "Average specific productivity in Table 13"),
    }, "Table 13, printed p. 29"),
    ("Digester 2", "Enhanced cellulase B", {
        "untreated_OLR": ("2.41", "kg DOM/m3/day", "Average operating parameter in Table 15"),
        "treated_OLR": ("1.19", "kg DOM/m3/day", "Average operating parameter in Table 15"),
        "untreated_HRT": ("37.13", "day", "Average operating parameter in Table 15"),
        "treated_HRT": ("15.55", "day", "Average operating parameter in Table 15"),
        "untreated_feed_DM": ("10.00", "%", "Table 15; distinct from Table 14 feed characterization value"),
        "treated_feed_DM": ("2.27", "%", "Table 15; treated feed concentration"),
        "untreated_actual_methane_productivity": ("189.13", "m3 CH4/tonne DOM", "Average specific productivity in Table 15"),
        "treated_actual_methane_productivity": ("168.37", "m3 CH4/tonne DOM", "Average specific productivity in Table 15"),
    }, "Table 15, printed p. 33"),
]:
    for metric, (value, unit, basis) in values.items():
        add(f"GUA19-{digester.upper().replace(' ', '-')}-{metric.upper()}", "5",
            "average_pilot_operating_outcome", "Batch 2; managed grassland",
            FIELD, f"{digester}; {treatment} comparison", metric, value, unit, basis,
            "Average conditions/performance as tabulated; each treatment had a single reactor configuration.",
            table, "Small pilot study without statistical uncertainty; OLR, HRT and feed DM differ from nominal Table 6 or feed-characterization table and are not merged.",
            evidence="B_primary_thesis_reported_pilot_average", transfer="Belgian_managed_grassland_comparator")

# In-paragraph gas-flow averages are retained separately from specific yield.
for record_id, batch, value, unit, condition in [
    ("GUA19-D1-UNTREATED-BIOGAS-RATE", "Batch 2 grassland untreated", "25.76", "L biogas/day", "Digester 1; 58.67% CH4 reported in the same text"),
    ("GUA19-D1-CELLULASE-A-FIRST-BATCH-RATE", "Batch 2 grassland; cellulase A hydrolysate batch 1", "13.51", "L biogas/day", "59% CH4 reported in the same text"),
    ("GUA19-D1-CELLULASE-A-SECOND-BATCH-RATE", "Batch 2 grassland; cellulase A hydrolysate batch 2", "8.95", "L biogas/day", "62.49% CH4 reported in the same text"),
]:
    add(record_id, "5", "reported_gas_flow_average", batch, FIELD,
        "Digester 1 gas meter", "average_biogas_volume_rate", value, unit,
        "Unnormalized pilot reactor gas volume per day; source does not state standard conditions for these litre/day figures.",
        condition, "Section 3.3.1, printed pp. 29–31",
        "Biogas flow is not methane flow; do not convert to CH4 yield without matching composition and normalization conditions.",
        evidence="B_primary_thesis_reported_pilot_average", transfer="Belgian_managed_grassland_comparator")

# The summary table is retained separately because its untreated values differ
# slightly from the Digester 1 narrative/Table 13 values.
for treatment, yield_value, methane_content in [
    ("untreated summary", "188.74", "58.29"),
    ("Cellulase A summary", "228.53", "60.38"),
    ("Cellulase B summary", "168.37", "57.49"),
]:
    for metric, value, unit in [
        ("actual_methane_productivity_summary_table16", yield_value, "m3 CH4/tonne DOM"),
        ("actual_methane_content_summary_table16", methane_content, "% CH4"),
    ]:
        add(f"GUA19-TABLE16-{treatment.upper().replace(' ', '-')}-{metric.upper()}", "5",
            "study_summary_value", treatment, "Batch 2; managed grassland", "Table 16 study summary",
            metric, value, unit,
            "As printed in summary Table 16; its untreated productivity/content differs from the Digester 1 section narrative/Table 13.",
            "Untreated or enzymatically pretreated Batch 2 grass, summary grouping not reactor-specific in the table heading.",
            "Table 16, printed p. 36",
            "Preserved as a distinct source summary, not reconciled with reactor-specific values; not suitable as a single calibration point.",
            evidence="B_primary_thesis_reported_summary", transfer="Belgian_managed_grassland_comparator")

# Digester sanitation test used commercial bird seed rather than recovered
# roadside weed species. This is a qualitative plant-seed proxy only.
SEED_TRANSFER = "Commercial_bird_seed_proxy_not_roadside_weed_species_or_digestate_regulatory_validation"
for metric, value, unit, basis, condition, location in [
    ("seed_sample_mass", "1", "g", "Seed mass used in the baseline germination test", "Commercial bird seed; source does not identify the botanical species in the methods excerpt", "Section 2.7.1, printed p. 21"),
    ("baseline_germination_observation_period", "5", "day", "Baseline seed germination observation duration", "Most untreated seeds showed root tails after five days", "Section 3.5, printed p. 37"),
    ("digester_seed_exposure_time_short", "15", "day", "Seed bag exposure time in digester", "Seeds were immersed in digestate at 51 degC; germinated for 14 days after retrieval; none germinated", "Sections 2.7.2 and 3.5, printed pp. 21, 37"),
    ("digester_seed_exposure_time_long", "30", "day", "Seed bag exposure time in digester", "Seeds were immersed in digestate at 51 degC; germinated for 14 days after retrieval; none germinated", "Sections 2.7.2 and 3.5, printed pp. 21, 37"),
    ("post_exposure_germination_observation", "14", "day", "Germination observation duration after seed-bag retrieval", "No seeds from the 15-day or 30-day exposure groups germinated", "Section 3.5, printed p. 37"),
]:
    add(f"GUA19-SEED-{metric.upper()}", "5;7", "sanitation_proxy_observation", "Bird-seed proxy",
        "Commercial bird seeds in cloth bag immersed in digestate", "51 degC thermophilic CSTR digestate exposure",
        metric, value, unit, basis, condition, location,
        "No roadside weed species, seed counts by species, germination denominator, or horticultural/fertilizer safety test reported.",
        evidence="B_primary_thesis_reported_method_or_qualitative_result", transfer=SEED_TRANSFER)

# Digestate analyses were performed but nutrient results are not tabulated in
# the accessible thesis text. Preserve the method evidence with empty numeric
# values rather than impute composition.
for analyte, method in [
    ("dry_matter", "BAM/deel3/03 gravimetry"),
    ("dry_organic_matter", "CMA/2/II/A.2 gravimetry"),
    ("crude_fat", "Soxhlet extraction and gravimetry"),
    ("volatile_fatty_acids", "GC-FID"),
    ("total_ammonia_nitrogen", "BAM/deel3/05 titrimetry"),
    ("total_nitrogen", "BAM/deel3/04 titrimetry"),
    ("pH_and_conductivity", "CMA/2/IV/13"),
    ("phosphorus", "EPA 3051A ICP-OES"),
]:
    add(f"GUA19-DIGESTATE-ASSAY-{analyte.upper()}", "7", "digestate_analysis_method",
        "Digestate from pilot CSTRs", "Digestate sampled weekly from both reactors",
        "digestate characterization", "analysis_protocol", "", "method",
        "Method only; thesis Table 8 lists the assay but the corresponding numeric nutrient/speciation results are not available in the extracted report tables.",
        "Weekly 100 mL digestate sample per reactor", "Table 8, printed p. 21",
        "Do not treat an assayed-but-unreported nutrient result as zero or as a fertilizer product composition.",
        evidence="B_primary_thesis_method_reported", transfer="Study-specific_digestate_method_no_numeric_result")


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], records: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def _upsert(path: Path, record: dict[str, str], key: str) -> None:
    fields, records = _read(path)
    if not fields:
        fields = list(record)
    old = next((row for row in records if row.get(key) == record[key]), None)
    if old is None:
        records.append(record)
    else:
        old.update(record)
    _write(path, fields, records)


def _update_registers() -> None:
    _upsert(FOLDER / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors_or_organization": AUTHOR,
        "year": "2019",
        "doi_or_stable_id": "No DOI identified; Ghent University master's dissertation, academic year 2018–2019",
        "source_url": SOURCE_URL,
    }, "source_id")
    _upsert(FOLDER / "dataset_manifest.csv", {
        "filename": CSV_PATH.name,
        "row_count": str(len(ROWS)),
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "reference_only_D3",
    }, "filename")

    audit = ROOT / "Greenhub/data/global_audit_package"
    relative = f"Bigas production + upgrade/AD reactor/{CSV_PATH.name}"
    _upsert(audit / "global_source_register.csv", {
        "dataset_path": relative,
        "dataset_group": "AD reactor",
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHOR,
        "year": "2019",
        "doi_or_stable_id": "No DOI identified; Ghent University master's dissertation, 2018–2019",
        "url": SOURCE_URL,
        "source_type": "Primary master's dissertation; experimental pilot-scale AD study",
        "notes": "Batch 1 was dried/ensiled Belgian roadside grass; Batch 2 was managed grassland. Tabulated source values and abstract-level limitations are staged separately; D3/reference-only.",
    }, "dataset_path")
    _upsert(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative,
        "category": "Biogas production + upgrade",
        "subgroup": "AD reactor",
        "filename": CSV_PATH.name,
        "row_count_observed": str(len(ROWS)),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Pilot-scale Belgian roadside/managed-grass AD comparator; single material batches, no uncertainty and incomplete nutrient results; not a runtime default.",
    }, "dataset_path")
    _upsert(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative,
        "category": "Biogas production + upgrade",
        "subgroup": "AD reactor",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": str(sum(1 for row in ROWS if row["reported_value"])),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "All table/text observations link to exact section/table/page; ambiguous Table 9 protein value is omitted; Table 16 summary conflict and missing digestate nutrient results are flagged.",
    }, "dataset_path")
    summary_path = audit / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifest = _read(audit / "global_dataset_manifest.csv")
    _, readiness = _read(audit / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for row in readiness:
        value = row.get("readiness", "")
        counts[value] = counts.get(value, 0) + 1
    summary["dataset_count"] = len(manifest)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    for row in ROWS:
        row["source_id"] = SOURCE_ID
    _write(CSV_PATH, FIELDS, ROWS)
    metadata = {
        "dataset_id": "urn:greenhub:dataset:ad:guanlao-2019-roadside-grass-pilot-digestion:v1",
        "title": TITLE,
        "source_id": SOURCE_ID,
        "authors": [AUTHOR],
        "publication_year": 2019,
        "source_url": SOURCE_URL,
        "doi": None,
        "persistent_identifier": "Ghent University master's dissertation, academic year 2018–2019; no DOI identified",
        "retrieval_date": RETRIEVED,
        "geography": "Zele and Quévy-le-Grand, Belgium; roadside batch origin and grassland comparator separately identified",
        "source_type": "Primary master's dissertation reporting two pilot CSTR experiments",
        "source_location": "Sections 2–3 and Tables 6–16, printed pp. 18–37; source URLs to the university library PDF",
        "license_or_rights": "No explicit open reuse license identified in the repository record or thesis. This extract contains short factual observations with citation; do not redistribute the thesis or figures.",
        "evidence_class": "B-tier primary experimental dissertation; reported pilot measurements, assay results and operating settings",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(ROWS),
        "sha256_csv": hashlib.sha256(CSV_PATH.read_bytes()).hexdigest(),
        "data_handling": "Transcribed only legible source-reported values and methods. The Table 9 protein row was omitted because extracted text alignment was ambiguous. Table 16 values are retained separately from the reactor-specific Table 13/narrative values rather than reconciled. No time-series graph points were digitized.",
        "limitations": [
            "Only Batch 1 is roadside grass; Batch 2 is a separate managed grassland comparator, with different harvest, drying and ensiling history.",
            "Batch 1 source is a heterogeneous roadside clipping batch from Zele, Belgium, not Dutch roadside/VARTA grass; crop composition and individual botanical fractions are not specified.",
            "One batch per feed class, small 33 L and 72 L pilot digesters, and no stated replicate uncertainty for yields.",
            "The source calls the EPi-test output biomethane potential. It is a source-specific calculation from feed composition, not a directly reported standardized BMP assay.",
            "Reported methane volumes are per tonne DOM; standard gas conditions are not stated, so values are not relabeled Nm3.",
            "Nominal operating conditions in Table 6 differ from average conditions in Tables 13 and 15; both are retained separately.",
            "Table 16 summary untreated methane productivity/content differs from the Digester 1 narrative and Table 13; no reconciliation is inferred.",
            "The enzyme tests apply to Batch 2 grassland, not Batch 1 roadside grass, and dilution sharply changed solids, OLR and HRT. Enzyme activity/dose per mass of dry feed and a water balance are unavailable.",
            "The methods list TAN, total N, phosphorus, conductivity and pH assays, but corresponding numeric nutrient/speciation results are not tabulated in the accessible thesis. Missing results remain missing, not zero.",
            "Sanitation used commercial bird seeds, not identified roadside weed species; this does not establish fertilizer or regulatory safety.",
            "No GreenHub default, model equation, UI setting, route, TEA/LCA factor or Pareto configuration consumes these records.",
        ],
    }
    CSV_PATH.with_suffix(".source.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _update_registers()
    print(f"wrote {len(ROWS)} reference-only thesis observations; sha256={metadata['sha256_csv']}")


if __name__ == "__main__":
    main()
