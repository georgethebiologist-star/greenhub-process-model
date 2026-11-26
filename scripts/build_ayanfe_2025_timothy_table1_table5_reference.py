"""Rebuild the traceable extract of Ayanfe et al. (2025), Tables 1 and 5."""

from __future__ import annotations

import csv
from pathlib import Path

SOURCE_ID = "S14_AYANFE_2025_GFS12722"
OUTPUT = (Path(__file__).resolve().parents[1] / "Greenhub" / "data" / "Pre-treatment" / "Mechanical" / "timothy_feed_and_press_liquid_ayanfe_2025_tables1_5_reference.csv")
FIELDS = ["record_id", "source_id", "table_number", "experiment_id", "harvest_stage", "feed_or_liquid_state", "press_type", "condition_id", "response_parameter", "reported_value", "reported_unit", "basis", "source_location", "source_statistic", "replicate_n", "quality_class", "activation_state", "transferability_class", "notes"]

FEED_CONDITIONS = [
    ("EXP1_PG_INTACT", "Exp. 1", "primary growth", "intact"),
    ("EXP1_PG_PULP", "Exp. 1", "primary growth", "pulp"),
    ("EXP2_REG_INTACT", "Exp. 2", "first regrowth", "intact"),
    ("EXP2_REG_PULP", "Exp. 2", "first regrowth", "pulp"),
    ("EXP2_REG_WILTED", "Exp. 2", "first regrowth", "wilted"),
]
TABLE1 = [
    ("dry_matter", "g/kg fresh matter", "fresh matter", ["276", "249", "195", "230", "301"]),
    ("buffering_capacity", "g lactic acid/100 g DM", "dry matter", ["4.89", "3.90", "4.73", "4.31", "5.09"]),
    ("fermentation_coefficient", "dimensionless", "source-defined coefficient", ["55", "58", "33", "35", "41"]),
    ("ash", "g/kg DM", "dry matter", ["70", "66", "90", "83", "91"]),
    ("crude_protein", "g/kg DM", "dry matter; crude protein", ["146", "145", "130", "130", "132"]),
    ("water_soluble_carbohydrates", "g/kg DM", "dry matter", ["169", "160", "80", "63", "69"]),
    ("nitrate_nitrogen", "g/kg DM", "dry matter; nitrate-N", ["0.011", "0.006", "0.144", "0.078", "0.076"]),
    ("neutral_detergent_fibre", "g/kg DM", "dry matter", ["492", "549", "596", "597", "578"]),
    ("in_vitro_organic_matter_digestibility", "g/g organic matter", "organic matter", ["0.837", "0.834", "0.753", "0.735", "0.747"]),
]
PRESS_CONDITIONS = [
    ("EXP1_PG_INTACT_PSS", "Exp. 1", "primary growth", "intact", "pilot single-screw press"),
    ("EXP2_REG_INTACT_PSS", "Exp. 2", "first regrowth", "intact", "pilot single-screw press"),
    ("EXP2_REG_INTACT_DSP", "Exp. 2", "first regrowth", "intact", "double-screw press"),
    ("EXP2_REG_PULP_DSP", "Exp. 2", "first regrowth", "pulp", "double-screw press"),
    ("EXP2_REG_WILTED_DSP", "Exp. 2", "first regrowth", "wilted", "double-screw press"),
]
TABLE5 = [
    ("liquid_yield", "g liquid/g fresh sample", "fresh-sample denominator as printed; added-water inclusion unresolved", ["0.301", "0.244", "0.607", "0.570", "0.393"]),
    ("liquid_dry_matter", "g/kg", "liquid fraction; table reports g/kg without an explicit denominator phrase", ["158", "47", "81", "88", "136"]),
    ("liquid_pH", "pH", "liquid fraction", ["5.78", "5.68", "5.60", "5.66", "5.57"]),
    ("liquid_ash", "g/kg DM", "liquid dry matter", ["124", "254", "168", "169", "197"]),
    ("liquid_crude_protein", "g/kg DM", "liquid dry matter; crude protein", ["129", "119", "139", "155", "121"]),
    ("liquid_water_soluble_carbohydrates", "g/kg DM", "liquid dry matter", ["73.8", "12.9", "33.7", "31.5", "30.0"]),
    ("liquid_lactic_acid", "g/kg DM", "liquid dry matter", ["0", "0", "0.12", "0.11", "0.07"]),
    ("liquid_acetic_acid", "g/kg DM", "liquid dry matter", ["0.90", "0.50", "0.74", "0.80", "0.59"]),
    ("captured_dry_matter_fraction", "g/g original material", "source-reported DM captured in liquid; basis preserved", ["0.172", "0.058", "0.251", "0.217", "0.177"]),
    ("captured_ash_fraction", "g/g original material", "source-reported ash captured in liquid; basis preserved", ["0.304", "0.164", "0.467", "0.440", "0.383"]),
    ("captured_crude_protein_fraction", "g/g original material", "source-reported CP captured in liquid; basis preserved", ["0.152", "0.054", "0.268", "0.259", "0.163"]),
    ("liquid_calcium", "g/kg DM", "liquid dry matter", ["5.1", "16.5", "8.8", "7.4", "8.9"]),
    ("liquid_phosphorus", "g/kg DM", "liquid dry matter", ["3.6", "4.0", "5.9", "6.3", "6.5"]),
    ("liquid_potassium", "g/kg DM", "liquid dry matter", ["51", "90", "82", "82", "89"]),
    ("liquid_magnesium", "g/kg DM", "liquid dry matter", ["2.6", "6.7", "4.7", "4.3", "4.9"]),
    ("liquid_sodium", "g/kg DM", "liquid dry matter", ["0.1", "0.3", "0.1", "0.1", "0.1"]),
    ("liquid_sulphur", "g/kg DM", "liquid dry matter", ["2.1", "3.1", "2.9", "2.9", "2.8"]),
    ("liquid_iron", "mg/kg DM", "liquid dry matter", ["200", "860", "149", "171", "125"]),
    ("liquid_copper", "mg/kg DM", "liquid dry matter", ["8.5", "28.0", "14.9", "17.1", "15.5"]),
    ("liquid_manganese", "mg/kg DM", "liquid dry matter", ["34", "95", "55", "53", "59"]),
    ("liquid_zinc", "mg/kg DM", "liquid dry matter", ["31", "45", "38", "39", "35"]),
]


