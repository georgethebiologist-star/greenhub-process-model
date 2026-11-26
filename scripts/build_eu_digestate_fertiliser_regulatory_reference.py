"""Stage EU and Dutch fertilizer-route requirements for Phase 7.

This is regulatory reference data. It does not select a product category,
establish project eligibility, provide measured product composition, or enable
fertilizer revenue in the model.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
PACKAGE = DATA / "Resource recovery" / "Digestate_and_Separation"
AUDIT = DATA / "global_audit_package"
FILENAME = "eu_digestate_fertiliser_regulatory_requirements_2019_1009_2026_reference.csv"
DATASET = f"Resource recovery/Digestate_and_Separation/{FILENAME}"
SOURCE_EU = "SRC-EU-REG-2019-1009-CONSOL-2026-07-01"
SOURCE_NL = "SRC-NL-BUSINESSGOV-FERTILISER-RESIDUE-ADMISSION"
SOURCE_RVO = "SRC-NL-RVO-ANNEX-AA-DIGESTATE-2026"
EU_URL = "https://eur-lex.europa.eu/eli/reg/2019/1009/2026-07-01/eng/pdf"
NL_URL = "https://business.gov.nl/regulations/artificial-fertilisers-biostimulants/"
RVO_URL = "https://www.rvo.nl/onderwerpen/mest/bewerken/afvalstoffen-reststoffen"
RETRIEVED = "2026-11-08"

FIELDS = [
    "record_id", "phase", "source_id", "jurisdiction", "legislation_version",
    "effective_from", "pathway", "cmc", "pfc", "requirement_type", "criterion",
    "analyte", "operator", "value", "unit", "value_max", "unit_max",
    "secondary_value", "secondary_unit", "tertiary_value", "tertiary_unit",
    "condition_text", "legal_location", "data_status", "evidence_class",
    "quality_class", "activation_state", "applicability", "notes",
]

EU_VERSION = "Regulation (EU) 2019/1009, consolidated reference text 2026-07-01"
EU_BASE_EFFECTIVE = "2022-07-16"
EU_COMMON = (
    "CE-marked EU fertilising product pathway only. Confirm the intended product function category (PFC), "
    "component material category (CMC), input eligibility and conformity-assessment route before applying. "
    "Reference-only; not a measured project result or a runtime default."
)
ROWS: list[dict[str, str]] = []


def add(
    code: str,
    *,
    source: str = SOURCE_EU,
    jurisdiction: str = "European Union",
    version: str = EU_VERSION,
    effective: str = EU_BASE_EFFECTIVE,
    pathway: str,
    cmc: str = "",
    pfc: str = "",
    kind: str = "regulatory_limit",
    criterion: str,
    analyte: str = "",
    operator: str = "",
    value: str = "",
    unit: str = "",
    value_max: str = "",
    unit_max: str = "",
    secondary: str = "",
    secondary_unit: str = "",
    tertiary: str = "",
    tertiary_unit: str = "",
    conditions: str = "",
    location: str,
    status: str = "official_regulatory_requirement",
    applicability: str = EU_COMMON,
    notes: str = "Directly transcribed; no inference or runtime activation.",
) -> None:
    ROWS.append({
        "record_id": f"EUFPR26-{code}",
        "phase": "7",
        "source_id": source,
        "jurisdiction": jurisdiction,
        "legislation_version": version,
        "effective_from": effective,
        "pathway": pathway,
        "cmc": cmc,
        "pfc": pfc,
        "requirement_type": kind,
        "criterion": criterion,
        "analyte": analyte,
        "operator": operator,
        "value": value,
        "unit": unit,
        "value_max": value_max,
        "unit_max": unit_max,
        "secondary_value": secondary,
        "secondary_unit": secondary_unit,
        "tertiary_value": tertiary,
        "tertiary_unit": tertiary_unit,
        "condition_text": conditions,
        "legal_location": location,
        "data_status": status,
        "evidence_class": "official_regulatory_requirement" if source == SOURCE_EU else "official_government_guidance",
        "quality_class": "not_applicable_regulatory",
        "activation_state": "reference_only",
        "applicability": applicability,
        "notes": notes,
    })


CMC45 = "CMC4 or CMC5; specific product eligibility must be checked"
CMC45_LOC = "Annex II, Part II, CMC4 point 3 and CMC5 point 3"
SANITATION_CONDITIONS = "All parts of each batch must be regularly and thoroughly moved and turned to ensure sanitation and homogeneity. Select one complete alternative profile; do not mix partial criteria."

add("CMC4_INPUT_SCOPE", pathway="EU CE-marked product; fresh-crop digestate", cmc="CMC4", kind="eligibility_gate", criterion="Eligible feedstock scope", location="Annex II, Part II, CMC4 point 1(a)-(c)", conditions="Plants or plant parts grown for biogas production; qualifying digestion additives; or material from those plants previously digested.", notes="Roadside grass is not assumed to have been grown for biogas. Confirm legal interpretation for the specific feedstock and its collection status.")
add("CMC5_INPUT_SCOPE", pathway="EU CE-marked product; digestate other than fresh-crop digestate", cmc="CMC5", kind="eligibility_gate", criterion="Eligible feedstock scope", location="Annex II, Part II, CMC5 point 1 and point 1a", conditions="Includes separately collected bio-waste and certain organisms/plant parts under specified processing limits; excludes materials from mixed municipal waste, sewage/industrial/dredged sludge, and covered animal by-products unless the separate legal conditions are met.", notes="Roadside mowings, litter, soil/sand, pre-processing, co-feeds and any waste/by-product status require project-specific legal classification; this row does not declare the project eligible.")
add("CMC4_LINE_SEPARATION", pathway="EU CE-marked product; fresh-crop digestate", cmc="CMC4", kind="process_control", criterion="Separated production lines", location="Annex II, Part II, CMC4 point 2(a)-(b)", conditions="Processing lines for qualifying CMC4 inputs must be clearly separated from lines for other inputs; physical contact between input and output material must be avoided, including during storage.")
add("CMC5_LINE_SEPARATION", pathway="EU CE-marked product; other digestate", cmc="CMC5", kind="process_control", criterion="Separated production lines", location="Annex II, Part II, CMC5 point 2(a)-(b)", conditions="Processing lines for qualifying CMC5 inputs must be clearly separated from lines for other inputs; physical contact between input and output material must be avoided, including during storage.")
add("CMC45_ADDITIVES_INPUT", pathway="EU CE-marked product; CMC4/CMC5 digestion", cmc=CMC45, kind="process_limit", criterion="Total digestion additives", operator="<=", value="5", unit="% of total input material mass", location="Annex II, Part II, CMC4 point 1(b)(ii); CMC5 point 1(d)(ii)", conditions="Additives must also satisfy the applicable CMC1 substance requirements.")

# The sanitation alternatives are explicit, source-located alternatives. The
# legal text cross-refers for pasteurisation details; those are intentionally not
# replaced by a value from a different regulation here.
add("SAN_THERMO_55_24H", pathway="EU CE-marked product; CMC4/CMC5 sanitation alternative A", cmc=CMC45, kind="alternative_sanitation_profile", criterion="Thermophilic AD followed by HRT", analyte="AD temperature; exposure duration; hydraulic retention time", operator=">=", value="55", unit="degC", secondary="24", secondary_unit="h", tertiary="20", tertiary_unit="d HRT", location=CMC45_LOC, conditions=SANITATION_CONDITIONS)
add("SAN_THERMO_55_PASTEURISATION", pathway="EU CE-marked product; CMC4/CMC5 sanitation alternative B", cmc=CMC45, kind="alternative_sanitation_profile", criterion="Thermophilic AD with pasteurisation", analyte="AD temperature", operator=">=", value="55", unit="degC", location=CMC45_LOC, conditions=SANITATION_CONDITIONS + " Pasteurisation must comply with Commission Regulation (EU) No 142/2011, Annex V, Chapter I, Section 1.", notes="The referenced pasteurisation rule is not numerically re-expressed in this record; check the applicable current animal-by-product requirements.")
for suffix, ad_temp, compost_temp, compost_days in (
    ("70C_3D", "55", "70", "3"),
    ("65C_5D", "55", "65", "5"),
    ("60C_7D", "55", "60", "7"),
    ("55C_14D", "55", "55", "14"),
):
    add(f"SAN_THERMO_COMPOST_{suffix}", pathway="EU CE-marked product; CMC4/CMC5 sanitation alternative C", cmc=CMC45, kind="alternative_sanitation_profile", criterion="Thermophilic AD followed by composting", analyte="AD temperature; compost temperature; compost duration", operator=">=", value=ad_temp, unit="degC AD", secondary=compost_temp, secondary_unit="degC compost", tertiary=compost_days, tertiary_unit="d compost", location=CMC45_LOC, conditions=SANITATION_CONDITIONS)
add("SAN_MESO_37_40_PASTEURISATION", pathway="EU CE-marked product; CMC4/CMC5 sanitation alternative D", cmc=CMC45, kind="alternative_sanitation_profile", criterion="Mesophilic AD with pasteurisation", analyte="AD temperature", operator="range", value="37", value_max="40", unit="degC", unit_max="degC", location=CMC45_LOC, conditions=SANITATION_CONDITIONS + " Pasteurisation must comply with Commission Regulation (EU) No 142/2011, Annex V, Chapter I, Section 1.", notes="The referenced pasteurisation rule is not numerically re-expressed in this record; check the applicable current animal-by-product requirements.")
for suffix, compost_temp, compost_days in (("70C_3D", "70", "3"), ("65C_5D", "65", "5"), ("60C_7D", "60", "7"), ("55C_14D", "55", "14")):
    add(f"SAN_MESO_COMPOST_{suffix}", pathway="EU CE-marked product; CMC4/CMC5 sanitation alternative E", cmc=CMC45, kind="alternative_sanitation_profile", criterion="Mesophilic AD followed by composting", analyte="AD temperature range; compost temperature; compost duration", operator="range/at least", value="37", unit="degC AD", value_max="40", unit_max="degC AD", secondary=compost_temp, secondary_unit="degC compost", tertiary=compost_days, tertiary_unit="d compost", location=CMC45_LOC, conditions=SANITATION_CONDITIONS)

add("CMC45_MECHANICAL_FRACTION", pathway="EU CE-marked product; digestate fraction", cmc=CMC45, kind="eligible_processing", criterion="Solid or liquid fraction", location="Annex II, Part II, CMC4 point 3a; CMC5 point 3a", conditions="A solid or liquid fraction obtained by mechanical separation of digestate compliant with the applicable feedstock and sanitation points may be included.")
add("CMC45_NH4_P_REMOVAL", pathway="EU CE-marked product; digestate nutrient recovery", cmc=CMC45, kind="eligible_processing", criterion="Removal of soluble ammonium and/or phosphate", location="Annex II, Part II, CMC4 point 3b; CMC5 point 3b", conditions="Removal to recover N and/or P is described for compliant digestate/fractions without intent to otherwise modify the digestate or fraction. Product status of the recovered N/P stream must be assessed separately.")
add("CMC45_WATER_REMOVAL", pathway="EU CE-marked product; digestate dewatering", cmc=CMC45, kind="eligible_processing", criterion="Physical water removal", location="Annex II, Part II, CMC4 point 3c; CMC5 point 3c", conditions="The permitted processing described is only physical water removal, subject to the upstream digestate/fraction conditions.")
add("CMC45_POST_ADDITIVES", pathway="EU CE-marked product; digestate post-processing", cmc=CMC45, kind="process_limit", criterion="Post-processing additives", operator="<=", value="5", unit="% of digestate/fraction input mass", location="Annex II, Part II, CMC4 point 3d(b); CMC5 point 3d(b)", conditions="Applies to additives needed in each specified post-processing step; additive must also comply with CMC1 point 2.")

add("CMC4_STABILITY_O2", pathway="EU CE-marked product; CMC4 digestate/fraction stability", cmc="CMC4", kind="alternative_stability_criterion", criterion="Oxygen uptake rate", analyte="O2 uptake per organic matter", operator="<=", value="25", unit="mmol O2/kg organic matter/h", location="Annex II, Part II, CMC4 point 4(a)", conditions="At least one listed CMC4 stability criterion must be met. Method is unsuitable where particles >10 mm exceed 20%.")
add("CMC4_STABILITY_BMP", pathway="EU CE-marked product; CMC4 digestate/fraction stability", cmc="CMC4", kind="alternative_stability_criterion", criterion="Residual biogas potential", analyte="biogas per volatile solids", operator="<=", value="0.25", unit="L biogas/g volatile solids", secondary="28", secondary_unit="d test", location="Annex II, Part II, CMC4 point 4(b)", conditions="Triplicate test; arithmetic mean used; volatile solids determined as loss on ignition of dry solids at 550 degC. This is a regulatory stability test, not a BMP yield factor.")

add("CMC5_PAH16", pathway="EU CE-marked product; CMC5 digestate/fraction", cmc="CMC5", kind="contaminant_limit", criterion="PAH16", analyte="sum of 16 specified PAHs", operator="<=", value="6", unit="mg/kg dry matter", location="Annex II, Part II, CMC5 point 4 and footnote 7")
add("CMC5_MACRO_INDIVIDUAL", pathway="EU CE-marked product; CMC5 digestate/fraction", cmc="CMC5", kind="contaminant_limit", criterion="Macroscopic impurities >2 mm, each listed material", analyte="glass OR metal OR plastic", operator="<=", value="3", unit="g/kg dry matter", location="Annex II, Part II, CMC5 point 5(a)")
add("CMC5_MACRO_SUM", pathway="EU CE-marked product; CMC5 digestate/fraction", cmc="CMC5", kind="contaminant_limit", criterion="Sum of macroscopic impurities >2 mm", analyte="glass + metal + plastic", operator="<=", value="5", unit="g/kg dry matter", location="Annex II, Part II, CMC5 point 5(b)")
add("CMC5_PLASTIC_2026", pathway="EU CE-marked product; CMC5 digestate/fraction", effective="2026-07-16", cmc="CMC5", kind="contaminant_limit", criterion="Plastic impurities >2 mm", analyte="plastic", operator="<=", value="2.5", unit="g/kg dry matter", location="Annex II, Part II, CMC5 point 5, sentence effective 16 July 2026", notes="Applies within the 3 g/kg individual macroscopic-impurity cap. The regulation states that this 2.5 g/kg limit is to be reassessed by 16 July 2029.")
add("CMC5_STABILITY_O2", pathway="EU CE-marked product; CMC5 digestate/fraction stability", cmc="CMC5", kind="alternative_stability_criterion", criterion="Oxygen uptake rate", analyte="O2 uptake per organic matter", operator="<=", value="25", unit="mmol O2/kg organic matter/h", location="Annex II, Part II, CMC5 point 6(a)", conditions="At least one listed CMC5 stability criterion must be met. Method is unsuitable where particles >10 mm exceed 20%.")
add("CMC5_STABILITY_BMP", pathway="EU CE-marked product; CMC5 digestate/fraction stability", cmc="CMC5", kind="alternative_stability_criterion", criterion="Residual biogas potential", analyte="biogas per volatile solids", operator="<=", value="0.25", unit="L biogas/g volatile solids", secondary="28", secondary_unit="d test", location="Annex II, Part II, CMC5 point 6(b)", conditions="Triplicate test; arithmetic mean used; volatile solids determined as loss on ignition of dry solids at 550 degC. This is a stability test, not a BMP yield factor.")

PFC1A = "PFC 1(A), organic fertiliser; pathway only if classification is verified"
PFC1A_LOC = "Annex I, Part II, PFC 1(A)"
for analyte, value in (("cadmium (Cd)", "1.5"), ("hexavalent chromium (Cr VI)", "2"), ("mercury (Hg)", "1"), ("nickel (Ni)", "50"), ("lead (Pb)", "120"), ("inorganic arsenic (As)", "40")):
    code = analyte.upper().replace(" ", "_").replace("(", "").replace(")", "")
    add(f"PFC1A_{code}", pathway=PFC1A, pfc="PFC1(A)", kind="contaminant_limit", criterion=f"{analyte} maximum", analyte=analyte, operator="<=", value=value, unit="mg/kg dry matter", location=f"{PFC1A_LOC}, point 2")
add("PFC1A_CU_MAX", pathway=PFC1A, pfc="PFC1(A)", kind="contaminant_limit", criterion="Copper maximum", analyte="copper (Cu)", operator="<=", value="300", unit="mg/kg dry matter", location=f"{PFC1A_LOC}, point 3")
add("PFC1A_ZN_MAX", pathway=PFC1A, pfc="PFC1(A)", kind="contaminant_limit", criterion="Zinc maximum", analyte="zinc (Zn)", operator="<=", value="800", unit="mg/kg dry matter", location=f"{PFC1A_LOC}, point 3")
add("PFC1A_BIURET_ABSENT", pathway=PFC1A, pfc="PFC 1(A)", kind="contaminant_limit", criterion="Biuret must not be present", analyte="biuret", operator="absent", location=f"{PFC1A_LOC}, point 2", conditions="No numerical tolerance is given; do not encode absence as a measured project value.")
add("PFC1A_SALMONELLA", pathway=PFC1A, pfc="PFC 1(A)", kind="pathogen_limit", criterion="Salmonella spp.", analyte="Salmonella spp.", operator="absent", location=f"{PFC1A_LOC}, point 4 and sampling-plan table", conditions="Sampling plan: n=5, c=0, m=0; absence in 25 g or 25 ml.")
add("PFC1A_ECOLI_ENTEROCOCCI", pathway=PFC1A, pfc="PFC 1(A)", kind="pathogen_limit", criterion="E. coli or enterococci", analyte="E. coli or enterococci", operator="<=", value="1000", unit="CFU/g or CFU/ml", location=f"{PFC1A_LOC}, point 4 and sampling-plan table", conditions="Sampling plan: n=5, c=5, m=0; maximum M=1000 in 1 g or 1 ml.")
add("PFC1A_ORIGIN", pathway=PFC1A, pfc="PFC 1(A)", kind="product_definition", criterion="Organic origin of nutrients and carbon", location=f"{PFC1A_LOC}, point 1", conditions="Product must contain organic carbon and nutrients of solely biological origin. This category may not fit recovered mineral nutrient salts or all formulated products.")

for phase, nutrient, single, multi in (
    ("SOLID", "total nitrogen (N)", "2.5", "1"),
    ("SOLID", "total phosphorus pentoxide (P2O5)", "2", "1"),
    ("SOLID", "total potassium oxide (K2O)", "2", "1"),
    ("LIQUID", "total nitrogen (N)", "2", "1"),
    ("LIQUID", "total phosphorus pentoxide (P2O5)", "1", "1"),
    ("LIQUID", "total potassium oxide (K2O)", "2", "1"),
):
    code = nutrient.split("(")[0].strip().upper().replace(" ", "_")
    pfc_subtype = f"PFC1A_{phase}"
    location = f"{PFC1A_LOC}, PFC 1(A)({'I' if phase == 'SOLID' else 'II'}), point 2"
    add(f"{pfc_subtype}_{code}_SINGLE", pathway=f"{PFC1A}; {phase.lower()} product; one declared primary nutrient", pfc="PFC1(A)(I)" if phase == "SOLID" else "PFC1(A)(II)", kind="minimum_nutrient_content", criterion=f"{nutrient} minimum when it is the only declared primary nutrient", analyte=nutrient, operator=">=", value=single, unit="mass-% of product", location=location)
    add(f"{pfc_subtype}_{code}_MULTI", pathway=f"{PFC1A}; {phase.lower()} product; multiple declared primary nutrients", pfc="PFC1(A)(I)" if phase == "SOLID" else "PFC1(A)(II)", kind="minimum_nutrient_content", criterion=f"{nutrient} minimum when multiple primary nutrients are declared", analyte=nutrient, operator=">=", value=multi, unit="mass-% of product", location=location, conditions="The separate combined nutrient-sum minimum also applies.")
add("PFC1A_SOLID_NPK_SUM", pathway=f"{PFC1A}; solid product; multiple declared primary nutrients", pfc="PFC1(A)(I)", kind="minimum_nutrient_content", criterion="Sum of declared N + P2O5 + K2O", operator=">=", value="4", unit="mass-% of product", location=f"{PFC1A_LOC}, PFC 1(A)(I), point 2")
add("PFC1A_LIQUID_NPK_SUM", pathway=f"{PFC1A}; liquid product; multiple declared primary nutrients", pfc="PFC1(A)(II)", kind="minimum_nutrient_content", criterion="Sum of declared N + P2O5 + K2O", operator=">=", value="3", unit="mass-% of product", location=f"{PFC1A_LOC}, PFC 1(A)(II), point 2")
add("PFC1A_SOLID_CORG_MIN", pathway=f"{PFC1A}; solid product", pfc="PFC1(A)(I)", kind="minimum_carbon_content", criterion="Organic carbon (Corg)", analyte="Corg", operator=">=", value="15", unit="mass-% of product", location=f"{PFC1A_LOC}, PFC 1(A)(I), point 3")
add("PFC1A_LIQUID_CORG_MIN", pathway=f"{PFC1A}; liquid product", pfc="PFC1(A)(II)", kind="minimum_carbon_content", criterion="Organic carbon (Corg)", analyte="Corg", operator=">=", value="5", unit="mass-% of product", location=f"{PFC1A_LOC}, PFC 1(A)(II), point 3")

add("NL_RESIDUE_ADMISSION", source=SOURCE_NL, jurisdiction="Netherlands", version="Business.gov.nl guidance retrieved 2026-11-08", effective="", pathway="Dutch national fertilizer route for products from waste/residues", kind="market_access_pathway", criterion="Special admission procedure", location="Business.gov.nl, Artificial fertilisers and biostimulants, section on new fertilisers made from waste and residues", status="official_government_guidance", applicability="National route only; assess the legal status of the material, RVO admission/positive-list criteria and intended product. This is separate from CE-marked EU FPR route.", conditions="Government guidance states that new fertilisers made from waste and residues require a special admission procedure through RVO; accepted products are placed on a positive list annexed to the Dutch Fertilisers Act Implementation Decree.", notes="No numerical nutrient, contaminant, or price acceptance is inferred from this guidance. Obtain current RVO decision and product-specific requirements.")

# The recovered-phosphate route is relevant to candidate struvite, but its
# source-material and PFC conditions are stricter than “contains phosphorus”.
CMC12_PATH = "EU CE-marked product; precipitated phosphate salt (CMC12)"
CMC12_LOC = "Annex II, Part II, CMC12"
add("CMC12_INPUT_SCOPE", pathway=CMC12_PATH, cmc="CMC12", kind="eligibility_gate", criterion="Permitted source-material classes", location=f"{CMC12_LOC}, point 1(a)-(f)", conditions="Precipitated phosphate salts must come exclusively from the listed wastewater/sludge, food-processing, separately collected bio-waste, specified biofuel residues, qualifying organisms/parts, or qualifying substances/mixtures. Additional allowed treatments and exclusions apply.", notes="This row is a legal classification gate, not confirmation that GreenHub grass digestate or a recovered salt qualifies. Determine the exact waste/by-product status, feedstock collection, co-feed and treatment chain with the competent authority/notified body.")
add("CMC12_ALLOWED_TREATMENT", pathway=CMC12_PATH, cmc="CMC12", kind="eligible_processing", criterion="Allowed processing before precipitation", location=f"{CMC12_LOC}, point 1 and point 1(f)", conditions="Listed processing includes manual/mechanical/gravitational processing, biodegradable-polymer solid-liquid fractionation, water dissolution/flotation/extraction, steam distillation, heating solely to remove water, thermal hydrolysis, anaerobic digestion or composting; process temperature must not exceed 275 degC.", notes="Do not infer eligibility for unlisted chemical or enzymatic treatments; classify each operation and the input chain first.")
add("CMC12_REACTOR_AND_CONTAMINATION", pathway=CMC12_PATH, cmc="CMC12", kind="process_control", criterion="Controlled precipitation and input contamination", location=f"{CMC12_LOC}, point 2", conditions="Precipitation must occur under controlled conditions in a reactor. Inputs must not be contaminated with other material streams except the narrowly described one-off trace-level contamination; input/output physical contact must be avoided after precipitation, including storage.")
add("CMC12_P2O5_MIN", pathway=CMC12_PATH, cmc="CMC12", kind="minimum_nutrient_content", criterion="Minimum phosphorus pentoxide", analyte="P2O5", operator=">=", value="16", unit="% of dry matter", location=f"{CMC12_LOC}, point 3(a)")
add("CMC12_CORG_MAX", pathway=CMC12_PATH, cmc="CMC12", kind="maximum_organic_carbon", criterion="Maximum organic carbon", analyte="Corg", operator="<=", value="3", unit="% of dry matter", location=f"{CMC12_LOC}, point 3(b)")
add("CMC12_MACRO_EACH_MAX", pathway=CMC12_PATH, cmc="CMC12", kind="contaminant_limit", criterion="Macroscopic impurities >2 mm, each material", analyte="organic matter OR glass OR stones OR metal OR plastics", operator="<=", value="3", unit="g/kg dry matter", location=f"{CMC12_LOC}, point 3(c)")
add("CMC12_MACRO_SUM_MAX", pathway=CMC12_PATH, cmc="CMC12", kind="contaminant_limit", criterion="Sum of macroscopic impurities >2 mm", analyte="sum of organic matter, glass, stones, metal and plastics", operator="<=", value="5", unit="g/kg dry matter", location=f"{CMC12_LOC}, point 3(d)")
add("CMC12_LINE_SEPARATION", pathway=CMC12_PATH, cmc="CMC12", kind="process_control", criterion="Separated production lines", location=f"{CMC12_LOC}, point 7", conditions="Lines for allowed CMC12 inputs must be clearly separated from lines for other inputs.")
add("CMC12_PATHOGEN_SALMONELLA", pathway=CMC12_PATH, cmc="CMC12", kind="conditional_pathogen_limit", criterion="Salmonella spp. sampling plan", analyte="Salmonella spp.", operator="absence", value="0", unit="in 25 g or 25 ml", secondary="5", secondary_unit="samples (n)", tertiary="0", tertiary_unit="positive samples allowed (c)", location=f"{CMC12_LOC}, point 8", conditions="Fallback CMC12 requirement applies only where the applicable PFC in Annex I has no Salmonella criterion; check whether the specified hygienisation exception applies.")
add("CMC12_PATHOGEN_ECOLI", pathway=CMC12_PATH, cmc="CMC12", kind="conditional_pathogen_limit", criterion="E. coli or enterococci sampling plan", analyte="E. coli or enterococci", operator="<=", value="1000", unit="CFU/g or CFU/ml", secondary="5", secondary_unit="samples (n)", tertiary="5", tertiary_unit="c (m=0)", location=f"{CMC12_LOC}, point 8", conditions="Fallback CMC12 requirement applies only where the applicable PFC in Annex I has no matching criterion; check whether the specified hygienisation exception applies.")
add("CMC12_MUNICIPAL_PAHS_MAX", pathway=CMC12_PATH, cmc="CMC12", kind="contaminant_limit", criterion="PAH16 for municipal-wastewater-derived salts", analyte="sum of 16 specified PAHs", operator="<=", value="6", unit="mg/kg dry matter", location=f"{CMC12_LOC}, point 11", conditions="Applies to salts obtained from input material in point 1(a) and their derivatives; it is not a universal extra threshold for every CMC12 feed source.")
add("CMC12_AL_FE_SUM_MAX", pathway=CMC12_PATH, cmc="CMC12", kind="contaminant_limit", criterion="Sum of aluminium and iron", analyte="Al + Fe", operator="<=", value="10", unit="% of dry matter", location=f"{CMC12_LOC}, point 12")
add("CMC12_DM_METHOD", pathway=CMC12_PATH, cmc="CMC12", kind="test_method", criterion="Dry-matter determination for specified limits", location=f"{CMC12_LOC}, point 14", conditions="For points 3, 11 and 12, measure dry matter by vacuum drying at 40 degC until constant mass to avoid loss of crystal-bound water.")

PFC1C = "PFC 1(C)(I)(a); solid inorganic macronutrient fertiliser, where classification is verified"
PFC1C_LOC = "Annex I, Part II, PFC 1(C)(I)(a)"
add("PFC1C_STRAIGHT_P_ONLY_MIN", pathway=f"{PFC1C}; only one declared nutrient", pfc="PFC 1(C)(I)(a)(i)", kind="minimum_nutrient_content", criterion="Minimum P2O5 where it is the only declared macronutrient", analyte="P2O5", operator=">=", value="12", unit="% by mass of product", location=f"{PFC1C_LOC}, point 2(b)", notes="Not applicable if the final product is classified as a compound fertilizer or declares other nutrients.")
for analyte, value, unit in (("total nitrogen (N)", "3", "% by mass of product"), ("total phosphorus pentoxide (P2O5)", "3", "% by mass of product"), ("total potassium oxide (K2O)", "3", "% by mass of product"), ("total magnesium oxide (MgO)", "1.5", "% by mass of product"), ("total calcium oxide (CaO)", "1.5", "% by mass of product"), ("total sulphur trioxide (SO3)", "1.5", "% by mass of product"), ("total sodium oxide (Na2O)", "1", "% by mass of product")):
    key = analyte.split("(")[0].strip().upper().replace(" ", "_")
    add(f"PFC1C_COMPOUND_{key}_MIN", pathway=f"{PFC1C}; compound product", pfc="PFC 1(C)(I)(a)(ii)", kind="minimum_declared_macronutrient", criterion=f"{analyte} threshold when declared in a compound product", analyte=analyte, operator=">=", value=value, unit=unit, location=f"{PFC1C_LOC}, point 2")
add("PFC1C_COMPOUND_NA2O_MAX", pathway=f"{PFC1C}; compound product", pfc="PFC 1(C)(I)(a)(ii)", kind="maximum_declared_macronutrient", criterion="Maximum total sodium oxide", analyte="Na2O", operator="<=", value="40", unit="% by mass of product", location=f"{PFC1C_LOC}, point 2")
add("PFC1C_COMPOUND_SUM_MIN", pathway=f"{PFC1C}; compound product", pfc="PFC 1(C)(I)(a)(ii)", kind="minimum_declared_macronutrient_sum", criterion="Sum of all declared macronutrient contents", operator=">=", value="18", unit="% by mass of product", location=f"{PFC1C_LOC}, point 2")

RVO_VERSION = "RVO guidance checked 2026-03-12; Annex Aa update dated 2026-02-10"
RVO_APPLICABILITY = "Dutch national route only. Requirements are summarized from RVO guidance; confirm the current binding Annex Aa entry for every input/product. No route eligibility is assigned to GreenHub roadside grass or its digestate."
add("NL_RVO_ANNEX_AA_GATE", source=SOURCE_RVO, jurisdiction="Netherlands", version=RVO_VERSION, effective="2026-02-10", pathway="Dutch national manure/fertiliser route; waste and residue materials", kind="eligibility_gate", criterion="Material must be included in current Annex Aa", location="RVO, Afval- en reststoffen als mest gebruiken, lines 17-30; Annex Aa, Uitvoeringsregeling Meststoffenwet", status="official_government_guidance", applicability=RVO_APPLICABILITY, conditions="Waste and residual substances may be used as fertiliser only where listed in Annex Aa; the RVO page states the Annex was amended 10 February 2026.", notes="The RVO summary page does not establish that roadside grass or GreenHub-specific digestate is listed. Verify exact Annex Aa entry and legal classification.")
add("NL_RVO_PLANT_DIGESTATE_CAT2", source=SOURCE_RVO, jurisdiction="Netherlands", version=RVO_VERSION, effective="2026-02-10", pathway="Dutch national route; plant-only digestate, Annex Aa Part IV Category 2", kind="eligibility_gate", criterion="Plant-only digestate input definition", location="RVO, Afval- en reststoffen als mest gebruiken, Annex Aa Part IV Categories 2-4, lines 38-42", status="official_government_guidance", applicability=RVO_APPLICABILITY, conditions="Category 2 is digestate from plant-based co-digestion materials in Part IV Category 1, A through G1, with no animal manure.")
add("NL_RVO_PLANT_DIGESTATE_THIN_CAT3", source=SOURCE_RVO, jurisdiction="Netherlands", version=RVO_VERSION, effective="2026-02-10", pathway="Dutch national route; thin digestate fraction, Annex Aa Part IV Category 3", kind="product_form_gate", criterion="Thin fraction definition", location="RVO, Afval- en reststoffen als mest gebruiken, Annex Aa Part IV Category 3, lines 40-42", status="official_government_guidance", applicability=RVO_APPLICABILITY, conditions="Category 3 is the pumpable thin fraction separated from eligible plant-only digestate; no animal manure is used.")
add("NL_RVO_PLANT_DIGESTATE_THICK_CAT4", source=SOURCE_RVO, jurisdiction="Netherlands", version=RVO_VERSION, effective="2026-02-10", pathway="Dutch national route; thick digestate fraction, Annex Aa Part IV Category 4", kind="product_form_gate", criterion="Thick fraction definition", location="RVO, Afval- en reststoffen als mest gebruiken, Annex Aa Part IV Category 4, lines 40-42", status="official_government_guidance", applicability=RVO_APPLICABILITY, conditions="Category 4 is the non-pumpable thick fraction separated from eligible plant-only digestate; no animal manure is used.")
add("NL_RVO_ADMISSION_PROPOSAL", source=SOURCE_RVO, jurisdiction="Netherlands", version=RVO_VERSION, effective="2026-02-10", pathway="Dutch national route; adding new waste/residue to Annex Aa", kind="market_access_pathway", criterion="Evidence required for new Annex Aa entry", location="RVO, Afval- en reststoffen als mest gebruiken, lines 45-73", status="official_government_guidance", applicability=RVO_APPLICABILITY, conditions="RVO requests evidence that the material can be used as fertiliser and is valuable to agriculture; CDM advises and the minister decides. Additions are generally made on 1 January and 1 July.", notes="This is a procedural description, not approval or evidence that the GreenHub feed/residue qualifies.")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_once(path: Path, row: dict[str, str], key: str) -> bool:
    fields, rows = read_csv(path)
    matches = [item for item in rows if item.get(key) == row.get(key)]
    if matches:
        # Source-register entries may already carry richer curated descriptions
        # than this generator. Treat the persistent ID plus URL as identity and
        # preserve the existing descriptive metadata instead of overwriting it.
        if len(matches) != 1 or ("url" in fields and matches[0].get("url", "") != row.get("url", "")):
            raise ValueError(f"Conflicting {key}={row.get(key)!r} in {path}")
        return False
    rows.append({field: row.get(field, "") for field in fields})
    write_csv(path, fields, rows)
    return True


def append_global_source(dataset_path: str, source_id: str, source_title: str, authors: str, year: str, stable_id: str, url: str, source_type: str, notes: str) -> None:
    path = AUDIT / "global_source_register.csv"
    fields, rows = read_csv(path)
    matches = [row for row in rows if row.get("dataset_path") == dataset_path and row.get("source_id") == source_id]
    new = {"dataset_path": dataset_path, "dataset_group": "Digestate_and_Separation", "source_id": source_id, "source_title": source_title, "authors": authors, "year": year, "doi_or_stable_id": stable_id, "url": url, "source_type": source_type, "notes": notes}
    if matches:
        # Preserve the existing source annotation if it points to the same
        # authoritative URL; do not reject harmless wording differences.
        if len(matches) != 1 or matches[0].get("url", "") != url:
            raise ValueError(f"Conflicting global source link {source_id}")
        return
    rows.append({field: new.get(field, "") for field in fields})
    write_csv(path, fields, rows)


def sync_local_metadata(numeric_row_count: int) -> None:
    local_source = PACKAGE / "source_register.csv"
    source_fields, _ = read_csv(local_source)
    source_entries = [
        {
            "source_id": SOURCE_EU,
            "source_title": "Regulation (EU) 2019/1009 on EU fertilising products, consolidated reference text of 1 July 2026",
            "authors": "European Parliament and Council of the European Union; amendments and corrigenda listed in the consolidated text",
            "year": "2019 (consolidated 2026-07-01)",
            "source_type": "official EU regulation; consolidated EUR-Lex documentation text",
            "doi_or_stable_id": "CELEX:32019R1009; ELI consolidated version 2026-07-01",
            "url": EU_URL,
            "materials": "Digestate CMC4/CMC5, precipitated phosphate salts CMC12, organic fertiliser PFC1(A), inorganic macronutrient fertiliser PFC1(C)",
            "data_used": "Annex II CMC4/CMC5/CMC12 and Annex I PFC1(A)/PFC1(C) requirements, transcribed as screening gates only",
            "quality_notes": "Official regulatory requirements, not measured or literature evidence. Consolidated text is documentation only; authentic amending acts govern. Product/feedstock pathway classification and conformity assessment remain project-specific. No runtime activation or revenue inference.",
        },
        {
            "source_id": SOURCE_NL,
            "source_title": "Artificial fertilisers and biostimulants: market access guidance",
            "authors": "Government of the Netherlands, Business.gov.nl",
            "year": "current page accessed 2026",
            "source_type": "official government guidance",
            "doi_or_stable_id": "Business.gov.nl artificial fertilisers and biostimulants guidance",
            "url": NL_URL,
            "materials": "Fertilisers made from waste and residues in the Netherlands",
            "data_used": "Description of special admission through RVO and a positive list under the Dutch Fertilisers Act Implementation Decree",
            "quality_notes": "Official process guidance, not a numerical product-quality specification or project approval. Route applicability and current admission requirements require confirmation with RVO.",
        },
        {
            "source_id": SOURCE_RVO,
            "source_title": "Afval- en reststoffen als mest gebruiken; current Annex Aa and digestate-product categories",
            "authors": "Rijksdienst voor Ondernemend Nederland (RVO)",
            "year": "2026; page checked 2026-03-12; Annex Aa updated 2026-02-10",
            "source_type": "official Dutch government guidance",
            "doi_or_stable_id": "RVO page; references Annex Aa, Uitvoeringsregeling Meststoffenwet",
            "url": RVO_URL,
            "materials": "Dutch waste/residue fertilizer route; plant-only digestate and separated fractions",
            "data_used": "Annex Aa listing gate; Part IV categories 2-4; procedure for proposing new entries",
            "quality_notes": "Procedural/category guidance only. Does not provide project-specific roadside-grass listing, fertilizer assays, or approval.",
        },
    ]
    for source in source_entries:
        append_once(local_source, source, "source_id")

    manifest_path = PACKAGE / "dataset_manifest.csv"
    manifest_fields, manifest_rows = read_csv(manifest_path)
    row = {
        "filename": FILENAME,
        "purpose": "EU digestate, recovered-phosphate and fertilizer-category screening plus Dutch Annex Aa route; reference-only legal data.",
        "row_count": str(len(ROWS)),
        "populated_numeric_rows": str(numeric_row_count),
        "missing_rows": "0",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "schema": "; ".join(FIELDS),
    }
    existing = next((item for item in manifest_rows if item.get("filename") == FILENAME), None)
    if existing:
        for field in manifest_fields:
            existing[field] = row.get(field, "")
    else:
        manifest_rows.append({field: row.get(field, "") for field in manifest_fields})
    for item in manifest_rows:
        if item.get("filename") == "source_register.csv":
            item["row_count"] = str(len(read_csv(local_source)[1]))
        if item.get("filename") == "assumption_and_missing_data_register.csv":
            item["row_count"] = str(len(read_csv(PACKAGE / "assumption_and_missing_data_register.csv")[1]))
        if item.get("filename") == "dataset_manifest.csv":
            item["row_count"] = str(sum(1 for record in manifest_rows if record.get("filename") != "dataset_manifest.csv"))
    write_csv(manifest_path, manifest_fields, manifest_rows)


def sync_global_metadata(numeric_row_count: int) -> None:
    manifest_path = AUDIT / "global_dataset_manifest.csv"
    manifest_fields, manifest_rows = read_csv(manifest_path)
    manifest_row = {
        "dataset_path": DATASET,
        "category": "Resource recovery",
        "subgroup": "Digestate_and_Separation",
        "filename": FILENAME,
        "row_count_observed": str(len(ROWS)),
        "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "official_regulatory_requirement;official_government_guidance",
        "detected_readiness": "D3",
        "notes": "Reference-only CMC4/5/12, PFC1(A)/1(C) and Dutch Annex Aa screening. Feedstock eligibility, final classification, assays and sale specifications remain unverified.",
    }
    found = next((row for row in manifest_rows if row.get("dataset_path") == DATASET), None)
    if found:
        found.update(manifest_row)
        write_csv(manifest_path, manifest_fields, manifest_rows)
    else:
        manifest_rows.append({field: manifest_row.get(field, "") for field in manifest_fields})
        write_csv(manifest_path, manifest_fields, manifest_rows)

    readiness_path = AUDIT / "global_dataset_readiness.csv"
    readiness_fields, readiness_rows = read_csv(readiness_path)
    readiness_row = {
        "dataset_path": DATASET,
        "category": "Resource recovery",
        "subgroup": "Digestate_and_Separation",
        "readiness": "D3",
        "duplicate_ids": "0",
        "duplicate_rows": "0",
        "numeric_rows": str(numeric_row_count),
        "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0",
        "unit_conflicts": "0",
        "basis_conflicts": "0",
        "cross_reference_issues": "0",
        "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0",
        "notes": "Official EU CMC4/5/12 and PFC1(A)/1(C) plus Dutch Annex Aa screening; no project classification, input listing, assays, national admission, buyer acceptance or runtime link.",
    }
    found = next((row for row in readiness_rows if row.get("dataset_path") == DATASET), None)
    if found:
        found.update(readiness_row)
        write_csv(readiness_path, readiness_fields, readiness_rows)
    else:
        readiness_rows.append({field: readiness_row.get(field, "") for field in readiness_fields})
        write_csv(readiness_path, readiness_fields, readiness_rows)

    sources = [
        (SOURCE_EU, "Regulation (EU) 2019/1009, consolidated reference text 2026-07-01", "European Parliament and Council of the European Union", "2019 (consolidated 2026)", "CELEX:32019R1009; ELI 2026-07-01", EU_URL, "official EU regulation", "CMC4/5/12 and PFC1(A)/1(C) requirements; classifications and applicability remain unselected."),
        (SOURCE_NL, "Artificial fertilisers and biostimulants: market access guidance", "Government of the Netherlands, Business.gov.nl", "2026", "Business.gov.nl guidance page", NL_URL, "official government guidance", "National special admission pathway for new fertilisers from waste/residues; process guidance only, no numeric limits or project approval."),
        (SOURCE_RVO, "Afval- en reststoffen als mest gebruiken", "Rijksdienst voor Ondernemend Nederland (RVO)", "2026; checked 2026-03-12", "RVO page; Annex Aa update 2026-02-10", RVO_URL, "official government guidance", "Annex Aa listing gate and national digestate categories 2-4; does not establish GreenHub input/product eligibility."),
    ]
    for source_id, title, authors, year, stable_id, url, source_type, notes in sources:
        append_global_source(DATASET, source_id, title, authors, year, stable_id, url, source_type, notes)

    variable_path = AUDIT / "global_variable_dictionary.csv"
    variable_fields, variable_rows = read_csv(variable_path)
    present = {(r.get("dataset_path"), r.get("row_id"), r.get("numeric_column")) for r in variable_rows}
    for row in ROWS:
        for value_col, unit_col in (("value", "unit"), ("value_max", "unit_max"), ("secondary_value", "secondary_unit"), ("tertiary_value", "tertiary_unit")):
            if not row[value_col]:
                continue
            key = (DATASET, row["record_id"], value_col)
            if key in present:
                continue
            variable_rows.append({
                "dataset_path": DATASET,
                "dataset_group": "Digestate_and_Separation",
                "row_id": row["record_id"],
                "python_variable": "",
                "parameter_name": row["criterion"],
                "numeric_column": value_col,
                "original_value": row[value_col],
                "original_unit": row[unit_col],
                "normalized_si_value": row[value_col],
                "normalized_si_unit": row[unit_col],
                "basis": row["condition_text"] or row["pathway"],
                "status_original": row["data_status"],
                "status_standardized": row["data_status"],
                "source_id": row["source_id"],
                "source_title": (
                    "Regulation (EU) 2019/1009, consolidated 2026-07-01"
                    if row["source_id"] == SOURCE_EU
                    else "RVO, Afval- en reststoffen als mest gebruiken"
                    if row["source_id"] == SOURCE_RVO
                    else "Business.gov.nl, Artificial fertilisers and biostimulants"
                ),
                "exact_location": row["legal_location"],
            })
            present.add(key)
    write_csv(variable_path, variable_fields, variable_rows)

    unit_path = AUDIT / "global_unit_registry.csv"
    unit_fields, unit_rows = read_csv(unit_path)
    unit_keys = {(r.get("dataset_path"), r.get("column_name"), r.get("unit_text"), r.get("status_standardized")) for r in unit_rows}
    for row in ROWS:
        for value_col, unit_col in (("value", "unit"), ("value_max", "unit_max"), ("secondary_value", "secondary_unit"), ("tertiary_value", "tertiary_unit")):
            if row[value_col] and row[unit_col]:
                key = (DATASET, unit_col, row[unit_col], row["data_status"])
                if key not in unit_keys:
                    unit_rows.append(dict(zip(unit_fields, key)))
                    unit_keys.add(key)
    write_csv(unit_path, unit_fields, unit_rows)

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["dataset_count"] = len(manifest_rows)
    counts: dict[str, int] = {}
    for item in readiness_rows:
        key = item.get("readiness", "")
        counts[key] = counts.get(key, 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_gap_register() -> None:
    for path in (
        ROOT / "docs" / "missing_data_gap_analysis.csv",
        DATA / "Pre-treatment" / "Feedstock" / "expanded_process_data_register.csv",
        DATA / "Pre-treatment" / "Feedstock" / "complete_missing_data_with_traceability.csv",
    ):
        fields, rows = read_csv(path)
        row = next(item for item in rows if item.get("gap_id") == "NU-002")
        row["status"] = "partially_implemented"
        row["suggested_source_or_estimation"] = f"{EU_URL}; {NL_URL}; {RVO_URL}; current Annex Aa and product-specific accredited laboratory analyses"
        row["data_required_and_units"] = "Choose applicable EU PFC/CMC or Dutch national admission route; measure N/P/K and dry-matter basis; product form/moisture; metals/PAH16; macroscopic plastics/glass/metal; pathogen panel; stability; buyer-grade and use-specific requirements"
        row["effect_on_model_outputs"] = "EU CMC12/PFC1(C) and Dutch Annex Aa screening are staged, but project input listing, product category, measured quality, route approval, sale price and fertilizer substitution remain unresolved; no revenue or LCA credit is activated."
        row["repository_trace"] = f"Greenhub/data/Resource recovery/Digestate_and_Separation/{FILENAME}; exact route and project product assays still missing"
        _write_fields = fields
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=_write_fields, lineterminator="\n", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    if len({row["record_id"] for row in ROWS}) != len(ROWS):
        raise ValueError("Duplicate regulation reference record IDs")
    path = PACKAGE / FILENAME
    existing_fields, existing = ([], [])
    if path.exists():
        existing_fields, existing = read_csv(path)
        if existing_fields != FIELDS:
            raise ValueError(f"Unexpected schema for {path}")
        current = {row["record_id"]: row for row in existing}
        for row in ROWS:
            if row["record_id"] in current and current[row["record_id"]] != row:
                raise ValueError(f"Conflicting requirement record {row['record_id']}")
        missing = [row for row in ROWS if row["record_id"] not in current]
        if missing:
            existing.extend(missing)
            write_csv(path, FIELDS, existing)
    else:
        write_csv(path, FIELDS, ROWS)
        existing = ROWS.copy()

    source_rows = [
        {
            "source_id": SOURCE_EU,
            "source_title": "Regulation (EU) 2019/1009 on EU fertilising products, consolidated reference text of 1 July 2026",
            "authors": "European Parliament and Council of the European Union",
            "year": "2019 (consolidated 2026-07-01)",
            "source_type": "official EU regulation; consolidated EUR-Lex documentation text",
            "doi_or_stable_id": "CELEX:32019R1009; ELI consolidated version 2026-07-01",
            "url": EU_URL,
            "materials": "Digestate CMC4/CMC5, precipitated phosphate salts CMC12, organic fertiliser PFC1(A), inorganic macronutrient fertiliser PFC1(C)",
            "data_used": "Annex II CMC4/CMC5/CMC12 and Annex I PFC1(A)/PFC1(C) screening requirements",
            "quality_notes": "Regulatory requirements; not measured/literature data. Product-route and roadside-feedstock applicability unverified. No runtime activation or revenue inference.",
        },
        {
            "source_id": SOURCE_NL,
            "source_title": "Artificial fertilisers and biostimulants: market access guidance",
            "authors": "Government of the Netherlands, Business.gov.nl",
            "year": "2026",
            "source_type": "official government guidance",
            "doi_or_stable_id": "Business.gov.nl guidance page",
            "url": NL_URL,
            "materials": "Dutch admission pathway for fertilisers from waste and residues",
            "data_used": "RVO special admission and positive-list pathway summary",
            "quality_notes": "Process guidance only. No numerical product-quality limit or project approval is supplied.",
        },
        {
            "source_id": SOURCE_RVO,
            "source_title": "Afval- en reststoffen als mest gebruiken",
            "authors": "Rijksdienst voor Ondernemend Nederland (RVO)",
            "year": "2026; checked 2026-03-12; Annex Aa updated 2026-02-10",
            "source_type": "official government guidance",
            "doi_or_stable_id": "RVO page; Annex Aa, Uitvoeringsregeling Meststoffenwet",
            "url": RVO_URL,
            "materials": "Waste/residue fertilizer route; plant-only digestate and separated fractions",
            "data_used": "Annex Aa requirement, plant digestate categories 2-4, and route for proposing additions",
            "quality_notes": "Procedural/category information only. No project-specific Annex Aa listing, material approval, numeric composition or fertilizer sale eligibility is inferred.",
        },
    ]
    local_source_path = PACKAGE / "source_register.csv"
    for row in source_rows:
        append_once(local_source_path, row, "source_id")

    missing_path = PACKAGE / "assumption_and_missing_data_register.csv"
    miss_fields, miss_rows = read_csv(missing_path)
    missing_id = "MISS_NU002_PRODUCT_ROUTE_CONFIRMATION"
    if not any(row.get("missing_id") == missing_id for row in miss_rows):
        miss_rows.append({
            "missing_id": missing_id,
            "target_file": FILENAME,
            "python_variable": "phase7_fertilizer_route_and_product_compliance",
            "required_parameter": "Selected legal route/PFC-CMC and laboratory-measured product grade/contaminants/pathogens",
            "reason_missing": "CE route applicability depends on feedstock eligibility and final product category; Dutch RVO admission and customer acceptance are project-specific. No product assays or approval decision are present.",
            "recommended_measurement_or_source": "Select intended route and off-taker, confirm input legal status with RVO/competent authority, then obtain accredited product and residual-stream analyses at the required wet/dry and chemical-speciation basis.",
            "priority": "high",
        })
        write_csv(missing_path, miss_fields, miss_rows)

    numeric_rows = sum(1 for row in ROWS if any(row[column] for column in ("value", "value_max", "secondary_value", "tertiary_value")))
    local_manifest_path = PACKAGE / "dataset_manifest.csv"
    local_fields, local_rows = read_csv(local_manifest_path)
    if not any(row.get("filename") == FILENAME for row in local_rows):
        local_rows.append({
            "filename": FILENAME,
            "purpose": "EU digestate, recovered-phosphate and fertilizer category screening plus Dutch Annex Aa route; reference-only legal data.",
            "row_count": str(len(ROWS)),
            "populated_numeric_rows": str(numeric_rows),
            "missing_rows": "0",
            "integration_status": "traceable_reference_only_not_runtime_eligible",
            "schema": "; ".join(FIELDS),
        })
    for row in local_rows:
        if row.get("filename") == FILENAME:
            row["row_count"] = str(len(ROWS))
            row["populated_numeric_rows"] = str(numeric_rows)
        elif row.get("filename") == "source_register.csv":
            row["row_count"] = str(len(read_csv(local_source_path)[1]))
        elif row.get("filename") == "assumption_and_missing_data_register.csv":
            row["row_count"] = str(len(miss_rows))
        elif row.get("filename") == "dataset_manifest.csv":
            row["row_count"] = str(sum(1 for item in local_rows if item.get("filename") != "dataset_manifest.csv"))
    write_csv(local_manifest_path, local_fields, local_rows)

    readme_path = PACKAGE / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    section = (
        "## Fertiliser product-route reference (Phase 7)\n"
        + f"`{FILENAME}` stages CMC4/CMC5 digestate, CMC12 precipitated phosphate salts, PFC 1(A) organic fertiliser, PFC 1(C) inorganic fertiliser, and the current Dutch Annex Aa categories for plant-only digestate/fractions. These are screening gates only. The final product route, material listing, roadside-grass legal status, conformity assessment, assays and buyer specification are unconfirmed. Struvite may only be assessed against a relevant CMC/PFC route after source-material and product classification; PFC 1(A) limits do not apply to it by default. Regulatory criteria are not measured product values or runtime parameters.\n"
    )
    heading = "## Fertiliser product-route reference (Phase 7)"
    if heading in readme:
        readme = readme[:readme.index(heading)].rstrip() + "\n\n"
    readme_path.write_text(readme + section, encoding="utf-8")

    update_gap_register()
    sync_local_metadata(numeric_rows)
    sync_global_metadata(numeric_rows)

    sidecar = {
        "dataset_id": "urn:greenhub:dataset:phase7:eu-digestate-fertiliser-regulatory-requirements:2026-07-01:v1.1",
        "dataset_version": "1.1.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "retrieval_date": RETRIEVED,
        "source_ids": [SOURCE_EU, SOURCE_NL, SOURCE_RVO],
        "access_protocol": "UTF-8 CSV/JSON and source links served over HTTPS",
        "evidence_class": "official regulation and official national government guidance; not A/B measured/literature data",
        "license_or_rights": "No CC license is asserted. The consolidated EU document says it is a documentation tool and authentic acts have legal effect. Dutch government pages are linked as guidance; their reuse/license terms have not been independently established.",
        "processing": "Thresholds and clauses were transcribed from the 2026-07-01 consolidated EU text (CMC4/CMC5/CMC12; PFC1(A)/PFC1(C)) and RVO guidance checked 2026-03-12. Requirements remain route-conditional. No project assays or conformity result is derived.",
        "runtime_policy": "Reference-only. No parameter registry, service, default, process chemistry, fertilizer revenue or LCA credit is connected.",
        "limitations": [
            "A CE-marked EU route is not the only possible Dutch market route; national admission for waste/residue fertilisers is separate.",
            "Roadside grass is not presumed eligible as CMC4 fresh-crop digestate because the legal wording requires plants or plant parts grown for biogas production.",
            "CMC5 input eligibility is not declared for roadside mowings, collected litter/sand, ensiling, co-feeds or project-specific pre-processing.",
            "PFC 1(A) is only one product-function category; struvite and recovered mineral nutrient salts may require other CMC/PFC rules not staged here.",
            "CMC12/PFC1(C) are screening pathways for candidate precipitated phosphate salts, not proof the project's material input, chemical processing chain or final salt qualifies.",
            "RVO guidance requires waste/residue materials to be listed in current Annex Aa; exact inclusion of roadside grass, GreenHub digestate and separated fractions has not been verified.",
            "No actual N/P/K, moisture, metals, PAH16, macroscopic impurity, pathogen, stability, PFAS, pesticide or buyer-grade measurement is provided.",
            "No fertilizer sale price, substitution credit, regulatory approval or runtime compliance claim is inferred.",
        ],
        "fair_metadata": {
            "findable": "Stable local URN, source IDs, EUR-Lex CELEX/ELI, Business.gov.nl and RVO source links.",
            "accessible": "Machine-readable UTF-8 CSV and JSON metadata; source documents linked over HTTPS.",
            "interoperable": "Requirement rows provide Phase 7, jurisdiction, version, CMC/PFC, threshold, units, legal location, pathway and applicability.",
            "reusable": "Applicability, route choice, measurement gaps, rights caveat and no-runtime policy are recorded.",
        },
    }
    (PACKAGE / f"{FILENAME}.source.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": FILENAME, "records": len(ROWS), "numeric_requirement_rows": numeric_rows, "source_ids": [SOURCE_EU, SOURCE_NL, SOURCE_RVO], "runtime_activation": False}, indent=2))


if __name__ == "__main__":
    main()
