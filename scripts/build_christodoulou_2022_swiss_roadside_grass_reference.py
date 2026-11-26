"""Build a traceable, reference-only extract of the Swiss MéthaRoad study.

The extract preserves reported sample-level BMP data, grouped contaminant
results, and explicitly separate author-estimated national supply scenarios.
It is not a Dutch/GreenHub feedstock calibration and never changes defaults.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
GROUP = DATA / "Bigas production + upgrade" / "Feed BMP"
FILENAME = "roadside_grass_bmp_seasonal_contamination_christodoulou_2022_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-ARAMIS-METHAROAD-SI502089-2022"
PROJECT_ID = "SI/502089-01"
PROJECT_URL = "https://www.aramis.admin.ch/Texte/?ProjectID=47377"
REPORT_URL = "https://www.aramis.admin.ch/Dokument.aspx?DocumentID=68742"
RETRIEVAL_DATE = date.today().isoformat()

FIELDS = [
    "observation_id", "source_id", "phase", "experiment_id", "material",
    "process_step", "metric", "reported_value", "numeric_value", "lower_bound",
    "upper_bound", "unit", "basis", "condition", "sample_count",
    "reported_uncertainty", "source_location", "evidence_class",
    "activation_state", "applicability", "limitations",
]

TRANSFER_LIMIT = (
    "Swiss roadside-grass comparator sampled at selected Vaud road locations; "
    "not Dutch VARTA/GreenHub grass. No runtime parameter or default inference."
)
ROWS: list[dict[str, str]] = []


def add(
    observation_id: str,
    phase: str,
    experiment_id: str,
    material: str,
    process_step: str,
    metric: str,
    reported_value: str,
    *,
    numeric_value: float | int | str = "",
    lower_bound: float | int | str = "",
    upper_bound: float | int | str = "",
    unit: str = "",
    basis: str = "",
    condition: str = "",
    sample_count: str = "",
    reported_uncertainty: str = "",
    source_location: str = "",
    evidence_class: str = "B_measured_literature_observation",
    limitations: str = TRANSFER_LIMIT,
) -> None:
    ROWS.append({
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
        "sample_count": sample_count,
        "reported_uncertainty": reported_uncertainty,
        "source_location": source_location,
        "evidence_class": evidence_class,
        "activation_state": "reference_only",
        "applicability": TRANSFER_LIMIT,
        "limitations": limitations,
    })


# Table 1: triplicate batch BMP values by roadside type and sampling campaign.
# The report prints ± values but does not identify SD vs SE; do not relabel.
BMP = {
    "RC604": ((55.2, 6.7, 345.2, 42.0), (63.4, 8.4, 342.1, 45.3)),
    "RC601B": ((113.7, 13.9, 422.5, 51.8), (110.4, 9.6, 349.8, 30.3)),
    "RC601H": ((95.6, 1.3, 392.6, 5.4), (95.6, 6.7, 339.1, 23.8)),
    "LA_VEYRE_INTENSIVE": ((64.5, 1.6, 315.9, 8.0), (90.8, 10.1, 312.4, 34.7)),
    "LA_VEYRE_TALUS_PLAT": ((86.8, 5.9, 414.2, 28.1), (120.7, 11.8, 337.4, 33.0)),
}
ROUTE_LABELS = {
    "RC604": "low-traffic cantonal road, flat extensive verge",
    "RC601B": "high-traffic cantonal road, descending slope",
    "RC601H": "high-traffic cantonal road, ascending slope",
    "LA_VEYRE_INTENSIVE": "motorway junction, intensive maintenance zone",
    "LA_VEYRE_TALUS_PLAT": "motorway junction, flat extensive verge",
}
CAMPAIGNS = ("June 2021", "September 2021")
for route, campaign_results in BMP.items():
    for campaign_index, values in enumerate(campaign_results):
        campaign = CAMPAIGNS[campaign_index]
        fresh_mean, fresh_pm, om_mean, om_pm = values
        for metric, mean, pm, unit, basis in (
            ("batch biochemical methane potential", fresh_mean, fresh_pm,
             "NL CH4 kg-1 fresh matter", "fresh matter"),
            ("batch biochemical methane potential", om_mean, om_pm,
             "NL CH4 kg-1 organic matter", "organic matter"),
        ):
            basis_id = "FM" if basis == "fresh matter" else "OM"
            add(
                f"METHAROAD-BMP-{route}-{campaign_index + 1}-{basis_id}", "5",
                f"{route}-{campaign_index + 1}", f"roadside grass; {ROUTE_LABELS[route]}",
                "mesophilic batch BMP", metric,
                f"{mean:g} ± {pm:g}", numeric_value=mean, unit=unit, basis=basis,
                condition=(f"{campaign}; three replicates; frozen at -20 °C before assay; "
                           "inoculum from Yverdon wastewater-treatment plant; 37 °C; "
                           "automated volumetric system"),
                sample_count="n=3",
                reported_uncertainty=f"± {pm:g}; statistic type not stated in report",
                source_location="Report Table 1, report p.25 (PDF p.25)",
                limitations=(TRANSFER_LIMIT + " BMP is batch potential, not continuous AD yield. "
                             "The source labels gas volume NL but does not state the exact reference "
                             "temperature/pressure in the table. Route/campaign aggregates are not raw replicates."),
            )

# Study-level feed composition summaries. The DM ranges are explicitly broad
# figure/text ranges, not digitized site means.
for campaign, low, high in (("June 2021", 20, 30), ("September 2021", 20, 40)):
    add(
        f"METHAROAD-TS-RANGE-{campaign.split()[0].upper()}", "1;5",
        f"campaign-{campaign.split()[0].lower()}", "roadside grass; five Vaud sampling points",
        "field sampling", "total solids range", f"approximately {low}–{high}%",
        lower_bound=low, upper_bound=high, unit="% fresh matter", basis="fresh matter",
        condition=campaign, sample_count="5 points; triplicate sampling described",
        source_location="Report Summary and §2.1, report pp.3 and 22 (PDF pp.3 and 22)",
        limitations=(TRANSFER_LIMIT + " Broad reported range only; Figure 13 was not digitized into "
                     "site-level values. Weather differed between campaigns (wet June, dry September)."),
    )

# Reported C:N ranges include an internal contradiction for the first campaign;
# retain both statements rather than select or average them.
for observation_id, campaign, low, high, location, note in (
    ("METHAROAD-CN-JUNE-SUMMARY", "June 2021", 21, 40,
     "Report Summary §2.1, report p.24 (PDF p.23)", "Summary statement."),
    ("METHAROAD-CN-SEPTEMBER-SUMMARY", "September 2021", 16, 31,
     "Report Summary §2.1, report p.24 (PDF p.23)", "Summary statement."),
    ("METHAROAD-CN-JUNE-CONFLICT", "June 2021", 16, 32,
     "Results §2.1, report p.24 (PDF p.23)",
     "Conflicts with the same report's earlier June range of 21–40; both are preserved."),
):
    add(
        observation_id, "1;5", f"campaign-{campaign.split()[0].lower()}",
        "roadside grass; five Vaud sampling points", "field sampling", "carbon-to-nitrogen ratio",
        f"{low}:1–{high}:1", lower_bound=low, upper_bound=high, unit="dimensionless C:N",
        basis="dry-matter elemental analysis; ratio source-reported", condition=campaign,
        sample_count="5 points", source_location=location,
        limitations=TRANSFER_LIMIT + " " + note + " Figure 14 was not digitized into point estimates.",
    )

# Macroplastic table: preserve every route/campaign cell. Dashes are not
# converted to zero or asserted as a quantitative non-detect.
MACROPLASTICS = {
    "RC604": (None, None),
    "RC601B": ((990, "9.0 × 2.5 cm", "3.31%"),
                (60, "multiple pieces; sizes listed in source table", "0.19%")),
    "RC601H": (None, (10, "0.9 × 0.2 × 0.2 cm", "0.03%")),
    "LA_VEYRE_INTENSIVE": (None, (1500, "many pieces of different sizes", "4.98%")),
    "LA_VEYRE_TALUS_PLAT": (None, None),
}
for route, pair in MACROPLASTICS.items():
    for index, result in enumerate(pair):
        campaign = CAMPAIGNS[index]
        if result is None:
            add(
                f"METHAROAD-MACROPLASTIC-{route}-{index + 1}", "1;7",
                f"{route}-{index + 1}", f"roadside grass; {ROUTE_LABELS[route]}",
                "manual extraction", "macroplastic (>5 mm) mass", "table dash; no numeric result",
                unit="mg", basis="source does not define denominator for reported mass/percentage",
                condition=campaign, sample_count="not specified per result",
                source_location="Report Table 2, report p.27 (PDF p.26)",
                limitations=TRANSFER_LIMIT + " A dash is preserved as unreported/not found in the table, not zero.",
            )
            continue
        mass, size, percentage = result
        add(
            f"METHAROAD-MACROPLASTIC-{route}-{index + 1}", "1;7",
            f"{route}-{index + 1}", f"roadside grass; {ROUTE_LABELS[route]}",
            "manual extraction", "macroplastic (>5 mm) mass",
            f"{mass} mg; source also prints {percentage}; size: {size}", numeric_value=mass,
            unit="mg", basis="source does not define denominator for reported mass/percentage",
            condition=campaign, sample_count="not specified per result",
            source_location="Report Table 2, report p.27 (PDF p.26)",
            limitations=(TRANSFER_LIMIT + " The source percentage denominator is unclear; the mass "
                         "is transcribed without conversion or compliance interpretation."),
        )

# Microplastic table (<50 µm). Source ATG interpretation is uncertain for some
# samples; the source's masses are retained, but not converted into a feed factor.
MICROPLASTICS = {
    "RC604": (None, None),
    "RC601B": (None, None),
    "RC601H": (None, (0.06, "0.0002%")),
    "LA_VEYRE_INTENSIVE": (None, (6.15, "0.02%")),
    "LA_VEYRE_TALUS_PLAT": ((6.26, "0.021%"), (0.66, "0.002%")),
}
for route, pair in MICROPLASTICS.items():
    for index, result in enumerate(pair):
        campaign = CAMPAIGNS[index]
        if result is None:
            add(
                f"METHAROAD-MICROPLASTIC-{route}-{index + 1}", "1;7",
                f"{route}-{index + 1}", f"roadside grass; {ROUTE_LABELS[route]}",
                "extraction and thermogravimetric screening", "microplastic (<50 µm) mass",
                "table dash; no numeric result", unit="mg",
                basis="source does not define mass denominator for reported percentage",
                condition=campaign, source_location="Report Table 3, report p.30 (PDF p.29)",
                limitations=(TRANSFER_LIMIT + " Dash is not zero. Source states that some ATG peaks "
                             "were not clear enough to confirm plastic identity."),
            )
            continue
        mass, percentage = result
        add(
            f"METHAROAD-MICROPLASTIC-{route}-{index + 1}", "1;7",
            f"{route}-{index + 1}", f"roadside grass; {ROUTE_LABELS[route]}",
            "extraction and thermogravimetric screening", "microplastic (<50 µm) mass",
            f"{mass:g} mg; source also prints {percentage}", numeric_value=mass,
            unit="mg", basis="source does not define mass denominator for reported percentage",
            condition=campaign, source_location="Report Table 3, report p.30 (PDF p.29)",
            limitations=(TRANSFER_LIMIT + " Some ATG peaks were not clear enough to confirm plastic "
                         "identity; source percentages are preserved in text only."),
        )

# PAH results are reported as below the listed threshold for each site/campaign.
# Keep them as censored observations (upper bounds), never as zero.
for route in ROUTE_LABELS:
    for index, campaign in enumerate(CAMPAIGNS):
        for analyte, limit in (("total 16 EPA-listed PAHs", 1.0), ("benzo[a]pyrene", 0.20)):
            add(
                f"METHAROAD-PAH-{route}-{index + 1}-{analyte.split()[0].upper()}", "1;7",
                f"{route}-{index + 1}", f"roadside grass; {ROUTE_LABELS[route]}",
                "GC-MS contamination analysis", analyte, f"< {limit:g} ppm",
                upper_bound=limit, unit="ppm", basis="mass basis not specified in the report",
                condition=f"{campaign}; sample dried at 40 °C and ground before analysis",
                sample_count="3 field replicates per site/campaign described; table is grouped",
                source_location="Report Table 6, report p.35 (PDF p.34)",
                limitations=(TRANSFER_LIMIT + " Censored at the report's listed result threshold; "
                             "not zero and not a Dutch fertilizer-compliance result."),
            )

# Laboratory limits and broad/grouped metal findings. Zinc's exact site values
# conflict with a general statement that it was below the laboratory LOQ.
METAL_LOQ = {"Hg": 0.5, "Pb": 2.5, "Cd": 0.0005, "Cu": 2.5, "Ni": 2.5, "Zn": 2.5}
for metal, loq in METAL_LOQ.items():
    add(
        f"METHAROAD-METAL-LOQ-{metal}", "1;7", "laboratory-method", "roadside grass",
        "metal analysis", f"laboratory quantification limit ({metal})", f"{loq:g} ppm",
        numeric_value=loq, unit="ppm", basis="sample basis not explicitly stated; samples dried at 40 °C",
        condition="Hg by ICP-OES; Pb/Cu/Ni/Zn by ICP-OES; Cd by ICP-MS",
        source_location="Report §1.8/Table 4, report pp.21 and 33 (PDF pp.20 and 32)",
        limitations=TRANSFER_LIMIT + " Analytical LOQ, not a measured grass concentration or regulatory limit.",
    )

for metal in ("Hg", "Pb", "Cu", "Ni"):
    add(
        f"METHAROAD-METAL-CENSORED-{metal}", "1;7", "all-site-campaign-summary", "roadside grass",
        "metal analysis", f"{metal} concentration", f"below laboratory LOQ ({METAL_LOQ[metal]:g} ppm)",
        upper_bound=METAL_LOQ[metal], unit="ppm",
        basis="sample basis not explicitly stated; samples dried at 40 °C",
        condition="report says results for both campaigns were below LOQ",
        sample_count="30 field samples planned (5 sites × 3 replicates × 2 campaigns)",
        source_location="Report §2.3, report p.33 (PDF p.32)",
        limitations=TRANSFER_LIMIT + " Censored source statement, not zero; source does not provide sample-level values.",
    )

for group, low, high in (("other reported sites", 0.02, 0.03),
                         ("La Veyre intensive zone", 0.008, 0.018),
                         ("La Veyre talus-plat", 0.05, 0.07)):
    add(
        f"METHAROAD-CD-{group.upper().replace(' ', '-')}", "1;7", "grouped-cadmium-results",
        f"roadside grass; {group}", "ICP-MS metal analysis", "cadmium concentration range",
        f"approximately {low:g}–{high:g} ppm", lower_bound=low, upper_bound=high,
        unit="ppm", basis="sample basis not explicitly stated; samples dried at 40 °C",
        condition="both campaigns; report prose summary; all values stated below the 1 ppm limit",
        source_location="Report §2.3, report p.34 (PDF p.33)",
        limitations=TRANSFER_LIMIT + " Grouped text range, not site-by-site paired observations.",
    )

for campaign, mean, pm in (("June 2021", 3.454, 0.23), ("September 2021", 5.767, 0.46)):
    add(
        f"METHAROAD-ZN-LA-VEYRE-INTENSIVE-{campaign.split()[0].upper()}", "1;7",
        f"LA_VEYRE_INTENSIVE-{campaign}", "roadside grass; La Veyre intensive motorway zone",
        "ICP-OES metal analysis", "zinc concentration", f"{mean:g} ± {pm:g} ppm",
        numeric_value=mean, unit="ppm", basis="sample basis not explicitly stated; samples dried at 40 °C",
        condition=campaign, sample_count="n=3",
        reported_uncertainty=f"± {pm:g}; statistic type not specified",
        source_location="Report §2.3/Figure 21 text, report p.33 (PDF p.32)",
        limitations=(TRANSFER_LIMIT + " The report's specific values exceed its listed Zn LOQ of 2.5 ppm, "
                     "contradicting its broad statement that Zn was below LOQ; preserve, do not censor or reconcile."),
    )

add(
    "METHAROAD-ZN-LOQ-CONFLICT", "1;7", "all-site-campaign-summary", "roadside grass",
    "metal analysis", "zinc below-LOQ general statement",
    "report states all Zn results were below 2.5 ppm LOQ; later reports 3.454 and 5.767 ppm at La Veyre intensive",
    unit="ppm", basis="source text conflict", sample_count="all sites/campaigns",
    source_location="Report §2.3, report pp.33–34 (PDF pp.32–33)",
    limitations=TRANSFER_LIMIT + " Conflicting statements retained; neither substituted for the two specific site values.",
)

# Table 8 is a report-level modeling summary, not a new calibration set.
for metric, value, unit, basis, note in (
    ("total solids", 29, "% fresh matter", "fresh matter", "Report says mean across five points and two campaigns."),
    ("organic matter", 87, "% dry matter", "dry matter", "Report says mean across five points and two campaigns."),
    ("methane yield used for national estimate", 350, "Nm3 CH4 t-1 organic matter", "organic matter", "Report-selected/conservative summary; do not treat as a raw replicate mean."),
    ("biogas yield used for national estimate", 600, "Nm3 biogas t-1 organic matter", "organic matter", "Approximate report summary; gas composition also summarized as 55% methane."),
    ("methane fraction used for national estimate", 55, "% biogas", "biogas volume", "Report-level summary, not a measured GreenHub gas specification."),
):
    add(
        f"METHAROAD-TABLE8-{metric.upper().replace(' ', '-').replace('/', '-')}", "1;5",
        "study-level-input-summary", "roadside grass; selected Vaud locations", "report synthesis",
        metric, str(value), numeric_value=value, unit=unit, basis=basis,
        source_location="Report Table 8, report p.37 (PDF p.36)",
        evidence_class="B_reported_literature_summary",
        limitations=TRANSFER_LIMIT + " Study synthesis only; keep distinct from sample-level Table 1 observations." + " " + note,
    )

# Phase 1 national resource numbers are explicitly study estimates, not measured
# biomass supply. The source itself says the estimate is highly uncertain.
for observation_id, metric, reported, numeric, low, high, unit, location, note in (
    ("METHAROAD-ESTIMATED-ROAD-YIELD-RATIO", "potential harvested grass per total road km per year",
     "2–3 t fresh matter per total road-km per year", "", 2, 3,
     "t fresh matter km-1 total road yr-1", "Report §2.5, report p.36 (PDF p.35)",
     "Author-selected ratio compiled from equipment-provider experience, neighboring-country pilots and agronomic yield references; not a measured Swiss roadside yield."),
    ("METHAROAD-ESTIMATED-SWISS-ROAD-GRASS-LOW", "estimated potentially harvestable national road grass",
     "39,000 t fresh matter per year", 39000, "", "", "t fresh matter yr-1",
     "Report Table 7, report p.37 (PDF p.36)",
     "National/cantonal road estimate derived using the study's 2–3 t/km/year ratio; not contracted or accessible feedstock."),
    ("METHAROAD-ESTIMATED-SWISS-ROAD-GRASS-HIGH", "estimated potentially harvestable national road grass",
     "58,000 t fresh matter per year", 58000, "", "", "t fresh matter yr-1",
     "Report Table 7, report p.37 (PDF p.36)",
     "National/cantonal road estimate derived using the study's 2–3 t/km/year ratio; not contracted or accessible feedstock."),
    ("METHAROAD-OFS-NATIONAL-ROAD-LENGTH", "national road length used in estimate", "2,255 km", 2255,
     "", "", "km", "Report Table 7, report p.37 (PDF p.36)", "OFS 2021 statistic reproduced by study."),
    ("METHAROAD-OFS-CANTONAL-ROAD-LENGTH", "cantonal road length used in estimate", "17,219 km", 17219,
     "", "", "km", "Report Table 7, report p.37 (PDF p.36)", "OFS 2021 statistic reproduced by study."),
):
    add(
        observation_id, "1", "Swiss national estimate", "roadside grass; Swiss national/cantonal roads",
        "resource potential estimation", metric, reported, numeric_value=numeric,
        lower_bound=low, upper_bound=high, unit=unit,
        basis="author-estimated national potential; not a measured harvest or accessible supply",
        source_location=location, evidence_class="C_literature_based_author_estimate",
        limitations=(TRANSFER_LIMIT + " " + note + " Not a Netherlands or GreenHub availability input."),
    )


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def append_once(path: Path, row: dict[str, object], key: str) -> None:
    fields, existing = read_csv(path)
    matches = [item for item in existing if item.get(key) == str(row.get(key, ""))]
    if matches:
        if len(matches) != 1:
            raise ValueError(f"Duplicate registration for {row.get(key)} in {path}")
        changed = [field for field in fields if matches[0].get(field, "") != str(row.get(field, ""))]
        if changed:
            raise ValueError(f"Conflicting registration for {row.get(key)} in {path}: {changed}")
        return
    with path.open("a", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore").writerow(
            {field: row.get(field, "") for field in fields}
        )


def main() -> None:
    if len({row["observation_id"] for row in ROWS}) != len(ROWS):
        raise ValueError("Observation IDs must be unique")
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()

    title = "MéthaRoad - Valorisation de la biomasse des fauches des bords des routes dans des installations de biogaz"
    authors = "Xenia Christodoulou; Elise Moatti"
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:feed-bmp:christodoulou-aramis-metharoad-2022-reference:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": f"Christodoulou, X., & Moatti, E. (2022). {title}. Swiss Federal Office of Energy final report, contract {PROJECT_ID}.",
        "publication_year": 2022,
        "report_date": "2022-02-28",
        "project_identifier": PROJECT_ID,
        "persistent_identifier": "Swiss ARAMIS project SI/502089; no DOI identified",
        "doi": "",
        "source_url": PROJECT_URL,
        "full_text_url": REPORT_URL,
        "retrieval_date": RETRIEVAL_DATE,
        "geography": "Selected roadside locations in Canton of Vaud, Switzerland; not a representative Dutch/GreenHub sample.",
        "material_scope": "Roadside grass at five road/verge types sampled in June and September 2021; triplicate BMP and contaminant analyses; national resource estimates are separate author scenarios.",
        "quality_class": "B for measured or directly reported study observations; C for author-estimated national resource potential",
        "license": "No explicit open reuse license identified on the ARAMIS page or report during retrieval. Factual observations are transcribed with attribution for internal research traceability; verify redistribution and commercial reuse rights.",
        "data_availability": "Official 47-page final report available through Swiss federal ARAMIS; no raw replicate data package identified.",
        "data_structure": "Long-form CSV separates sample/site/campaign, mean and printed uncertainty, censored values, report-level summaries, and C-class national estimates. Blank numeric cells are not zero. Source locations refer to report page and PDF page.",
        "phase_coverage": {
            "1": "Vaud roadside type/campaign sampling, reported seasonal solids/C:N ranges, macro/microplastic contamination and explicitly author-estimated Swiss resource scenarios; no Dutch accessible supply.",
            "2": "Two seasonal sampling dates only; no controlled storage duration, aerobic/anaerobic degradation kinetics or storage emissions.",
            "3": "No GreenHub pretreatment, pressing, extraction, water addition or separation data.",
            "4": "No protein extraction, product quality or drying data.",
            "5": "Triplicate mesophilic batch BMP by route/campaign and a report-level digester integration estimate; no continuous GreenHub residual AD calibration.",
            "6": "No gas upgrading, methane recovery/slip or upgrader utility observations.",
            "7": "Feed contamination and selected metal/PAH screening relevant to digestate/fertilizer quality; digestate HAP results were not measured and this is not nutrient recovery or fertilizer substitution evidence."
        },
        "limitations": [
            "Sampling is from five selected road/verge types in Vaud, Switzerland; it is not a representative national or Dutch roadside survey.",
            "Campaigns differed in weather and cutting equipment; June motorway samples followed heavy rain, while September sampling followed dry weather.",
            "BMP is batch potential at 37 °C using wastewater-treatment sludge inoculum, not continuous digester performance; printed ± values have no identified statistic type and NL reference conditions are not fully specified.",
            "The report's C:N narrative gives conflicting first-campaign ranges (21–40 and 16–32); both are retained.",
            "The report's zinc narrative says values were below 2.5 ppm LOQ but separately reports 3.454 and 5.767 ppm for La Veyre intensive; both statements are retained without reconciliation.",
            "PAH and general metal non-detects are censored and not zero. Mass bases are not consistently stated.",
            "Macroplastic table percentages have an unclear denominator; values are not converted into concentration or regulatory-compliance factors.",
            "The 2–3 t fresh matter per total road-km/year factor and Swiss national annual tonnage are author estimates compiled from secondary sources; not measured, accessible, contracted, or GreenHub feedstock.",
            "No explicit open reuse license was identified; review rights before external redistribution or commercial reuse."
        ],
        "conversion_or_processing": "Direct transcription from report tables/text; no figure digitization, unit conversion, extrapolation to GreenHub, imputation, or fitted model.",
        "uncertainty": "Printed ± values are retained without SD/SE interpretation; grouped ranges and censored bounds stay explicit; author-estimated supply bounds are not statistical confidence intervals.",
        "runtime_policy": "Reference-only; not connected to parameter registry, model defaults, route calculations, TEA/LCA, scenario generation, or Pareto results.",
        "access_protocol": "HTTPS ARAMIS project metadata page and final-report PDF; stable project identifier recorded; no DOI identified.",
        "fair_metadata": {
            "findable": "Local URN, stable Swiss ARAMIS project identifier, catalog-indexed dataset, title/authors/year, and SHA-256.",
            "accessible": "HTTPS project and report links; access is open through the federal ARAMIS portal, while reuse rights remain unverified.",
            "interoperable": "UTF-8 CSV using the GreenHub long-form observation schema with phases, units, bases, censoring bounds, and source locations.",
            "reusable": "Citation, retrieval date, geography, methods, row-level evidence classes, uncertainty, limitations, and explicit runtime exclusion are included."
        }
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID, "source_title": title, "authors": authors, "year": "2022",
        "doi_or_stable_id": PROJECT_ID,
        "source_type": "Swiss Federal Office of Energy final report; primary roadside sampling and laboratory study",
        "url": REPORT_URL,
        "material_scope": sidecar["material_scope"],
        "quality_notes": "B-tier measured Vaud roadside BMP/contamination observations; C-tier Swiss national potential estimates are separately labeled. No DOI/license identified; reference-only and not GreenHub-specific."
    }
    append_once(GROUP / "source_register.csv", local_source, "source_id")
    append_once(GROUP / "ad_source_register.csv", local_source, "source_id")
    append_once(GROUP / "dataset_manifest.csv", {
        "filename": FILENAME,
        "description": "Vaud roadside-grass seasonal BMP, solids/C:N summaries, censored contaminant observations, and separately labeled Swiss resource estimates; reference-only.",
        "row_count": len(ROWS), "schema_version": "1.0", "encoding": "UTF-8 with BOM",
        "delimiter": ",", "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "observation_id",
    }, "filename")

    relative_path = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
    audit = DATA / "global_audit_package"
    append_once(audit / "global_source_register.csv", {
        "dataset_path": relative_path, "dataset_group": "Feed BMP", "source_id": SOURCE_ID,
        "source_title": title, "authors": authors, "year": "2022",
        "doi_or_stable_id": PROJECT_ID, "url": REPORT_URL,
        "source_type": "Swiss Federal Office of Energy final report; primary roadside sampling and laboratory study",
        "notes": "Cross-phase comparator for Phases 1, 5 and 7. B-tier sample observations and C-tier national estimate kept separate; Vaud, Switzerland; no runtime activation."
    }, "dataset_path")
    append_once(audit / "global_dataset_manifest.csv", {
        "dataset_path": relative_path, "category": "Bigas production + upgrade", "subgroup": "Feed BMP",
        "filename": FILENAME, "row_count_observed": len(ROWS), "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;C;reference_only",
        "detected_readiness": "D3",
        "notes": "Source-located measured BMP/contamination plus separate author-estimated Swiss supply; conflicts/censoring explicit; no GreenHub parameter connection."
    }, "dataset_path")

    numeric_rows = sum(bool(row["numeric_value"] or row["lower_bound"] or row["upper_bound"]) for row in ROWS)
    append_once(audit / "global_dataset_readiness.csv", {
        "dataset_path": relative_path, "category": "Bigas production + upgrade", "subgroup": "Feed BMP",
        "readiness": "D3", "duplicate_ids": 0, "duplicate_rows": 0, "numeric_rows": numeric_rows,
        "unsourced_numeric_rows": 0, "numeric_rows_missing_exact_location": 0, "unit_conflicts": 0,
        "basis_conflicts": 0, "cross_reference_issues": 0, "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "Stable ARAMIS project ID, no DOI; all numeric observations have exact report locations; censored bounds and author estimates remain separate; reference-only."
    }, "dataset_path")

    summary_path = audit / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = read_csv(audit / "global_dataset_manifest.csv")
    _, readiness = read_csv(audit / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary["readiness_counts"] = {}
    for item in readiness:
        status = item.get("readiness", "")
        summary["readiness_counts"][status] = summary["readiness_counts"].get(status, 0) + 1
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "dataset": CSV_PATH.relative_to(ROOT).as_posix(), "record_count": len(ROWS),
        "numeric_or_censored_records": numeric_rows, "sha256": digest,
        "quality": "B observations; C resource estimates", "activation": "reference_only"
    }, indent=2))


if __name__ == "__main__":
    main()
