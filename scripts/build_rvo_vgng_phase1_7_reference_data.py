"""Build traceable, reference-only grass-supply and biogas evidence extracts.

This extract preserves statements from the RVO-commissioned 2014 study and
the 2025 Van Gras Naar Gas report. It is a literature/economic comparator,
not a source of GreenHub defaults or runtime parameters.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP"
RETRIEVED = "2026-11-08"
RVO_ID = "SRC-RVO-BRINKMANN-GRASS-2014"
VGNG_ID = "SRC-VGNG-INTERREG-2025"
RVO_URL = "https://www.rvo.nl/sites/default/files/2014/04/Definitief_Een%20studie%20naar%20kansen%20voor%20grasvergisting.pdf"
VGNG_URL = "https://www.hanze.nl/binaries/_cb_1758882594458/content/assets/hanze/nl/onderzoeken/kenniscentra-en-centres-of-expertise/kenniscentrum-biobased-economy/eindrapport-van-gras-naar-gas.pdf"

FIELDS = [
    "record_id", "source_id", "phase_relevance", "record_type", "material",
    "geography", "metric", "value_text", "value_numeric", "lower_bound",
    "upper_bound", "unit", "basis", "reference_period", "condition_scope",
    "source_location", "evidence_class", "quality_class", "activation_state",
    "transferability", "validation_status", "limitations",
]

RVO_ROWS: list[dict[str, str]] = []
VGNG_ROWS: list[dict[str, str]] = []


def add(rows, source_id, record_id, phases, record_type, material, geography,
        metric, value_text, unit, basis, period, conditions, location,
        limitations, *, value_numeric="", lower_bound="", upper_bound="",
        evidence="directly_reported_in_official_or_project_report",
        quality="B", validation="reported_value_preserved",
        transfer="Dutch_or_border_region_comparator_not_GreenHub_measurement"):
    rows.append({
        "record_id": record_id,
        "source_id": source_id,
        "phase_relevance": phases,
        "record_type": record_type,
        "material": material,
        "geography": geography,
        "metric": metric,
        "value_text": value_text,
        "value_numeric": value_numeric,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "unit": unit,
        "basis": basis,
        "reference_period": period,
        "condition_scope": conditions,
        "source_location": location,
        "evidence_class": evidence,
        "quality_class": quality,
        "activation_state": "reference_only",
        "transferability": transfer,
        "validation_status": validation,
        "limitations": limitations,
    })


def rvo(record_id, phases, record_type, material, metric, value_text, unit,
        basis, location, limitations, *, value_numeric="", lower_bound="",
        upper_bound="", period="reported in 2014 study; source period as noted",
        conditions="", quality="B", validation="reported_value_preserved",
        evidence="directly_reported_in_official_or_project_report"):
    add(RVO_ROWS, RVO_ID, record_id, phases, record_type, material, "Netherlands",
        metric, value_text, unit, basis, period, conditions, location, limitations,
        value_numeric=value_numeric, lower_bound=lower_bound, upper_bound=upper_bound,
        quality=quality, validation=validation, evidence=evidence,
        transfer="Historical_Netherlands_estimate_or_case_not_current_delivered_GreenHub_supply")


def vgng(record_id, phases, record_type, material, metric, value_text, unit,
         basis, location, limitations, *, geography="Netherlands/Germany border-region report",
         value_numeric="", lower_bound="", upper_bound="", period="reported in 2025 report; underlying period not specified",
         conditions="", quality="B", validation="reported_value_preserved",
         evidence="directly_reported_in_project_report", transfer=None):
    add(VGNG_ROWS, VGNG_ID, record_id, phases, record_type, material, geography,
        metric, value_text, unit, basis, period, conditions, location, limitations,
        value_numeric=value_numeric, lower_bound=lower_bound, upper_bound=upper_bound,
        quality=quality, validation=validation, evidence=evidence,
        transfer=transfer or "Regional_project_estimate_or_cross-feedstock_comparator_not_GreenHub_measurement")


# RVO (2014): the report itself explains that it synthesizes prior studies,
# LMA/BVOR waste statistics, and stakeholder interviews rather than repeating
# a national primary biomass survey.
RVO_AVAILABILITY_LIMIT = (
    "The RVO report explicitly says exact national quantities are unavailable. "
    "This is a secondary estimate, not a measured or contracted supply; source "
    "definitions and collection eligibility differ. Do not aggregate with other estimates."
)
for record_id, material, metric, value, unit, basis, location, low, high, note in [
    ("RVO14-PROCEDE-VERGE-DM", "roadside verge grass", "annual_dry_mass_estimate", "240000", "tonne DM/year", "Procedé Biomass 2009 estimate as summarized by RVO", "§2.2, summary of Procedé Biomass (2009), printed p. 7", "", "", "The source's own estimate; not a current inventory."),
    ("RVO14-PROCEDE-VERGE-FRESH-LOW", "roadside verge grass", "annual_fresh_mass_estimate_lower", "800000", "tonne fresh matter/year", "Procedé Biomass estimate converted by RVO using 20–30% DM", "§2.2, summary of Procedé Biomass (2009), printed p. 7", "800000", "1200000", "The 0.8–1.2 million tonne fresh range is represented by paired low/high rows."),
    ("RVO14-PROCEDE-VERGE-FRESH-HIGH", "roadside verge grass", "annual_fresh_mass_estimate_upper", "1200000", "tonne fresh matter/year", "Procedé Biomass estimate converted by RVO using 20–30% DM", "§2.2, summary of Procedé Biomass (2009), printed p. 7", "800000", "1200000", "The 0.8–1.2 million tonne fresh range is represented by paired low/high rows."),
    ("RVO14-PROCEDE-VERGE-DM-FRACTION", "roadside verge grass", "dry_matter_fraction_assumed_for_fresh_conversion", "20–30", "% fresh matter", "The report gives a range used to translate dry matter to fresh mass", "§2.2, summary of Procedé Biomass (2009), printed p. 7", "20", "30", "This is a conversion range in the summarized source, not a VARTA measurement."),
    ("RVO14-PROCEDE-WATERWAY-FRESH", "waterway vegetation/ditch clippings", "annual_fresh_mass_estimate", "1000000", "tonne fresh matter/year", "Procedé Biomass estimate summarized by RVO", "§2.2, summary of Procedé Biomass (2009), printed p. 7", "", "", "RVO says most of this stream remains at source and is difficult to quantify."),
    ("RVO14-PROCEDE-WATERWAY-DM", "waterway vegetation/ditch clippings", "annual_dry_mass_estimate_as_printed", "350", "tonne DM/year as printed; possible scale ambiguity", "Procedé Biomass estimate summarized by RVO; the report text says 350 tonnes DM without a kton qualifier", "§2.2, summary of Procedé Biomass (2009), printed p. 7", "", "", "The printed fresh-to-dry scale is implausible for this stream. Preserve the report wording; do not infer 350 kton."),
    ("RVO14-ECOFYS-VERGE-FRESH-2020", "roadside verge grass", "annual_fresh_mass_projection", "500000", "tonne fresh matter/year", "Ecofys 2008 projected 2020 production estimate", "§2.2, summary of Ecofys (2008), printed p. 7", "", "", "The source reports other studies ranging 400–1000 kton/year; keep the range separate."),
    ("RVO14-ECOFYS-VERGE-DM-2020", "roadside verge grass", "annual_dry_mass_projection", "250000", "tonne DM/year", "Ecofys 2008 projected 2020 estimate", "§2.2, summary of Ecofys (2008), printed p. 7", "", "", "Projected value, not measured collection."),
    ("RVO14-ECOFYS-VERGE-RANGE-LOW", "roadside verge grass", "reported_cross-study_fresh_mass_range_lower", "400000", "tonne fresh matter/year", "RVO reports studies ranging 400–1000 kton/year", "§2.2, summary of Ecofys (2008), printed p. 7", "400000", "1000000", "Cross-study range; exact studies and boundaries vary."),
    ("RVO14-ECOFYS-VERGE-RANGE-HIGH", "roadside verge grass", "reported_cross-study_fresh_mass_range_upper", "1000000", "tonne fresh matter/year", "RVO reports studies ranging 400–1000 kton/year", "§2.2, summary of Ecofys (2008), printed p. 7", "400000", "1000000", "Cross-study range; exact studies and boundaries vary."),
    ("RVO14-ECOFYS-NATURE-DM", "nature grass", "annual_dry_mass_projection", "1000000", "tonne DM/year", "Ecofys estimate summarized by RVO", "§2.2, summary of Ecofys (2008), printed p. 7", "", "", "Not the same as collectable or delivered quantity."),
    ("RVO14-ECOFYS-NATURE-AVAILABLE-FRACTION", "nature grass", "conditional_energy_availability_fraction", "32", "% of estimated production", "Ecofys estimate for the share conditionally available, as summarized by RVO", "§2.2, summary of Ecofys (2008), printed p. 7", "", "", "RVO says the 32% availability fraction is not further substantiated."),
    ("RVO14-ECOFYS-NATURE-AVAILABLE-DM", "nature grass", "annual_dry_mass_conditionally_available", "345000", "tonne DM/year", "RVO's reported corresponding availability estimate", "§2.2, summary of Ecofys (2008), printed p. 7", "", "", "RVO reports 345 kton; 32% of 1,000 kton would be 320 kton. Preserve discrepancy; do not correct."),
]:
    record_period = "source-specific estimate; see basis; not current-year supply"
    if "2020" in record_id:
        record_period = "Ecofys projected year 2020"
    validation = "source_unit_scale_anomaly_unresolved" if record_id == "RVO14-PROCEDE-WATERWAY-DM" else (
        "secondary_estimate_not_primary_measurement" if "PROCEDE" in record_id or "ECOFYS" in record_id
        else "reported_value_preserved"
    )
    rvo(record_id, "1", "national_resource_estimate", material, metric, value, unit,
        basis, location, RVO_AVAILABILITY_LIMIT + " " + note,
        value_numeric=value if value.replace(".", "", 1).isdigit() else "",
        lower_bound=low, upper_bound=high, period=record_period,
        quality="B", validation=validation)

for record_id, material, metric, value, unit, basis, note, low, high in [
    ("RVO14-BVOR-COMPOST-FEED-GREEN-WASTE-LOW", "grass and ditch clippings in green waste", "annual_quantity_lower", "1500000", "tonne/year", "BVOR estimate: 4–5 Mt total green waste × 30–40% grass including ditch clippings", "RVO says quantitative data for unreported and locally processed routes are unavailable; not a weighbridge census.", "1500000", "2000000"),
    ("RVO14-BVOR-COMPOST-FEED-GREEN-WASTE-HIGH", "grass and ditch clippings in green waste", "annual_quantity_upper", "2000000", "tonne/year", "BVOR estimate: 4–5 Mt total green waste × 30–40% grass including ditch clippings", "RVO says quantitative data for unreported and locally processed routes are unavailable; not a weighbridge census.", "1500000", "2000000"),
    ("RVO14-VERGE-GRASS-COLLECTED-LOWER-BOUND", "roadside verge grass", "annual_quantity_lower_bound", ">1000000", "tonne/year; moisture basis varies across underlying studies", "RVO synthesis of prior studies; says the largest share of the collected grass is verge grass", "The report itself notes moisture-basis differences among studies.", "1000000", ""),
    ("RVO14-NATURE-DITCH-COLLECTED-RANGE", "nature grass and ditch clippings", "annual_quantity_collected_for_offsite_processing", "500000–1000000", "tonne/year; moisture basis varies across underlying studies", "RVO synthesis; quantities mown are higher than amounts transported off-site", "Do not treat as all biomass cut or as available to GreenHub.", "500000", "1000000"),
    ("RVO14-CURRENT-GRASS-AD-LOWER-BOUND", "grass in anaerobic digestion", "annual_digestive_use_upper_bound", "<50000", "tonne/year; basis inherited from source summary", "RVO synthesis of BVOR/LMA analysis and stakeholder input", "Not a precise measured national total; co-digester reporting was incomplete.", "", "50000"),
]:
    rvo(record_id, "1;5", "national_resource_or_route_estimate", material, metric, value, unit,
        basis, "§2.2–2.4, printed pp. 7–9", RVO_AVAILABILITY_LIMIT + " " + note,
        value_numeric="", lower_bound=low, upper_bound=high,
        period="historical estimate around 2012–2014; exact year depends on underlying source",
        quality="B", validation="secondary_estimate_not_primary_measurement")

for record_id, metric, value_text, value_numeric, unit, basis, location, note in [
    ("RVO14-COMPOST-FEE", "professional_composting_fee", "10–20", "", "EUR/t incoming grass; wet-mass basis stated for chain cost context", "Range for professional composting; no site/date-specific quote", "§2.3–2.4, printed pp. 8–9", "Historical nominal cost comparator; do not use as current GreenHub logistics cost without repricing."),
    ("RVO14-LOCAL-SPREAD-FEE", "local_land_application_cost", "a few euros", "", "EUR/t grass; wet-mass basis not separately stated", "Qualitative lower-cost alternative reported by RVO", "§2.3, printed p. 8", "No exact amount or underlying contract evidence."),
    ("RVO14-GRASS-BIOGAS-LITERATURE-RANGE", "specific_biogas_yield_range", "30–300", "", "Nm3 biogas/t grass; source bases across cited literature vary", "RVO's broad literature range; gas is biogas, not methane", "§2.4, printed p. 9", "Underlying source studies, moisture basis and assay conditions are not collated in this statement; not a yield distribution."),
    ("RVO14-GRASS-CHAIN-EXTRA-HARVEST-ENSILE", "incremental_harvest_collection_ensiling_cost", "10–20", "", "EUR/t grass; wet-mass basis", "Interviewed market participants' range for adapted mowing, collection and ensiling", "§6.3, printed p. 37", "Historical interview range; details of quotes and price year are unavailable."),
    ("RVO14-GRASS-CHAIN-EXTRA-PRETREAT", "pretreatment_incremental_cost", "10–16", "", "EUR/t grass; wet-mass basis", "Interviewed market participants' range for intensive size reduction/extrusion and material opening", "§6.2, printed p. 35", "Historical interview range; the study warns SDE+ assumptions may be optimistic for grass."),
    ("RVO14-JANSEN-EXTRUSION-COST", "extrusion_cost", "approximately 16", "", "EUR/t extruded grass; wet-mass basis in chain-cost context", "Single JansenWijhe business-case report", "§6.2, printed p. 36", "One co-digestion case; includes a depreciation amount net of provincial investment subsidy."),
    ("RVO14-JANSEN-EXTRUSION-MAINTENANCE", "extrusion_maintenance_wear_cost", ">8", "", "EUR/t extruded grass", "Reported as the largest part of approximately EUR 16/t extrusion cost", "§6.2, printed p. 36", "Approximate lower bound; not independent of the total extrusion cost."),
    ("RVO14-JANSEN-EXTRUSION-CAPITAL", "extrusion_capital_insurance_interest_cost", ">4", "", "EUR/t extruded grass", "Reported depreciation, insurance and interest; investment subsidy already included in depreciation kental", "§6.2, printed p. 36", "Approximate lower bound; not independent of the total extrusion cost."),
    ("RVO14-JANSEN-EXTRUSION-ENERGY", "extrusion_energy_cost", ">1", "", "EUR/t extruded grass", "Reported energy component", "§6.2, printed p. 36", "Approximate lower bound; no kWh/t energy consumption is provided."),
    ("RVO14-JANSEN-EXTRUSION-LABOUR", "extrusion_labour_cost", "2.25", "2.25", "EUR/t extruded grass", "Reported labour component", "§6.2, printed p. 36", "One co-digestion case; historical nominal value, cost year and operating schedule are not normalized."),
    ("RVO14-JANSEN-ENSILING-COST", "ensiling_cost_at_digester", "approximately 1.60", "", "EUR/t product; wet-mass basis in chain-cost context", "Reported cost of ensiling at the digester's bunker silo", "§6.2, printed p. 36", "One case; not a regional or current quote."),
    ("RVO14-JANSEN-TOTAL-PRETREATMENT-COST", "total_extrusion_plus_ensiling_cost", "approximately 18", "", "EUR/t product; wet-mass basis in chain-cost context", "RVO report's rounded total of extrusion plus ensiling", "§6.2, printed p. 36", "Preserve the reported total; do not reconstruct it from rounded and lower-bound components."),
]:
    rvo(record_id, "1;3;5;TEA", "historical_cost_or_yield_benchmark", "roadside/nature grass as specified per record", metric, value_text, unit,
        basis, location, note + " No inflation adjustment or GreenHub route mapping is applied.",
        value_numeric=value_numeric, period="nominal historical values reported in 2014 study; price year not explicitly normalized",
        quality="B", validation="interview_or_case_estimate_not_current_quote")

for record_id, metric, value, unit, basis, location, note in [
    ("RVO14-STORAGE-POTENTIAL-LOSS-GOOD", "biogas_potential_loss_during_good_ensiling", "15–20", "% initial biogas potential", "RVO statement for rapidly and successfully ensiled grass", "§5.2.3, printed p. 26", "Interview-based reported potential loss, not fresh-mass or dry-matter loss and not a time-resolved rate."),
    ("RVO14-STORAGE-POTENTIAL-LOSS-POOR", "biogas_potential_loss_during_ineffective_ensiling", "25–30", "% initial biogas potential", "RVO statement for insufficiently effective ensiling", "§5.2.3, printed p. 26", "Interview-based reported potential loss, not fresh-mass or dry-matter loss and not a time-resolved rate."),
    ("RVO14-STORAGE-FIELD-WINDOW", "maximum_field_period_before_ensiling", "2", "day", "RVO summarizes forage practice as a maximum field period", "§5.2.3, printed p. 27", "A practice recommendation, not a measured optimum for roadside grass."),
    ("RVO14-STORAGE-DRY-MATTER-TARGET-LOW", "target_dry_matter_before_ensiling_lower", "35", "% fresh mass", "Recommended grass dry matter range 35–40%", "§5.2.3, printed p. 27", "Agricultural silage handling comparator; not a VARTA roadside measurement."),
    ("RVO14-STORAGE-DRY-MATTER-TARGET-HIGH", "target_dry_matter_before_ensiling_upper", "40", "% fresh mass", "Recommended grass dry matter range 35–40%", "§5.2.3, printed p. 27", "Agricultural silage handling comparator; not a VARTA roadside measurement."),
    ("RVO14-STORAGE-CHOPPED-DENSITY", "ensiled_dry_matter_density_chopped", "250", "kg DM/m3", "Laboratory test, chopped crop length 20 mm", "§5.2.3, printed p. 27", "Reported as up to 250 kg DM/m3; compaction and vessel conditions are not fully specified."),
    ("RVO14-STORAGE-UNCHOPPED-DENSITY", "ensiled_dry_matter_density_unchopped", "approximately 150", "kg DM/m3", "Laboratory test, unchopped grass comparator", "§5.2.3, printed p. 27", "Approximate source value; compaction and vessel conditions are not fully specified."),
    ("RVO14-GRASS-ASH-CONTAMINATION-THRESHOLD", "soil_contamination_indicator", ">120", "g crude ash/kg DM", "RVO states this crude-ash level indicates soil contamination", "§5.2.3, printed p. 27", "Source-level screening statement, not a regulatory limit or GreenHub acceptance criterion."),
    ("RVO14-ENSILING-CUT-SIZE", "chopped_crop_length_for_density_test", "20", "mm", "Short chopped material in laboratory packing comparison", "§5.2.3, printed p. 27", "A tested condition, not a universal optimum or verified GreenHub pretreatment setpoint."),
]:
    rvo(record_id, "1;2;3;5", "storage_or_supply_chain_observation", "grass; study comparator", metric, value, unit,
        basis, location, note, period="reported in 2014 study; original experiment period not specified",
        conditions=basis, quality="B", validation="reported_practice_or_interview_comparator")

for record_id, metric, gas_yield, value_text, lower, upper in [
    ("RVO14-SDE-GRASS-PRICE-50", "implied_grass_substrate_price", "50", "-8 to -2", "-8", "-2"),
    ("RVO14-SDE-GRASS-PRICE-75", "implied_grass_substrate_price", "75", "-4 to 2", "-4", "2"),
    ("RVO14-SDE-GRASS-PRICE-100", "implied_grass_substrate_price", "100", "0 to 6", "0", "6"),
    ("RVO14-SDE-GRASS-PRICE-150", "implied_grass_substrate_price", "150", "8 to 14", "8", "14"),
]:
    rvo(record_id, "1;5;TEA", "historical_sde_based_scenario", "grass substrate", metric, value_text,
        "EUR/t grass (report chain costs are wet-mass based)",
        f"SDE+ 2014-derived substrate-price range for {gas_yield} Nm3 biogas/t grass, including allowance for additional digester equipment",
        "Table 6.1, printed p. 35", "The report says applying SDE+ assumptions to grass is probably optimistic because grass has lower energy density and longer retention needs. Not a price observation or current market quote.",
        value_numeric="", lower_bound=lower, upper_bound=upper,
        period="SDE+ 2014 scenario; nominal euros, no inflation adjustment",
        conditions=f"assumed biogas yield {gas_yield} Nm3/t grass",
        quality="B", validation="modeled_historical_price_scenario_not_observed_price")

# The report's JansenWijhe example contains a repeated 30% DM label attached
# to two different gas yields. Preserve both source statements and quarantine
# any inferred yield equation.
for record_id, value, basis in [
    ("RVO14-JANSEN-GAS-30DM-EXAMPLE-A", "90", "Report says one tonne extruded grass gives 3 m3 biogas per percentage point DM; example states 30% DM corresponds to 90 m3/t."),
    ("RVO14-JANSEN-GAS-30DM-EXAMPLE-B", "120", "Adjacent source sentence again says 30% DM corresponds to 120 m3/t; report text is internally inconsistent."),
]:
    rvo(record_id, "5;TEA", "single_facility_case_statement", "extruded nature grass", "reported_biogas_yield_example", value,
        "m3 biogas/t extruded grass", basis, "§6.2, printed p. 36",
        "Case-specific JansenWijhe statement; not a methane yield. The source repeats 30% DM for both 90 and 120 m3/t, so no equation, corrected DM value, or GreenHub yield is inferred.",
        value_numeric=value, period="historical case; report published 2014",
        conditions="extruded grass at JansenWijhe co-digestion facility",
        quality="B", validation="source_internal_contradiction_quarantined")

# 2025 Interreg project report: regional table values and scenario outputs.
vgng_rows = [
    ("VGNG25-T2-VERGE-NL", "roadside verge grass, Netherlands", "annual_dry_matter_availability_estimate", "1000", "kton DM", "Table 2 reports d.s. availability; underlying year and route eligibility not specified.", "§1 Results, Table 2, printed p. 5", "Regional/national estimate; not weighed collected grass.", "Netherlands"),
    ("VGNG25-T2-VERGE-NORTH", "roadside verge grass, North Netherlands", "annual_dry_matter_availability_estimate", "274", "kton DM", "Table 2; report says North Netherlands value is allocated from national values using provincial area distribution.", "§1 Results, Table 2 and availability discussion, printed pp. 5–6", "Derived regional allocation from older national studies; no accessible fraction or delivery quantity.", "North Netherlands"),
    ("VGNG25-T2-NATURE-DITCH-NL", "nature grass and ditch clippings", "annual_dry_matter_availability_estimate", "500", "kton DM", "Table 2; source period and inclusion/access boundaries not specified.", "§1 Results, Table 2, printed p. 5", "Secondary estimate; not all mown biomass is necessarily collected or suitable.", "Netherlands"),
    ("VGNG25-T2-NATURE-DITCH-NORTH", "nature grass and ditch clippings", "annual_dry_matter_availability_estimate", "137", "kton DM", "Table 2; regional allocation from national source using provincial area distribution.", "§1 Results, Table 2 and availability discussion, printed pp. 5–6", "Derived regional allocation; not a measured or contracted feed supply.", "North Netherlands"),
    ("VGNG25-T2-SILAGE-NORTH", "ensiled agricultural grass", "annual_dry_matter_availability_estimate", "1267", "kton DM", "Table 2 includes North Netherlands and Overijssel; not a roadside-grass stream.", "§1 Results, Table 2, printed p. 5", "Agricultural silage comparator; distinct from roadside/nature/ditch grass.", "North Netherlands incl. Overijssel"),
    ("VGNG25-T2-STRAW-NORTH", "straw", "annual_dry_matter_availability_estimate", "95", "kton DM", "Table 2; comparator feed, not grass.", "§1 Results, Table 2, printed p. 5", "Non-grass comparator; no use as GreenHub feedstock.", "North Netherlands"),
]
for rid, material, metric, value, unit, basis, loc, note, geography in vgng_rows:
    vgng(rid, "1", "regional_availability_estimate", material, metric, value, unit,
         basis, loc, note, geography=geography, value_numeric=value,
         quality="B", validation="secondary_or_area_allocated_estimate_not_measurement")

vgng("VGNG25-NORTH-NL-GRASS-411", "1", "regional_summary_estimate",
     "grass residues in North Netherlands", "reported_dry_matter_availability_summary",
     "411", "kton DM", "The report states 411 kton DM from multiple studies; this equals Table 2's 274+137 but is not an independent observation.",
     "Conclusions, printed p. 31", "Do not add this summary to the Table 2 component rows.", geography="North Netherlands",
     value_numeric="411", validation="reported_summary_duplicates_table2_subtotal")

vgng("VGNG25-FACTOR-THEORETICAL-METHANE", "5;7", "reported_theoretical_conversion_factor",
     "grass organic dry matter", "theoretical_methane_potential_factor", "580", "Nm3 CH4/t organic DM",
     "The report states this as the theoretical methane potential used to frame Table 4.",
     "§1 Results, paragraph preceding Table 4, printed p. 7", "The factor and Table 4's green-gas totals do not reconcile; no correction or upgrading efficiency is inferred.",
     geography="North Netherlands", value_numeric="580", validation="inconsistent_with_table4_reported_potential")

availability_2025 = [
    ("VGNG25-IDAFEHN-RADIUS", "assessment radius around Idafehn", "40", "km", "Scenario boundary in report narrative; not a GIS-derived supply curve."),
    ("VGNG25-IDAFEHN-AREA", "grassland area considered", "5000", "ha", "Report describes this area as available for development; parcel access, grass cover and collectable fraction are not specified."),
    ("VGNG25-IDAFEHN-YIELD-LOW", "harvest yield per cut lower", "1", "t/ha/cut", "Source does not identify wet/dry basis or crop subset."),
    ("VGNG25-IDAFEHN-YIELD-HIGH", "harvest yield per cut upper", "2", "t/ha/cut", "Source does not identify wet/dry basis or crop subset."),
    ("VGNG25-IDAFEHN-CUTS-LOW", "annual harvest frequency lower", "1", "cut/year", "Weather-dependent scenario; not a fixed regional schedule."),
    ("VGNG25-IDAFEHN-CUTS-HIGH", "annual harvest frequency upper", "2", "cut/year", "Weather-dependent scenario; not a fixed regional schedule."),
    ("VGNG25-IDAFEHN-ANNUAL-FEED", "reported annual substrate volume", "19500", "t/year; wet/dry basis not stated", "Report gives this as the result of the Idafehn area/yield/cut scenario; no moisture or accessible-area factor is disclosed."),
]
for rid, metric, value, unit, note in availability_2025:
    vgng(rid, "1", "site_planning_scenario", "grassland around Idafehn", metric,
         value, unit, "Narrative planning scenario, not measured collection.",
         "§1 availability discussion, printed p. 5", note,
         geography="40 km radius around Idafehn, North Germany", value_numeric=value,
         validation="scenario_basis_incomplete")

for rid, feedstock, values in [
    ("VGNG25-T3-CATTLE-MANURE", "cattle manure", ["9", "80", "47", "55", "26", "358", "-86"]),
    ("VGNG25-T3-RYE-GPS", "whole-crop rye silage (GPS of rye)", ["33", "95", "201", "54", "107", "348", "41"]),
    ("VGNG25-T3-MAIZE-SILAGE", "maize silage", ["33", "93", "195", "53", "103", "341", "44"]),
    ("VGNG25-T3-CUT-GRASS", "cut grass", ["18", "90", "95", "54", "57", "351", ""]),
    ("VGNG25-T3-GRASS-SILAGE", "grass silage", ["35", "83", "188", "54", "101", "351", "44"]),
    ("VGNG25-T3-STRAW", "straw", ["86", "91", "322", "51", "164", "210", "10"]),
]:
    for metric, value, unit, basis in [
        ("total_solids", values[0], "% fresh matter", "TS as reported in Table 3; source methods and sample identity are not supplied with this table."),
        ("organic_solids", values[1], "% DM", "Ots as percent of dry matter, following the table heading."),
        ("biogas_yield", values[2], "m3 biogas/t fresh matter", "Table 3 source value; gas reference state and underlying assay/source are not stated."),
        ("methane_fraction", values[3], "% biogas", "Table 3 value; source method and gas state are not stated."),
        ("methane_yield_fresh_matter", values[4], "m3 CH4/t fresh matter", "Reported Table 3 value; no recomputation from rounded biogas and methane fraction."),
        ("methane_yield_organic_solids", values[5], "m3 CH4/t organic dry matter", "Reported Table 3 value; underlying method and gas reference conditions are not identified."),
        ("emission_factor", values[6], "g CO2eq/MJ", "Table 3 labels an emission factor but gives no functional unit boundary, counterfactual, method/version or source citation at the table."),
    ]:
        status = "not_reported" if value == "" else "table_value_preserved_source_lineage_incomplete"
        vgng(f"VGNG25-T3-{feedstock.upper().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')}-{metric.upper()}",
             "5;7" if metric == "emission_factor" else "1;5", "cross_feedstock_quality_comparator",
             feedstock, metric, value, unit, basis, "§1 Results, Table 3, printed pp. 5–6",
             "Table is a secondary compilation and does not name row-level source studies, sample population, uncertainty or measurement methods. Not transferable to a GreenHub stream, and not an LCA factor without boundary/method verification.",
             geography="Mixed/unstated source geographies in the report's compiled comparison",
             value_numeric=value, quality="B", validation=status,
             transfer="Cross-feedstock_literature_compilation_unverified_source_lineage_reference_only")

for feed, dm, odm, gas, label in [
    ("roadside verge grass", "274", "197", "67", "Bermgras"),
    ("nature grass and ditch clippings", "137", "126", "43", "Natuurgras en slootmaaisel"),
    ("ensiled grass", "1267", "1098", "375", "Ingekuild gras"),
    ("straw", "95", "89", "31", "Stro"),
]:
    for metric, value, unit, basis in [
        ("dry_matter_availability", dm, "kton DM", "Table 4 repeats Table 2 dry-matter availability figures."),
        ("organic_dry_matter_availability", odm, "kton organic DM", "Table 4 source-reported organic dry matter; measurement/calculation source not given."),
        ("reported_total_green_gas_potential", gas, "MNm3 green gas", "Table 4 labels this as total green-gas potential; source does not state upgrading recovery or losses."),
    ]:
        validation = "table_potential_not_reconciled_to_580_factor" if metric == "reported_total_green_gas_potential" else "reported_table_value_source_method_incomplete"
        vgng(f"VGNG25-T4-{label.upper().replace(' ', '-')}-{metric.upper()}",
             "1;5;7", "regional_theoretical_potential_scenario", feed, metric, value, unit, basis,
             "§1 Results, Table 4, printed p. 7",
             "Table is a regional theoretical estimate, not observed gas production. The table's green-gas values correspond to about 341–348 Nm3/t organic DM, whereas the adjacent text states 580 Nm3 CH4/t organic DM. This is retained as an unresolved source inconsistency; do not reinterpret the difference as upgrading recovery.",
             geography="North Netherlands", value_numeric=value, validation=validation,
             transfer="Regional_theoretical_potential_not_a_measured_or_runtime_yield")

for rid, metric, value, unit, basis, note in [
    ("VGNG25-TEA-GRASS-FEED", "annual_grass_feed", "15000", "t/year; moisture basis not stated", "KTBL Probiogas case described in the 2025 report", "Case combines grass with pig manure; not a grass-only GreenHub route."),
    ("VGNG25-TEA-PIG-MANURE-FEED", "annual_pig_manure_feed", "15000", "t/year; moisture basis not stated", "KTBL Probiogas case described in the 2025 report", "Co-feed quantity; manure properties and exact feed basis are not disclosed in the summary."),
    ("VGNG25-TEA-DIESEL-OFFSET", "diesel_demand_displaced", "830000", "L diesel/year (period inferred from annual case context)", "Report says the case replaces the full diesel demand of Loonbedrijf Thomssen", "Not an independently metered displacement result; energy conversion and vehicle efficiency are not supplied."),
    ("VGNG25-TEA-CAPEX", "estimated_investment", ">4000000", "EUR; excludes land", "KTBL Probiogas case, report summary", "Cost year, equipment boundary and financing assumptions are not supplied."),
    ("VGNG25-TEA-OPEX", "annual_operating_cost", "approximately 1570000", "EUR/year", "KTBL Probiogas case, report summary", "Cost year, itemized quantities, subsidy treatment and full boundary are not supplied."),
    ("VGNG25-TEA-PROFIT", "profit_contribution", ">300000", "EUR; period not explicitly stated", "KTBL Probiogas case, report summary", "Definition of profit, period, subsidies, depreciation and revenue boundary are not supplied."),
    ("VGNG25-TEA-ROA", "return_on_assets", "approximately 15", "%", "KTBL Probiogas case, report summary", "Formula, asset definition, financing, price year and uncertainty are not supplied."),
]:
    vgng(rid, "1;5;TEA", "reported_techno_economic_case_output", "grass plus pig manure case", metric,
         value, unit, basis, "§4 Techno-economic analysis, summary, printed pp. 24–26",
         note + " These values are a report-level comparator only; do not mix them with GreenHub component costs or model outputs.",
         geography="Loonbedrijf Thomssen case, North Germany", value_numeric="",
         quality="B", validation="case_output_boundary_and_basis_incomplete",
         transfer="Single_project_case_not_comparable_without_full_process_and_financial_basis")


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert(path: Path, record: dict[str, str], key: str) -> None:
    fields, records = read_rows(path)
    if not fields:
        fields = list(record)
    existing = next((row for row in records if row.get(key) == record[key]), None)
    if existing is None:
        records.append(record)
    else:
        existing.update(record)
    write_rows(path, fields, records)


def output_dataset(filename: str, rows: list[dict[str, str]], metadata: dict) -> None:
    path = FOLDER / filename
    write_rows(path, FIELDS, rows)
    meta = {
        "dataset_id": metadata["dataset_id"],
        "dataset_version": "1.0.0",
        "dataset_file": filename,
        "source_file": filename,
        "record_count": len(rows),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_id": metadata["source_id"],
        "citation": metadata["citation"],
        "publication_year": metadata["publication_year"],
        "doi": None,
        "source_url": metadata["source_url"],
        "retrieval_date": RETRIEVED,
        "source_location": metadata["source_location"],
        "geography": metadata["geography"],
        "material_scope": metadata["material_scope"],
        "evidence_class": metadata["evidence_class"],
        "quality_class": "B",
        "license_or_rights": "No explicit reuse license identified on the cited source pages/PDF during retrieval. The source report is not redistributed; factual observations are attributed and remain subject to source-specific rights.",
        "access_protocol": "HTTPS PDF hosted by the source institution/official report host.",
        "data_structure": "Long-form UTF-8 CSV. Source-reported text, numeric values and range bounds are separate. Blank numeric fields indicate that a numeric value was not reported or not safely separable; they are not zero.",
        "conversion_or_processing": metadata["processing"],
        "uncertainty": metadata["uncertainty"],
        "limitations": metadata["limitations"],
        "phase_coverage": metadata["phase_coverage"],
        "runtime_policy": "reference_only; no parameter registry, default, process equation, TEA/LCA factor, scenario or Pareto mapping is created",
        "calculation_connected": False,
        "fair_metadata": {
            "findable": "Repository-local URN, source ID, content hash and catalog-indexed path; no DOI is fabricated.",
            "accessible": "Source URL is recorded using HTTPS; the source report itself is not copied into the repository.",
            "interoperable": "UTF-8 long-form CSV with explicit source, phase, value, unit, basis, time context, source location and missingness fields.",
            "reusable": "Citation, retrieval date, rights warning, evidence class, applicability, uncertainty, validation flags and limitations are recorded.",
        },
    }
    path.with_suffix(".source.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    upsert(FOLDER / "dataset_manifest.csv", {
        "filename": filename,
        "description": metadata["manifest_description"],
        "row_count": str(len(rows)),
        "schema_version": "1.0",
        "encoding": "UTF-8 with BOM",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }, "filename")
    upsert(FOLDER / "source_register.csv", {
        "source_id": metadata["source_id"],
        "source_title": metadata["title"],
        "authors": metadata["authors"],
        "year": str(metadata["publication_year"]),
        "doi_or_stable_id": metadata["persistent_identifier"],
        "source_type": metadata["source_type"],
        "url": metadata["source_url"],
        "material_scope": metadata["material_scope"],
        "quality_notes": metadata["quality_notes"],
    }, "source_id")
    _update_global_audit(filename, rows, metadata, path)


def _update_global_audit(filename: str, rows: list[dict[str, str]], metadata: dict, path: Path) -> None:
    audit = ROOT / "Greenhub/data/global_audit_package"
    relative = f"Bigas production + upgrade/Feed BMP/{filename}"
    numeric_rows = sum(bool(row["value_numeric"] or row["lower_bound"] or row["upper_bound"]) for row in rows)
    notes = metadata["quality_notes"]
    upsert(audit / "global_source_register.csv", {
        "dataset_path": relative,
        "dataset_group": "Feed BMP",
        "source_id": metadata["source_id"],
        "source_title": metadata["title"],
        "authors": metadata["authors"],
        "year": str(metadata["publication_year"]),
        "doi_or_stable_id": metadata["persistent_identifier"],
        "url": metadata["source_url"],
        "source_type": metadata["source_type"],
        "notes": notes,
    }, "dataset_path")
    upsert(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative,
        "category": "Biogas production + upgrade",
        "subgroup": "Feed BMP",
        "filename": filename,
        "row_count_observed": str(len(rows)),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": notes,
    }, "dataset_path")
    upsert(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative,
        "category": "Biogas production + upgrade",
        "subgroup": "Feed BMP",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": str(numeric_rows),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": notes,
    }, "dataset_path")
    upsert(audit / "source_dataset_checksums.csv", {
        "dataset_path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "byte_size": str(path.stat().st_size),
    }, "dataset_path")

    summary_path = audit / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = read_rows(audit / "global_dataset_manifest.csv")
    _, readiness = read_rows(audit / "global_dataset_readiness.csv")
    readiness_counts: dict[str, int] = {}
    for row in readiness:
        key = row.get("readiness", "")
        readiness_counts[key] = readiness_counts.get(key, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = readiness_counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    output_dataset(
        "rvo_2014_grass_supply_storage_chain_cost_reference.csv", RVO_ROWS, {
            "dataset_id": "urn:greenhub:dataset:feed-bmp:rvo-2014-grass-supply-storage-cost-reference:v1",
            "source_id": RVO_ID,
            "citation": "Brinkmann Consultancy (A. Brinkmann). (2014). Biogas uit gras – een onderbenut potentieel: Een studie naar kansen voor grasvergisting. Final report commissioned by Rijksdienst voor Ondernemend Nederland; definitive version, March 2014.",
            "authors": "Brinkmann Consultancy; A. Brinkmann (author); commissioned by Rijksdienst voor Ondernemend Nederland",
            "publication_year": 2014,
            "persistent_identifier": "No DOI; official RVO report, definitive March 2014",
            "source_url": RVO_URL,
            "title": "Biogas uit gras – een onderbenut potentieel: Een studie naar kansen voor grasvergisting",
            "source_type": "Official commissioned report synthesizing prior studies, LMA/BVOR statistics and stakeholder interviews",
            "source_location": "Sections 2.2–2.4, 5.2.1–5.2.3 and 6.2–6.3; per-row section/page locations are retained.",
            "geography": "Netherlands; selected supply-chain and single-facility examples in the Netherlands",
            "material_scope": "Roadside verge grass, nature grass, ditch clippings and grass feed for anaerobic digestion; secondary national quantity estimates, preservation practices and historical cost/yield comparators.",
            "evidence_class": "B-tier official literature evidence; individual records distinguish secondary estimate, stakeholder interview, laboratory comparator and case-specific output.",
            "processing": "Direct transcription of report statements and ranges. No inflation adjustment, cross-study averaging, conversion of potential loss to mass loss, or runtime mapping. Apparent source inconsistencies are preserved and flagged.",
            "uncertainty": "The report states exact national grass quantities are unavailable. Underlying studies differ in dry-matter assumptions and supply boundaries; interview samples, quotes, assay conditions and uncertainty intervals are not reported consistently.",
            "limitations": [
                "The study is from 2014 and is not current Dutch supply, a GreenHub project measurement, or a delivered-feed contract.",
                "National availability numbers combine older studies, waste reporting, industry estimates and stakeholder interviews; boundaries and moisture bases vary.",
                "Reported ensiling losses are biogas-potential losses, not dry-matter or fresh-mass inventory losses, and are not time-resolved kinetics.",
                "Storage-density values are a laboratory comparison with incomplete test-method detail, not a plant-specific storage design value.",
                "Historical costs and substrate-price scenarios are nominal and not inflation-adjusted; subsidy, plant boundary and itemization are incomplete.",
                "The JansenWijhe yield examples repeat 30% DM for both 90 and 120 m3/t; both are retained without correction.",
                "No upgrading performance, GreenHub-specific protein route, lifecycle inventory or fertilizer substitution is established by this source.",
                "No explicit reuse license was identified; only short factual transcriptions are stored, not the source PDF.",
            ],
            "phase_coverage": {
                "1": "Historical national biomass quantities, collected/off-site versus total mown distinctions, season/harvest context and supply constraints; not accessible current delivered supply.",
                "2": "Field-period and ensiling practices, reported biogas-potential preservation losses and storage-density comparator; no roadside-specific loss kinetics.",
                "3": "Cut length, chopping/extrusion, contamination screening and historical pretreatment-cost observations; no GreenHub press or extraction balance.",
                "4": "No protein extraction, precipitation, reagent demand or product quality data.",
                "5": "Broad literature biogas yield range and historical grass substrate scenarios; not residual-specific continuous AD.",
                "6": "No gas upgrading recovery, impurity removal, energy, water or product-specification dataset.",
                "7": "No defensible LCA method, boundary or fertilizer substitution factor; this report does not close the LCA inventory.",
            },
            "manifest_description": "Historical Dutch grass availability, field-to-silage conditions, potential-loss ranges and 2014 chain-cost/yield comparators from the RVO-commissioned study; reference-only.",
            "quality_notes": "Official traceable report (no DOI), but quantity/cost observations are largely secondary literature or interview/case estimates. Old, heterogeneous bases and unresolved source inconsistencies are preserved. Reference-only; no GreenHub runtime/default activation.",
        })
    output_dataset(
        "van_gras_naar_gas_2025_regional_feed_quality_tea_reference.csv", VGNG_ROWS, {
            "dataset_id": "urn:greenhub:dataset:feed-bmp:van-gras-naar-gas-2025-regional-feed-quality-tea-reference:v1",
            "source_id": VGNG_ID,
            "citation": "Krooneman, J. (2025). Van Gras Naar Gas Eindrapport: Haalbaarheid, technologieën en economische kansen voor biogasproductie uit grasreststromen in Nederland en Duitsland. Interreg Deutschland-Nederland project report.",
            "authors": "Janneke Krooneman (repository product citation); project partners are listed in the report",
            "publication_year": 2025,
            "persistent_identifier": "No DOI identified; institutional/project report",
            "source_url": VGNG_URL,
            "title": "Van Gras Naar Gas: Haalbaarheid, technologieën en economische kansen voor biogasproductie uit grasreststromen in Nederland en Duitsland",
            "source_type": "Interreg Deutschland-Nederland feasibility report; secondary literature tables, regional planning scenario and KTBL Probiogas case summary",
            "source_location": "Chapter 1 Tables 2–4 and North Germany availability text; Chapter 4 TEA summary; per-row section/table/page locations are retained.",
            "geography": "Netherlands and Germany border region; individual records retain their specific region.",
            "material_scope": "Regional roadside, nature/ditch and agricultural grass availability; compiled feed-quality comparison; theoretical gas potential and grass-plus-manure TEA comparator.",
            "evidence_class": "B-tier directly reported project-report statements; underlying availability/quality sources, measurements and KTBL case details are incomplete.",
            "processing": "Table values and narrative figures transcribed as reported. No annualization, mass-balance closure, estimate correction, yield recomputation or GreenHub parameter mapping.",
            "uncertainty": "Underlying years, source studies, region-allocation calculations, feedstock moisture bases, uncertainty, detailed KTBL assumptions, cost year and boundaries are mostly absent.",
            "limitations": [
                "Table 2 national and North Netherlands values are secondary estimates; the North values are translated by provincial area distribution and do not represent collected/delivered supply.",
                "Table 3 does not identify source studies or analytical methods for each feedstock; the emission-factor boundary and method are unspecified.",
                "Table 4's green-gas potential values do not reconcile with the adjacent stated 580 Nm3 CH4/t organic-DM factor. No upgrading recovery explanation is given; raw values remain separate and uncorrected.",
                "The Idafehn scenario omits moisture basis, parcel eligibility and collection share; its 19,500 t/y figure cannot be reproduced from the stated area/yield/cut range without extra assumptions.",
                "The KTBL Probiogas TEA summary lacks cost year, project life, financial assumptions, itemization and explicit profit definition; not comparable with GreenHub TEA outputs.",
                "The repository record identifies rights as unknown/all rights reserved for some copies; no open reuse license was identified. The report PDF is not redistributed.",
                "No values are activated in GreenHub defaults, process calculations, TEA/LCA factors or Pareto scenarios.",
            ],
            "phase_coverage": {
                "1": "Regional availability estimates and one planning scenario; not current accessible or delivered supply.",
                "2": "No storage time-course or loss inventory.",
                "3": "No GreenHub mechanical fractionation performance or stream balance.",
                "4": "No protein extraction or precipitation data.",
                "5": "Cross-feedstock biogas/methane comparator and theoretical regional potential; not GreenHub residual BMP or continuous digestion.",
                "6": "No methane recovery, upgrading energy or impurity data.",
                "7": "Table 3 includes unbounded emission-factor comparators only; no usable LCA method/factor, digestate or substitution data.",
            },
            "manifest_description": "Regional availability, compiled feed quality, theoretical gas-potential and grass/manure TEA records from the 2025 Van Gras Naar Gas report; source inconsistencies and missing bases retained; reference-only.",
            "quality_notes": "Direct transcription from a public project report (no DOI); most numerical values are secondary estimates, cross-feedstock compilation or scenario outputs. Reference-only with incomplete underlying provenance and no GreenHub activation.",
        })
    print(json.dumps({"rvo_2014_rows": len(RVO_ROWS), "van_gras_naar_gas_2025_rows": len(VGNG_ROWS)}, indent=2))


if __name__ == "__main__":
    main()
