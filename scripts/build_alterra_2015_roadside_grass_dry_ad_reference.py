"""Build a source-located, reference-only extract of Alterra Report 2661.

The report contains Dutch roadside/nature-grass field samples and dry-AD case
observations. Results from mixed-feed plants and modeled climate balances are
kept distinct from feed assays and are not GreenHub defaults.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data"
FOLDER = DATA / "Bigas production + upgrade/Feed BMP"
AUDIT = DATA / "global_audit_package"
FILENAME = "alterra_2015_roadside_grass_dry_ad_reference.csv"
SOURCE_ID = "SRC-ALTERRA-2661-ZWART-DEBOER-2015"
SOURCE_RECORD_URL = "https://research.wur.nl/en/publications/droge-vergisting-van-berm-en-natuurgras/"
SOURCE_PDF_URL = "https://www.researchgate.net/publication/283403753_Droge_vergisting_van_berm-_en_natuurgras"
INSTITUTIONAL_PDF_URL = "https://edepot.wur.nl/350624"
RETRIEVED = "2026-11-08"
OUT = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP" / FILENAME

FIELDS = [
    "record_id", "source_id", "phase_relevance", "record_type", "material",
    "geography", "metric", "value_text", "value_numeric", "unit", "basis",
    "reference_period", "condition_scope", "source_location", "evidence_class",
    "quality_class", "activation_state", "transferability", "validation_status",
    "limitations",
]
ROWS: list[dict[str, str]] = []

COMMON_LIMITS = (
    "2013 Dutch field samples, not GreenHub/VARTA measurements. Cultivar, replicate count, "
    "analytical uncertainty and full sampling protocol are not supplied in the summary tables. "
    "Use only as a contextual comparator; do not overwrite the selected GreenHub feed profile."
)


def add(record_id: str, phases: str, kind: str, material: str, metric: str,
        value_text: str, unit: str, basis: str, location: str, limitations: str,
        *, numeric: str = "", period: str = "2013 samples; digestion in 2014 or 2015 as identified",
        conditions: str = "", evidence: str = "author_reported_laboratory_measurement",
        quality: str = "B", validation: str = "reported_value_preserved") -> None:
    ROWS.append({
        "record_id": record_id, "source_id": SOURCE_ID, "phase_relevance": phases,
        "record_type": kind, "material": material, "geography": "Drenthe/Groningen, Netherlands; process cases in Dörpen/Ostrhauderfehn, Germany",
        "metric": metric, "value_text": value_text, "value_numeric": numeric,
        "unit": unit, "basis": basis, "reference_period": period,
        "condition_scope": conditions, "source_location": location,
        "evidence_class": evidence, "quality_class": quality,
        "activation_state": "reference_only",
        "transferability": "Dutch roadside/nature grass comparator; local case conditions and mixed-feed boundaries do not represent GreenHub",
        "validation_status": validation, "limitations": limitations,
    })


SAMPLES = {
    "SPRING_VERGE": ("roadside verge grass, spring cut", "Borger-Odoorn, harvested June 2013"),
    "AUTUMN_VERGE": ("roadside verge grass, autumn cut", "Borger-Odoorn plus additional southeast Drenthe municipalities, harvested September 2013"),
    "SELLINGEN_NATURE": ("nature grass", "SBB nature area near Sellingen, Groningen, harvested 2013"),
}

# Phase 1–2: site and harvesting/storage context. Text-only records deliberately
# retain unknowns instead of manufacturing a storage duration or accessible yield.
for rid, metric, value, unit, loc, limitation in [
    ("ALT15-P1-ROAD-NETWORK", "municipal_road_network_length", "approximately 800", "km road", "§2.1, printed p. 10", "Municipality-level context, not grassed/mowable length or GreenHub catchment."),
    ("ALT15-P1-ECOLOGICALLY-MANAGED", "ecologically_managed_road_length", "approximately 100", "km road", "§2.1, printed p. 10", "Management extent, not area, yield, access rights or collected biomass."),
    ("ALT15-P1-MOW-FREQUENCY", "mowing_frequency_by_management_type", "some sections mown once and others twice", "cuts/year; source gives qualitative categories", "§2.1, printed p. 10", "No asset-level locations, proportions or biomass per cut are reported."),
    ("ALT15-P1-HARVEST-MONTHS", "reported_2013_harvest_months", "June (spring cut); September (autumn cut)", "calendar month", "§2.1, printed p. 11", "Two study-period mowing events do not define a general seasonal supply curve."),
    ("ALT15-P1-AUTUMN-SUPPLEMENT", "additional_municipalities_used_for_autumn_sample", "Emmen, Coevorden and Midden-Drenthe", "municipality names", "§2.1, printed p. 11", "Autumn material from these municipalities was added because the 2013 dry summer reduced Borger-Odoorn volume; no added mass is reported."),
    ("ALT15-P2-VERGE-SILAGE-INTERVAL", "harvest_to_digestion_storage_interval", "harvested and ensiled in 2013; stored at contractor Potze in Roswinkel until digestion in 2014", "qualitative interval; exact days/months not reported", "§2.1, printed p. 11", "Does not provide storage temperature, oxygen exposure, silage mass loss or composition time course."),
    ("ALT15-P2-NATURE-SILAGE-INTERVAL", "harvest_to_digestion_storage_interval", "harvested and ensiled in 2013 at/near Sellingen until digestion in 2015", "qualitative interval; exact days/months not reported", "§2.2, printed p. 12", "Does not provide storage temperature, oxygen exposure, silage mass loss or composition time course."),
]:
    add(rid, "1;2", "field_management_or_storage_context", "Borger-Odoorn roadside grass or Sellingen nature grass", metric,
        value, unit, "As stated in report narrative; no further normalization.", loc,
        limitation, evidence="direct_report_narrative", quality="B", validation="reported_context_not_site_supply_measurement")

# Phase 3/5: feed characterization and potential biogas. Tables report kg/t;
# wet/as-sampled basis is strongly implied by the water content but is not
# separately defined in their column heading, so the basis note remains explicit.
feed_rows = {
    "moisture": ("moisture_content", "kg/t reported ensiled material", {"SPRING_VERGE": "510", "AUTUMN_VERGE": "670", "SELLINGEN_NATURE": "640"}),
    "dry_matter": ("dry_matter_content", "kg/t reported ensiled material", {"SPRING_VERGE": "490", "AUTUMN_VERGE": "330", "SELLINGEN_NATURE": "360"}),
    "organic_matter": ("organic_matter_content", "kg/t reported ensiled material", {"SPRING_VERGE": "370", "AUTUMN_VERGE": "224", "SELLINGEN_NATURE": "328"}),
    "ash": ("ash_content", "kg/t reported ensiled material", {"SPRING_VERGE": "120", "AUTUMN_VERGE": "106", "SELLINGEN_NATURE": "32"}),
}
for code, (metric, unit, values) in feed_rows.items():
    for sample, (material, origin) in SAMPLES.items():
        add(f"ALT15-T2-{sample}-{code.upper()}", "1;3;5", "laboratory_feed_characterization", material,
            metric, values[sample], unit,
            "Report Table 2: kg per tonne of ensiled grass. The wet/as-sampled interpretation follows the water row and table context; table heading does not explicitly state moisture basis.",
            "§3.1, Table 2, printed p. 19", COMMON_LIMITS + " Sample origin: " + origin,
            numeric=values[sample], conditions="Ensiled sample; Eurofins laboratory analysis reported by authors.")

nutrients = {
    "total_n": ("total_nitrogen", "kg N/t reported ensiled material", {"SPRING_VERGE": "7.4", "AUTUMN_VERGE": "4.7", "SELLINGEN_NATURE": "5.1"}),
    "ammonium_n": ("ammonium_nitrogen", "kg NH4-N/t reported ensiled material", {"SPRING_VERGE": "2.9", "AUTUMN_VERGE": "1.9", "SELLINGEN_NATURE": "0.5"}),
    "p2o5": ("phosphorus_as_P2O5", "kg P2O5/t reported ensiled material", {"SPRING_VERGE": "3.3", "AUTUMN_VERGE": "2.4", "SELLINGEN_NATURE": "2.5"}),
    "k2o": ("potassium_as_K2O", "kg K2O/t reported ensiled material", {"SPRING_VERGE": "11.5", "AUTUMN_VERGE": "6.9", "SELLINGEN_NATURE": "5.1"}),
}
for code, (metric, unit, values) in nutrients.items():
    for sample, (material, origin) in SAMPLES.items():
        add(f"ALT15-T3-{sample}-{code.upper()}", "1;3;5;7", "laboratory_feed_nutrient_characterization", material,
            metric, values[sample], unit,
            "Report Table 3: kg per tonne of ensiled grass; table does not separately specify water basis.",
            "§3.1, Table 3, printed p. 19", COMMON_LIMITS + " Sample origin: " + origin,
            numeric=values[sample], conditions="Ensiled sample; source says composition analyzed by Eurofins.")

for sample, (material, origin) in SAMPLES.items():
    potential_per_t = {"SPRING_VERGE": "210", "AUTUMN_VERGE": "130", "SELLINGEN_NATURE": "190"}[sample]
    potential_per_os = {"SPRING_VERGE": "570", "AUTUMN_VERGE": "580", "SELLINGEN_NATURE": "580"}[sample]
    for metric, value, unit, basis, suffix in [
        ("reported_potential_biogas_yield", potential_per_t, "m3 biogas/t reported material", "Table 4 potential calculated from the composition; exact calculation method, test conditions and reference gas state not supplied.", "PER-MATERIAL"),
        ("reported_potential_biogas_yield", potential_per_os, "m3 biogas/t organic matter", "Table 4 potential per organic matter; exact calculation method, test conditions and reference gas state not supplied.", "PER-OS"),
    ]:
        add(f"ALT15-T4-{sample}-{suffix}", "5", "source_calculated_biogas_potential", material, metric,
            value, unit, basis, "§3.1, Table 4, printed p. 20",
            "Not a standardized measured BMP; no explicit reference gas temperature/pressure. " + COMMON_LIMITS,
            numeric=value, conditions="Source potential estimate from reported feed composition.",
            evidence="source_reported_potential_calculation", validation="calculated_potential_method_incomplete")

# Independent test quoted for autumn sample, distinct from Table 4 potential.
add("ALT15-LUFA-AUTUMN-BIOGAS-TEST", "5", "laboratory_gas_test_result", "roadside verge grass, autumn cut",
    "reported_biogas_yield", "123", "m3 biogas/t sample", "Report states LUFA Oldenburg measured yield before digestion; denominator moisture basis, assay protocol and standard gas state are not given.",
    "§3.1, printed p. 20", "Single source-reported laboratory result; not methane yield, standardized BMP or a GreenHub residual test.",
    numeric="123", conditions="Autumn 2013 ensiled sample; laboratory measurement by LUFA Oldenburg.",
    evidence="laboratory_measurement_reported_by_author", validation="measurement_reported_method_and_basis_incomplete")

# Phase 3/5 contamination suitability: preserve reported limit and sample
# measurements separately. The limit is historical (report-era regulation),
# not a current regulatory threshold.
contaminants = {
    "CD": ("cadmium", "0.8", {"SPRING_VERGE": "0.5", "AUTUMN_VERGE": "0.6", "SELLINGEN_NATURE": "0.4"}),
    "CR": ("chromium", "50", {"SPRING_VERGE": "6.9", "AUTUMN_VERGE": "7.4", "SELLINGEN_NATURE": "5.5"}),
    "CU": ("copper", "50", {"SPRING_VERGE": "12.1", "AUTUMN_VERGE": "14.8", "SELLINGEN_NATURE": "10.3"}),
    "HG": ("mercury", "0.5", {"SPRING_VERGE": "0.1", "AUTUMN_VERGE": "0.1", "SELLINGEN_NATURE": "0.1"}),
    "NI": ("nickel", "20", {"SPRING_VERGE": "6.6", "AUTUMN_VERGE": "7.4", "SELLINGEN_NATURE": "5.5"}),
    "PB": ("lead", "67", {"SPRING_VERGE": "13.1", "AUTUMN_VERGE": "14.8", "SELLINGEN_NATURE": "11"}),
    "ZN": ("zinc", "200", {"SPRING_VERGE": "87.8", "AUTUMN_VERGE": "77", "SELLINGEN_NATURE": "96.9"}),
    "AS": ("arsenic", "10", {"SPRING_VERGE": "6.6", "AUTUMN_VERGE": "7.4", "SELLINGEN_NATURE": "5.5"}),
}
for code, (name, limit, values) in contaminants.items():
    add(f"ALT15-T5-LIMIT-{code}", "3;7", "historical_regulatory_comparator", "ensiled roadside/nature grass",
        f"historical_maximum_permitted_{name}", limit, "mg/kg organic matter", "Maximum permitted value printed in report Table 5 under the regulation cited as of 2015; not a current compliance criterion.",
        "§3.1, Table 5, printed p. 20", "Historical limit is preserved only for comparison. Current legal requirements and material/product scope must be checked independently.",
        numeric=limit, evidence="report_quoted_historical_regulatory_limit", validation="historical_limit_not_current_regulatory_input")
    for sample, (material, origin) in SAMPLES.items():
        add(f"ALT15-T5-{sample}-{code}", "3;7", "laboratory_contaminant_assay", material,
            f"{name}_concentration", values[sample], "mg/kg organic matter", "Report Table 5 states mg/kg organic matter.",
            "§3.1, Table 5, printed p. 20", COMMON_LIMITS + " Report says values are below the report-era permitted values; not a current certification.",
            numeric=values[sample], conditions="Ensiled sample; source-reported chemical analysis.")

# Phase 5 digestion operation/case comparators. Mixed-feed gas values cannot be
# attributed to grass alone; mass-flow values are approximate and not closed.
for rid, metric, value, unit, basis, loc, note, validation in [
    ("ALT15-DORPEN-MAX-GRASS-FRACTION", "maximum_roadside_grass_fraction_in_fresh_digester_feed", "60", "% fresh input", "Manager-selected operating ceiling in a mixed green-waste/kitchen-waste dry digester due to perceived process-disturbance risk.", "§2.4.1, printed p. 16", "Not a measured biological threshold or GreenHub route constraint.", "operator_judgment_not_experimental_limit"),
    ("ALT15-OSTRA-POULTRY-FRACTION", "solid_poultry_manure_fraction_in_fresh_feed_mix", "25", "% fresh feed mix", "Reported Ostrhauderfehn feed recipe.", "§2.4.2, printed p. 18", "Co-digestion case includes manure, maize, grass and recycled digestate; not a grass-only route.", "reported_mixed_feed_recipe"),
    ("ALT15-OSTRA-MAIZE-FRACTION", "maize_fraction_in_fresh_feed_mix", "10", "% fresh feed mix", "Reported Ostrhauderfehn feed recipe.", "§2.4.2, printed p. 18", "Co-digestion case includes manure, maize, grass and recycled digestate; not a grass-only route.", "reported_mixed_feed_recipe"),
    ("ALT15-OSTRA-GRASS-FRACTION", "grass_fraction_in_fresh_feed_mix", "65", "% fresh feed mix", "Reported Ostrhauderfehn feed recipe.", "§2.4.2, printed p. 18", "Grass includes farm grass or grazed-dike grass; not GreenHub feed.", "reported_mixed_feed_recipe"),
    ("ALT15-OSTRA-RECYCLE-FRACTION", "preceding_digestate_recycle_fraction", "50", "% of fresh mixture; denominator/report wording retained", "Source says fresh material was mixed with a share of material from the preceding digester; exact denominator wording is not fully specified.", "§2.4.2, printed p. 18", "Do not combine the stated percentages into one normalized recipe without clarifying the recycle denominator.", "reported_recycle_basis_incomplete"),
    ("ALT15-OSTRA-MIX-GAS-WEIDE", "total_mixed_feed_biogas_yield_with_meadow_grass", "approximately 170", "m3 biogas/t total mixture", "Total mixture output before replacing meadow grass with nature grass, with same stated container residence time.", "§3.2.1.4, printed p. 25", "Source does not report exact gas standard state, uncertainty, or grass-specific gas contribution. Not a GreenHub grass yield.", "reported_mixed_feed_case_observation"),
    ("ALT15-OSTRA-MIX-GAS-NATURE", "total_mixed_feed_biogas_yield_with_nature_grass", "approximately 140", "m3 biogas/t total mixture", "Total mixture output after meadow grass was replaced with nature grass, with same stated container residence time.", "§3.2.1.4, printed p. 25", "Source does not report exact gas standard state, uncertainty, or grass-specific gas contribution. Not a GreenHub grass yield.", "reported_mixed_feed_case_observation"),
    ("ALT15-DORPEN-CASE-GRASS-INPUT", "roadside_grass_input_in_illustrative_1000t_mass_flow", "approximately 850", "tonne per reported 1000 tonne total input", "Narrative summary of Figure 3.3: approx. 850 t roadside grass plus 150 t digestate; input/output boundaries are not fully closed in text.", "§3.2.1.1, printed p. 23", "Approximate illustrative case, not a balanced GreenHub process or transferable yield.", "approximate_case_massflow_not_closed"),
    ("ALT15-DORPEN-CASE-DIGESTATE-INPUT", "digestate_input_in_illustrative_1000t_mass_flow", "approximately 150", "tonne per reported 1000 tonne total input", "Narrative summary of Figure 3.3: approx. 850 t roadside grass plus 150 t digestate.", "§3.2.1.1, printed p. 23", "Approximate illustrative case, not a balanced GreenHub process or transferable yield.", "approximate_case_massflow_not_closed"),
    ("ALT15-DORPEN-CASE-COMPOST-OUTPUT", "marketable_compost_from_illustrative_1000t_input", "approximately 270", "tonne per reported 1000 tonne total input", "Narrative summary of Figure 3.3.", "§3.2.1.1, printed p. 23", "Other gaseous, evaporative, leachate and screened outputs are not all quantified in this narrative; no closure is implied.", "approximate_case_massflow_not_closed"),
]:
    q = "C" if "gas yield" in metric or "biogas_yield" in metric else "B"
    add(rid, "5", "digestion_case_operating_or_massflow_observation", "mixed-feed dry anaerobic digestion case", metric,
        value, unit, basis, loc, note, numeric="" if "approximately" in value else value,
        conditions="Dörpen or Ostrhauderfehn installation as identified; historical report case.",
        evidence="reported_case_observation_or_operator_statement", quality=q, validation=validation)

# Phase 7: reported compost/digestate assays. These streams come from two
# different facilities and feed recipes, so the rows are not a paired process
# balance or a GreenHub fertilizer specification.
OUTPUTS = {
    "DORPEN-COMPOST-WITH-VERGE": ("Dörpen compost produced with roadside grass; report says the value is the average of the last two grass-containing loads", "Dörpen, Germany"),
    "DORPEN-COMPOST-WITHOUT-VERGE": ("Dörpen compost produced without roadside grass", "Dörpen, Germany"),
    "OSTRA-DIGESTATE-NATURE": ("Ostrhauderfehn digestate from a mixed feed containing nature grass", "Ostrhauderfehn, Germany"),
    "OSTRA-DIGESTATE-MEADOW": ("Ostrhauderfehn digestate from a mixed feed containing meadow grass", "Ostrhauderfehn, Germany"),
}
product_metrics = {
    "dry_matter": ("dry_matter_content", "kg/t reported product"),
    "organic_matter": ("organic_matter_content", "kg/t reported product"),
    "ash": ("ash_content", "kg/t reported product"),
    "total_n": ("total_nitrogen", "kg N/t reported product"),
    "ammonium_n": ("ammonium_nitrogen", "kg NH4-N/t reported product"),
    "nitrate_n": ("nitrate_nitrogen", "kg nitrate-N/t reported product"),
    "p2o5": ("phosphorus_as_P2O5", "kg P2O5/t reported product"),
    "k2o": ("potassium_as_K2O", "kg K2O/t reported product"),
    "mgo": ("magnesium_as_MgO", "kg MgO/t reported product"),
    "cao": ("calcium_as_CaO", "kg CaO/t reported product"),
    "sulfur": ("sulfur", "kg S/t reported product"),
}
product_values = {
    "dry_matter": ("578", "565", "222.4", "324.5"),
    "organic_matter": ("369", "188", "111.2", "180.7"),
    "ash": ("209", "377", "111.2", "144.2"),
    "total_n": ("16.5", "7.8", "7.51", "11.4"),
    "ammonium_n": ("0.37", "0.57", "1.23", "1.6"),
    "nitrate_n": ("0.20", "0.03", "<0.01", "<0.01"),
    "p2o5": ("7.45", "3.5", "3.13", "1.6"),
    "k2o": ("10.8", "5.5", "7.74", "5.4"),
    "mgo": ("4.55", "2.3", "1.64", "3.0"),
    "cao": ("28.5", "14.4", "3.15", "6.3"),
    "sulfur": ("-", "-", "0.83", "1.3"),
}
output_keys = tuple(OUTPUTS)
for code, (metric, unit) in product_metrics.items():
    for output_key, value in zip(output_keys, product_values[code]):
        material, site = OUTPUTS[output_key]
        if value == "-":
            value_text, numeric, validation = "not determined (source table marks '-')", "", "not_determined_in_source"
        elif value.startswith("<"):
            value_text, numeric, validation = value, "", "below_reported_quantification_limit"
        else:
            value_text, numeric, validation = value, value, "reported_value_preserved"
        product_limits = COMMON_LIMITS + " Product streams are not from one matched process; the grass-containing Dörpen compost is an average of the final two grass-containing loads."
        if output_key == "OSTRA-DIGESTATE-MEADOW" and code == "dry_matter":
            validation = "source_table_component_closure_difference_preserved"
            product_limits += " Table 7 reports DM 324.5 kg/t while OM 180.7 plus ash 144.2 equals 324.9 kg/t; the 0.4 kg/t discrepancy is preserved, not adjusted."
        add(f"ALT15-T7-{output_key}-{code.upper()}", "5;7", "laboratory_digestate_or_compost_characterization",
            material, metric, value_text, unit,
            "Report Table 7; table states kg/t but does not explicitly specify product moisture basis. Metals are separately reported per kg dry matter.",
            "§3.2.3.1, Table 7, printed p. 27", product_limits,
            numeric=numeric, period="Historical report samples; process campaigns 2014–2015",
            conditions=site + "; feed recipe and post-treatment differ between sites.",
            validation=validation)

product_metals = {
    "copper": ("copper", "mg/kg dry matter", ("55.9", "33.7", "19.8", "24.5")),
    "zinc": ("zinc", "mg/kg dry matter", ("167", "133", "118.1", "142.9")),
    "lead": ("lead", "mg/kg dry matter", ("18.0", "16.9", "-", "-")),
    "cadmium": ("cadmium", "mg/kg dry matter", ("0.32", "0.28", "-", "-")),
    "nickel": ("nickel", "mg/kg dry matter", ("6.65", "5.8", "-", "-")),
    "mercury": ("mercury", "mg/kg dry matter", ("0.05", "0.06", "-", "-")),
}
for code, (metric, unit, values) in product_metals.items():
    for output_key, value in zip(output_keys, values):
        material, site = OUTPUTS[output_key]
        if value == "-":
            value_text, numeric, validation = "not determined (source table marks '-')", "", "not_determined_in_source"
        else:
            value_text, numeric, validation = value, value, "reported_value_preserved"
        add(f"ALT15-T7-{output_key}-METAL-{code.upper()}", "7", "laboratory_product_metal_assay",
            material, f"{metric}_concentration", value_text, unit,
            "Report Table 7 explicitly states mg/kg dry matter for the metals block.",
            "§3.2.3.1, Table 7, printed p. 27", "Not a current fertilizer-compliance assessment; product values from different facilities/feed recipes are not directly paired.",
            numeric=numeric, period="Historical report samples; process campaigns 2014–2015",
            conditions=site + "; metal reporting is on dry-matter basis.", validation=validation)

# The PDF text extraction places the chromium line as four cells but does not
# reliably establish the column alignment. Preserve the source sequence only.
add("ALT15-T7-CHROMIUM-ROW-QUARANTINE", "7", "quarantined_table_row", "Table 7 chromium row across four product columns",
    "chromium_concentration", "20 | 15.1 | - | -", "mg/kg dry matter as table-block heading",
    "Literal sequence from report Table 7; sample-column alignment cannot be established with sufficient confidence from accessible text extraction.",
    "§3.2.3.1, Table 7, printed p. 27", "Do not assign these values to individual products or use them as a compliance check.",
    evidence="source_table_text_alignment_uncertain", validation="quarantined_source_alignment_ambiguity")

# Phase 7: report-modeled climate comparator and explicit emissions gaps.
for rid, metric, value, unit, basis, loc in [
    ("ALT15-LCA-GHG-GROSS-SAVING", "gross_avoided_greenhouse_gas_emissions", "approximately 150", "t CO2-equivalent/1000 t roadside grass", "Report's Dörpen scenario versus natural-gas use, before listed chain burdens.", "§3.2.2.1, printed p. 26"),
    ("ALT15-LCA-GHG-NET-SAVING", "net_avoided_greenhouse_gas_emissions", "approximately 60", "t CO2-equivalent/1000 t roadside grass", "Report's Dörpen scenario versus natural-gas use after transport, electricity, heat and assumed 1% biogas leakage.", "§3.2.2.1, printed p. 26"),
    ("ALT15-LCA-TRANSPORT", "transport_distance_assumption", "25", "km one-way/report scenario distance", "Energy-balance discussion uses a 25 km transport distance; exact load, return trip and vehicle fuel assumptions are not supplied here.", "§3.2.1.3, printed p. 24"),
    ("ALT15-LCA-METHANE-LEAK-ASSUMPTION", "biogas_leakage_assumption_in_ghg_case", "1", "% biogas production", "Dörpen GHG scenario explicitly assumes 1% biogas leakage; the surrounding report gives typical leak statement 1–2%, but this is not measured at the site.", "§3.2.2, printed p. 26"),
]:
    add(rid, "7", "historical_modeled_lca_scenario_result_or_assumption", "Dörpen dry digestion case", metric,
        value, unit, basis, loc,
        "Historical report scenario only. Functional-unit details, characterization method/version, complete inventory, biogenic-carbon treatment and reproducible calculation files are not reported; not an LCA factor or GreenHub result.",
        numeric=value if value.isdigit() else "", conditions="Dörpen dry digestion compared with natural-gas use.",
        evidence="author_modeled_scenario_result_or_assumption", quality="C",
        validation="historical_scenario_incomplete_lca_boundary")

for rid, metric, value in [
    ("ALT15-LCA-OPEN-DIGESTATE-CH4", "open_digestate_methane_emissions", "Not measured/quantified; report flags likely volatilization."),
    ("ALT15-LCA-OPEN-DIGESTATE-NH3", "open_digestate_ammonia_emissions", "Not measured/quantified; report flags likely volatilization."),
    ("ALT15-LCA-OSTRA-BALANCE", "Ostrhauderfehn_mass_energy_ghg_balance", "Not calculated because required data were unavailable."),
]:
    add(rid, "7", "explicit_source_missingness_or_unquantified_emission", "Ostrhauderfehn mixed-feed digestate or process", metric,
        value, "not reported", "Qualitative source statement; do not convert to zero.", "§2.4.2 and §3.2.2.2, printed pp. 18 and 26",
        "This source explicitly identifies a missing value; no numeric emission or balance is inferred.",
        evidence="source_explicitly_reports_missing_measurement", quality="B", validation="not_reported_not_zero")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def upsert(path: Path, record: dict[str, str], key: str) -> None:
    fields, rows = read_csv(path)
    if not fields:
        fields = list(record)
    old = next((row for row in rows if row.get(key) == record[key]), None)
    if old is None:
        rows.append(record)
    else:
        old.update(record)
    write_csv(path, fields, rows)


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    write_csv(OUT, FIELDS, ROWS)
    checksum = hashlib.sha256(OUT.read_bytes()).hexdigest()
    metadata = {
        "dataset_id": "urn:greenhub:dataset:feed-bmp:alterra-2661-roadside-grass-dry-ad-reference:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": checksum,
        "source_id": SOURCE_ID,
        "citation": "Zwart, K.B. & de Boer, D. (2015). Droge vergisting van berm- en natuurgras. Alterra-rapport 2661. Wageningen: Alterra Wageningen UR. ISSN 1566-7197.",
        "publication_year": 2015,
        "doi": None,
        "persistent_identifier": "No DOI identified; Alterra report 2661, ISSN 1566-7197; WUR repository record retained.",
        "source_url": SOURCE_RECORD_URL,
        "source_pdf_url": INSTITUTIONAL_PDF_URL,
        "accessible_full_text_url": SOURCE_PDF_URL,
        "retrieval_date": RETRIEVED,
        "source_location": "Report sections 2.1–2.4, 3.1, 3.2.1–3.2.2; exact section/table/printed-page location is stored per row.",
        "geography": "Borger-Odoorn and southeast Drenthe, Sellingen (Netherlands); digestion cases Dörpen and Ostrhauderfehn (Germany).",
        "material_scope": "2013 ensiled Dutch roadside verge grass and nature grass; dry digestion cases co-process grass with other materials; compost and digestate comparisons.",
        "evidence_class": "B-class primary project-report measurements and case observations; modeled environmental comparison is separately marked C and reference-only.",
        "quality_class": "B; row-level C retained for modeled LCA comparator records.",
        "license_or_rights": "No explicit open reuse license identified on WUR record or report copy; source PDF is not redistributed. Short factual observations are attributed; reuse rights require confirmation.",
        "access_protocol": "HTTPS to WUR repository record/institutional PDF and an author-uploaded full-text mirror; institutional PDF endpoint returned access denial to automated retrieval during research.",
        "data_structure": "Long-form UTF-8 CSV with unique record IDs; source text, numeric value, unit, basis, condition, source location, evidence, validation and limitations are separate.",
        "conversion_or_processing": "Direct transcription from Tables 2–5 and selected report narrative statements. No unreported SD, standard-state conversion, gas upgrading, mass closure, or emission factor was derived. Water basis remains explicitly qualified where not stated.",
        "uncertainty": "No replicate count or uncertainty interval is available in summary feed tables. The dry-digestion cases use mixed feeds and differing installations; grass-specific yields and several emissions are not measured. Historical modeled climate results are not reproducible from the report alone.",
        "limitations": [
            "Local 2013 samples and historical cases do not represent current GreenHub/VARTA feed, delivery or operations.",
            "The summary table basis is kg/t and the wet/as-sampled interpretation is inferred from context rather than explicit in the table heading.",
            "Potential biogas yields are not standardized BMP endpoints; no standard gas conditions are stated.",
            "The Ostrhauderfehn results involve manure, maize, grass and recycled digestate; mixed-mixture gas yield cannot be assigned to grass alone.",
            "The report compares two different facilities, so process and digestate outputs are not matched controlled configurations.",
            "Historical contaminant limits are not current legal thresholds or product acceptance data.",
            "Historical GHG scenario lacks a reproducible full LCA boundary, method/version and inventory; it must not be presented as a GreenHub LCA result.",
            "No direct information is supplied for protein extraction/precipitation (Phase 4) or gas upgrading recovery/specification (Phase 6).",
            "No explicit reuse license was identified.",
        ],
        "phase_coverage": {
            "1": "Local road length, ecological management extent, mowing frequency/month context, sample origins and an autumn shortfall; not accessible/current delivered supply.",
            "2": "Harvest and ensiling-to-use intervals are described but storage days, temperature, losses and time-course chemistry are not measured.",
            "3": "Feed DM/organic matter/ash and contaminant assays inform feed quality, but no GreenHub pretreatment or fractionation balance.",
            "4": "No protein extraction, precipitation, reagent use or product recovery measurements.",
            "5": "Feed nutrient composition, potential biogas estimates, one lab gas result and mixed-feed dry-AD operating observations; not post-protein residual kinetics.",
            "6": "No gas-upgrading energy, methane recovery, impurity removal or saleable gas specification.",
            "7": "Historical modeled GHG comparison and explicitly unquantified open digestate emissions; not a complete or current LCA inventory.",
        },
        "runtime_policy": "reference_only; no parameter registry, default, process equation, TEA/LCA factor, route, scenario or Pareto mapping is created.",
        "calculation_connected": False,
        "fair_metadata": {
            "findable": "Repository-local URN, stable report/source IDs, SHA-256 and catalog-indexed relative path; no DOI is fabricated.",
            "accessible": "WUR record, institutional endpoint and accessible author-uploaded report mirror are linked; no source file is copied.",
            "interoperable": "Long-form UTF-8 CSV with explicit units, bases, periods, conditions, evidence and source locations.",
            "reusable": "Full citation, retrieval date, rights caveat, row validation, transferability, uncertainty and limitations are recorded.",
        },
    }
    OUT.with_suffix(".source.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = FOLDER / "dataset_manifest.csv"
    upsert(manifest, {
        "filename": FILENAME,
        "description": "Alterra 2661 local roadside/nature-grass feed assays, storage context, mixed-feed dry-AD and digestate/compost comparators; reference-only.",
        "row_count": str(len(ROWS)), "schema_version": "1.0", "encoding": "UTF-8 with BOM",
        "delimiter": ",", "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "record_id",
    }, "filename")
    upsert(FOLDER / "source_register.csv", {
        "source_id": SOURCE_ID,
        "source_title": "Droge vergisting van berm- en natuurgras (Alterra-rapport 2661)",
        "authors": "Kor B. Zwart; Dirk de Boer",
        "year": "2015", "doi_or_stable_id": "No DOI; Alterra report 2661; ISSN 1566-7197",
        "source_type": "Institutional applied research report with field sample analyses and historical dry-digestion cases",
        "url": SOURCE_RECORD_URL,
        "material_scope": "Dutch 2013 roadside verge and nature grass; mixed-feed dry digestion and output-product comparators",
        "quality_notes": "Feed assays are direct report measurements (B, reference-only); gas potential and mixed-feed case results have incomplete methods/bases; modeled GHG rows are C/reference-only. No runtime activation.",
    }, "source_id")

    relative = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
    quality_notes = "Local 2013 source; mixed-feed and modeled outputs remain reference-only; source bases/uncertainties and full LCA boundary are incomplete."
    for filename, record, key in [
        ("global_source_register.csv", {
            "dataset_path": relative, "dataset_group": "Feed BMP", "source_id": SOURCE_ID,
            "source_title": "Droge vergisting van berm- en natuurgras (Alterra-rapport 2661)",
            "authors": "Kor B. Zwart; Dirk de Boer", "year": "2015",
            "doi_or_stable_id": "No DOI; Alterra report 2661; ISSN 1566-7197",
            "url": SOURCE_RECORD_URL, "source_type": "Institutional applied research report",
            "notes": quality_notes,
        }, "dataset_path"),
        ("global_dataset_manifest.csv", {
            "dataset_path": relative, "category": "Biogas production + upgrade", "subgroup": "Feed BMP",
            "filename": FILENAME, "row_count_observed": str(len(ROWS)), "header_count": str(len(FIELDS)),
            "headers": "; ".join(FIELDS), "standardized_status_values": "B/C;reference_only",
            "detected_readiness": "D3", "notes": quality_notes,
        }, "dataset_path"),
        ("global_dataset_readiness.csv", {
            "dataset_path": relative, "category": "Biogas production + upgrade", "subgroup": "Feed BMP",
            "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
            "numeric_rows": str(sum(bool(r["value_numeric"]) for r in ROWS)), "unsourced_numeric_rows": "0",
            "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0", "basis_conflicts": "0",
            "cross_reference_issues": "0", "equation_missing_inputs": "0", "equation_symbol_mismatches": "0",
            "notes": quality_notes,
        }, "dataset_path"),
        ("source_dataset_checksums.csv", {
            "dataset_path": relative, "sha256": checksum, "byte_size": str(OUT.stat().st_size),
        }, "dataset_path"),
    ]:
        upsert(AUDIT / filename, record, key)

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, global_manifests = read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness_rows = read_csv(AUDIT / "global_dataset_readiness.csv")
    readiness_counts: dict[str, int] = {}
    for row in readiness_rows:
        readiness_counts[row.get("readiness", "")] = readiness_counts.get(row.get("readiness", ""), 0) + 1
    summary["dataset_count"] = len(global_manifests)
    summary["readiness_counts"] = readiness_counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": FILENAME, "rows": len(ROWS), "sha256": checksum}, indent=2))


if __name__ == "__main__":
    main()
