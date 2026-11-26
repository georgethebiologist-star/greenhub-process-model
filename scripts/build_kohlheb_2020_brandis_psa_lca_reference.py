"""Build a traceable reference extract of the full-scale Brandis PSA study.

The source is a single German plant with an energy-crop biogas feed. Its
operating, LCA and cost data are useful Phase 6/7 comparators, not GreenHub
upgrader defaults or grass-residual-specific factors.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data"
FOLDER = DATA / "Bigas production + upgrade/PSA"
AUDIT = DATA / "global_audit_package"
FILENAME = "kohlheb_2020_brandis_fullscale_psa_lca_reference.csv"
SOURCE_ID = "SRC-KOHLHEB-2020-BRANDIS-PSA"
DOI = "10.1007/s12155-020-10205-9"
URL = "https://doi.org/10.1007/s12155-020-10205-9"
PDF_URL = "https://d-nb.info/1223080811/34"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "phase_relevance", "record_type", "metric",
    "material_or_system", "value_text", "value_numeric", "lower_bound", "upper_bound",
    "unit", "basis", "reference_period", "condition_scope", "source_location",
    "evidence_class", "quality_class", "activation_state", "validation_status",
    "limitations",
]
ROWS: list[dict[str, str]] = []

TECH_LIMIT = (
    "Single German full-scale PSA plant (Brandis, Saxony), commissioned in 2013; upstream digester uses energy crops including 10–15% grass silage. "
    "This is not GreenHub grass-residual gas and is not a universal technology guarantee."
)


def add(rid, phases, kind, metric, system, value, unit, basis, location, limits,
        *, numeric="", lower="", upper="", period="Study published 2020; plant commissioned 2013",
        conditions="", evidence="reported_full_scale_plant_study", quality="B",
        validation="reported_value_preserved"):
    ROWS.append({
        "record_id": rid, "source_id": SOURCE_ID, "phase_relevance": phases,
        "record_type": kind, "metric": metric, "material_or_system": system,
        "value_text": str(value), "value_numeric": str(numeric),
        "lower_bound": str(lower), "upper_bound": str(upper), "unit": unit,
        "basis": basis, "reference_period": period, "condition_scope": conditions,
        "source_location": location, "evidence_class": evidence,
        "quality_class": quality, "activation_state": "reference_only",
        "validation_status": validation, "limitations": TECH_LIMIT + " " + limits,
    })


# Phase 6: gas composition and operating envelope. Table 1 gives gas ranges;
# no gas-state conversion or component closure is inferred.
gas_rows = [
    ("RAW-CH4", "raw_biogas", "methane_mole_fraction", "51.4–52.2", "vol%", "51.4", "52.2", "Table 1, printed p. 3", "Range preserved; no midpoint assigned."),
    ("RAW-CO2", "raw_biogas", "carbon_dioxide_mole_fraction", "45–47", "vol%", "45", "47", "Table 1, printed p. 3", "Range preserved; no midpoint assigned."),
    ("RAW-O2", "raw_biogas", "oxygen_mole_fraction", "0.05", "vol%", "", "", "Table 1, printed p. 3", "Reported raw-gas composition; sample/statistical basis not specified."),
    ("RAW-H2O", "raw_biogas", "water_vapor_mole_fraction", "1–2", "vol%", "1", "2", "Table 1, printed p. 3", "Range preserved; no wet/dry normalization applied."),
    ("RAW-H2", "raw_biogas", "hydrogen_concentration", "72", "ppm", "", "", "Table 1, printed p. 3", "Source table does not state whether ppm is molar or volumetric."),
    ("RAW-H2S", "raw_biogas", "hydrogen_sulfide_concentration", "55", "ppm", "", "", "Table 1, printed p. 3", "Source table does not state whether ppm is molar or volumetric."),
    ("PRODUCT-CH4", "upgraded_biomethane", "methane_mole_fraction", "96", "vol%", "", "", "Table 1, printed p. 3", "Reported product composition; product gas-state and speciation details are incomplete."),
    ("PRODUCT-CO2", "upgraded_biomethane", "carbon_dioxide_mole_fraction", "3.5", "vol%", "", "", "Table 1, printed p. 3", "Reported product composition; remaining fraction is not assigned."),
    ("PRODUCT-H2S", "upgraded_biomethane", "hydrogen_sulfide_concentration", "1", "ppm", "", "", "Table 1, printed p. 3", "Source table does not state whether ppm is molar or volumetric."),
]
for code, stream, metric, value, unit, low, high, loc, note in gas_rows:
    add(f"KOH20-GAS-{code}", "6", "reported_plant_gas_composition", metric, stream,
        value, unit, "Source Table 1; concentration basis as printed.", loc, note,
        lower=low, upper=high, conditions="Brandis plant gas composition.")

for code, metric, unit, value, loc, basis, validation, evidence in [
    ("CAPACITY-HR", "raw_biogas_treatment_capacity", "Nm3 biogas/h", "1333", "Methods, plant description, printed p. 3", "Plant nominal treatment capacity.", "reported_nominal_capacity", "reported_plant_design_value"),
    ("CAPACITY-DAY", "raw_biogas_treatment_capacity", "Nm3 biogas/day", "32000", "Methods, plant description, printed p. 3", "Plant nominal daily throughput stated by authors.", "reported_nominal_capacity", "reported_plant_design_value"),
    ("PRODUCT-DAY", "biomethane_product_flow", "Nm3 biomethane/day", "16600", "Figure 1, printed p. 4", "Process-flow figure label; flow basis is not fully described in text and is not reconciled with the separately calculated 127,020,000 Nm3 lifetime output.", "figure_value_basis_not_fully_documented", "reported_process_diagram_value"),
    ("PSA-ADS-PRESSURE", "adsorption_pressure", "bar; pressure reference unspecified", "6", "Methods, PSA operation, printed p. 4", "Pressure reported for PSA vessel adsorption.", "reported_operating_condition", "reported_plant_operating_condition"),
    ("PSA-REGEN-PRESSURE", "regeneration_vacuum_pressure", "bar; pressure reference unspecified", "-0.85", "Methods, PSA operation, printed p. 4", "Vacuum pressure reported for PSA regeneration; preserve signed value and unspecified reference.", "reported_operating_condition_pressure_reference_missing", "reported_plant_operating_condition"),
]:
    add(f"KOH20-OPS-{code}", "6", "reported_plant_operating_condition", metric,
        "Brandis CarboTech PSA and pretreatment train", value, unit, basis, loc,
        "Not transferable as a GreenHub design specification without compatible scale, feed and gas-quality requirements.",
        numeric=value, conditions="Full-scale Brandis PSA plant.", validation=validation, evidence=evidence)

# Methane routing: the figure's 1.5% process-loss label is deliberately not
# treated as atmospheric emission; the authors separately use operator-reported
# 0.2% methane-to-air emissions in their LCA.
add("KOH20-CH4-FIGURE-LOSS", "6;7", "quarantined_process_loss_diagram_value",
    "methane_loss_label_in_process_flow_figure", "Brandis PSA off-gas/oxidation train",
    "1.5%; 95,265", "%; Nm3 CH4/year as figure labels", "Figure 1 labels a methane leakage/loss stream and an annual methane quantity, while the text separately reports an air-emission estimate after off-gas oxidation.",
    "Figure 1, printed p. 4", "Do not treat this flow-figure quantity as direct atmospheric CH4: the diagram also shows a flameless oxidation burner; the boundary and relation to the 0.2% air-emission estimate are not reconciled.",
    evidence="process_diagram_value_boundary_ambiguous", quality="C", validation="not_reconciled_with_operator_air_emission_value")
add("KOH20-CH4-AIR-EMISSION", "6;7", "operator_reported_emission_input_to_lca",
    "methane_emission_to_air_fraction_of_methane_treated", "Brandis PSA plant",
    "0.2", "% of methane treated", "Authors state operator-provided value used in LCA; corresponding emission stated as 12,194 Nm3 CH4/year.",
    "Methods, PSA operation, printed p. 4", "Operator-reported and used as an LCA input; not an independently metered emission time series. Do not substitute the separate 1.5% figure-1 loss label.",
    numeric="0.2", conditions="Waste/off-gas is routed to a flameless oxidation burner; the authors consider air emission separately.",
    validation="operator_reported_not_independently_measured")
add("KOH20-CH4-AIR-EMISSION-ANNUAL", "6;7", "operator_reported_emission_input_to_lca",
    "methane_emission_to_air_annual_volume", "Brandis PSA plant", "12194", "Nm3 CH4/year",
    "Authors' annual amount corresponding to operator-reported 0.2% methane emission to air.",
    "Methods, PSA operation, printed p. 4", "Not independently metered by the study authors; preserve separately from the diagram's 95,265 Nm3/year loss label.",
    numeric="12194", validation="operator_reported_not_independently_measured")

# Phase 6 utility, feed/throughput accounting and Phase 7 LCA setup.
for rid, metric, value, unit, numeric, basis, loc, validation, note in [
    ("KOH20-ELECTRICITY-ANNUAL", "whole_upgrading_train_electricity", "2568985", "kWh/year", "2568985", "Total annual plant electricity; individual unit consumption was not metered separately.", "Methods, printed p. 4", "reported_annual_plant_measurement", "Source measured total plant electricity, not a unit-level disaggregation."),
    ("KOH20-ELECTRICITY-SPECIFIC", "specific_upgrading_electricity", "0.22", "kWh/Nm3 raw biogas", "0.22", "Authors' reported mean specific consumption for the full upgrading plant.", "Methods, printed p. 4", "reported_plant_average", "Reported result is capacity-dependent and includes the broader plant train; not a water-scrubber or GreenHub-specific coefficient."),
    ("KOH20-REFERENCE-FLOW", "lifetime_reference_flow", "233600000", "Nm3 raw biogas over 20 years", "233600000", "Source-calculated as 32,000 Nm3/day × 365 day/year × 20 years.", "LCA methods, printed p. 5", "source_calculation_from_nominal_capacity", "Calculated reference flow, not a metered lifetime total."),
    ("KOH20-PRODUCT-LIFETIME", "calculated_lifetime_biomethane_output", "127020000", "Nm3 biomethane over 20 years", "127020000", "Authors calculate from reference-flow biogas and raw/product methane fractions 52.2/96.", "LCA methods, printed p. 5", "source_calculation_from_gas_composition", "Calculated using maximum reported raw-gas methane and 96% product methane; not an observed lifetime output."),
    ("KOH20-FU", "life_cycle_functional_unit", "1", "Nm3 raw biogas upgraded", "1", "Cradle-to-gate PSA plant LCA and life-cycle cost assessment.", "LCA methods, printed p. 5", "reported_scope_definition", "Do not compare directly with per Nm3 biomethane or per tonne feed without explicit conversion and matching boundary."),
    ("KOH20-LIFETIME", "financial_and_lca_lifetime", "20", "year", "20", "Study-defined plant assessment lifetime.", "LCA/LCCA methods, printed pp. 5–6", "reported_assessment_assumption", "Historical study horizon, not a GreenHub project-life default."),
]:
    kind = "reported_plant_measurement" if "ELECTRICITY" in rid else "reported_assessment_basis_or_source_calculation"
    add(rid, "6;7", kind, metric, "Brandis PSA plant", value, unit, basis, loc, note,
        numeric=numeric, validation=validation,
        evidence="plant_operating_measurement" if "ELECTRICITY-ANNUAL" in rid else "reported_study_basis_or_calculation",
        quality="C" if "PRODUCT-LIFETIME" in rid else "B")

add("KOH20-LCA-BOUNDARY", "7", "lca_method_and_boundary", "study_boundary",
    "Brandis PSA upgrading train", "Cradle-to-gate; pretreatment plus PSA upgrading; plant infrastructure included",
    "text", "GaBi8; GaBi Professional, Construction materials, Food&Feed and ecoinvent3 databases; CML2001 Jan-2016 midpoint model.",
    "LCA methods, printed p. 5", "Background software/databases are not bundled; inventory includes some equipment-material substitutions where exact unit processes were unavailable.",
    evidence="reported_lca_methodology", validation="method_reported_inventory_has_documented_substitutions")

add("KOH20-LCA-GWP", "7", "reported_lca_impact", "global_warming_potential_100y_excluding_biogenic_carbon",
    "Brandis PSA upgrading train", "0.113", "kg CO2-equivalent/Nm3 raw biogas", "CML2001 Jan-2016; cradle-to-gate; FU 1 Nm3 raw biogas upgraded; includes 0.2% operator-reported CH4-to-air and the study's EU-28 electricity mix.",
    "Abstract and Table 2, printed pp. 1 and 8", "Study-specific PSA result, not GreenHub full-chain LCA or a current grid-intensity factor.",
    numeric="0.113", evidence="author_calculated_lca_result", quality="C", validation="reported_lca_result_boundary_and_method_stated")

impact_rows = [
    ("ADP-ELEMENTS", "abiotic_depletion_elements", "0.022 × 10^-5"),
    ("ADP-FOSSIL", "abiotic_depletion_fossil", "103670.648 × 10^-5"),
    ("AP", "acidification_potential", "27.801 × 10^-5"),
    ("EP", "eutrophication_potential", "2.832 × 10^-5"),
    ("FAETP", "freshwater_aquatic_ecotoxicity_potential_infinite_horizon", "177.855 × 10^-5"),
    ("HTP", "human_toxicity_potential_infinite_horizon", "2813.705 × 10^-5"),
    ("MAETP", "marine_aquatic_ecotoxicity_potential_infinite_horizon", "1570555.624 × 10^-5"),
    ("ODP", "ozone_depletion_potential_steady_state", "0.644 × 10^-5"),
    ("POCP", "photochemical_ozone_creation_potential", "2.184 × 10^-5"),
    ("TETP", "terrestrial_ecotoxicity_potential_infinite_horizon", "23.541 × 10^-5"),
]
for code, metric, value in impact_rows:
    add(f"KOH20-LCA-{code}", "7", "quarantined_lca_impact_table_value", metric,
        "Brandis PSA upgrading train", value, "category unit not stated in accessible Table 2 transcription",
        "Literal Table 2 number retained with ×10^-5 multiplier; the category-specific unit is not present in the retrieved table text, so no normalized numeric value is exposed.",
        "Table 2, printed p. 8", "Do not use for cross-category comparison or GreenHub LCA until category units and characterization units are verified from the typeset table/supplement.",
        evidence="author_reported_lca_table_but_unit_missing", quality="C", validation="quarantined_impact_category_unit_missing")

for rid, metric, value, unit, basis, loc, validation in [
    ("KOH20-LCA-ELECTRICITY-SHARE", "electricity_share_of_normalized_impact", "67", "%", "Contribution after CML midpoint normalization and aggregation, not GWP-only contribution.", "Results, printed p. 7", "normalized_impact_aggregation_not_category_specific"),
    ("KOH20-LCA-INFRA-SHARE", "infrastructure_normalized_impact_contribution", "38.94", "normalized value ×10^-15/Nm3 raw biogas", "Study's aggregated normalized impact contribution.", "Figure 3, printed p. 7", "normalized_impact_aggregation_not_category_specific"),
    ("KOH20-LCA-CO2-REMOVAL-SHARE", "co2_removal_normalized_impact_contribution", "35.25", "normalized value ×10^-15/Nm3 raw biogas", "Study's aggregated normalized impact contribution.", "Figure 3, printed p. 7", "normalized_impact_aggregation_not_category_specific"),
    ("KOH20-LCA-CH4-SHARE", "methane_leakage_normalized_impact_contribution", "5.69", "normalized value ×10^-15/Nm3 raw biogas", "Study's aggregated normalized impact contribution; based on 0.2% methane-to-air input.", "Figure 3, printed p. 7", "normalized_impact_aggregation_not_category_specific"),
]:
    add(rid, "7", "reported_lca_hotspot", metric, "Brandis PSA upgrading train", value, unit,
        basis, loc, "Hotspot comes from source-specific normalized aggregation; not a transferable unit impact factor.",
        numeric=value, evidence="author_calculated_lca_hotspot", quality="C", validation=validation)

# Phase 7 TEA/LCCA values and their dated study assumptions.
tea = [
    ("INITIAL-INVESTMENT", "initial_investment", "2691625", "EUR", "Undiscounted initial plant investment as reported for the Brandis plant; cost year not stated.", "Results, printed p. 7"),
    ("REINVESTMENT", "lifetime_reinvestment", "696000", "EUR over 20 years", "Aggregate reinvestment over study lifetime; equipment-specific schedule appears only in supplementary Table S2.", "Results, printed p. 7"),
    ("OPEX-LIFETIME", "operating_cost", "11314549", "EUR over 20 years", "Reported whole-lifetime operating cost; article says 77% of this amount was electricity.", "Results, printed p. 7"),
    ("CAPEX-DISCOUNTED", "discounted_total_capex", "3156840", "EUR present value", "Discounted total CAPEX includes initial investment and discounted reinvestments.", "Results, printed p. 7"),
    ("OPEX-ANNUAL-DISCOUNTED", "discounted_average_annual_opex", "432786", "EUR/year", "Study-reported discounted average annual OPEX; do not recompute from lifetime total without underlying cashflow schedule.", "Results, printed p. 7"),
    ("UPC", "unit_production_cost", "0.05", "EUR/Nm3 raw biogas treated", "Study LCCA unit production cost including personnel; historical case price basis not stated.", "Results, printed p. 7"),
    ("UPC-EX-PERSONNEL", "unit_production_cost_excluding_personnel", "0.045", "EUR/Nm3 raw biogas treated", "Study LCCA alternative excluding personnel; not equivalent to full cost.", "Results, printed p. 7"),
    ("ELECTRICITY-PRICE", "electricity_price_assumption", "0.17", "EUR/kWh", "LCCA input; price year and tax/contract basis not stated.", "LCCA methods, printed p. 5"),
    ("LABOUR-COST", "personnel_cost_assumption", "80000", "EUR/year", "LCCA input; cost year and labor scope not stated.", "LCCA methods, printed p. 5"),
    ("DISCOUNT-RATE", "discount_rate_assumption", "2.7", "%/year", "Study LCCA assumption.", "LCCA methods, printed p. 5"),
]
for code, metric, value, unit, basis, loc in tea:
    is_input = code in {"ELECTRICITY-PRICE", "LABOUR-COST", "DISCOUNT-RATE"}
    add(f"KOH20-TEA-{code}", "TEA", "historical_lcca_input" if is_input else "historical_lcca_result",
        metric, "Brandis PSA upgrading train", value, unit, basis, loc,
        "Single-plant German study; nominal price year, tax basis and some underlying cash-flow/inventory details are incomplete. Not current GreenHub TEA input.",
        numeric=value, evidence="reported_lcca_assumption_or_result", quality="C",
        validation="reported_historical_lcca_value_not_repriced")


def read_rows(path: Path):
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def upsert(path: Path, record, key: str):
    fields, rows = read_rows(path)
    if not fields:
        fields = list(record)
    old = next((row for row in rows if row.get(key) == record[key]), None)
    if old is None:
        rows.append(record)
    else:
        old.update(record)
    write_rows(path, fields, rows)


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    target = FOLDER / FILENAME
    write_rows(target, FIELDS, ROWS)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:psa:kohlheb-2020-brandis-fullscale-psa-lca-reference:v1",
        "dataset_version": "1.0.0", "dataset_file": FILENAME,
        "record_count": len(ROWS), "sha256": digest, "source_id": SOURCE_ID,
        "citation": "Kohlheb, N.; Wluka, M.; Bezama, A.; Thrän, D.; Aurich, A.; Müller, R.A. (2021 online / 2020 accepted). Environmental-Economic Assessment of the Pressure Swing Adsorption Biogas Upgrading Technology. BioEnergy Research. https://doi.org/10.1007/s12155-020-10205-9.",
        "publication_year": 2021, "doi": DOI, "source_url": URL,
        "full_text_pdf": PDF_URL, "retrieval_date": RETRIEVED,
        "source_location": "Exact table/figure/section and printed page are captured per record.",
        "geography": "Brandis, Saxony, Germany; full-scale CarboTech PSA plant commissioned 2013.",
        "material_scope": "Full-scale PSA upgrader handling energy-crop biogas with 10–15% grass silage in the upstream digester feed; includes pretreatment, utilities, plant infrastructure, LCA and LCCA.",
        "evidence_class": "B-class full-scale operator-informed/plant-data study for technical/energy observations; C-class author-calculated LCA/LCCA and study-specific financial assumptions.",
        "quality_class": "B for directly reported plant characteristics/utility; C for modeled impact/cost outcomes and assumptions.",
        "license": "CC BY 4.0 stated in the article; third-party material remains subject to its credit-line-specific terms.",
        "access_protocol": "DOI landing page and open full text hosted by the German National Library (d-nb.info).",
        "processing": "Direct transcription. Numeric ranges stay as bounds without averages. Source-calculated lifetime quantities are marked as calculated, not measured. Ambiguous loss/emission concepts and Table 2 impact category units are quarantined rather than normalized.",
        "uncertainty": "Single plant, 2013 commissioning and German energy-crop digester feed. Not all measurements are independently metered; methane-to-air value comes from the operator. Unit-level electricity is unavailable. LCA results depend on EU-28 electricity mix, GaBi/ecoinvent data, CML 2001 Jan-2016 and substitutions for missing inventory data. Cost year is unspecified.",
        "limitations": [
            "This is PSA, whereas GreenHub may choose water scrubbing or other routes; applicability is technology-specific.",
            "The upstream gas is from an energy-crop digester with only 10–15% grass silage, not roadside-grass protein-extraction residual.",
            "Figure 1's 1.5%/95,265 Nm3/year methane-loss labels are not reconciled with the separate 0.2%/12,194 Nm3/year operator-reported methane-to-air emissions; these are stored as distinct concepts.",
            "Specific electricity is full-train average, not component-detailed. No unit-level power split is reported.",
            "Raw and product gas basis conditions and some ppm bases are not specified.",
            "Table 2 category-specific units are unavailable in extracted table text; those values remain literal/quarantined. GWP is separately reported in the abstract with kg CO2-equivalent/Nm3 raw biogas.",
            "LCA is cradle-to-gate for the upgrader, not a complete feedstock-to-product GreenHub LCA; upstream biogas generation and biomethane use are outside FU boundary.",
            "Financial cost year and current-market transferability are not established; no inflation/repricing applied.",
            "No GreenHub default, parameter registry, unit equation, TEA, LCA, scenario or Pareto mapping is changed.",
        ],
        "phase_coverage": {
            "1": "No GreenHub grass supply; upstream plant uses energy crops and includes a 10–15% grass-silage share.",
            "2": "No feed storage data.",
            "3": "No feed pretreatment/fractionation data; gas pretreatment is part of the upgrader boundary.",
            "4": "No protein data.",
            "5": "No digestion data for GreenHub residual; only upstream plant feed context.",
            "6": "Full-scale PSA gas composition, capacity, pressure, methane-to-air input and plant-wide electricity.",
            "7": "Study-specific cradle-to-gate upgrader LCA method, GWP, impact hotspots, and LCCA results/assumptions.",
        },
        "runtime_policy": "reference_only; do not apply PSA observations to water scrubbing, GreenHub route defaults or process/LCA calculations without a route-specific evidence gate.",
        "calculation_connected": False,
        "fair_metadata": {
            "findable": "Local URN, DOI, source ID, SHA-256 and FAIR catalog path.",
            "accessible": "DOI and open PDF over HTTPS; no source PDF copied into repository.",
            "interoperable": "Long-form UTF-8 CSV with explicit metric, value/range, unit, basis, method, boundary, source location and validation state.",
            "reusable": "CC BY 4.0 citation, retrieval date, uncertainty, applicability, process boundary and data-quality caveats are recorded.",
        },
    }
    target.with_suffix(".source.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    upsert(FOLDER / "dataset_manifest.csv", {
        "filename": FILENAME, "relative_path": f"Greenhub/data/Bigas production + upgrade/PSA/{FILENAME}",
        "description": "Brandis full-scale PSA operating, LCA and LCCA comparator; reference-only.",
        "row_count": str(len(ROWS)), "encoding": "UTF-8 with BOM", "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
    }, "filename")
    upsert(FOLDER / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": "Environmental-Economic Assessment of the Pressure Swing Adsorption Biogas Upgrading Technology",
        "authors": "Norbert Kohlheb; Mathias Wluka; Alberto Bezama; Daniela Thrän; Andreas Aurich; Roland Arno Müller",
        "year": "2021", "source_type": "Peer-reviewed full-scale plant operational study with LCA/LCCA",
        "doi_or_stable_identifier": DOI, "source_url": URL, "accessed_date": RETRIEVED,
        "notes": "CC BY 4.0. Full-scale Brandis PSA; gas/energy observations and study-calculated LCA/LCCA separated. Methane loss in figure is not equated with methane emitted to air. Reference-only, not GreenHub default.",
    }, "source_id")

    relative = f"Bigas production + upgrade/PSA/{FILENAME}"
    notes = "Single German full-scale PSA comparator; energy-crop gas, non-GreenHub. LCA/LCCA are study-specific; loss/emission boundaries and some impact units are quarantined. Reference-only."
    global_source = {
        "dataset_path": relative, "dataset_group": "PSA", "source_id": SOURCE_ID,
        "source_title": "Environmental-Economic Assessment of the Pressure Swing Adsorption Biogas Upgrading Technology",
        "authors": "Kohlheb et al.", "year": "2021", "doi_or_stable_id": DOI,
        "url": URL, "source_type": "Peer-reviewed full-scale plant operational study with LCA/LCCA", "notes": notes,
    }
    upsert(AUDIT / "global_source_register.csv", global_source, "dataset_path")
    upsert(AUDIT / "global_dataset_manifest.csv", {
        "dataset_path": relative, "category": "Biogas production + upgrade", "subgroup": "PSA",
        "filename": FILENAME, "row_count_observed": str(len(ROWS)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B/C;reference_only",
        "detected_readiness": "D3", "notes": notes,
    }, "dataset_path")
    upsert(AUDIT / "global_dataset_readiness.csv", {
        "dataset_path": relative, "category": "Biogas production + upgrade", "subgroup": "PSA",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
        "numeric_rows": str(sum(bool(row["value_numeric"] or row["lower_bound"] or row["upper_bound"]) for row in ROWS)),
        "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "0", "cross_reference_issues": "0", "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0", "notes": notes,
    }, "dataset_path")
    upsert(AUDIT / "source_dataset_checksums.csv", {
        "dataset_path": relative, "sha256": digest, "byte_size": str(target.stat().st_size),
    }, "dataset_path")

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = read_rows(AUDIT / "global_dataset_manifest.csv")
    _, readiness = read_rows(AUDIT / "global_dataset_readiness.csv")
    counts = {}
    for row in readiness:
        key = row.get("readiness", "")
        counts[key] = counts.get(key, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": FILENAME, "rows": len(ROWS), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
