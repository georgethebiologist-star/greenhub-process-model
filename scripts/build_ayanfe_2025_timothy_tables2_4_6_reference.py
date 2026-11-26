"""Build source-faithful reference extracts for Ayanfe et al. (2025), Tables 2–4 and 6.

The records are published treatment means and descriptive effluent results.
They are reference-only and are never loaded into runtime parameters.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
OUT_DIR = DATA / "storage"
CSV_PATH = OUT_DIR / "timothy_silage_fermentation_effluent_and_press_liquid_ayanfe_2025_tables2_4_6_reference.csv"
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "S14_AYANFE_2025_GFS12722"
DOI = "10.1111/gfs.12722"
URL = "https://doi.org/10.1111/gfs.12722"


def metric(name, unit, basis, values, sem="", p_bt="", p_add="", p_interaction="", letters=None, note=""):
    return {
        "name": name, "unit": unit, "basis": basis, "values": values, "sem": sem,
        "p_biomass_type": p_bt, "p_additive": p_add, "p_interaction": p_interaction,
        "letters": letters or [""] * len(values), "note": note,
    }


TABLES = [
    {
        "table": "2", "experiment": "1", "harvest": "Primary growth", "material_state": "ensiled silage",
        "press_type": "not applicable; silage chemistry before post-ensiling pressing",
        "conditions": [("Intact", "Control"), ("Intact", "LAB"), ("Intact", "FA1"),
                       ("Pulp", "Control"), ("Pulp", "LAB"), ("Pulp", "FA1")],
        "n": 4,
        "replication": "Four silage replicates per treatment; treatment means from the mixed model; table-wide SEM and factor p-values are repeated on each metric row.",
        "metrics": [
            metric("dry_matter", "g/kg", "fresh ensiled material", [268,277,279,244,242,249], 2.2, "<0.001", "0.006", "0.073", ["b","ab","a","c","c","c"]),
            metric("pH", "pH", "ensiled material", [4.05,3.76,3.81,3.74,3.92,3.71], 0.018, "<0.001", "<0.001", "<0.001", ["a","cd","c","cd","b","d"]),
            metric("ammonia_n", "g/kg total N", "ensiled material", [48,34,28,32,33,25], 0.9, "<0.001", "<0.001", "<0.001", ["a","b","cd","bc","b","d"]),
            metric("water_soluble_carbohydrates", "g/kg DM", "dry matter", [50,71,44,24,44,38], 5.8, "<0.001", "0.003", "0.109", ["ab","a","bc","c","bc","bc"]),
            metric("ethanol", "g/kg DM", "dry matter", [31.8,14.7,9.6,43.5,13.3,8.9], 1.12, "0.002", "<0.001", "<0.001", ["b","c","d","a","cd","d"]),
            metric("lactic_acid", "g/kg DM", "dry matter", [66,105,63,97,65,60], 2.6, "0.069", "<0.001", "<0.001", ["b","a","b","a","b","b"]),
            metric("acetic_acid", "g/kg DM", "dry matter", [20.6,25.3,26.8,15.8,47.1,27.0], 1.53, "<0.001", "<0.001", "<0.001", ["bc","b","b","c","a","b"]),
            metric("propionic_acid", "g/kg DM", "dry matter", [0.06,0.10,2.75,0.04,0.04,2.96], 0.048, "0.259", "<0.001", "0.028", ["b","b","a","b","b","a"], "FA1 contains propionic acid; the paper notes its contribution to the FA1 values."),
            metric("butyric_acid", "g/kg DM", "dry matter", [2.46,0.04,0.06,0.05,0.04,0.05], 0.053, "<0.001", "<0.001", "<0.001", ["a","b","b","b","b","b"]),
            metric("total_volatile_fatty_acids", "g/kg DM", "dry matter; source-defined sum", [23.2,25.4,29.5,15.9,47.2,30.0], 1.53, "0.001", "<0.001", "<0.001", ["b","b","b","c","a","b"]),
            metric("total_fermentation_acids", "g/kg DM", "dry matter; total VFA plus lactic acid", [90,131,93,113,112,90], 3.5, "0.786", "<0.001", "<0.001", ["c","a","c","b","b","c"]),
            metric("total_fermentation_products", "g/kg DM", "dry matter; total fermentation acids plus ethanol", [121,146,102,157,126,99], 2.9, "0.109", "<0.001", "<0.001", ["b","a","c","a","b","c"]),
            metric("lactic_to_acetic_acid_ratio", "g/g", "ratio of source-reported DM-basis concentrations", [3.42,4.20,2.36,6.16,1.40,2.23], 0.211, "0.709", "<0.001", "<0.001", ["b","b","c","a","c","c"]),
            metric("fermentation_losses", "g/kg initial DM", "initial dry matter; source-calculated loss", [32,25,23,30,25,22], 2.5, "0.645", "0.008", "0.895"),
            metric("aerobic_stability", "h", "time to 2°C above ambient; observation lasted 172 h", [88,172,172,42,156,172], 10.8, "0.025", "<0.001", "0.112", ["b","a","a","b","a","a"], "Values at the 172 h observation limit are retained as printed; possible censoring is not resolved by the article."),
        ],
    },
    {
        "table": "3", "experiment": "2", "harvest": "First regrowth", "material_state": "ensiled silage",
        "press_type": "not applicable; silage chemistry before post-ensiling pressing",
        "conditions": [(b,a) for b in ("Intact","Pulp","Wilted") for a in ("Control","LAB","FA2")],
        "n": 3,
        "replication": "Three silage replicates per treatment; least-squares means; table-wide SEM and factor p-values are repeated on each metric row.",
        "metrics": [
            metric("dry_matter", "g/kg", "fresh ensiled material", [193,192,199,227,230,233,301,294,299], 3.9, "<0.001", "0.283", "0.696", ["c","c","c","b","b","b","a","a","a"]),
            metric("pH", "pH", "ensiled material", [3.93,3.95,3.95,3.74,3.99,3.82,4.43,4.11,4.58], 0.050, "<0.001", "0.062", "<0.001", ["bc","bc","bc","c","bc","c","a","b","a"]),
            metric("ammonia_n", "g/kg total N", "ensiled material", [62,65,34,52,51,20,51,54,35], 2.7, "<0.001", "<0.001", "0.065", ["ab","a","c","b","b","d","b","ab","c"]),
            metric("ash", "g/kg DM", "dry matter", [95,99,94,89,89,86,94,96,92], 0.8, "<0.001", "<0.001", "0.153", ["abc","a","bc","de","de","e","bc","ab","cd"]),
            metric("crude_protein", "g/kg DM", "dry matter", [134,136,131,136,136,133,131,133,128], 2.0, "0.043", "0.080", "0.965"),
            metric("water_soluble_carbohydrates", "g/kg DM", "dry matter", [25.4,15.6,39.1,6.0,0.2,0.4,1.6,0.6,135.7], 5.76, "<0.001", "<0.001", "<0.001", ["bc","bc","b","c","c","c","c","c","a"]),
            metric("ethanol", "g/kg DM", "dry matter", [7.6,9.1,11.2,8.9,9.8,7.8,7.0,6.9,4.5], 0.55, "<0.001", "0.199", "<0.001", ["bc","abc","a","abc","ab","bc","cd","cd","d"]),
            metric("lactic_acid", "g/kg DM", "dry matter", [89.5,70.7,36.9,91.6,86.3,49.1,44.9,68.7,8.8], 4.46, "<0.001", "<0.001", "0.003", ["ab","abc","d","a","ab","cd","d","bc","e"]),
            metric("acetic_acid", "g/kg DM", "dry matter", [23.0,40.7,17.3,22.8,32.2,20.2,16.9,29.0,7.1], 1.24, "<0.001", "<0.001", "0.001", ["cd","a","d","d","b","d","d","bc","e"]),
            metric("propionic_acid", "g/kg DM", "dry matter", [0.08,0.05,0.05,0.29,0.74,0.06,0.03,0.03,0.08], 0.131, "0.013", "0.161", "0.074", ["b","b","b","ab","a","b","b","b","b"]),
            metric("butyric_acid", "g/kg DM", "dry matter", [0.10,0.08,1.08,0.08,0.04,0.11,0.07,0.03,0.05], 0.231, "0.115", "0.129", "0.145"),
            metric("total_volatile_fatty_acids", "g/kg DM", "dry matter; source-defined sum", [23.2,40.9,18.6,23.1,32.9,20.4,17.0,29.1,7.2], 1.02, "<0.001", "<0.001", "<0.001", ["c","a","cd","c","b","cd","d","b","e"]),
            metric("total_fermentation_acids", "g/kg DM", "dry matter; total VFA plus lactic acid", [113,112,56,115,119,69,62,98,16], 4.6, "<0.001", "<0.001", "0.003", ["a","a","b","a","a","b","b","a","c"]),
            metric("total_fermentation_products", "g/kg DM", "dry matter; total fermentation acids plus ethanol", [120,121,67,124,129,77,69,105,20], 4.7, "<0.001", "<0.001", "0.005", ["ab","ab","c","ab","a","c","c","b","d"]),
            metric("lactic_to_acetic_acid_ratio", "g/g", "ratio of source-reported DM-basis concentrations", [3.96,1.74,2.13,4.02,2.71,2.44,2.66,2.37,1.24], 0.238, "<0.001", "<0.001", "0.010", ["a","bc","bc","a","b","bc","b","bc","c"]),
            metric("fermentation_losses", "g/kg initial DM", "initial dry matter; source-calculated loss", [11.3,13.2,12.7,11.0,12.9,11.0,12.5,16.7,9.7], 0.78, "0.137", "<0.001", "0.007", ["b","ab","b","b","ab","b","b","a","b"]),
            metric("aerobic_stability", "h", "time to 2°C above ambient; observation lasted 244 h", [118,148,136,166,195,236,134,244,117], 20.4, "0.006", "0.022", "0.008", ["bc","abc","abc","abc","ab","ab","abc","a","c"], "Values reaching the 244 h observation length are retained as printed; possible censoring is not resolved by the article."),
        ],
    },
    {
        "table": "4", "experiment": "2", "harvest": "First regrowth", "material_state": "spontaneous silo effluent",
        "press_type": "not mechanically pressed; effluent collected from silos",
        "conditions": [("Intact silage", "Control"), ("Intact silage", "LAB"), ("Intact silage", "FA2")],
        "n": 3,
        "replication": "Effluent originated from three silos per treatment but samples were pooled to one treatment composite; no independent analytical replicate or SEM is reported.",
        "metrics": [
            metric("effluent_yield", "g/g fresh silage", "fresh silage", [0.002,0.003,0.020], note="Descriptive pooled-treatment result."),
            metric("dry_matter", "g/kg", "fresh effluent", [72,58,62]),
            metric("pH", "pH", "effluent", [4.14,4.26,4.16]),
            metric("ammonia_n", "g/kg total N", "effluent", [9.2,10.9,0]),
            metric("ash", "g/kg DM", "dry matter", [250,273,243]),
            metric("crude_protein", "g/kg DM", "dry matter", [190,199,136]),
            metric("water_soluble_carbohydrates", "g/kg DM", "dry matter", [3.0,2.6,22.3]),
            metric("lactic_acid", "g/kg DM", "dry matter", [16.6,14.9,0.7]),
            metric("acetic_acid", "g/kg DM", "dry matter", [2.70,2.40,1.00]),
            metric("butyric_acid", "g/kg DM", "dry matter", [0,0.10,0]),
            metric("calcium", "g/kg DM", "dry matter", [9.7,12.4,11.0]),
            metric("phosphorus", "g/kg DM", "dry matter", [7.3,8.4,7.2]),
            metric("potassium", "g/kg DM", "dry matter", [88,114,105]),
            metric("magnesium", "g/kg DM", "dry matter", [5.4,7.0,6.3]),
            metric("sodium", "g/kg DM", "dry matter", [0.2,0.3,2.7], note="FA2 treatment sodium includes sodium formate contribution."),
            metric("sulphur", "g/kg DM", "dry matter", [3.1,3.7,3.1]),
            metric("iron", "mg/kg DM", "dry matter", [210,220,157]),
            metric("copper", "mg/kg DM", "dry matter", [3.6,5.1,2.4]),
            metric("manganese", "mg/kg DM", "dry matter", [66,55,87]),
            metric("zinc", "mg/kg DM", "dry matter", [56,69,60]),
        ],
    },
    {
        "table": "6", "experiment": "2", "harvest": "First regrowth", "material_state": "liquid pressed from ensiled biomass",
        "press_type": "double-screw press (DSP); frozen, thawed silage",
        "conditions": [(b,a) for b in ("Intact","Pulp","Wilted") for a in ("Control","LAB","FA2")],
        "n": 3,
        "replication": "Three silage replicates per treatment; least-squares means; table-wide SEM and factor p-values are repeated on each metric row.",
        "metrics": [
            metric("liquid_yield", "g/g fresh matter", "fresh ensiled material", [0.702,0.689,0.706,0.627,0.633,0.634,0.553,0.523,0.517], 0.0110, "<0.001", "0.399", "0.252", ["a","ab","a","c","c","bc","d","d","d"]),
            metric("dry_matter", "g/kg", "fresh liquid", [86,77,84,89,85,92,135,124,130], 2.1, "<0.001", "<0.001", "0.426", ["cd","d","cd","c","cd","c","a","b","ab"]),
            metric("pH", "pH", "liquid", [3.89,4.01,3.94,3.74,3.91,3.76,4.41,4.06,4.46], 0.042, "<0.001", "0.210", "<0.001", ["bc","b","bc","c","bc","c","a","b","a"]),
            metric("ammonia_n", "g/kg total N", "liquid", [3.28,3.27,3.87,1.97,2.89,3.73,2.11,2.08,2.44], 0.335, "0.001", "0.014", "0.279", ["abc","abc","a","c","abc","ab","bc","bc","abc"]),
            metric("ash", "g/kg DM", "dry matter", [173,183,183,189,195,179,190,201,197], 4.4, "0.001", "0.067", "0.201", ["c","abc","abc","abc","ab","bc","abc","a","ab"]),
            metric("crude_protein", "g/kg DM", "dry matter", [221,248,193,237,256,182,220,243,198], 4.1, "0.308", "<0.001", "0.006", ["c","ab","de","b","a","e","c","ab","d"]),
            metric("water_soluble_carbohydrates", "g/kg DM", "dry matter", [5.7,3.5,12.2,2.2,3.7,6.1,13.2,6.7,41.4], 1.72, "<0.001", "<0.001", "0.001", ["bcd","d","bc","d","cd","bcd","b","bcd","a"]),
            metric("lactic_acid", "g/kg DM", "dry matter", [29.4,26.0,13.2,35.8,29.8,15.7,14.4,24.1,3.1], 1.30, "<0.001", "<0.001", "<0.001", ["ab","b","c","a","ab","c","c","b","d"]),
            metric("acetic_acid", "g/kg DM", "dry matter", [5.7,11.8,4.6,6.8,10.2,5.8,4.5,8.0,2.0], 0.34, "<0.001", "<0.001", "0.001", ["cd","a","d","bc","a","cd","d","b","e"]),
            metric("propionic_acid", "g/kg DM", "dry matter", [0.038,0,0,0.112,0.278,0,0,0,0], 0.0379, "0.001", "0.026", "0.009", ["b","b","b","ab","a","b","b","b","b"]),
            metric("butyric_acid", "g/kg DM", "dry matter", [0.038,0,0.286,0,0,0,0,0,0], 0.0776, "0.173", "0.289", "0.296"),
            metric("total_volatile_fatty_acids", "g/kg DM", "dry matter; source-defined sum", [5.9,11.8,4.9,7.0,10.5,5.8,4.5,8.0,2.0], 0.28, "<0.001", "<0.001", "0.001", ["cd","a","d","bc","a","cd","d","b","e"]),
            metric("total_fermentation_acids", "g/kg DM", "dry matter; total VFA plus lactic acid", [35.3,37.9,18.1,42.8,40.3,21.5,19.0,32.0,5.1], 1.27, "<0.001", "<0.001", "<0.001", ["bc","abc","d","a","ab","d","d","c","e"]),
            metric("lactic_to_acetic_acid_ratio", "g/g", "ratio of source-reported DM-basis concentrations", [5.24,2.20,2.84,5.26,2.97,2.72,3.20,3.01,1.53], 0.265, "<0.001", "<0.001", "0.001", ["a","bc","bc","a","b","bc","b","b","c"]),
            metric("calcium", "g/kg DM", "dry matter", [8.8,9.6,8.6,8.3,8.7,8.0,8.8,10.0,9.1], 0.12, "<0.001", "<0.001", "0.028", ["bcd","a","cd","de","bcd","e","bc","a","b"]),
            metric("phosphorus", "g/kg DM", "dry matter", [6.71,7.47,6.76,7.73,8.03,7.23,7.79,8.30,7.93], 0.122, "<0.001", "<0.001", "0.080", ["d","bc","d","abc","ab","cd","abc","a","ab"]),
            metric("potassium", "g/kg DM", "dry matter", [78,87,79,84,87,82,83,91,87], 1.2, "<0.001", "<0.001", "0.029", ["d","ab","cd","bc","ab","bcd","bcd","a","ab"]),
            metric("magnesium", "g/kg DM", "dry matter", [4.71,5.22,4.70,4.85,4.94,4.63,5.11,5.70,5.32], 0.085, "<0.001", "<0.001", "0.045", ["d","bc","d","cd","bcd","d","bc","a","ab"]),
            metric("sodium", "g/kg DM", "dry matter", [0.06,0.06,1.41,0.06,0.06,1.39,0.05,0.09,1.10], 0.018, "<0.001", "<0.001", "<0.001", ["c","c","a","c","c","a","c","c","b"], "FA2 treatment sodium includes sodium formate contribution."),
            metric("sulphur", "g/kg DM", "dry matter", [3.24,3.62,3.04,3.29,3.55,3.01,3.28,3.61,3.19], 0.036, "0.048", "<0.001", "0.080", ["b","a","cd","b","a","d","b","a","bc"]),
            metric("iron", "mg/kg DM", "dry matter", [167,143,129,213,201,163,146,162,159], 7.1, "<0.001", "0.001", "0.003", ["bc","cd","d","a","ab","cd","cd","cd","cd"]),
            metric("copper", "mg/kg DM", "dry matter", [7.9,9.3,7.5,9.6,10.2,8.1,7.0,7.8,6.8], 0.26, "<0.001", "<0.001", "0.084", ["cd","ab","cd","a","a","bc","cd","cd","d"]),
            metric("manganese", "mg/kg DM", "dry matter", [68,78,71,76,78,72,73,86,75], 1.7, "0.002", "<0.001", "0.027", ["c","b","bc","b","ab","bc","bc","a","bc"]),
            metric("zinc", "mg/kg DM", "dry matter", [56,66,56,62,67,57,47,54,51], 4.2, "0.010", "0.063", "0.842"),
        ],
    },
]


FIELDS = [
    "observation_id", "source_id", "source_table", "experiment", "harvest_stage",
    "biomass_type", "additive", "material_state", "stream", "press_type",
    "parameter", "reported_mean", "unit", "basis", "reported_sem",
    "p_biomass_type", "p_additive", "p_biomass_type_x_additive",
    "tukey_group", "replicates_per_treatment", "replication_context",
    "source_note", "quality_class", "runtime_status",
]


def build_rows():
    result = []
    for table in TABLES:
        for metric_row in table["metrics"]:
            count = len(table["conditions"])
            if not all(len(metric_row[field]) == count for field in ("values", "letters")):
                raise ValueError(f"Table {table['table']} metric {metric_row['name']} has wrong condition count")
            for index, ((biomass, additive), value, letter) in enumerate(zip(
                table["conditions"], metric_row["values"], metric_row["letters"], strict=True
            ), start=1):
                result.append({
                    "observation_id": f"AY25_T{table['table']}_{metric_row['name'].upper()}_{index:02d}",
                    "source_id": SOURCE_ID,
                    "source_table": table["table"],
                    "experiment": table["experiment"],
                    "harvest_stage": table["harvest"],
                    "biomass_type": biomass,
                    "additive": additive,
                    "material_state": table["material_state"],
                    "stream": "ensiled biomass" if table["table"] in {"2", "3"} else ("spontaneous effluent" if table["table"] == "4" else "pressed liquid fraction"),
                    "press_type": table["press_type"],
                    "parameter": metric_row["name"],
                    "reported_mean": value,
                    "unit": metric_row["unit"],
                    "basis": metric_row["basis"],
                    "reported_sem": metric_row["sem"],
                    "p_biomass_type": metric_row["p_biomass_type"],
                    "p_additive": metric_row["p_additive"],
                    "p_biomass_type_x_additive": metric_row["p_interaction"],
                    "tukey_group": letter,
                    "replicates_per_treatment": table["n"],
                    "replication_context": table["replication"],
                    "source_note": metric_row["note"],
                    "quality_class": "B",
                    "runtime_status": "reference_only_not_runtime_eligible",
                })
    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "dataset_id": "urn:greenhub:dataset:ayanfe-2025-timothy-tables2-4-6-reference",
        "title": "Timothy silage fermentation, effluent, and post-ensiling press-liquid measurements",
        "version": "1.0.0",
        "dataset_file": CSV_PATH.name,
        "source_id": SOURCE_ID,
        "authors": ["Nisola Ayanfe", "Marcia Franco", "Taina Jalava", "Tomasz Stefański", "Marketta Rinne"],
        "publication_year": 2025,
        "source_title": "Chemical Characterisation and Biorefinery Efficiency of Timothy Grass and Pulp Silages",
        "journal": "Grass and Forage Science 80(2), e12722",
        "doi": DOI,
        "source_url": URL,
        "full_text_url": "https://onlinelibrary.wiley.com/doi/10.1111/gfs.12722",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "retrieval_date": "2026-11-07",
        "source_location": "Tables 2, 3, 4 and 6; methods §§2.1–2.5",
        "geography": "Jokioinen, Finland; cultivated timothy grass",
        "evidence_class": "peer-reviewed primary experimental measurements; treatment least-squares means and descriptive pooled effluent chemistry",
        "quality_class": "B",
        "coverage": {
            "phase_2": "88-day ensiling endpoints, source-calculated fermentation losses, aerobic stability, and spontaneous first-regrowth effluent chemistry",
            "phase_3": "Double-screw-pressed liquid yield and composition of first-regrowth silages after freezing and thawing",
        },
        "data_structure": "Long-form table means. SEM and p-values are table-level statistics repeated on each matching metric-condition row; they are not per-cell standard deviations.",
        "limitations": [
            "Cultivated Finnish timothy is a literature comparator, not Dutch roadside grass or GreenHub batch data.",
            "Tables 2, 3, and 6 report least-squares means with SEM and factor p-values; these are not raw replicate observations.",
            "Table 4 effluent chemistry was pooled by treatment from silo samples, limiting inferential replication; no SEM or p-values are reported.",
            "Aerobic-stability observations lasted 172 h in Table 2 and 244 h in Table 3; means equal to the observation duration are preserved as printed and potential censoring is unresolved.",
            "FA1 contains propionic acid; sodium in FA2 effluent/liquid partly reflects sodium formate added with the treatment.",
            "The article reports measured storage and pressing results for experimental silage; no component mass balance, roadside transfer, GreenHub calibration, or default activation is inferred.",
            "Underlying research data are available from the corresponding author on reasonable request; no row-level raw replicate data are included here.",
        ],
        "runtime_policy": "Reference-only; not connected to runtime parameters, defaults, chemistry, UI inputs, TEA/LCA factors or Pareto scenarios.",
        "access_protocol": "HTTPS publisher DOI landing page and open full text",
        "reproducible_build_script": "scripts/build_ayanfe_2025_timothy_tables2_4_6_reference.py",
        "record_count": len(rows),
        "sha256": hashlib.sha256(CSV_PATH.read_bytes()).hexdigest(),
    }
    SIDECAR_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "tables": sorted({row['source_table'] for row in rows}), "output": str(CSV_PATH)}, indent=2))


if __name__ == "__main__":
    main()
