"""Build a source-located, reference-only extract from Kim's 2018 report."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub/data/Pre-treatment/Thermal_Enzymatic"
DATA_PATH = GROUP / "alfalfa_enzyme_assisted_protein_isolation_2018_reference.csv"
SIDECAR_PATH = Path(str(DATA_PATH) + ".source.json")
SOURCE_ID = "SRC-ENZ-003"
TITLE = "Enzyme-assisted Protein Isolation from Alfalfa Leaves"
AUTHORS = "Youngmi Kim"
SOURCE_URL = "https://alfalfa.org/pdf/USAFRI/Final%20Reports/2018/18Kim.pdf"
RETRIEVED = "2026-11-08"
DATASET_ID = "urn:greenhub:dataset:thermal-enzymatic:kim-2018-alfalfa-protein-isolation:v1"

FIELDS = [
    "record_id", "record_type", "phase", "stage", "material", "metric", "value",
    "value_low", "value_high", "unit", "basis", "operating_conditions", "source_id",
    "source_title", "authors", "year", "doi_or_stable_identifier", "source_url",
    "exact_source_location", "reported_uncertainty", "replicate_count", "evidence_class",
    "quality_class", "transferability", "calculation_or_transform", "notes",
]

EXTRACTION_CONDITIONS = (
    "2-L process run in two 1-L flasks; nominal 10% w/v dry-leaf slurry; fresh-leaf category, "
    "ground material; Viscozyme L + Pectinex Ultra SP-L at 1:1 v/v, 6 mg enzyme protein/g dry alfalfa; "
    "enzyme stage 8 h at 50 °C and 150 rpm; adjust to pH 9 with 2 M NaOH, then 6 h at 50 °C and 150 rpm; "
    "centrifuge 4500 rpm for 20 min; adjust supernatant to pH 3.5 with 1 M HCl for 2 h; recover precipitate "
    "at 4500 rpm for 5 min; lyophilize at -40 °C for 24 h."
)
SCREEN_CONDITIONS = (
    "6.4% w/v (dry basis) ground alfalfa leaves in pH 5 sodium-citrate buffer; enzyme treatment at 50 °C, "
    "150 rpm; 0.5 M NaOH adjustment to pH 9 followed by 6 h at 50 °C, 150 rpm."
)


def record(
    record_id: str,
    *,
    phase: str,
    stage: str,
    material: str,
    metric: str,
    value: str | int | float = "",
    value_low: str | int | float = "",
    value_high: str | int | float = "",
    unit: str = "",
    basis: str = "",
    conditions: str = "",
    location: str,
    uncertainty: str = "",
    replicates: str = "",
    record_type: str = "literature-reported",
    notes: str = "",
    transformation: str = "Direct transcription; no conversion, curve fitting, or GreenHub parameter mapping.",
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "record_type": record_type,
        "phase": phase,
        "stage": stage,
        "material": material,
        "metric": metric,
        "value": str(value),
        "value_low": str(value_low),
        "value_high": str(value_high),
        "unit": unit,
        "basis": basis,
        "operating_conditions": conditions,
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2018",
        "doi_or_stable_identifier": "",
        "source_url": SOURCE_URL,
        "exact_source_location": location,
        "reported_uncertainty": uncertainty,
        "replicate_count": replicates,
        "evidence_class": "primary_experimental_research_report",
        "quality_class": "B",
        "transferability": "alfalfa_laboratory_reference_only_not_roadside_or_greenhub",
        "calculation_or_transform": transformation,
        "notes": notes,
    }


def build_records() -> list[dict[str, str]]:
    result: list[dict[str, str]] = []

    def add(record_id: str, **kwargs: object) -> None:
        result.append(record(record_id, **kwargs))  # type: ignore[arg-type]

    material = "Alfalfa (Medicago sativa L.) leaves, Wisconsin, USA"
    proximate = (
        ("PROX-01", "crude protein", 30.7, 0.1),
        ("PROX-02", "crude fat", 3.1, 0.1),
        ("PROX-03", "crude fibre", 9.3, 0.15),
        ("PROX-04", "ash", 9.7, 0.1),
    )
    for suffix, metric, value, sd in proximate:
        add(f"KIM18-{suffix}", phase="1/4", stage="feed characterization",
            material=material, metric=metric, value=value, unit="% dry matter",
            basis="reported dry-basis proximate composition",
            location="§2 Materials, alfalfa leaf composition paragraph", uncertainty=f"±{sd}; report states error bars are SD",
            replicates="2 or 3 per general methods statement; property-specific n not stated",
            notes="Leaves were hand-picked at Mann Valley Farm, River Falls, Wisconsin; source category and sample preparation are described in §2.")
    add("KIM18-PROX-05", phase="1/4", stage="feed characterization", material=material,
        metric="other substances", value=47, unit="% dry matter",
        basis="reported dry-basis proximate composition", location="§2 Materials, alfalfa leaf composition paragraph",
        notes="Reported as other substances; not reallocated among carbohydrate, lignin, or other components.")

    enzyme_data = (
        ("ENZ-01", "Cellic CTec2 enzyme-protein concentration", 173.5, 24.5),
        ("ENZ-02", "Viscozyme L enzyme-protein concentration", 43.3, 9.0),
        ("ENZ-03", "Pectinex Ultra SP-L enzyme-protein concentration", 13.1, 4.1),
    )
    for suffix, metric, value, sd in enzyme_data:
        add(f"KIM18-{suffix}", phase="4", stage="enzyme characterization", material="Commercial enzyme preparation",
            metric=metric, value=value, unit="mg protein/mL enzyme preparation",
            basis="protein assay of commercial preparation using DC assay with BSA standard",
            location="§3.2.1 Enzymatic treatment, enzyme-protein concentration paragraph",
            uncertainty=f"±{sd}; SD as described by report", replicates="2 or 3 per general methods statement; property-specific n not stated",
            notes="This is enzyme-preparation protein concentration, not catalytic activity (U/mL) or a GreenHub-specific dose response.")

    for suffix, material_state, yield_value, preparation in (
        ("DRY-01", "air-dried alfalfa leaves", 41.0, "Leaf material was collected from bales, frozen, lyophilized, and ground for the assay."),
        ("DRY-02", "fresh-category alfalfa leaves", 46.8, "Leaves were hand-picked, frozen, lyophilized to minimize pore collapse, and ground; this was not a wet-leaf extraction."),
    ):
        add(f"KIM18-{suffix}", phase="2/4", stage="drying-state comparison", material=material_state,
            metric="protein extracted in no-enzyme control", value=yield_value,
            unit="% of total leaf protein", basis="author-reported soluble-protein yield in control run",
            conditions="Alfalfa leaves in the report's drying-state comparison; control without enzymes; " + preparation,
            location="§5.1 Dry vs. fresh leaves and Figure 2 discussion",
            notes="The comparison is a cultivated alfalfa leaf-state comparator, not a roadside-grass storage-loss measurement or storage time series.")
    add("KIM18-DRY-03", phase="2/4", stage="drying-state comparison", material="Fresh-category versus air-dried alfalfa leaves",
        metric="protein extraction yield ratio at 10 mg/g enzyme loading", value=1.6, unit="fold",
        basis="fresh-category leaf yield divided by air-dried leaf yield as reported by authors",
        conditions="C+V+P enzyme mixture at 1:1:1 v/v; 10 mg enzyme protein/g dry alfalfa; 6.4% w/v dry solids; enzyme treatment 24 h at 50 °C, 150 rpm; pH 9 alkaline extraction 6 h at 50 °C, 150 rpm. Fresh-category samples were frozen and lyophilized before assay.",
        location="§5.1 Dry vs. fresh leaves and Figure 2 discussion",
        notes="Source states fresh-category leaves yielded 1.6 times the protein extracted from dry leaves at the lowest enzyme dose tested. This does not quantify storage degradation or wet-biomass behavior.")

    add("KIM18-SCR-01", phase="4", stage="dose/time response", material=material,
        metric="protein solubilized after enzyme-assisted alkaline extraction", value=73.6,
        unit="% of initial leaf protein", basis="author-reported protein extraction yield",
        conditions=SCREEN_CONDITIONS + " C+V+P enzyme blend at 1:1:1 v/v; 51 mg total enzyme protein/g dry alfalfa; enzyme stage 12 h before alkaline stage.",
        location="§5.2 and Figure 3 caption/text",
        notes="The report says no further increase occurred after 12 h. This is alfalfa leaf extractability, not recovered precipitate/product yield.")
    add("KIM18-SCR-02", phase="4", stage="dose/time response", material=material,
        metric="enzyme-treatment time at reported protein-extraction plateau", value=12, unit="h",
        basis="first reported plateau time under the stated three-enzyme condition",
        conditions=SCREEN_CONDITIONS + " C+V+P at 1:1:1 v/v; 51 mg total enzyme protein/g dry alfalfa.",
        location="§5.2 and Figure 3 caption/text",
        notes="Source reports 73.6% at 12 h and no further increase after that point; no kinetic curve was fitted.")
    for suffix, dose, yield_value, blend, ratio in (
        ("SCR-03", 6, 69.9, "Viscozyme L + Pectinex Ultra SP-L", "1:1 v/v"),
        ("SCR-04", 13, 74.7, "Viscozyme L + Pectinex Ultra SP-L", "1:1 v/v"),
        ("SCR-05", 26, 71.4, "Cellic CTec2 + Viscozyme L + Pectinex Ultra SP-L", "1:1:1 v/v"),
    ):
        add(f"KIM18-{suffix}", phase="4", stage="enzyme blend screen", material=material,
            metric="protein solubilized after enzyme-assisted alkaline extraction", value=yield_value,
            unit="% of initial leaf protein", basis="author-reported protein extraction yield",
            conditions=SCREEN_CONDITIONS + f" {blend} at {ratio}; total enzyme protein dose {dose} mg/g dry alfalfa; 24 h enzyme treatment.",
            location="§5.3 and Figure 5 discussion/caption",
            notes="Screening result; enzyme dose is total enzyme protein per dry alfalfa. Do not treat as a saleable protein-product yield.")
    add("KIM18-SCR-06", phase="4", stage="single-enzyme screen", material=material,
        metric="protein extraction yield with Pectinex Ultra SP-L at doses below 3 mg/g", value_low=65,
        value_high=70, unit="% of initial leaf protein", basis="author describes yield as close to this interval",
        conditions=SCREEN_CONDITIONS + " Pectinex Ultra SP-L single-enzyme dose below 3 mg protein/g dry alfalfa; 24 h enzyme treatment.",
        location="§5.3 single-enzyme results", record_type="reported-range",
        notes="Approximate interval stated in report text, not pointwise values transcribed from Figure 4.")
    for suffix, enzyme, dose, change in (
        ("SCR-07", "Cellic CTec2", 39, "No increase versus control was reported."),
        ("SCR-08", "Cellic CTec2", 139, "A marginal 8% improvement versus control was reported."),
        ("SCR-09", "Viscozyme L", 5, "A 12% enhancement versus control was reported."),
        ("SCR-10", "Viscozyme L", 10, "A 20% enhancement versus control was reported."),
    ):
        numeric = "" if dose == 39 else (8 if dose == 139 else (12 if dose == 5 else 20))
        add(f"KIM18-{suffix}", phase="4", stage="single-enzyme screen", material=material,
            metric=f"reported protein-extraction change with {enzyme}", value=numeric,
            unit="% change as worded by source; relative-vs-percentage-point convention unspecified" if numeric != "" else "",
            basis="comparison with no-enzyme control; source text does not define percentage convention",
            conditions=SCREEN_CONDITIONS + f" {enzyme} at {dose} mg enzyme protein/g dry alfalfa; 24 h enzyme treatment.",
            location="§5.3 and Figure 4 discussion/caption",
            record_type="literature-reported" if numeric != "" else "qualitative-reported",
            notes=change + " Numeric change is retained exactly as reported; no absolute yield is reconstructed.")

    add("KIM18-MB-01", phase="4", stage="2-L extraction mass balance", material=material,
        metric="initial alfalfa leaf dry mass", value=190, unit="g dry matter",
        basis="initial mass for the extraction/recovery run", conditions=EXTRACTION_CONDITIONS,
        location="Table 1; §5.4 mass-balance discussion", replicates="Table 1 values are means of duplicate measurements")
    add("KIM18-MB-02", phase="4", stage="2-L extraction mass balance", material=material,
        metric="total solids remaining after enzyme treatment and alkaline extraction", value=99, unit="g dry matter",
        basis="solid fraction recovered after ET + pH 9 alkaline stage", conditions=EXTRACTION_CONDITIONS,
        location="Table 1 total-solids mass balance", replicates="Table 1 values are means of duplicate measurements")
    add("KIM18-MB-03", phase="4", stage="2-L extraction mass balance", material=material,
        metric="solids in liquid after enzyme treatment and alkaline extraction", value=91, unit="g dry matter",
        basis="source states this amount was determined by difference: initial solids minus insolubilized solids",
        conditions=EXTRACTION_CONDITIONS, location="Table 1 total-solids mass-balance footnote",
        replicates="Table 1 values are means of duplicate measurements", record_type="reported-derived",
        transformation="Preserve the source's own difference result; value was not independently recomputed.",
        notes="Author-derived by difference, not a directly isolated/dried measurement.")
    add("KIM18-MB-04", phase="4", stage="isoelectric precipitation", material="Alfalfa extraction liquid",
        metric="acid-precipitated solids mass", value=12, unit="g dry matter",
        basis="solids recovered after acid treatment at pH 3.5", conditions=EXTRACTION_CONDITIONS,
        location="Table 1 total-solids mass balance", replicates="Table 1 values are means of duplicate measurements")
    for suffix, metric, value, unit, basis, note in (
        ("MB-05", "protein content of initial leaf material", 30.7, "% dry matter", "crude protein content", "Reported composition; initial protein mass is separately source-reported in the same table."),
        ("MB-06", "protein content of solids after ET + alkaline extraction", 28.6, "% dry matter", "crude protein content of recovered solids", "The report warns this may be overestimated because solubilized protein remained in retained liquid in the centrifuged solids."),
        ("MB-07", "protein content of acid precipitate", 35.6, "% dry matter", "crude protein content of freeze-dried precipitated solids", "Crude protein purity only; precipitate contains non-protein material."),
        ("MB-08", "protein mass in initial leaf material", 58.3, "g", "source-reported initial protein mass", "Table 1 source-reported value."),
        ("MB-09", "protein mass in solids after ET + alkaline extraction", 28.2, "g", "source-reported protein in recovered solids", "Potential overlap with retained liquid is discussed by the authors."),
        ("MB-10", "protein mass in liquid after ET + alkaline extraction", 36.6, "g", "source-reported solubilized protein mass", "The source notes some liquid and its soluble protein remained in centrifuged solids, creating double counting."),
        ("MB-11", "protein mass in acid precipitate", 4.2, "g", "source-reported protein recovered in acid precipitate", "Final isolated protein mass in this run; precipitate total solids were 12 g."),
    ):
        add(f"KIM18-{suffix}", phase="4", stage="2-L extraction mass balance", material=material,
            metric=metric, value=value, unit=unit, basis=basis, conditions=EXTRACTION_CONDITIONS,
            location="Table 1 protein-content and protein-mass balance", replicates="Table 1 values are means of duplicate measurements", notes=note)
    for suffix, metric, value, unit, basis, note in (
        ("MB-12", "total solids solubilized after ET + alkaline extraction", 48, "% initial dry solids", "source-reported solids balance", "Source table reports 91 g as 48% solubilized."),
        ("MB-13", "soluble protein relative to initial protein", 62.8, "% initial leaf protein", "source-reported protein balance", "Distinct from acid-precipitated/recovered protein."),
        ("MB-14", "protein precipitated from solubilized liquid", 11.5, "% solubilized protein", "source-reported precipitated protein / protein in liquid", "Only 4.2 g of 36.6 g protein in the liquid was precipitated."),
        ("MB-15", "final precipitated protein relative to initial protein", 7, "% initial leaf protein", "source-reported final protein yield", "Do not confuse with 62.8% upstream protein solubilization."),
        ("MB-16", "reported protein balance closure", 110, "% initial protein", "(protein in retained solids + protein in liquid) / initial protein", "Source explicitly attributes overclosure to soluble proteins remaining in liquid retained with centrifuged solids and double counted across output fractions; do not force this balance to close."),
        ("MB-17", "solids precipitated from liquid fraction", 13, "% solids in liquid after ET + alkaline extraction", "source-reported total-solids balance", "Table footnote defines the denominator as the mass solubilized after ET + alkaline treatment."),
    ):
        add(f"KIM18-{suffix}", phase="4", stage="2-L extraction mass balance", material=material,
            metric=metric, value=value, unit=unit, basis=basis, conditions=EXTRACTION_CONDITIONS,
            location="Table 1; §5.4 mass-balance discussion", replicates="Table 1 values are means of duplicate measurements",
            record_type="reported-derived", notes=note)

    add("KIM18-QUAL-01", phase="4", stage="control product", material="Alfalfa acid precipitate from no-enzyme control",
        metric="crude protein content of control acid precipitate", value=26.4, unit="% dry matter",
        basis="source-reported text; control data are not shown in the report",
        conditions="Control run identical to the 2-L recovery procedure except no enzymes were added.",
        location="§5.4 control-product paragraph", record_type="literature-reported",
        notes="Source says these control data were not shown; no replicate count or uncertainty is given here.")
    for suffix, condition, value in (("QUAL-02", "enzyme-treated acid precipitate", 30.1),
                                     ("QUAL-03", "no-enzyme control acid precipitate", 22.6)):
        add(f"KIM18-{suffix}", phase="4", stage="protein product quality", material=f"Alfalfa {condition}",
            metric="total amino-acid content", value=value, unit="% dry matter",
            basis="author-reported total amino-acid content of precipitated protein product",
            conditions=EXTRACTION_CONDITIONS, location="§5.4 amino-acid composition paragraph",
            notes="Report states enzyme/control composition difference was not statistically significant (p > 0.05); data are means but condition-specific uncertainty is not printed in the cited text.")
    add("KIM18-PEP-01", phase="4", stage="downstream peptide hydrolysis", material="Dried alfalfa acid precipitate",
        metric="alfalfa precipitate protein hydrolyzed to peptides", value=87, unit="% precipitate protein",
        basis="source-reported hydrolysis outcome", conditions="5% w/v dry precipitate suspension; 0.1 M phosphate buffer pH 8; Alcalase 2.4L at 5% w/w dry solids; 60 °C, 150 rpm, 4 h; pH maintained at 8.",
        location="§3.3 and §5.5 peptide hydrolysis", notes="Separate peptide-production experiment; not a protein recovery or GreenHub route yield.")
    add("KIM18-PEP-02", phase="4", stage="downstream peptide hydrolysis", material="Alfalfa peptide hydrolysate",
        metric="peptide concentration", value=16, unit="g/L",
        basis="concentration in hydrolysate from 5% w/v dry acid-precipitate slurry",
        conditions="Alcalase 2.4L at 5% w/w dry solids; pH 8; 60 °C, 150 rpm, 4 h.",
        location="§5.5 peptide hydrolysis", notes="No uncertainty or replicate count is reported for this concentration in the cited result text.")

    if len({row["record_id"] for row in result}) != len(result):
        raise ValueError("record_id values must be unique")
    return result


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def upsert_csv(path: Path, key: str, row: dict[str, str]) -> None:
    fields, rows = read_csv(path)
    matches = [item for item in rows if item.get(key) == row.get(key)]
    if len(matches) > 1:
        raise ValueError(f"Duplicate {key}={row.get(key)} in {path}")
    if matches:
        matches[0].update({column: row.get(column, "") for column in fields})
    else:
        rows.append({column: row.get(column, "") for column in fields})
    write_csv(path, fields, rows)


def main() -> None:
    rows = build_records()
    write_csv(DATA_PATH, FIELDS, rows)
    digest = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": DATASET_ID,
        "dataset_version": "1.0.0",
        "dataset_file": DATA_PATH.name,
        "record_count": len(rows),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Kim, Y. (2018). Enzyme-assisted Protein Isolation from Alfalfa Leaves. United States Alfalfa Farmer's Research Initiative final report.",
        "doi": "",
        "stable_source_identifier": SOURCE_URL,
        "source_url": SOURCE_URL,
        "retrieval_date": RETRIEVED,
        "license": "No explicit reuse license identified in the report; source PDF is not bundled or redistributed.",
        "geography": "Mann Valley Farm, River Falls, Wisconsin, USA.",
        "feedstock_scope": "Alfalfa leaves, not roadside grass, cultivated ryegrass, or GreenHub feed.",
        "experimental_scope": "Laboratory enzyme-assisted alkaline extraction, acid precipitation, centrifugation, and peptide hydrolysis; screen assays and a 2-L extraction/recovery run.",
        "quality_class": "B_measured_primary_research_report; reference_only",
        "data_structure": "Long-form factual records from report Methods, text results, and Table 1. Graph-only point values were not digitized. No regressions or inferred missing values are included.",
        "phase_coverage": {
            "1": "Alfalfa leaf dry-basis composition only; no roadside-grass supply or seasonal yield.",
            "2": "Fresh-category versus air-dried alfalfa leaf extractability comparator; no storage duration, degradation, or wet-grass kinetics.",
            "4": "Enzyme dose/blend and time response, alkaline solubilization, acid precipitation, solids/protein accounting, and peptide hydrolysis.",
        },
        "reported_methods": "Feed characterization was on dry basis; enzyme protein concentration measured by DC assay with BSA standard; extraction screening used 6.4% w/v dry solids; the 2-L run used two 1-L flasks and nominal 10% w/v dry solids.",
        "uncertainty": "Reported ± values are retained as printed. The report states methods measurements were duplicates or triplicates and error bars are SD, but property-specific replicate counts are not given. Table 1 values are means of duplicate measurements. Many text-reported outcome values have no uncertainty.",
        "known_accounting_issue": "The source reports 110% protein closure and explains that soluble protein in liquid retained by centrifuged solids was counted in both fractions. The recorded overclosure is evidence, not an adjusted balance.",
        "applicability_limitations": [
            "Alfalfa leaves differ from roadside grass in species, composition, contaminants, and protein fractions.",
            "The assay material described as fresh-leaf category was frozen, lyophilized, and ground; this is not a wet roadside-grass slurry.",
            "Bench-scale shaking and centrifuge rpm are not transferable to industrial residence time, power, RCF, or separation efficiency.",
            "High upstream solubilization did not translate into high precipitated-product recovery: the source reports 62.8% solubilization but only 7% final precipitated protein relative to initial feed protein.",
            "No GreenHub mass-flow, energy, water, chemical-dose, plant-scale, product-price, or environmental-impact parameter is activated.",
        ],
        "conversion_or_processing": "Direct transcription. One 91 g solids-in-liquid result is retained as source-stated difference by initial-minus-insolubilized solids. Source-reported ratios and 110% closure are preserved; not independently recomputed.",
        "runtime_policy": "Reference-only. Does not enable enzyme-assisted extraction, change the baseline, supply defaults, or calibrate GreenHub roadside-grass response.",
        "fair_metadata": {
            "findable": "Local URN, stable report URL, source-register ID, and FAIR catalog entry.",
            "accessible": "Publicly hosted report URL; no explicit reuse license identified.",
            "interoperable": "UTF-8 CSV with units, material basis, phase, stage, source location, and status per record.",
            "reusable": "Methods, uncertainty, accounting anomaly, source limitations, retrieval date, and rights note accompany the data.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source_row = {
        "source_id": SOURCE_ID, "source_type": "funded experimental research report", "title": TITLE,
        "authors": AUTHORS, "year": "2018", "doi_or_stable_identifier": "",
        "publisher": "United States Alfalfa Farmer's Research Initiative (USAFRI)",
        "url": SOURCE_URL, "material_scope": "Alfalfa leaves; cell-wall enzyme extraction, alkaline solubilization, acid precipitation, and peptide hydrolysis.",
        "source_quality": "Primary experimental report; full public PDF; no DOI; reuse license not identified.",
        "access_date": RETRIEVED,
        "notes": "Direct data extract is reference-only. Graph-only values were not digitized. Not roadside grass and not GreenHub-calibrated.",
    }
    upsert_csv(GROUP / "source_register.csv", "source_id", source_row)

    manifest_path = GROUP / "dataset_manifest.csv"
    manifest_fields, manifest_rows = read_csv(manifest_path)
    manifest_row = {
        "dataset_id": "DS-TE-011", "filename": DATA_PATH.name,
        "purpose": "Source-located alfalfa enzyme-assisted protein extraction, recovery mass balance, product quality, and peptide outcomes; reference-only comparator.",
        "row_count": str(len(rows)), "primary_key": "record_id", "encoding": "UTF-8 with BOM",
        "delimiter": ",", "integration_readiness": "reference_only",
        "known_limitations": "Alfalfa laboratory comparator; no explicit reuse license; reported protein balance overcloses at 110%; no GreenHub activation.",
    }
    if not any(row["filename"] == DATA_PATH.name for row in manifest_rows):
        manifest_rows.append({field: manifest_row.get(field, "") for field in manifest_fields})
    else:
        existing = next(row for row in manifest_rows if row["filename"] == DATA_PATH.name)
        existing.update({field: manifest_row.get(field, "") for field in manifest_fields})
    for row in manifest_rows:
        if row["filename"] == "source_register.csv":
            row["row_count"] = str(len(read_csv(GROUP / "source_register.csv")[1]))
        if row["filename"] == "dataset_manifest.csv":
            row["row_count"] = str(len(manifest_rows))
    write_csv(manifest_path, manifest_fields, manifest_rows)

    validation_path = GROUP / "validation_report.csv"
    validation_fields, validation_rows = read_csv(validation_path)
    validation_row = {
        "filename": DATA_PATH.name, "primary_key": "record_id", "row_count": str(len(rows)),
        "unique_nonblank_primary_keys": "pass", "utf8_encoding": "pass", "comma_delimiter": "pass",
        "populated_numeric_traceability": "pass",
        "notes": "Source/table/section traceability, uncertainty, and reference-only status checked; graph points not digitized.",
    }
    if not any(row["filename"] == DATA_PATH.name for row in validation_rows):
        validation_rows.append({field: validation_row.get(field, "") for field in validation_fields})
    else:
        existing = next(row for row in validation_rows if row["filename"] == DATA_PATH.name)
        existing.update({field: validation_row.get(field, "") for field in validation_fields})
    for row in validation_rows:
        if row["filename"] == "validation_report.csv":
            row["row_count"] = str(len(validation_rows))
    write_csv(validation_path, validation_fields, validation_rows)

    gaps_path = GROUP / "assumption_and_missing_data_register.csv"
    _, gaps = read_csv(gaps_path)
    gap = next(row for row in gaps if row["register_id"] == "AMR-TE-005")
    gap.update({
        "reason_missing_or_assumed": "The ASABE 2021 conference abstract still gives only an aggregate 1.4–1.6-fold range without allocating response to its dose conditions. A separate 2018 alfalfa research report now supplies dose/blend and 2-L recovery comparators; it is not the same experiment and does not resolve the 2021 condition-specific values or GreenHub response.",
        "recommended_measurement_or_source": "Use the 2018 report as a separate alfalfa reference only; obtain the full 2021 proceedings paper or author data to resolve that study's exact response by dose and blend.",
        "model_consequence": "Related alfalfa evidence is available, but the requested 2021 dose allocation and roadside/GreenHub enzyme response remain uncalibrated.",
    })
    write_csv(gaps_path, list(gaps[0]), gaps)

    global_manifest_path = ROOT / "Greenhub/data/global_audit_package/global_dataset_manifest.csv"
    global_fields, global_rows = read_csv(global_manifest_path)
    rel_path = "Pre-treatment/Thermal_Enzymatic/" + DATA_PATH.name
    global_row = {
        "dataset_path": rel_path, "category": "Pre-treatment", "subgroup": "Thermal_Enzymatic",
        "filename": DATA_PATH.name, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "literature-reported;reported-derived;reported-range;qualitative-reported",
        "detected_readiness": "D3", "notes": "Primary alfalfa research-report evidence; source-located and reference-only. Graph-only points excluded; reuse license unidentified; accounting overclosure preserved.",
    }
    if not any(row["dataset_path"] == rel_path for row in global_rows):
        global_rows.append({field: global_row.get(field, "") for field in global_fields})
    else:
        existing = next(row for row in global_rows if row["dataset_path"] == rel_path)
        existing.update({field: global_row.get(field, "") for field in global_fields})
    write_csv(global_manifest_path, global_fields, global_rows)

    readiness_path = ROOT / "Greenhub/data/global_audit_package/global_dataset_readiness.csv"
    readiness_fields, readiness_rows = read_csv(readiness_path)
    readiness_row = {
        "dataset_path": rel_path, "category": "Pre-treatment", "subgroup": "Thermal_Enzymatic",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
        "numeric_rows": str(sum(bool(row["value"]) or bool(row["value_low"]) or bool(row["value_high"]) for row in rows)),
        "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "0", "cross_reference_issues": "0", "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0", "notes": "Directly source-located primary alfalfa report values; reference-only, no runtime mapping.",
    }
    if not any(row["dataset_path"] == rel_path for row in readiness_rows):
        readiness_rows.append({field: readiness_row.get(field, "") for field in readiness_fields})
    else:
        existing = next(row for row in readiness_rows if row["dataset_path"] == rel_path)
        existing.update({field: readiness_row.get(field, "") for field in readiness_fields})
    write_csv(readiness_path, readiness_fields, readiness_rows)

    source_global_path = ROOT / "Greenhub/data/global_audit_package/global_source_register.csv"
    source_global_fields, source_global_rows = read_csv(source_global_path)
    source_global_row = {
        "dataset_path": "Pre-treatment/Thermal_Enzymatic/source_register.csv",
        "dataset_group": "Thermal_Enzymatic", "source_id": SOURCE_ID, "source_title": TITLE,
        "authors": AUTHORS, "year": "2018", "doi_or_stable_id": "", "url": SOURCE_URL,
        "source_type": "funded experimental research report",
        "notes": "Full public report; direct alfalfa lab observations; no DOI or explicit reuse license; reference-only.",
    }
    if not any(row["source_id"] == SOURCE_ID for row in source_global_rows):
        source_global_rows.append({field: source_global_row.get(field, "") for field in source_global_fields})
    else:
        existing = next(row for row in source_global_rows if row["source_id"] == SOURCE_ID)
        existing.update({field: source_global_row.get(field, "") for field in source_global_fields})
    write_csv(source_global_path, source_global_fields, source_global_rows)

    summary_path = ROOT / "Greenhub/data/global_audit_package/global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if int(summary["dataset_count"]) < len(global_rows):
        summary["dataset_count"] = len(global_rows)
        summary.setdefault("readiness_counts", {})["D3"] = summary.get("readiness_counts", {}).get("D3", 0) + 1
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"dataset": rel_path, "records": len(rows), "numeric_records": readiness_row["numeric_rows"],
                      "source_id": SOURCE_ID, "activation": "reference-only"}, indent=2))


if __name__ == "__main__":
    main()