def build_rows() -> list[dict[str, str]]:
    rows = []
    for metric, unit, basis, values in TABLE1:
        for i, (condition, experiment, growth, biomass) in enumerate(FEED_CONDITIONS):
            rows.append({
                "record_id": f"AY25-T1-{condition}-{metric.upper()}", "source_id": SOURCE_ID,
                "table_number": "1", "experiment_id": experiment, "harvest_stage": growth,
                "feed_or_liquid_state": f"{biomass} feed before ensiling", "press_type": "not applicable; feed characterization",
                "condition_id": condition, "response_parameter": metric, "reported_value": values[i],
                "reported_unit": unit, "basis": basis, "source_location": "Table 1",
                "source_statistic": "table-reported value; no row-level dispersion transcribed", "replicate_n": "",
                "quality_class": "B", "activation_state": "reference_only",
                "transferability_class": "cultivated Finnish timothy-grass comparator",
                "notes": "Not roadside grass; no transfer to GreenHub defaults or runtime parameters.",
            })
    for metric, unit, basis, values in TABLE5:
        for i, (condition, experiment, growth, biomass, press_type) in enumerate(PRESS_CONDITIONS):
            notes = "Liquid-yield and capture bases retained as printed; no conversion or balance closure inferred."
            if condition == "EXP1_PG_INTACT_PSS":
                notes += " Source reports 0.4 L water/kg fresh grass added during first and second pressing cycles; inclusion in the fresh-sample yield denominator is unresolved."
            rows.append({
                "record_id": f"AY25-T5-{condition}-{metric.upper()}", "source_id": SOURCE_ID,
                "table_number": "5", "experiment_id": experiment, "harvest_stage": growth,
                "feed_or_liquid_state": f"liquid from {biomass} biomass before ensiling", "press_type": press_type,
                "condition_id": condition, "response_parameter": metric, "reported_value": values[i],
                "reported_unit": unit, "basis": basis, "source_location": "Table 5",
                "source_statistic": "table-reported value; no row-level dispersion transcribed", "replicate_n": "",
                "quality_class": "B", "activation_state": "reference_only",
                "transferability_class": "cultivated Finnish timothy-grass comparator",
                "notes": notes + " No GreenHub parameter/default activation.",
            })
    return rows


def main() -> None:
    rows = build_rows()
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} reference records to {OUTPUT}")


if __name__ == "__main__":
    main()
