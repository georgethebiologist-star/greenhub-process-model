"""Build a traceable literature-only extract from Jurgutis et al. (2021).

The observations describe Lithuanian semi-natural grassland dominated by
switchgrass and digestate from a mixed-feed full-scale digester. They are
comparators, not Dutch roadside-grass measurements or GreenHub defaults.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Bigas production + upgrade" / "Feed BMP"
FILENAME = "field_grass_digestate_fertilisation_yield_nutrients_bmp_jurgutis_2021_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-JURGUTIS-FIELD-GRASS-DIGESTATE-2021"
DOI = "10.1016/j.biombioe.2021.106211"
DOI_URL = f"https://doi.org/{DOI}"
PDF_URL = "https://www.lammc.lt/data/public/uploads/2021/11/lino-jurgucio-disertacija.pdf"
RETRIEVAL_DATE = "2026-11-08"

FIELDS = [
    "observation_id", "source_id", "phase", "experiment_id", "material",
    "process_step", "metric", "reported_value", "numeric_value", "lower_bound",
    "upper_bound", "unit", "basis", "condition", "sample_count",
    "reported_uncertainty", "source_location", "evidence_class",
    "activation_state", "applicability", "limitations",
]

COMMON_LIMIT = (
    "Lithuanian semi-natural grassland, mainly switchgrass (Panicum virgatum), "
    "fertilised with digestate from a mixed-feed full-scale digester. Not Dutch "
    "roadside grass, VARTA samples, or GreenHub process streams; comparator only."
)


def _row(
    observation_id: str,
    phase: str,
    experiment_id: str,
    material: str,
    process_step: str,
    metric: str,
    reported_value: str,
    numeric_value: float | int | str = "",
    lower_bound: float | int | str = "",
    upper_bound: float | int | str = "",
    unit: str = "",
    basis: str = "",
    condition: str = "",
    sample_count: str = "",
    reported_uncertainty: str = "",
    source_location: str = "",
    applicability: str = "",
    limitations: str = COMMON_LIMIT,
) -> dict[str, str]:
    return {
        "observation_id": observation_id,
        "source_id": SOURCE_ID,
        "phase": phase,
        "experiment_id": experiment_id,
        "material": material,
        "process_step": process_step,
        "metric": metric,
        "reported_value": str(reported_value),
        "numeric_value": str(numeric_value),
        "lower_bound": str(lower_bound),
        "upper_bound": str(upper_bound),
        "unit": unit,
        "basis": basis,
        "condition": condition,
        "sample_count": str(sample_count),
        "reported_uncertainty": reported_uncertainty,
        "source_location": source_location,
        "evidence_class": "B_measured_literature_observation",
        "activation_state": "reference_only",
        "applicability": applicability or COMMON_LIMIT,
        "limitations": limitations,
    }


ROWS: list[dict[str, str]] = []

# Phase 1: Figure 4 treatment/year yields. The source describes a single annual
# cut; these are treatment response values, not natural roadside supply rates.
YIELDS = {
    "CONTROL": ("no digestate", {"2018": (5.08, ""), "2020": (4.76, ""), "2018-2020 mean": (4.92, "")}),
    "N85-SOLID": ("85 kg N ha-1 solid digestate", {"2018": (8.91, "*"), "2020": (10.08, "*"), "2018-2020 mean": (9.49, "*")}),
    "N85-LIQUID": ("85 kg N ha-1 liquid digestate", {"2018": (9.51, ""), "2020": (10.72, "*"), "2018-2020 mean": (10.10, "")}),
    "N170-SOLID": ("170 kg N ha-1 solid digestate", {"2018": (12.52, "*"), "2020": (17.23, "*"), "2018-2020 mean": (14.90, "*")}),
    "N170-LIQUID": ("170 kg N ha-1 liquid digestate", {"2018": (12.02, "*"), "2020": (13.24, "*"), "2018-2020 mean": (12.60, "*")}),
}
for treatment, (label, values) in YIELDS.items():
    for year, (value, significance) in values.items():
        uncertainty = "±0.22; statistic not specified" if treatment == "CONTROL" and year == "2018-2020 mean" else ""
        ROWS.append(_row(
            f"JURGUTIS21-YIELD-{treatment}-{year.upper().replace('-', '_').replace(' ', '_')}",
            "1", treatment, "semi-natural grassland above-ground biomass", "field harvest",
            "fresh biomass yield", f"{value:g}{significance}", value, unit="t fresh matter ha-1 yr-1",
            basis="fresh yield per hectare; source weighs fresh-cut biomass immediately after harvest",
            condition=f"{label}; {year}; * denotes p<0.05 versus unfertilised control",
            sample_count="3 field plot replicates", reported_uncertainty=uncertainty,
            source_location="Figure 4; Results §3.3.1; methods §2.1 and §2.4",
            applicability="Digestate-fertilisation yield response comparator; not roadside availability or an untreated GreenHub yield default.",
        ))
ROWS.append(_row(
    "JURGUTIS21-YIELD-N85-LIQUID-MEAN-SOURCE-DISAGREEMENT", "1", "N85-LIQUID",
    "semi-natural grassland above-ground biomass", "source discrepancy",
    "reported 2018-2020 mean fresh biomass yield", "Figure 4: 10.10; Results §3.3.1: 10.11",
    unit="t fresh matter ha-1 yr-1", basis="source statements disagree; no adjudicated value",
    source_location="Figure 4 versus Results §3.3.1",
    applicability="Source QA flag; neither value is selected as canonical in this record.",
))

# Phase 1/7: crop N, P and K concentrations printed on Figures 5–7.
PLANT_NPK = {
    "N": {
        "CONTROL": {2018: (1.09, ""), 2020: (1.28, "")},
        "N85-SOLID": {2018: (1.34, "*"), 2020: (2.20, "*")},
        "N85-LIQUID": {2018: (1.33, "*"), 2020: (2.85, "*")},
        "N170-SOLID": {2018: (1.38, "*"), 2020: (2.33, "*")},
        "N170-LIQUID": {2018: (1.78, "*"), 2020: (3.19, "*")},
    },
    "P": {
        "CONTROL": {2018: (0.322, ""), 2020: (0.294, "")},
        "N85-SOLID": {2018: (0.342, "*"), 2020: (0.354, "*")},
        "N85-LIQUID": {2018: (0.343, "*"), 2020: (0.412, "*")},
        "N170-SOLID": {2018: (0.349, "*"), 2020: (0.353, "*")},
        "N170-LIQUID": {2018: (0.333, ""), 2020: (0.434, "*")},
    },
    "K": {
        "CONTROL": {2018: (2.70, ""), 2020: (1.46, "")},
        "N85-SOLID": {2018: (3.47, "*"), 2020: (1.83, "*")},
        "N85-LIQUID": {2018: (3.33, "*"), 2020: (2.10, "*")},
        "N170-SOLID": {2018: (3.70, "*"), 2020: (1.91, "*")},
        "N170-LIQUID": {2018: (4.00, "*"), 2020: (2.12, "*")},
    },
}
for element, treatment_values in PLANT_NPK.items():
    for treatment, years in treatment_values.items():
        for year, (value, significance) in years.items():
            ROWS.append(_row(
                f"JURGUTIS21-PLANT-{element}-{treatment}-{year}", "1;7", treatment,
                "harvested semi-natural grassland biomass", "plant composition analysis",
                f"total {element} concentration", f"{value:g}{significance}", value,
                unit=f"% {element} of dry matter", basis="dry matter, as labelled in figure caption",
                condition=f"{year}; {treatment}; * denotes p<0.05 versus unfertilised control",
                sample_count="3 field plot replicates; figure-label statistic not described",
                source_location=f"Figure {dict(N='5', P='6', K='7')[element]}; Results §3.3.2",
                applicability="Crop nutrient composition response to digestate fertilisation; not digestate nutrient recovery or GreenHub feed composition.",
                limitations=COMMON_LIMIT + " Values are printed figure labels; no figure-derived uncertainty was assigned.",
            ))

# Phase 1/5: Table 4's explicitly reported treatment/year solids. The source
# table omits the 2020 control; it is not reconstructed from pooled averages.
GRASS_TS_VS = {
    ("N85-SOLID", 2020): (28.38, 0.98, 26.32, 0.77),
    ("N85-SOLID", 2018): (30.29, 1.01, 27.97, 0.98),
    ("N85-LIQUID", 2020): (23.92, 0.78, 22.13, 1.05),
    ("N85-LIQUID", 2018): (28.92, 0.88, 26.34, 0.65),
    ("N170-SOLID", 2020): (25.51, 1.03, 24.01, 0.87),
    ("N170-SOLID", 2018): (28.59, 0.77, 26.50, 0.54),
    ("N170-LIQUID", 2020): (28.21, 0.95, 26.66, 0.34),
    ("N170-LIQUID", 2018): (27.21, 1.11, 25.92, 0.44),
    ("CONTROL", 2018): (29.78, 1.21, 27.59, 1.04),
}
for (treatment, year), (ts, ts_sd, vs, vs_sd) in GRASS_TS_VS.items():
    for metric, value, sd in (("total solids", ts, ts_sd), ("volatile solids", vs, vs_sd)):
        ROWS.append(_row(
            f"JURGUTIS21-GRASS-{metric.upper().replace(' ', '-')}-{treatment}-{year}",
            "1;5", treatment, "harvested grass biomass", "feed characterization",
            metric, f"{value:g} ± {sd:g}", value, unit="% fresh matter",
            basis="fresh-matter basis as stated in Table 4",
            condition=f"{year}; {treatment}", sample_count="3 field plot replicates",
            reported_uncertainty=f"±{sd:g}; statistic not identified in table",
            source_location="Table 4; Results §3.3.1",
            applicability="Field-grass characterization comparator and BMP feed-basis context only.",
            limitations=COMMON_LIMIT + " Table 4 has no 2020 control row; this missing observation is not imputed.",
        ))
for metric in ("total solids", "volatile solids"):
    ROWS.append(_row(
        f"JURGUTIS21-GRASS-{metric.upper().replace(' ', '-')}-CONTROL-2020",
        "1;5", "CONTROL", "harvested grass biomass", "feed characterization", metric,
        "", unit="% fresh matter", basis="fresh-matter basis as stated in Table 4",
        condition="2020; unfertilised control",
        source_location="Table 4; missing treatment-year row",
        applicability="Explicit missingness marker; the paper provides no 2020 control value.",
        limitations=COMMON_LIMIT + " Not reported in Table 4; not inferred from pooled averages or other years.",
    ))

# Phase 5: Table 5, direct batch BMP outcomes (four source-reported metrics).
BMP = {
    ("CONTROL", 2018): (312, 10, 53, 1, 165, 11, 86, 1),
    ("CONTROL", 2020): (322, 12, 52, 1, 167, 10, 85, 2),
    ("N85-SOLID", 2018): (320, 11, 54, 2, 173, 13, 89, 2),
    ("N85-SOLID", 2020): (372, 7, 54, 2, 201, 9, 82, 1),
    ("N85-LIQUID", 2018): (371, 11, 55, 1, 204, 7, 98, 1),
    ("N85-LIQUID", 2020): (311, 13, 54, 1, 168, 11, 75, 3),
    ("N170-SOLID", 2018): (321, 12, 55, 2, 176, 8, 85, 2),
    ("N170-SOLID", 2020): (344, 10, 57, 1, 196, 4, 92, 2),
    ("N170-LIQUID", 2018): (368, 8, 56, 1, 206, 6, 95, 1),
    ("N170-LIQUID", 2020): (389, 9, 57, 1, 222, 5, 95, 1),
}
BMP_METRICS = (
    ("biogas yield", "L biogas kg-1 VS added", 0, 1, "per kg volatile solids added"),
    ("methane fraction", "% CH4 in biogas", 2, 3, "volume fraction as reported; reference gas conditions not specified in the extracted table"),
    ("methane yield", "L CH4 kg-1 VS added", 4, 5, "per kg volatile solids added"),
    ("biogas yield", "L biogas kg-1 fresh matter", 6, 7, "per kg fresh matter"),
)
for (treatment, year), values in BMP.items():
    for metric, unit, value_index, sd_index, basis in BMP_METRICS:
        value, sd = values[value_index], values[sd_index]
        ROWS.append(_row(
            f"JURGUTIS21-BMP-{treatment}-{year}-{value_index}", "5", treatment,
            "harvested semi-natural grassland biomass", "triplicate batch biomethane potential assay",
            metric, f"{value} ± {sd}", value, unit=unit, basis=basis,
            condition=f"{year}; mesophilic BMP; 35 ± 1 °C; 40 days; substrate:inoculum 2:1 by weight",
            sample_count="triplicate BMP assay; three field replicates also reported; exact averaging hierarchy not stated",
            reported_uncertainty=f"±{sd}; statistic not identified in Table 5",
            source_location="Table 5; methods §2.6; Results §3.4",
            applicability="Batch BMP comparator for digestate-fertilised field grass; not continuous AD yield or post-protein GreenHub residue.",
            limitations=COMMON_LIMIT + " Standard-state gas reference conditions and the meaning of ± are not stated in the table.",
        ))

# Phase 7: Table 2 separated-digestate analytical values. Keep its printed
# units, including volumetric ammonium-N and VFA measured before separation.
DIGESTATE = {
    (2018, "solid"): {"pH": ("8.74 ± 0.1", 8.74, 0.1, "dimensionless"), "TS": ("208 ± 10", 208, 10, "g kg-1 FM"), "VS": ("20.3 ± 1.1", 20.3, 1.1, "%"), "TKN": ("0.735 ± 0.05", 0.735, 0.05, "%"), "N-NH4": ("3.5 ± 0.5", 3.5, 0.5, "g L-1"), "TP": ("0.17 ± 0.01", 0.17, 0.01, "%"), "TK": ("0.259 ± 0.02", 0.259, 0.02, "%"), "OC": ("10.0 ± 0.5", 10.0, 0.5, "%"), "DOC": ("1.1 ± 0.1", 1.1, 0.1, "%")},
    (2018, "liquid"): {"pH": ("8.17 ± 0.41", 8.17, 0.41, "dimensionless"), "TS": ("77.5 ± 1.5", 77.5, 1.5, "g kg-1 FM"), "VS": ("7.58 ± 0.04", 7.58, 0.04, "%"), "TKN": ("0.68 ± 0.03", 0.68, 0.03, "%"), "N-NH4": ("4.5 ± 0.4", 4.5, 0.4, "g L-1"), "TP": ("0.15 ± 0.01", 0.15, 0.01, "%"), "TK": ("0.271 ± 0.03", 0.271, 0.03, "%"), "OC": ("1.85 ± 0.01", 1.85, 0.01, "%"), "DOC": ("1.23 ± 0.04", 1.23, 0.04, "%")},
    (2019, "solid"): {"pH": ("8.01 ± 0.2", 8.01, 0.2, "dimensionless"), "TS": ("301.4 ± 15.2", 301.4, 15.2, "g kg-1 FM"), "VS": ("27.42 ± 1.37", 27.42, 1.37, "%"), "TKN": ("0.26 ± 0.02", 0.26, 0.02, "%"), "N-NH4": ("3.0 ± 0.1", 3.0, 0.1, "g L-1"), "TP": ("0.09 ± 0.03", 0.09, 0.03, "%"), "TK": ("0.063 ± 0.03", 0.063, 0.03, "%"), "OC": ("12.55 ± 0.02", 12.55, 0.02, "%"), "DOC": ("1.34 ± 0.01", 1.34, 0.01, "%")},
    (2019, "liquid"): {"pH": ("8.05 ± 0.1", 8.05, 0.1, "dimensionless"), "TS": ("55.2 ± 2.7", 55.2, 2.7, "g kg-1 FM"), "VS": ("6.34 ± 0.18", 6.34, 0.18, "%"), "TKN": ("0.933 ± 0.2", 0.933, 0.2, "%"), "N-NH4": ("3.2 ± 0.1", 3.2, 0.1, "g L-1"), "TP": ("0.15 ± 0.03", 0.15, 0.03, "%"), "TK": ("0.183 ± 0.02", 0.183, 0.02, "%"), "OC": ("1.77 ± 0.01", 1.77, 0.01, "%"), "DOC": ("1.13 ± 0.04", 1.13, 0.04, "%")},
    (2020, "solid"): {"pH": ("8.4 ± 0.3", 8.4, 0.3, "dimensionless"), "TS": ("257.02 ± 12.85", 257.02, 12.85, "g kg-1 FM"), "VS": ("24.05 ± 1.20", 24.05, 1.20, "%"), "TKN": ("0.45 ± 0.03", 0.45, 0.03, "%"), "N-NH4": ("5.2 ± 0.1", 5.2, 0.1, "g L-1"), "TP": ("0.15 ± 0.02", 0.15, 0.02, "%"), "TK": ("0.12 ± 0.01", 0.12, 0.01, "%"), "OC": ("16.04 ± 0.05", 16.04, 0.05, "%"), "DOC": ("2.1 ± 0.1", 2.1, 0.1, "%")},
    (2020, "liquid"): {"pH": ("7.94 ± 0.41", 7.94, 0.41, "dimensionless"), "TS": ("49.09 ± 2.31", 49.09, 2.31, "g kg-1 FM"), "VS": ("3.75 ± 0.19", 3.75, 0.19, "%"), "TKN": ("0.63 ± 0.02", 0.63, 0.02, "%"), "N-NH4": ("5.7 ± 0.3", 5.7, 0.3, "g L-1"), "TP": ("0.13 ± 0.01", 0.13, 0.01, "%"), "TK": ("0.18 ± 0.02", 0.18, 0.02, "%"), "OC": ("2.7 ± 0.1", 2.7, 0.1, "%"), "DOC": ("2.12 ± 0.02", 2.12, 0.02, "%")},
}
for (year, fraction), metrics in DIGESTATE.items():
    for metric, (reported, value, sd, unit) in metrics.items():
        basis = "as-reported; Table 2 caption identifies separated digestate chemistry as fresh matter" if unit != "g L-1" else "volumetric concentration as printed; do not convert to mass fraction without density"
        ROWS.append(_row(
            f"JURGUTIS21-DIGESTATE-{year}-{fraction.upper()}-{metric}", "7", f"{year}-{fraction.upper()}",
            f"{fraction} digestate", "digestate characterization", metric, reported, value,
            unit=unit, basis=basis, condition=f"{year}; {fraction} fraction separated at full-scale co-digester",
            reported_uncertainty=f"±{sd}; statistic not specified in Table 2",
            source_location="Table 2; Results §3.1",
            applicability="Mixed-feed co-digester digestate comparator; not GreenHub digestate yield, composition, recovery, product quality, or substitution factor.",
            limitations=COMMON_LIMIT + " Feed mix changed between years; source notes chicken manure dominated 2018 and food waste/animal by-products dominated 2019–2020.",
        ))
for year, value, sd in ((2018, 4.0, 0.2), (2019, 4.3, 0.3), (2020, 7.9, 0.4)):
    ROWS.append(_row(
        f"JURGUTIS21-DIGESTATE-{year}-BEFORE-SEPARATION-VFA", "7", str(year),
        "whole digestate before solid-liquid separation", "digestate characterization", "volatile fatty acids",
        f"{value:g} ± {sd:g}", value, unit="g L-1", basis="volumetric concentration as printed",
        condition=f"{year}; sampled before solid/liquid separation",
        reported_uncertainty=f"±{sd:g}; statistic not specified in Table 2",
        source_location="Table 2 caption and VFA row; Results §3.1",
        applicability="Digester stability comparator only; not a GreenHub inhibition threshold.",
    ))

# Phase 7: soil outcomes in Table 3 are treatment-level, three-year summaries.
SOIL = {
    "CONTROL": {"pH": ("7.68 ± 0.06", 7.68, 0.06, "dimensionless", ""), "SOC": ("1.34 ± 0.06", 1.34, 0.06, "% DM", ""), "MHA": ("0.225 ± 0.018", 0.225, 0.018, "% DM", ""), "Ntot": ("0.96 ± 0.07", 0.96, 0.07, "g kg-1", ""), "Nmin": ("10.32 ± 0.99", 10.32, 0.99, "mg kg-1", ""), "N-NH4": ("3.11 ± 0.30", 3.11, 0.30, "mg kg-1", "")},
    "N85-SOLID": {"pH": ("7.82 ± 0.06", 7.82, 0.06, "dimensionless", ""), "SOC": ("1.50 ± 0.10", 1.50, 0.10, "% DM", ""), "MHA": ("0.311 ± 0.037*", 0.311, 0.037, "% DM", "*"), "Ntot": ("1.20 ± 0.10", 1.20, 0.10, "g kg-1", ""), "Nmin": ("19.91 ± 4.49", 19.91, 4.49, "mg kg-1", ""), "N-NH4": ("14.29 ± 5.79", 14.29, 5.79, "mg kg-1", "")},
    "N170-LIQUID": {"pH": ("7.77 ± 0.05", 7.77, 0.05, "dimensionless", ""), "SOC": ("1.39 ± 0.10", 1.39, 0.10, "% DM", ""), "MHA": ("0.265 ± 0.018", 0.265, 0.018, "% DM", ""), "Ntot": ("1.10 ± 0.10", 1.10, 0.10, "g kg-1", ""), "Nmin": ("29.98 ± 7.97*", 29.98, 7.97, "mg kg-1", "*"), "N-NH4": ("16.74 ± 7.10*", 16.74, 7.10, "mg kg-1", "*")},
    "N85-LIQUID": {"pH": ("7.82 ± 0.05", 7.82, 0.05, "dimensionless", ""), "SOC": ("1.33 ± 0.06", 1.33, 0.06, "% DM", ""), "MHA": ("0.255 ± 0.020", 0.255, 0.020, "% DM", ""), "Ntot": ("1.11 ± 0.06", 1.11, 0.06, "g kg-1", ""), "Nmin": ("14.70 ± 1.72", 14.70, 1.72, "mg kg-1", ""), "N-NH4": ("7.76 ± 1.84", 7.76, 1.84, "mg kg-1", "")},
    "N170-SOLID": {"pH": ("7.80 ± 0.06", 7.80, 0.06, "dimensionless", ""), "SOC": ("1.55 ± 0.10", 1.55, 0.10, "% DM", ""), "MHA": ("0.301 ± 0.030*", 0.301, 0.030, "% DM", "*"), "Ntot": ("1.20 ± 0.10", 1.20, 0.10, "g kg-1", ""), "Nmin": ("26.02 ± 6.23*", 26.02, 6.23, "mg kg-1", "*"), "N-NH4": ("20.51 ± 7.14*", 20.51, 7.14, "mg kg-1", "*")},
}
for treatment, metrics in SOIL.items():
    for metric, (reported, value, sd, unit, significance) in metrics.items():
        ROWS.append(_row(
            f"JURGUTIS21-SOIL-{treatment}-{metric}", "7", treatment,
            "soil, 0-10 cm layer", "post-fertilisation soil characterization", metric,
            reported, value, unit=unit, basis="soil sample; basis not stated unless unit includes DM",
            condition=f"three-year field-treatment summary; {treatment}; * denotes p<0.05 versus control",
            reported_uncertainty=f"±{sd}; statistic not specified in Table 3",
            source_location="Table 3; Results §3.2",
            applicability="Soil-response comparator for digestate application; not a GreenHub LCA soil-carbon credit or nutrient-loss factor.",
        ))

# Protocol and source limitations useful to interpreting Phases 1, 3, 5, 7.
CONTEXT = [
    ("FIELD-REPLICATES", "field trial", "number of field replicates", "3", 3, "plots per treatment", "Methods §2.1", "Three field plot replicates; plots were 2 × 3 m."),
    ("PLOT-AREA", "field trial", "plot area", "6", 6, "m2", "Methods §2.1", "Plot size 2 × 3 m."),
    ("TRIAL-YEARS", "field trial", "field campaign duration", "2018-2020", 3, "years", "Methods §2.1", "Three consecutive years on the same fields; no yearly yield value for 2019 is supplied in Figure 4."),
    ("FERTILISATION-DATE", "field operations", "digestate application timing", "first week of May", "", "calendar period", "Methods §2.1", "Manual operation; application rate based on digestate TKN."),
    ("HARVEST-TIMING-CONFLICT", "field operations", "harvest timing as reported", "Methods: first week of July; Results: second half of September", "", "conflicting calendar periods", "Methods §2.1 versus Results §3.3.1", "Internal source inconsistency; do not select one timing as definitive."),
    ("CUT-FREQUENCY", "field operations", "annual harvest frequency", "once per year", 1, "cut yr-1", "Methods §2.1", "Once-a-year semi-natural grassland cut; not a roadside mowing schedule."),
    ("CUT-LENGTH", "sample preparation", "reduced biomass length", "35-40", "", "mm", "Methods §2.4", "Size reduction simulated machinery chopping; no energy demand reported."),
    ("BMP-TEMPERATURE", "BMP protocol", "incubation temperature", "35 ± 1", 35, "°C", "Methods §2.6", "Mesophilic batch BMP."),
    ("BMP-DURATION", "BMP protocol", "incubation duration", "40", 40, "days", "Methods §2.6", "Batch BMP endpoint; not a continuous digester HRT."),
    ("BMP-INOCULUM-RATIO", "BMP protocol", "substrate to inoculum ratio", "2:1", "", "mass ratio", "Methods §2.6", "Source states substrate:inoculum = 2:1 by weight."),
    ("DIGESTATE-INPUTS", "digestate source", "full-scale digester feedstocks", "chicken manure; food waste; agricultural biomass; second-category animal by-products", "", "qualitative source description", "Results §3.1", "Feed mix changed over years; source says chicken manure dominated 2018 and organic food waste/second-category animal by-products dominated 2019-2020."),
    ("YIELD-MEAN-DISAGREEMENT", "source QA", "85 kg N ha-1 liquid digestate mean yield", "Figure 4: 10.10; Results §3.3.1: 10.11", "", "t fresh matter ha-1 yr-1", "Figure 4 versus Results §3.3.1", "The two source locations report different values; preserved as a discrepancy and not resolved by averaging."),
]
for key, experiment, metric, reported, numeric, unit, location, note in CONTEXT:
    ROWS.append(_row(
        f"JURGUTIS21-CONTEXT-{key}", "1;3;5;7", experiment,
        "field grass / digestate study", "study protocol and context", metric,
        reported, numeric_value=numeric, unit=unit, basis="reported study condition",
        source_location=location, applicability=note,
        limitations=COMMON_LIMIT + " Context only; not a GreenHub operating specification.",
    ))


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def _append_once(
    path: Path,
    row: dict[str, object],
    key: str,
    mutable_fields: set[str] | None = None,
) -> None:
    fields, existing = _read_csv(path)
    matches = [item for item in existing if item.get(key) == str(row.get(key, ""))]
    if matches:
        if len(matches) != 1:
            raise ValueError(f"Conflicting registration already exists in {path}: {row.get(key)}")
        changed = {
            field for field in fields
            if matches[0].get(field, "") != str(row.get(field, ""))
        }
        if changed:
            if mutable_fields is None or not changed.issubset(mutable_fields):
                raise ValueError(f"Conflicting registration already exists in {path}: {row.get(key)}")
            matches[0].update({field: str(row.get(field, "")) for field in changed})
            had_bom = path.read_bytes().startswith(b"\xef\xbb\xbf")
            temporary = path.with_suffix(path.suffix + ".tmp")
            with temporary.open("w", encoding="utf-8-sig" if had_bom else "utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
                writer.writeheader()
                writer.writerows(existing)
            temporary.replace(path)
        return
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writerow({field: row.get(field, "") for field in fields})


def main() -> None:
    if len({row["observation_id"] for row in ROWS}) != len(ROWS):
        raise ValueError("Observation IDs must be unique")
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    title = "The effect of digestate fertilisation on grass biogas yield and soil properties in field-biomass-biogas-field renewable energy production approach in Lithuania"
    authors = "Linas Jurgutis; A. Šlepetienė; K. Amalevičiūtė-Volungė; J. Volungevičius; J. Šlepetys"
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:feed-bmp:jurgutis-2021-field-grass-digestate-reference:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": f"Jurgutis, L., Šlepetienė, A., Amalevičiūtė-Volungė, K., Volungevičius, J., & Šlepetys, J. (2021). {title}. Biomass and Bioenergy, 153, 106211. {DOI_URL}",
        "publication_year": 2021,
        "journal": "Biomass and Bioenergy, volume 153, article 106211",
        "doi": DOI,
        "source_url": DOI_URL,
        "accessible_full_text": PDF_URL,
        "retrieval_date": RETRIEVAL_DATE,
        "geography": "Semi-natural grassland experiment near Elektrėnai, Lithuania; eroded loamy Retisol.",
        "material_scope": "Grassland was mainly switchgrass (Panicum virgatum); single annual harvest; digestate sourced from a full-scale mixed-feed anaerobic digester.",
        "evidence_class": "B_measured_literature_observations_and_reported_protocol",
        "quality_class": "B",
        "license": "No explicit open reuse license was identified for the publisher article or dissertation PDF during retrieval. The repository contains a limited attributed factual extract, not a copy of the source tables or article. Review rights before external redistribution or commercial reuse.",
        "data_availability": "Selected table values and figure labels are accessible in the published article reproduced in the public institutional dissertation PDF; no raw-data package was identified.",
        "data_structure": "Long-form observations preserve experiment/treatment/year, value as reported, numeric value, unit, basis, method/condition, uncertainty note, exact source table/figure/section, evidence class, activation state, applicability and limitation. Empty numeric values mean non-numeric context, not zero.",
        "phase_coverage": {
            "1": "Digestate-fertilisation grass yield, grass total solids/volatile solids, and plant N/P/K response; not Dutch roadside availability or collection logistics.",
            "2": "No storage/degradation experiment; no storage kinetics or emissions.",
            "3": "Sample chopped to 35–40 mm for laboratory work; no GreenHub press, extraction, water or unit-energy balance.",
            "4": "No protein recovery operation or product data.",
            "5": "Batch BMP for fertilised field grass at mesophilic conditions; no post-protein residual or continuous-reactor calibration.",
            "6": "Biogas/methane potential only; no upgrading, recovery, slip or utility data.",
            "7": "Mixed-feed digestate composition, fertilisation rates, grass nutrient response, and selected soil response; no nutrient recovery yield, GreenHub digestate flow, product compliance or substitution factor.",
        },
        "limitations": [
            "The grass is Lithuanian semi-natural grassland, mainly switchgrass, not Dutch roadside/VARTA grass or GreenHub feed.",
            "Fertilisation is a field treatment; observed yield response is not natural supply, harvestability, or a sustainable roadside nutrient-management recommendation.",
            "The source has an internal harvest-timing inconsistency: methods say first week of July, while Results §3.3.1 says second half of September; retained as an unresolved conflict.",
            "The 85 kg N ha-1 liquid-digestate three-year mean yield is 10.10 in Figure 4 and 10.11 in Results §3.3.1; both statements are retained and neither is treated as canonical.",
            "Table 4 does not report a 2020 control TS/VS result; no value is inferred from pooled means.",
            "Figure-label values have no reported uncertainty in the extract; Table 2/3/5 ± statistic is not specified and is preserved verbatim.",
            "The BMP is batch potential, not continuous AD performance; standard gas reference conditions are not identified in Table 5.",
            "Digestate came from a full-scale mixed-feed plant whose feed mix changed across years; it is not GreenHub digestate.",
            "Digestate composition contains mixed percentage and volumetric bases. No density-based conversion, nutrient balance, legal compliance, or fertilizer substitution credit is inferred.",
            "No explicit reuse license was found; this extract is for internal research traceability and remains subject to rights review before redistribution.",
        ],
        "conversion_or_processing": "Direct transcription of table values and printed figure labels; no digitization, calculation, basis conversion, imputation, kinetic fitting, or GreenHub parameter mapping.",
        "uncertainty": "Table-reported ± terms are retained without assigning SD/SE. Figure labels have no uncertainty. Field and BMP replicate hierarchy is described in methods but not linked unambiguously to each reported uncertainty.",
        "runtime_policy": "Reference-only; not linked to runtime parameters, defaults, process equations, TEA/LCA factors, scenario generation, or Pareto outputs.",
        "access_protocol": "HTTPS DOI and publicly accessible Lithuanian institutional dissertation PDF containing the article text; reuse terms were not identified.",
        "fair_metadata": {
            "findable": "Local versioned URN, DOI, source ID, and catalog-indexed dataset path.",
            "accessible": "HTTPS DOI and institutional full-text link are recorded; access and reuse caveats are explicit.",
            "interoperable": "UTF-8 CSV with common GreenHub long-form observation fields, explicit phases, units, bases and source locations.",
            "reusable": "Citation, retrieval date, checksum, evidence class, uncertainty, limitations, no-conversion policy and runtime exclusion are recorded.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID, "source_title": title, "authors": authors, "year": "2021",
        "doi_or_stable_id": DOI, "source_type": "peer-reviewed primary field and laboratory study; limited table/figure transcription",
        "url": DOI_URL, "material_scope": sidecar["material_scope"],
        "quality_notes": "B-tier measured Lithuanian grassland/digestate comparator; mixed-feed digestate, harvest-timing inconsistency and transfer limits recorded; reference-only.",
    }
    _append_once(GROUP / "source_register.csv", local_source, "source_id")
    _append_once(GROUP / "ad_source_register.csv", local_source, "source_id")
    _append_once(GROUP / "dataset_manifest.csv", {
        "filename": FILENAME,
        "description": "Field grass yields, NPK/TS/VS, batch BMP, mixed-feed digestate chemistry, and soil-response observations; reference-only.",
        "row_count": len(ROWS), "schema_version": "1.0", "encoding": "UTF-8 with BOM", "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "observation_id",
    }, "filename", mutable_fields={"row_count"})

    relative_path = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
    _append_once(DATA / "global_audit_package" / "global_source_register.csv", {
        "dataset_path": relative_path, "dataset_group": "Feed BMP", "source_id": SOURCE_ID,
        "source_title": title, "authors": authors, "year": "2021", "doi_or_stable_id": DOI,
        "url": DOI_URL, "source_type": "peer-reviewed primary field and laboratory study; limited table/figure transcription",
        "notes": "B-tier comparator spanning Phases 1, 5 and 7; Lithuania semi-natural grassland and mixed-feed digestate; not GreenHub roadside feed or digestate; no runtime activation.",
    }, "dataset_path")
    _append_once(DATA / "global_audit_package" / "global_dataset_manifest.csv", {
        "dataset_path": relative_path, "category": "Bigas production + upgrade", "subgroup": "Feed BMP",
        "filename": FILENAME, "row_count_observed": len(ROWS), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3", "notes": "Measured field/BMP/digestate comparator; treatment and method context retained; no GreenHub parameter connection.",
    }, "dataset_path", mutable_fields={"row_count_observed", "header_count", "headers", "standardized_status_values", "detected_readiness", "notes"})
    numeric_rows = sum(bool(row["numeric_value"] or row["lower_bound"] or row["upper_bound"]) for row in ROWS)
    _append_once(DATA / "global_audit_package" / "global_dataset_readiness.csv", {
        "dataset_path": relative_path, "category": "Bigas production + upgrade", "subgroup": "Feed BMP",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": numeric_rows,
        "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "DOI-linked; numeric values have source table/figure locations. Mixed bases and transfer limits remain explicit; reference-only.",
    }, "dataset_path", mutable_fields={"numeric_rows", "notes"})

    summary_path = DATA / "global_audit_package" / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(DATA / "global_audit_package" / "global_dataset_manifest.csv")
    _, readiness = _read_csv(DATA / "global_audit_package" / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary["readiness_counts"] = {}
    for item in readiness:
        status = item.get("readiness", "")
        summary["readiness_counts"][status] = summary["readiness_counts"].get(status, 0) + 1
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": str(CSV_PATH.relative_to(ROOT)), "rows": len(ROWS), "numeric_rows": numeric_rows, "sha256": digest, "quality_class": "B", "activation_state": "reference_only"}, indent=2))


if __name__ == "__main__":
    main()
