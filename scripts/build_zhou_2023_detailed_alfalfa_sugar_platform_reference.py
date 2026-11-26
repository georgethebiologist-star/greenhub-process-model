"""Stage detailed alfalfa-pulp pretreatment and fermentation table evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Thermal_Enzymatic"
AUDIT = DATA / "global_audit_package"
FILENAME = "alfalfa_sodium_chlorite_and_sugar_fermentation_tables_zhou_2023_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-ZHOU-DTU-THESIS-2023-ALFALFA-PROTEIN"
DOI = "10.1016/j.indcrop.2023.117927"
PDF_URL = "https://backend.orbit.dtu.dk/ws/portalfiles/portal/363463153/PhD_thesis_-_Fa_Zhou.pdf"
RECORD_URL = "https://orbit.dtu.dk/en/publications/valorization-of-green-biomass-alfalfa-pulp-as-a-potential-platfor/"
ARTICLE_URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"
TITLE = "Valorization of Green Biomass: Alfalfa Pulp as a Potential Platform for Food and Biochemicals"
AUTHORS = "Fa Zhou"
FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_section", "material",
    "process_step", "metric", "value", "unit", "basis", "condition_scope",
    "statistic", "replicate_count", "uncertainty", "source_location", "evidence_class",
    "quality_class", "activation_state", "transferability", "limitations",
]

TABLE_42_METRICS = {
    "solid_recovery": ("%", "Reported solid recovery; denominator is not separately defined in Table 4.2."),
    "glucan_content": ("% of DM", "Mass fraction of dry pretreated pulp; Table 4.2 caption specifies % of DM."),
    "xylan_content": ("% of DM", "Mass fraction of dry pretreated pulp; Table 4.2 caption specifies % of DM."),
    "lignin_content": ("% of DM", "Mass fraction of dry pretreated pulp; Table 4.2 caption specifies % of DM."),
    "delignification": ("%", "Reported fraction of initial lignin removed; see the source component-loss equation."),
    "deacetylation": ("%", "Reported fraction of initial acetyl groups removed; see the source component-loss equation."),
    "glucan_loss": ("%", "Fraction of initial glucan mass lost; source Eq. (1) accounts for solid recovery."),
    "xylan_loss": ("%", "Fraction of initial xylan mass lost; source Eq. (1) accounts for solid recovery."),
    "protein_loss": ("%", "Fraction of initial protein mass lost; source Eq. (1) accounts for solid recovery."),
    "color_L": ("CIELAB coordinate", "Reported color lightness coordinate; not a mass fraction."),
    "color_delta_a": ("CIELAB coordinate", "Reported red-green color coordinate difference; not a mass fraction."),
    "color_delta_b": ("CIELAB coordinate", "Reported yellow-blue color coordinate difference; not a mass fraction."),
}

FERMENTATION_METRICS = [
    ("initial_glucose", "g/L", "Initial glucose concentration in the ASH/BJ medium."),
    ("initial_xylose", "g/L", "Initial xylose concentration in the ASH/BJ medium."),
    ("glucose_consumption", "g/L", "Reported glucose consumption concentration."),
    ("xylose_consumption", "g/L", "Reported xylose consumption concentration."),
    ("maximum_lactic_acid_concentration", "g/L", "Maximum reported lactic acid concentration."),
    ("maximum_lactic_acid_productivity", "g/L/h", "Maximum reported lactic acid productivity."),
    ("acetic_acid_concentration", "g/L", "Reported acetic acid concentration."),
    ("ethanol_concentration", "g/L", "Reported ethanol concentration."),
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read(path)
    keys = key.split("|")
    indexed = {tuple(row.get(item, "") for item in keys): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(item, "") for item in keys)
        if identity in indexed:
            indexed[identity].update(entry)
        else:
            rows.append(entry)
            indexed[identity] = rows[-1]
    _write(path, fields or list(entries[0]), rows)


def _make_row(
    record_id: str,
    phase: str,
    section: str,
    process: str,
    metric: str,
    value: str,
    unit: str,
    basis: str,
    condition: str,
    uncertainty: str,
    source_location: str,
    status: str = "reported_mean",
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "source_id": SOURCE_ID,
        "phase_relevance": phase,
        "source_section": section,
        "material": "Cultivated alfalfa pulp and alfalfa-derived brown juice / sugar hydrolysate",
        "process_step": process,
        "metric": metric,
        "value": value,
        "unit": unit,
        "basis": basis,
        "condition_scope": condition,
        "statistic": status,
        "replicate_count": "Biological replicates were used (at least); exact n is not reported.",
        "uncertainty": uncertainty,
        "source_location": source_location,
        "evidence_class": "B_primary_thesis_table_measurement_mean_and_SD",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "Cultivated alfalfa and the thesis sugar-platform route; not Dutch roadside/VARTA grass or GreenHub operating data.",
        "limitations": "Reference comparator only. Do not infer GreenHub yields, reagent demand, route performance, utility use, or runtime defaults from this crop and laboratory process.",
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    press_metrics = [
        ("color_L", "CIELAB coordinate", "Reported color lightness coordinate; not a mass fraction."),
        ("color_delta_a", "CIELAB coordinate", "Reported red-green color coordinate difference; not a mass fraction."),
        ("color_delta_b", "CIELAB coordinate", "Reported yellow-blue color coordinate difference; not a mass fraction."),
        ("temperature_at_step_end", "°C", "Feed/pulp temperature range at the end of each step, as marked by the Table 4.1 footnote."),
        ("pulp_recovery", "%", "Reported pulp recovery; table footnote says based on wet mass of pulp after each step; exact denominator is not further defined."),
        ("moisture", "%", "Moisture percentage; basis is not further specified in Table 4.1."),
        ("ash", "g/100 g DM", "Mass per 100 g dry matter."),
        ("protein", "g/100 g DM", "Mass per 100 g dry matter; source reports Dumas nitrogen analysis using N × 6.25."),
        ("extractives", "g/100 g DM", "Mass per 100 g dry matter."),
        ("glucan", "g/100 g DM", "Mass per 100 g dry matter."),
        ("xylan", "g/100 g DM", "Mass per 100 g dry matter."),
        ("arabinan", "g/100 g DM", "Mass per 100 g dry matter."),
        ("lignin", "g/100 g DM", "Mass per 100 g dry matter."),
    ]
    press_stages = [
        ("RAW", "Raw alfalfa", {
            "color_L": ("58.91", "1.97"), "color_delta_a": ("-8.89", "0.45"),
            "color_delta_b": ("12.23", "1.86"), "temperature_at_step_end": ("2 - 5", ""),
            "pulp_recovery": ("-", ""), "moisture": ("82.28", "0.28"), "ash": ("4.44", "0.11"),
            "protein": ("22.63", "1.44"), "extractives": ("25.56", "2.91"), "glucan": ("20.59", "0.63"),
            "xylan": ("9.86", "0.44"), "arabinan": ("2.70", "0.10"), "lignin": ("14.29", "0.58"),
        }),
        ("PRESS1", "First-pressed alfalfa pulp", {
            "color_L": ("58.30", "1.00"), "color_delta_a": ("-8.28", "0.13"),
            "color_delta_b": ("15.67", "0.03"), "temperature_at_step_end": ("25 - 34", ""),
            "pulp_recovery": ("29.25", "0.80"), "moisture": ("56.78", "0.41"), "ash": ("2.51", "0.02"),
            "protein": ("19.50", "0.68"), "extractives": ("19.32", "0.48"), "glucan": ("27.45", "0.41"),
            "xylan": ("11.45", "0.61"), "arabinan": ("3.89", "0.35"), "lignin": ("15.90", "0.92"),
        }),
        ("PRESS2", "Second-pressed alfalfa pulp", {
            "color_L": ("64.02", "0.63"), "color_delta_a": ("-6.27", "0.50"),
            "color_delta_b": ("15.90", "0.12"), "temperature_at_step_end": ("37 - 47", ""),
            "pulp_recovery": ("85.76", "1.32"), "moisture": ("55.35", "0.45"), "ash": ("1.73", "0.07"),
            "protein": ("17.27", "0.20"), "extractives": ("18.30", "0.94"), "glucan": ("28.89", "1.07"),
            "xylan": ("13.13", "0.36"), "arabinan": ("3.68", "0.42"), "lignin": ("17.00", "0.41"),
        }),
    ]
    for stage_id, material, observations in press_stages:
        for metric, unit, basis in press_metrics:
            value, sd = observations[metric]
            if metric == "temperature_at_step_end":
                statistic, uncertainty = "reported_range", ""
            elif value == "-":
                statistic, uncertainty = "source_not_applicable", ""
            else:
                statistic, uncertainty = "mean", f"SD={sd}"
            row = _make_row(
                f"ZHOU23-T41-{stage_id}-{metric.upper()}", "1;3", "§4.4.1, Table 4.1",
                "twin-screw pressing and feed/fraction characterization", metric, value, unit, basis,
                f"Sampling stage: {material}; measurements during twin-screw juicer processing.",
                uncertainty,
                "Table 4.1, printed p. 90; PDF extracted-text lines 1733–1749; methods §4.3.2 and §4.3.5",
                statistic,
            )
            row["material"] = material
            rows.append(row)

    pretreatment_conditions = (
        "Twice-pressed alfalfa pulp dried at 80°C for 48 h; sodium-chlorite solution at 2–10% w/v, "
        "solid:liquid 1:20 g/mL, 75°C for 2 h; recovered by vacuum filtration, washed to neutrality, "
        "then dried at 50°C for 24 h. 0% is the non-pretreated control."
    )
    table_42 = {
        "0": {
            "glucan_content": ("28.89", "1.07", "e"), "xylan_content": ("13.13", "0.36", "e"),
            "lignin_content": ("17.00", "0.41", "a"), "color_L": ("64.02", "0.63", "c"),
            "color_delta_a": ("-6.27", "0.50", "cd"), "color_delta_b": ("15.90", "0.12", "ab"),
        },
        "2": {
            "solid_recovery": ("83.95", "2.33", "a"), "glucan_content": ("35.46", "0.62", "d"),
            "xylan_content": ("15.13", "0.40", "d"), "lignin_content": ("9.01", "0.94", "b"),
            "delignification": ("59.60", "3.80", "c"), "deacetylation": ("13.51", "1.48", "e"),
            "glucan_loss": ("8.00", "1.43", "b"), "xylan_loss": ("13.62", "2.03", "d"),
            "protein_loss": ("52.43", "0.20", "d"), "color_L": ("89.00", "0.70", "b"),
            "color_delta_a": ("-6.06", "0.12", "c"), "color_delta_b": ("16.37", "0.48", "a"),
        },
        "4": {
            "solid_recovery": ("73.33", "1.45", "b"), "glucan_content": ("40.04", "0.81", "c"),
            "xylan_content": ("16.08", "0.39", "c"), "lignin_content": ("7.01", "0.52", "c"),
            "delignification": ("72.72", "1.80", "b"), "deacetylation": ("21.76", "1.93", "d"),
            "glucan_loss": ("10.84", "1.62", "ab"), "xylan_loss": ("21.20", "1.70", "c"),
            "protein_loss": ("61.70", "0.81", "c"), "color_L": ("89.10", "0.97", "b"),
            "color_delta_a": ("-5.44", "0.25", "b"), "color_delta_b": ("11.69", "0.21", "b"),
        },
        "6": {
            "solid_recovery": ("68.41", "1.33", "c"), "glucan_content": ("43.30", "1.89", "b"),
            "xylan_content": ("16.67", "0.21", "bc"), "lignin_content": ("5.75", "0.49", "d"),
            "delignification": ("79.57", "1.55", "a"), "deacetylation": ("38.77", "1.98", "c"),
            "glucan_loss": ("10.93", "3.48", "ab"), "xylan_loss": ("24.56", "0.86", "b"),
            "protein_loss": ("69.18", "1.36", "b"), "color_L": ("90.76", "0.15", "a"),
            "color_delta_a": ("-5.36", "0.11", "ab"), "color_delta_b": ("11.29", "0.22", "b"),
        },
        "8": {
            "solid_recovery": ("64.75", "0.61", "c"), "glucan_content": ("46.22", "1.27", "a"),
            "xylan_content": ("17.52", "0.35", "a"), "lignin_content": ("5.10", "0.75", "d"),
            "delignification": ("82.99", "2.24", "a"), "deacetylation": ("57.65", "2.13", "b"),
            "glucan_loss": ("10.79", "2.20", "ab"), "xylan_loss": ("25.58", "1.31", "b"),
            "protein_loss": ("74.38", "1.19", "a"), "color_L": ("90.64", "0.61", "a"),
            "color_delta_a": ("-5.15", "0.05", "ab"), "color_delta_b": ("10.90", "0.69", "bc"),
        },
        "10": {
            "solid_recovery": ("61.58", "1.43", "d"), "glucan_content": ("46.80", "1.07", "a"),
            "xylan_content": ("16.92", "0.52", "ab"), "lignin_content": ("5.43", "0.66", "d"),
            "delignification": ("82.91", "1.86", "a"), "deacetylation": ("65.97", "1.45", "a"),
            "glucan_loss": ("14.81", "1.75", "a"), "xylan_loss": ("32.24", "1.88", "a"),
            "protein_loss": ("74.33", "0.25", "a"), "color_L": ("90.57", "0.47", "a"),
            "color_delta_a": ("-5.05", "0.03", "a"), "color_delta_b": ("10.34", "0.30", "c"),
        },
    }
    for loading, observations in table_42.items():
        condition = f"{loading}% (w/v) sodium-chlorite treatment; {pretreatment_conditions}"
        for metric, (unit, basis) in TABLE_42_METRICS.items():
            observation = observations.get(metric)
            value, uncertainty, status = (observation[0], f"SD={observation[1]}; Fisher LSD group={observation[2]} (p<0.05)", "mean") if observation else ("na", "", "source_not_applicable")
            rows.append(_make_row(
                f"ZHOU23-T42-SC{loading}-{metric.upper()}", "3", "§4.4.2, Table 4.2",
                "sodium-chlorite pretreatment of twice-pressed alfalfa pulp", metric, value, unit,
                basis, condition, uncertainty,
                "Table 4.2, printed p. 92; PDF text lines 1762–1873; methods §4.3.3, printed pp. 87–88",
                status,
            ))

    fermentation_cases = [
        ("0", "100% BJ"), ("15", "15% ASH + 85% BJ"), ("30", "30% ASH + 70% BJ"),
        ("50", "50% ASH + 50% BJ"), ("70", "70% ASH + 30% BJ"), ("85", "85% ASH + 15% BJ"),
    ]
    tables = {
        "43": {
            "duration": "14 h", "vessel": "50 mL Schott Duran bottle with sealed polypropylene cap",
            "pH_schedule": "initial pH 7; adjusted to 7 every 2 h",
            "page": "Table 4.3, printed p. 102; PDF text lines 2005–2088",
            "values": [
                [("8.0", "0.19", "f"), ("2.3", "0.18", "f"), ("6.1", "1.64", "e"), ("2.3", "0.18", "d"), ("12.8", "0.17", "e"), ("2.8", "0.12", "ab"), ("1.0", "0.09", "e"), ("0.5", "0.16", "a")],
                [("13.3", "0.32", "e"), ("4.5", "0.32", "e"), ("11.6", "1.36", "d"), ("4.5", "0.32", "b"), ("17.4", "0.13", "d"), ("2.9", "0.31", "ab"), ("1.2", "0.22", "de"), ("0.3", "0.05", "b")],
                [("17.2", "0.57", "d"), ("5.5", "0.20", "d"), ("16.5", "0.51", "c"), ("5.0", "0.32", "a"), ("22.8", "0.08", "b"), ("3.4", "0.07", "a"), ("1.5", "0.09", "d"), ("0.4", "0.08", "ab")],
                [("23.0", "0.47", "c"), ("6.4", "0.21", "c"), ("22.7", "0.49", "b"), ("4.5", "0.48", "b"), ("28.6", "0.03", "a"), ("2.9", "0.67", "ab"), ("1.9", "0.14", "c"), ("0.4", "0.05", "ab")],
                [("30.2", "0.84", "b"), ("8.9", "0.42", "b"), ("24.4", "1.15", "a"), ("3.3", "0.28", "c"), ("28.8", "0.61", "a"), ("2.6", "0.32", "b"), ("2.7", "0.12", "b"), ("0.4", "0.06", "ab")],
                [("35.1", "0.93", "a"), ("10.3", "0.56", "a"), ("20.2", "0.34", "b"), ("2.3", "0.22", "d"), ("21.8", "0.58", "c"), ("2.5", "0.13", "b"), ("3.1", "0.13", "a"), ("0.4", "0.09", "ab")],
            ],
        },
        "44": {
            "duration": "48 h", "vessel": "150 mL shake flask",
            "pH_schedule": "initial pH 7; adjusted to 7 every 6 h",
            "page": "Table 4.4, printed p. 104; PDF text lines 2097–2180",
            "values": [
                [("6.9", "0.06", "f"), ("3.2", "0.14", "f"), ("4.4", "0.08", "d"), ("3.2", "0.14", "d"), ("9.9", "0.73", "e"), ("1.3", "0.00", "a"), ("5.0", "0.03", "a"), ("1.1", "0.02", "e")],
                [("11.1", "0.23", "e"), ("4.9", "0.42", "e"), ("9.4", "0.34", "c"), ("4.9", "0.42", "d"), ("13.5", "0.29", "d"), ("1.2", "0.15", "ab"), ("4.8", "0.10", "b"), ("2.1", "0.22", "d")],
                [("15.1", "0.27", "d"), ("6.5", "0.05", "d"), ("13.9", "0.41", "b"), ("6.5", "0.05", "b"), ("16.4", "0.38", "c"), ("1.3", "0.02", "a"), ("3.7", "0.03", "c"), ("3.8", "0.08", "c")],
                [("20.8", "0.51", "c"), ("8.7", "0.05", "c"), ("20.1", "0.61", "a"), ("4.7", "0.01", "c"), ("21.5", "0.83", "b"), ("1.2", "0.06", "b"), ("3.0", "0.03", "d"), ("5.3", "0.18", "a")],
                [("25.9", "0.84", "b"), ("10.8", "0.11", "b"), ("25.7", "1.33", "a"), ("2.1", "0.86", "d"), ("26.4", "0.40", "a"), ("0.9", "0.01", "c"), ("3.2", "0.07", "d"), ("4.7", "0.16", "b")],
                [("29.8", "0.29", "a"), ("12.5", "0.76", "a"), ("16.8", "0.05", "e"), ("1.0", "0.24", "e"), ("20.7", "1.15", "b"), ("0.7", "0.01", "d"), ("2.9", "0.16", "e"), ("2.4", "0.19", "d")],
            ],
        },
    }
    for table_number, table in tables.items():
        for (ash_fraction, media), values in zip(fermentation_cases, table["values"], strict=True):
            condition = (
                f"{media}; {table['vessel']}; 30°C for {table['duration']}; {table['pH_schedule']}; "
                "Lactococcus lactis KF147."
            )
            for (metric, unit, basis), (value, sd, group) in zip(FERMENTATION_METRICS, values, strict=True):
                rows.append(_make_row(
                    f"ZHOU23-T{table_number}-ASH{ash_fraction}-{metric.upper()}", "5",
                    f"§4.4.5, Table 4.{table_number}", "lactic-acid fermentation of alfalfa pulp hydrolysate and brown juice",
                    metric, value, unit, basis, condition,
                    f"SD={sd}; Fisher LSD group={group} (p<0.05)",
                    f"{table['page']}; fermentation methods §4.3.4.3, printed pp. 88–89",
                ))

    if len(rows) != 207 or len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Unexpected Zhou detailed alfalfa reference record count or duplicate IDs")
    return rows


def _number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    _write(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    numeric_rows = sum(_number(row["value"]) for row in rows)
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:pre-treatment:zhou-2023-alfalfa-detailed-sugar-platform:v1",
        "dataset_version": "1.0.0",
        "persistent_identifier_status": "Repository-local URN identifies this derived transcription. The thesis is identified by the DTU Orbit record; related peer-reviewed article DOI is recorded as a qualified cross-reference.",
        "title": "Alfalfa pressing, pulp pretreatment and brown-juice fermentation table observations",
        "source_id": SOURCE_ID,
        "citation": f"Zhou, F. (2023). {TITLE}. PhD thesis, Technical University of Denmark. Related article: Zhou, F. et al. (2024). Development of a sugar platform and fermentation media from residues from alfalfa biorefining. Industrial Crops and Products, 209, 117927. {ARTICLE_URL}",
        "doi": DOI,
        "source_url": PDF_URL,
        "repository_record": RECORD_URL,
        "related_article_url": ARTICLE_URL,
        "retrieval_date": RETRIEVED,
        "source_locations": [
            "Table 4.1, printed p. 90; PDF extracted-text lines 1733–1749",
            "Table 4.2, printed p. 92; PDF extracted-text lines 1762–1873",
            "Table 4.3, printed p. 102; PDF extracted-text lines 2005–2088",
            "Table 4.4, printed p. 104; PDF extracted-text lines 2097–2180",
            "Methods §4.3.3–4.3.6, printed pp. 87–90",
        ],
        "geography": "Technical University of Denmark research; alfalfa harvested by Biotest ApS, Middelfart, Denmark, as described in the thesis materials section.",
        "material_scope": "Cultivated alfalfa pulp from twin-screw fractionation, and alfalfa-derived hydrolysate/brown juice used in laboratory fermentation.",
        "license_or_rights": "No explicit reuse license identified for the thesis or extracted tables. The DOI cross-reference identifies a peer-reviewed article but does not establish a reuse license for thesis table transcription; verify rights before external redistribution.",
        "evidence_class": "B_primary_thesis_experimental_table_means_and_SD",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "numeric_row_count": numeric_rows,
        "sha256_csv": digest,
        "transcription_policy": "Transcribe Table 4.1–4.4 values, SDs, significance groups, source ranges and explicitly stated conditions. Preserve source dash and 'na' cells as non-applicable text; do not impute, normalize to GreenHub feed, or combine the independent laboratory fermentation configurations.",
        "statistical_metadata": "The thesis states analytical results used at least biological replicates and reports mean ± SD with Fisher LSD at p<0.05. Exact replicate count is not reported; no n is inferred.",
        "limitations": [
            "Alfalfa is a cultivated comparator crop, not Dutch roadside/VARTA grass or GreenHub process feed.",
            "Table 4.1 does not further specify the moisture-percent basis. Its raw-feed pulp-recovery cell is a source dash, retained as non-applicable; the two pressing-stage recoveries are transcribed without recalculation.",
            "Table 4.1 temperature values are ranges at the end of the process steps, not point setpoints or continuous profiles.",
            "Table 4.2 solid-recovery denominator is not separately stated in its caption; the reported value is preserved without recalculation.",
            "Table 4.2 composition is explicitly % of dry matter; color coordinates are not compositional fractions.",
            "The exact biological replicate count is not reported. Standard deviations and Fisher LSD grouping letters are preserved as published.",
            "Pretreatment uses sodium chlorite and long batch drying/washing steps not established as GreenHub route operations; these data do not provide a GreenHub chemical-treatment recipe or energy balance.",
            "Tables 4.3 and 4.4 are separate fermentation configurations (sealed bottle, 14 h, pH adjusted every 2 h; versus shake flask, 48 h, pH adjusted every 6 h). They are not continuous-process performance or anaerobic-digestion yields.",
            "The article abstract contains some overlapping endpoints; this extract adds press-series composition, full table uncertainties, pretreatment dose-response details, additional media levels and fermentation coproducts. Overlapping values are not treated as independent experiments.",
            "No GreenHub runtime parameters, process defaults, route chemistry, TEA/LCA factors or Pareto results consume this dataset.",
            "No explicit thesis-table reuse license was identified; check publisher and institutional terms before redistribution.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _upsert(FOLDER / "source_register.csv", "source_id", [{
        "source_id": SOURCE_ID, "source_type": "doctoral thesis; experimental table transcription",
        "title": TITLE, "authors": AUTHORS, "year": "2023", "doi_or_stable_identifier": DOI,
        "publisher": "Technical University of Denmark; related article: Industrial Crops and Products",
        "url": PDF_URL, "material_scope": "Cultivated alfalfa pulp, alfalfa sugar hydrolysate and brown juice",
        "source_quality": "Primary thesis tables with means, SD and Fisher LSD groups; related peer-reviewed article DOI cross-reference.",
        "access_date": RETRIEVED,
        "notes": "Tables 4.1–4.4 from the DTU thesis. Exact replicate count is not reported. Reference-only, not GreenHub roadside-grass calibration. No explicit data-reuse license identified.",
    }])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "dataset_id": "DS-TE-ZHOU23-DETAIL-001", "filename": FILENAME,
        "purpose": "Table 4.1 raw/pressed alfalfa composition and pulp recovery; Table 4.2 sodium-chlorite dose response; Tables 4.3–4.4 alfalfa-hydrolysate/brown-juice fermentation; Phases 1, 3 and 5 comparator.",
        "row_count": str(len(rows)), "primary_key": "record_id", "encoding": "UTF-8",
        "delimiter": ",", "integration_readiness": "reference_only_D3",
        "known_limitations": "Cultivated alfalfa; laboratory route; exact replicate n and explicit reuse license not identified; not GreenHub calibration or runtime input.",
    }])

    rel = f"Pre-treatment/Thermal_Enzymatic/{FILENAME}"
    source_entry = {
        "dataset_path": rel, "dataset_group": "Pre-treatment/Thermal_Enzymatic", "source_id": SOURCE_ID,
        "source_title": TITLE, "authors": AUTHORS, "year": "2023", "doi_or_stable_id": DOI,
        "url": PDF_URL, "source_type": "doctoral thesis; experimental table transcription",
        "notes": "DTU thesis Tables 4.1–4.4; DOI is a related peer-reviewed article cross-reference. B-tier, reference-only; cultivated alfalfa, not GreenHub feed; no explicit reuse license identified.",
    }
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [source_entry])
    group = "alfalfa feed/press series, sodium-chlorite pretreatment and sugar fermentation; Phases 1, 3 and 5"
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": group,
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Thesis Table 4.1–4.4 values, SDs and significance groups; source dash/na and temperature ranges retained; distinct laboratory conditions; no runtime mapping.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": group,
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
        "numeric_rows": str(numeric_rows), "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0", "basis_conflicts": "0",
        "cross_reference_issues": "0", "equation_missing_inputs": "0", "equation_symbol_mismatches": "0",
        "notes": "Numeric measurements have table/page locations; SD and Fisher LSD groups retained; source dash/na cells are non-applicable, not zero; three reported temperature ranges remain strings.",
    }])
    checksums = [
        {"dataset_path": f"Pre-treatment/Thermal_Enzymatic/{path.name}",
         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "byte_size": str(path.stat().st_size)}
        for path in (CSV_PATH, SIDECAR_PATH)
    ]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)
    _upsert(AUDIT / "dataset_activation_matrix.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Pre-treatment", "subgroup": group,
        "audit_readiness": "D3", "integration_eligibility": "reference_only",
        "default_eligibility": "False", "calculation_connected": "False", "active": "False",
        "source_issue_count": "0", "quarantine_row_count": "0", "issue_types": "none",
        "cost_pathway_status": "not_applicable",
        "selection_reason": "Traceable thesis table data are useful laboratory comparators but do not validate GreenHub roadside feed or its configured route.",
        "required_action": "Obtain matched GreenHub feed and unit-operation data, reconcile applicable bases, and pass equation-specific tests before activation.",
        "source_checksum_sha256": digest,
    }])

    activation_path = AUDIT / "dataset_activation_matrix.csv"
    _, activation = _read(activation_path)
    eligibility_counts: dict[str, int] = {}
    for item in activation:
        key = item.get("integration_eligibility", "")
        eligibility_counts[key] = eligibility_counts.get(key, 0) + 1
    registry_summary_path = AUDIT / "checkpoint1_registry_summary.json"
    registry_summary = json.loads(registry_summary_path.read_text(encoding="utf-8"))
    registry_summary.update(
        source_dataset_count=len(activation),
        dataset_eligibility_counts=dict(sorted(eligibility_counts.items())),
        active_dataset_count=sum(item.get("active") == "True" for item in activation),
        default_eligible_dataset_count=sum(item.get("default_eligibility") == "True" for item in activation),
        source_checksum_count=sum(bool(item.get("source_checksum_sha256")) for item in activation),
    )
    registry_summary_path.write_text(json.dumps(registry_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read(AUDIT / "global_dataset_readiness.csv")
    readiness_counts: dict[str, int] = {}
    for item in readiness:
        key = item.get("readiness", "")
        readiness_counts[key] = readiness_counts.get(key, 0) + 1
    summary.update(
        dataset_count=len(manifests), readiness_counts=readiness_counts,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "dataset": str(CSV_PATH), "rows": len(rows), "numeric_rows": numeric_rows,
        "non_numeric_rows": len(rows) - numeric_rows, "sha256": digest,
    }, indent=2))


if __name__ == "__main__":
    main()
