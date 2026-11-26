"""Build a traceable, reference-only extract from Chopda et al. (2025).

The source is meadow grass from Ireland, not Dutch roadside grass. Transcribed
observations are comparators only; this builder does not map them to runtime
parameters, defaults, routes, TEA, or LCA calculations.
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
FILENAME = "meadow_grass_pretreatment_bmp_digestate_chopda_2025_reference.csv"
CSV_PATH = GROUP / FILENAME
SIDECAR_PATH = Path(str(CSV_PATH) + ".source.json")
SOURCE_ID = "SRC-CHOPDA-MEADOW-GRASS-2025"
DOI = "10.1007/s13399-024-05776-y"
DOI_URL = f"https://doi.org/{DOI}"
DTU_RECORD = "https://orbit.dtu.dk/en/publications/from-grass-to-lactic-acid-and-energy-evaluating-pretreatment-tech/"
MANUSCRIPT = "https://backend.orbit.dtu.dk/ws/files/368289470/Final-GrassBiorefinery_2.pdf"
RETRIEVAL_DATE = "2026-11-08"

FIELDS = [
    "observation_id", "source_id", "phase", "experiment_id", "material",
    "process_step", "metric", "reported_value", "numeric_value", "lower_bound",
    "upper_bound", "unit", "basis", "condition", "sample_count",
    "reported_uncertainty", "source_location", "evidence_class",
    "activation_state", "applicability", "limitations",
]

COMMON_LIMIT = (
    "Meadow-grass study at UCD Lyons Farms, Ireland; not Dutch roadside grass, "
    "VARTA samples, or the GreenHub post-protein residual. Do not use as a "
    "GreenHub default or full-scale unit coefficient."
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

# Phase 1: reported feed identity and structural composition. The article does
# not explicitly state the denominator for these percentages, so retain it as
# unresolved rather than silently interpreting them as dry-matter fractions.
ROWS.extend([
    _row("CHOPDA25-FEED-HARVEST-MONTH", "1", "feedstock", "meadow grass", "harvest", "harvest month", "June 2021", unit="calendar month", basis="reported date", source_location="Materials and Methods §2.1, accepted manuscript p. 6", applicability="Season/context marker only; not a seasonal availability profile."),
    _row("CHOPDA25-FEED-BOTANICAL-MIX", "1", "feedstock", "meadow grass", "feed characterization", "reported botanical mixture", "ryegrass; white clover; red clover; Yorkshire fog; creeping buttercup; chickweed", unit="species list", basis="qualitative study description", source_location="Materials and Methods §2.1, accepted manuscript p. 6", applicability="Botanical identity comparator; no species proportions are reported."),
    _row("CHOPDA25-FEED-CELLULOSE", "1", "feedstock", "meadow grass", "feed characterization", "cellulose", "29.4 ± 0.4", 29.4, unit="%", basis="percentage basis not stated in the source passage", reported_uncertainty="±0.4; statistic type not specified adjacent to this composition result", source_location="Materials and Methods §2.1, accepted manuscript p. 6", applicability="Measured composition comparator; dry/wet-basis normalization is unresolved."),
    _row("CHOPDA25-FEED-HEMICELLULOSE", "1", "feedstock", "meadow grass", "feed characterization", "hemicellulose", "14.3 ± 3.0", 14.3, unit="%", basis="percentage basis not stated in the source passage", reported_uncertainty="±3.0; statistic type not specified adjacent to this composition result", source_location="Materials and Methods §2.1, accepted manuscript p. 6", applicability="Measured composition comparator; dry/wet-basis normalization is unresolved."),
    _row("CHOPDA25-FEED-LIGNIN-TOTAL", "1", "feedstock", "meadow grass", "feed characterization", "total lignin", "27", 27, unit="%", basis="percentage basis not stated in the source passage", source_location="Materials and Methods §2.1, accepted manuscript p. 6", applicability="Measured composition comparator; dry/wet-basis normalization is unresolved."),
    _row("CHOPDA25-FEED-LIGNIN-ACID-INSOLUBLE", "1", "feedstock", "meadow grass", "feed characterization", "acid-insoluble lignin", "12.3", 12.3, unit="%", basis="percentage basis not stated in the source passage", source_location="Materials and Methods §2.1, accepted manuscript p. 6", applicability="Measured composition comparator; dry/wet-basis normalization is unresolved."),
    _row("CHOPDA25-FEED-LIGNIN-ACID-SOLUBLE", "1", "feedstock", "meadow grass", "feed characterization", "acid-soluble lignin", "14.7", 14.7, unit="%", basis="percentage basis not stated in the source passage", source_location="Materials and Methods §2.1, accepted manuscript p. 6", applicability="Measured composition comparator; dry/wet-basis normalization is unresolved."),
])

# Phase 2–3: matched treatment labels and post-treatment TS/VS observations.
# These are endpoint concentrations, not retained-mass or loss coefficients.
for treatment, ts, vs in (("U", 23.4, 94.4), ("M", 23.3, 95.0), ("E", 21.9, 93.6), ("EM", 23.2, 93.9)):
    label = {"U": "untreated", "M": "milled", "E": "ensiled", "EM": "milled and ensiled"}[treatment]
    ROWS.append(_row(
        f"CHOPDA25-{treatment}-TS", "2;3", treatment, f"meadow grass ({label})",
        "pretreatment endpoint", "total solids", str(ts), ts, unit="%",
        basis="sample total-solids concentration; exact denominator convention not expanded in table",
        condition=f"Treatment={treatment}; ensiling where applicable at 35 °C for 3 weeks",
        sample_count="3", reported_uncertainty="SD <0.1% across analyzed conditions",
        source_location="Table 1, accepted manuscript p. 7",
        applicability="Endpoint concentration only; not a mass-retention or water-loss estimate.",
    ))
    ROWS.append(_row(
        f"CHOPDA25-{treatment}-VS", "2;3", treatment, f"meadow grass ({label})",
        "pretreatment endpoint", "volatile solids", str(vs), vs, unit="% of TS",
        basis="volatile solids as a percentage of total solids",
        condition=f"Treatment={treatment}; ensiling where applicable at 35 °C for 3 weeks",
        sample_count="3", reported_uncertainty="SD <0.1% across analyzed conditions",
        source_location="Table 1, accepted manuscript p. 7",
        applicability="Endpoint concentration only; not a mass-retention or methane-conversion factor.",
    ))

ROWS.extend([
    _row("CHOPDA25-MILL-SIZE", "3", "pretreatment", "meadow grass", "milling", "target particle size", "10", 10, unit="mm", basis="reported mill size-reduction target", condition="Retsch SM2000 cutting mill", source_location="Materials and Methods §2.2, accepted manuscript p. 7", applicability="Lab pretreatment condition; no specific milling energy reported for this grass experiment."),
    _row("CHOPDA25-ENSILE-TEMPERATURE", "2", "ensiling", "meadow grass", "ensiling", "storage temperature", "35", 35, unit="°C", basis="controlled laboratory bottle condition", condition="Anaerobic bottles; nitrogen flushed; sealed", source_location="Materials and Methods §2.2, accepted manuscript p. 7", applicability="Laboratory ensiling condition; not a seasonal outdoor-storage rate."),
    _row("CHOPDA25-ENSILE-DURATION", "2", "ensiling", "meadow grass", "ensiling", "storage duration", "3", 3, unit="weeks", basis="controlled laboratory bottle condition", condition="100 g in 500 mL anaerobic bottles", source_location="Materials and Methods §2.2, accepted manuscript p. 7", applicability="Laboratory endpoint; no intermediate time series or degradation kinetics reported."),
    _row("CHOPDA25-ENSILE-SAMPLE-MASS", "2", "ensiling", "meadow grass", "ensiling", "sample mass per bottle", "100", 100, unit="g", basis="initial grass sample mass", condition="500 mL anaerobic bottle; nitrogen flushed and sealed", source_location="Materials and Methods §2.2, accepted manuscript p. 7", applicability="Laboratory protocol condition only; not a full-scale storage loading density."),
    _row("CHOPDA25-ENSILE-BOTTLE-VOLUME", "2", "ensiling", "meadow grass", "ensiling", "bottle nominal volume", "500", 500, unit="mL", basis="anaerobic bottle size", condition="100 g grass sample; nitrogen flushed and sealed", source_location="Materials and Methods §2.2, accepted manuscript p. 7", applicability="Laboratory protocol condition only."),
    _row("CHOPDA25-ENSILE-FINAL-PH", "2", "ensiling", "meadow grass", "ensiling", "final pH range", "4.2–4.5", lower_bound=4.2, upper_bound=4.5, unit="pH", basis="measured final pH range", condition="After 3 weeks at 35 °C", source_location="Materials and Methods §2.2, accepted manuscript p. 7", applicability="Endpoint quality indicator; not a pH trajectory."),
])

# A separate acid/enzyme sugar-release route was investigated. It is retained
# as an alternate-route comparator and is not GreenHub's protein extraction.
ROWS.extend([
    _row("CHOPDA25-ACID-LOADING", "3", "hydrolysis", "milled and ensiled meadow grass (EM)", "acid pretreatment", "solids loading", "18", 18, unit="%", basis="solids-loading denominator convention not specified in source", condition="Autoclave at 121 °C for 40 min; 1% sulfuric-acid solution", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; not the GreenHub protein route."),
    _row("CHOPDA25-ACID-CONCENTRATION", "3", "hydrolysis", "milled and ensiled meadow grass (EM)", "acid pretreatment", "sulfuric acid concentration", "1", 1, unit="%", basis="source wording: 1% sulfuric-acid solution; concentration basis not expanded", condition="Autoclave at 121 °C for 40 min", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; concentration basis needs source-level verification before scale-up."),
    _row("CHOPDA25-ACID-TEMPERATURE", "3", "hydrolysis", "milled and ensiled meadow grass (EM)", "acid pretreatment", "temperature", "121", 121, unit="°C", basis="autoclave temperature", condition="40 min; 18% solids; 1% sulfuric-acid solution", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; not a GreenHub default."),
    _row("CHOPDA25-ACID-DURATION", "3", "hydrolysis", "milled and ensiled meadow grass (EM)", "acid pretreatment", "duration", "40", 40, unit="min", basis="autoclave treatment duration", condition="121 °C; 18% solids; 1% sulfuric-acid solution", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; not a GreenHub default."),
    _row("CHOPDA25-ENZYME-LOADING", "3", "hydrolysis", "acid-treated meadow grass (EM)", "enzymatic hydrolysis", "cellulase loading", "10", 10, unit="FPU/g glucan", basis="enzyme activity per glucan", condition="2 L bioreactor; 200 rpm; 50 °C; pH 4.8; 24 h", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; enzyme identity SAE0020; not GreenHub protein extraction."),
    _row("CHOPDA25-ENZYME-TEMPERATURE", "3", "hydrolysis", "acid-treated meadow grass (EM)", "enzymatic hydrolysis", "temperature", "50", 50, unit="°C", basis="controlled bioreactor condition", condition="200 rpm; pH 4.8; 24 h", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; not a GreenHub default."),
    _row("CHOPDA25-ENZYME-DURATION", "3", "hydrolysis", "acid-treated meadow grass (EM)", "enzymatic hydrolysis", "duration", "24", 24, unit="h", basis="controlled bioreactor condition", condition="200 rpm; 50 °C; pH 4.8", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; not a GreenHub default."),
    _row("CHOPDA25-ENZYME-AGITATION", "3", "hydrolysis", "acid-treated meadow grass (EM)", "enzymatic hydrolysis", "agitation speed", "200", 200, unit="rpm", basis="reported bioreactor agitation", condition="2 L bioreactor; 10 FPU/g glucan; 50 °C; pH 4.8; 24 h", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Lab hydrolysis condition; not a scale-independent mixing-energy input."),
    _row("CHOPDA25-ENZYME-PH", "3", "hydrolysis", "acid-treated meadow grass (EM)", "enzymatic hydrolysis", "pH setpoint", "4.8", 4.8, unit="pH", basis="automatically controlled pH", condition="2 L bioreactor; 200 rpm; 50 °C; 24 h", source_location="Materials and Methods §2.4, accepted manuscript p. 8", applicability="Alternate sugar-hydrolysis route; not a GreenHub protein precipitation setpoint."),
    _row("CHOPDA25-HYDROLYSATE-CENTRIFUGE-SPEED", "3", "hydrolysis", "enzymatic hydrolysate/residue", "solid-liquid separation", "centrifuge speed", "10000", 10000, unit="rpm", basis="reported rotational speed", condition="10 min; separates hydrolysate (LEMEh) and solid residue (EMEh)", source_location="Materials and Methods §2.5, accepted manuscript p. 8", applicability="Lab separation condition; rotor radius/RCF and scale-up separation performance are not provided."),
    _row("CHOPDA25-HYDROLYSATE-CENTRIFUGE-DURATION", "3", "hydrolysis", "enzymatic hydrolysate/residue", "solid-liquid separation", "centrifugation duration", "10", 10, unit="min", basis="reported separation duration", condition="10000 rpm; separates hydrolysate (LEMEh) and solid residue (EMEh)", source_location="Materials and Methods §2.5, accepted manuscript p. 8", applicability="Lab separation condition; rotor radius/RCF and scale-up separation performance are not provided."),
    _row("CHOPDA25-LA-LDELBRUECKII", "4", "fermentation", "hydrolysate from EM grass", "lactic-acid fermentation", "lactic acid yield, L. delbrueckii", "240", 240, unit="kg LA/t fresh matter", basis="per tonne fresh matter of grass", condition="Hydrolysate from acid plus enzymatic treatment; batch fermentation", source_location="Results §3.3, accepted manuscript p. 15", applicability="Alternative sugar-to-lactic-acid route only; not protein recovery, juice precipitation, or protein-product quality."),
    _row("CHOPDA25-LA-PACIDILACTICI", "4", "fermentation", "hydrolysate from EM grass", "lactic-acid fermentation", "lactic acid yield, P. acidilactici", "230", 230, unit="kg LA/t fresh matter", basis="per tonne fresh matter of grass", condition="Hydrolysate from acid plus enzymatic treatment; batch fermentation", source_location="Results §3.3, accepted manuscript p. 15", applicability="Alternative sugar-to-lactic-acid route only; not protein recovery, juice precipitation, or protein-product quality."),
    _row("CHOPDA25-LA-SUGAR-CONVERSION", "4", "fermentation", "hydrolysate from EM grass", "lactic-acid fermentation", "sugar-to-lactic-acid conversion efficiency", "0.7", 0.7, unit="g LA/g sugar", basis="reported conversion efficiency", condition="Batch fermentation; 24 h endpoint described in Methods", source_location="Results §3.3, accepted manuscript p. 15", applicability="Alternative lactic-acid route only; do not map to protein recovery."),
    _row("CHOPDA25-LA-FERMENTER-TEMPERATURE", "4", "fermentation", "hydrolysate from EM grass", "lactic-acid fermentation", "fermentation temperature", "37", 37, unit="°C", basis="reported jacketed-bottle temperature", condition="Anaerobic 1 L bottles; 60 rpm; initial pH 8; 24 h", source_location="Materials and Methods §2.5, accepted manuscript p. 9", applicability="Alternative batch fermentation route only; not protein precipitation."),
    _row("CHOPDA25-LA-FERMENTER-AGITATION", "4", "fermentation", "hydrolysate from EM grass", "lactic-acid fermentation", "agitation speed", "60", 60, unit="rpm", basis="magnetic stirrer speed", condition="37 °C; anaerobic 1 L bottles; initial pH 8; 24 h", source_location="Materials and Methods §2.5, accepted manuscript p. 9", applicability="Alternative batch fermentation route only."),
    _row("CHOPDA25-LA-INITIAL-PH", "4", "fermentation", "hydrolysate from EM grass", "lactic-acid fermentation", "initial pH", "8", 8, unit="pH", basis="set using 10 M NaOH after inoculation; no later pH control", condition="37 °C; anaerobic 1 L bottles; 60 rpm", source_location="Materials and Methods §2.5, accepted manuscript p. 9", applicability="Alternative batch fermentation condition; not GreenHub protein-route pH."),
    _row("CHOPDA25-LA-FERMENTATION-DURATION", "4", "fermentation", "hydrolysate from EM grass", "lactic-acid fermentation", "duration to stable pH", "24", 24, unit="h", basis="source-reported endpoint time", condition="Fermentation concluded when constant pH observed; 37 °C; 60 rpm", source_location="Materials and Methods §2.5, accepted manuscript p. 9", applicability="Batch fermentation endpoint; not a continuous residence time."),
])

# Phase 5: batch biochemical methane-potential measurements, not continuous
# digester performance. The CH4 fraction is a source-reported range only.
for treatment, material, value in (
    ("U", "untreated meadow grass", 289),
    ("E", "ensiled meadow grass", 332),
    ("M", "milled meadow grass", 324),
    ("EM", "milled and ensiled meadow grass", 343),
):
    ROWS.append(_row(
        f"CHOPDA25-{treatment}-BMP-VS", "5", treatment, material,
        "batch biochemical methane potential assay", "methane yield", str(value), value,
        unit="m³ CH₄/t volatile solids", basis="per tonne volatile solids",
        condition="Hashøj inoculum; 37 °C; triplicate bottles; steady-pressure endpoint",
        sample_count="3", reported_uncertainty="Mean reported; the exact treatment-specific SD was not transcribed from the figure",
        source_location="Results §3.1, accepted manuscript p. 12",
        applicability="Batch BMP endpoint; not continuous-reactor yield, HRT kinetics, or post-protein residual performance.",
    ))
ROWS.extend([
    _row("CHOPDA25-BMP-METHANE-FRACTION", "5;6", "BMP gas", "U/E/M/EM meadow-grass BMP bottles", "batch biochemical methane potential assay", "methane fraction in biogas", "68–77", lower_bound=68, upper_bound=77, unit="% of produced biogas", basis="reported across BMP samples; treatment-specific values not transcribed from figure", condition="Batch assay; 37 °C", sample_count="3 per treatment", source_location="Results §3.1, accepted manuscript p. 12", applicability="Raw BMP gas composition context only; no gas-upgrading recovery, slip, energy, or product specification is reported."),
    _row("CHOPDA25-BMP-ORGANIC-LOADING", "5", "BMP protocol", "meadow-grass treatment streams", "batch biochemical methane potential assay", "organic loading", "2", 2, unit="g VS/L", basis="volatile solids per working volume", condition="200 mL working volume; 340 mL headspace; 37 °C", source_location="Materials and Methods §2.3, accepted manuscript p. 8", applicability="Laboratory assay condition; not a continuous digester loading rate."),
    _row("CHOPDA25-BMP-WORKING-VOLUME", "5", "BMP protocol", "meadow-grass treatment streams", "batch biochemical methane potential assay", "working volume", "200", 200, unit="mL", basis="liquid working volume per bottle", condition="340 mL headspace; 37 °C", source_location="Materials and Methods §2.3, accepted manuscript p. 8", applicability="Laboratory assay condition only."),
    _row("CHOPDA25-BMP-HEADSPACE", "5", "BMP protocol", "meadow-grass treatment streams", "batch biochemical methane potential assay", "headspace volume", "340", 340, unit="mL", basis="headspace volume per bottle", condition="200 mL working volume; 37 °C", source_location="Materials and Methods §2.3, accepted manuscript p. 8", applicability="Laboratory assay condition only."),
    _row("CHOPDA25-BMP-TEMPERATURE", "5", "BMP protocol", "meadow-grass treatment streams", "batch biochemical methane potential assay", "incubation temperature", "37", 37, unit="°C", basis="controlled bottle temperature", condition="Manual shaking every other day; endpoint at steady pressure", source_location="Materials and Methods §2.3, accepted manuscript p. 8", applicability="Batch assay condition, not proof of continuous digester performance."),
    _row("CHOPDA25-EM-BMP-FM", "5", "EM", "milled and ensiled meadow grass", "batch biochemical methane potential assay", "methane yield", "75", 75, unit="m³ CH₄/t fresh matter", basis="per tonne fresh matter", condition="Abstract-reported EM result; stated as 17% higher than untreated", source_location="Abstract; accepted manuscript p. 1", applicability="Abstract-level cross-check; not an absolute post-protein residual yield.", limitations="Abstract-reported value for this Irish meadow-grass experiment; treatment and basis are stated in the abstract. Not GreenHub roadside/VARTA grass or a runtime default."),
    _row("CHOPDA25-EMEH-BMP-VS", "5", "EMEh", "solid residue after acid/enzyme hydrolysis of EM grass", "batch biochemical methane potential assay", "methane yield", "118", 118, unit="m³ CH₄/t volatile solids", basis="per tonne volatile solids", condition="Lignin-rich solid residue after cellulose hydrolysis", source_location="Results §3.3, accepted manuscript p. 15", applicability="Alternate sugar-hydrolysis route residual; not the GreenHub protein-extraction residual."),
    _row("CHOPDA25-EMEH-BMP-FM", "5", "EMEh", "solid residue after acid/enzyme hydrolysis of EM grass", "batch biochemical methane potential assay", "methane yield", "4", 4, unit="m³ CH₄/t fresh matter", basis="per tonne fresh matter; reported by source", condition="Lignin-rich solid residue after cellulose hydrolysis", source_location="Results §3.3, accepted manuscript p. 15", applicability="Source-reported fresh-matter equivalent; not recalculated here and not GreenHub post-protein residual."),
])

# Phase 7: nutrient amounts as reported for the study's grass digestates. These
# are nutrient-content observations, not fertilizer substitution or compliance.
for treatment, nutrients in (
    ("U", {"N": 3, "P": 11, "K": 45}),
    ("M", {"N": 3, "P": 10, "K": 31}),
    ("E", {"N": 7, "P": 8, "K": 42}),
    ("EM", {"N": 6, "P": 10, "K": 31}),
):
    for element, value in nutrients.items():
        ROWS.append(_row(
            f"CHOPDA25-{treatment}-DIGESTATE-{element}", "7", treatment,
            f"digestate from {treatment} meadow grass", "digestate characterization",
            f"{element} nutrient content", str(value), value,
            unit=f"kg {element}/t DM",
            basis="source reports per tonne dry matter; the denominator is not clearly identified as digestate or grass feed in the text",
            condition=f"Grass stream={treatment}; mono-digested grass BMP feed",
            source_location="Results §3.2 and Figure 3, accepted manuscript p. 14",
            applicability="Nutrient-content comparator only; no digestate flow, availability, speciation, regulatory compliance, or substitution credit is established.",
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
            encoding = "utf-8-sig" if had_bom else "utf-8"
            with temporary.open("w", encoding=encoding, newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
                writer.writeheader()
                writer.writerows(existing)
            temporary.replace(path)
        return
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writerow({field: row.get(field, "") for field in fields})


def _ensure_utf8_bom(path: Path) -> None:
    """Preserve this local manifest's existing UTF-8-with-BOM convention."""
    content = path.read_bytes()
    if not content.startswith(b"\xef\xbb\xbf"):
        path.write_bytes(b"\xef\xbb\xbf" + content)


def main() -> None:
    if len({row["observation_id"] for row in ROWS}) != len(ROWS):
        raise ValueError("Observation IDs must be unique")
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ROWS)

    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    source_title = "From grass to lactic acid and energy: evaluating pretreatment techniques for enhanced biorefinery outputs"
    authors = "Rushab Chopda; Panagiotis Tsapekos; Ana Robles-Aguilar; Marcella Fernandes de Souza; Çağrı Akyol; Stijn Speelman; Irini Angelidaki; Erik Meers"
    source_location = "Accepted author manuscript: §2.1–2.5, Table 1, §3.1–3.3, Figure 3, and Abstract; page/section locations are retained in each CSV row."
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:feed-bmp:meadow-grass-pretreatment-bmp-digestate-chopda-2025-reference:v1",
        "dataset_version": "1.0.0",
        "dataset_file": FILENAME,
        "source_file": FILENAME,
        "record_count": len(ROWS),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Chopda, R., Tsapekos, P., Robles-Aguilar, A., de Souza, M. F., Akyol, Ç., Speelman, S., Angelidaki, I., & Meers, E. (2025). From grass to lactic acid and energy: evaluating pretreatment techniques for enhanced biorefinery outputs. Biomass Conversion and Biorefinery, 15, 7179–7189. https://doi.org/10.1007/s13399-024-05776-y",
        "publication_year": 2025,
        "journal": "Biomass Conversion and Biorefinery, volume 15, pages 7179–7189",
        "doi": DOI,
        "source_url": DOI_URL,
        "institutional_record": DTU_RECORD,
        "accepted_author_manuscript": MANUSCRIPT,
        "retrieval_date": RETRIEVAL_DATE,
        "source_location": source_location,
        "geography": "UCD Lyons Farms, Newcastle, County Dublin, Ireland; feed transported to Denmark for experimentation.",
        "material_scope": "Meadow-grass mixture including ryegrass, white clover, red clover, Yorkshire fog, creeping buttercup, and chickweed; harvested June 2021.",
        "evidence_class": "B_measured_literature_observations_and_source_reported_conditions",
        "quality_class": "B",
        "license": "No open reuse license identified for the accepted author manuscript. DTU Orbit general-rights notice permits one copy for private study/research, prohibits further distribution and commercial use, and permits distribution of the record URL. The repository extract contains attributed facts and values only; review rights before any external redistribution.",
        "data_availability": "No separate raw-data repository or supplementary dataset was identified in the institutional record during retrieval. Values are limited transcriptions from source tables, text, and abstract; no figure digitization was performed.",
        "data_structure": "Long-form observations with reported value, numeric/range fields, unit, basis, experiment/treatment, condition, replicate count, uncertainty note, and exact section/table location. Empty numeric cells mean no numeric value is transcribed; they are not zero.",
        "phase_coverage": {
            "1": "Feed identity, harvest-month context, and reported lignocellulosic composition; no annual supply, accessible area, collection, moisture profile, or roadside-specific availability.",
            "2": "Laboratory ensiling duration, temperature, final pH, and post-treatment TS/VS endpoints; no mass-retention series, gas/emission losses, leachate, aerobic storage, or kinetic parameters.",
            "3": "Milling size and an alternative acid/enzyme hydrolysis route; no screw-press performance, extraction balance, dilution water, or GreenHub unit-energy data.",
            "4": "Lactic-acid fermentation from hydrolysate is included as an alternate pathway only; no protein solubilization, isoelectric precipitation, protein recovery, or protein-product quality.",
            "5": "Triplicate batch BMP and limited gas composition for meadow grass and an acid/enzyme hydrolysis residue; no continuous residual digester kinetics or post-protein residual-specific BMP.",
            "6": "Raw batch-biogas methane fraction only; no upgrading technology, methane recovery/slip, parasitic energy, water, cost, or product-specification evidence.",
            "7": "Reported N/P/K amounts in study digestates; no GreenHub flow-weighted nutrient balance, nutrient speciation, fertilizer processing, compliance, or substitution validation.",
        },
        "limitations": [
            "The study material is cultivated meadow grass from Ireland, not roadside grass, Dutch VARTA samples, or GreenHub's protein-depleted process streams.",
            "The source does not explicitly state the denominator for the cellulose, hemicellulose, and lignin percentages; these bases remain unresolved and no dry-basis conversion was made.",
            "Table 1 reports means of triplicates and SD below 0.1% for measured conditions; treatment-specific SDs for methane yield and gas composition are not transcribed from the figure.",
            "The 3-week ensiling data are laboratory endpoints and cannot define full-scale storage kinetics, wet-mass loss, methane loss, or emissions.",
            "BMP data are batch biochemical-potential results, not continuous digester performance or a validated scale-up relationship.",
            "Digestate N/P/K values are reported per t DM, but the article text does not unambiguously identify whether that dry-matter denominator is digestate or grass input; they also do not define nutrient availability, downstream product grade, lawful application, or avoided-fertilizer credits.",
            "The manuscript's repository terms restrict redistribution; only the source URL may be freely distributed under the stated notice.",
        ],
        "conversion_or_processing": "Direct transcription of the reported values, ranges, and conditions; no conversions, imputations, graph digitization, kinetic fitting, or GreenHub parameter mapping.",
        "uncertainty": "Replicate count and the source-reported Table 1 SD bound are retained where given. Exact BMP treatment SDs, composition-basis uncertainty, and scale-up uncertainty are not resolved.",
        "runtime_policy": "Reference-only; no parameter registry, default, process equation, TEA/LCA factor, scenario, or Pareto mapping.",
        "access_protocol": "HTTPS DOI and DTU Orbit record; accepted manuscript accessible at the institutional repository URL subject to the stated general-rights notice.",
        "fair_metadata": {
            "findable": "Repository-local URN, stable DOI, source ID, and catalog-indexed dataset path.",
            "accessible": "HTTPS links to DOI and DTU repository; manuscript access conditions and reuse restrictions are recorded.",
            "interoperable": "UTF-8 long-form CSV with explicit phase, experiment, treatment, metric, reported value, numeric/range fields, units, basis, conditions, and source location.",
            "reusable": "Citation, retrieval date, SHA-256, evidence class, applicability, uncertainty, limitations, conversion policy, and license status are recorded.",
        },
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_source = {
        "source_id": SOURCE_ID,
        "source_title": source_title,
        "authors": authors,
        "year": "2025",
        "doi_or_stable_id": DOI,
        "source_type": "peer-reviewed primary experimental article; direct transcription from accepted manuscript",
        "url": DOI_URL,
        "material_scope": sidecar["material_scope"],
        "quality_notes": "B-tier measured literature observations; basis and transferability limitations preserved; no open reuse license identified; reference-only.",
    }
    _append_once(GROUP / "source_register.csv", local_source, "source_id")
    _append_once(GROUP / "ad_source_register.csv", local_source, "source_id")
    _append_once(GROUP / "dataset_manifest.csv", {
        "filename": FILENAME,
        "description": "Source-located meadow-grass composition, milling/ensiling endpoints, batch BMP, alternative hydrolysate fermentation, raw gas methane range, and digestate NPK; reference-only.",
        "row_count": len(ROWS),
        "schema_version": "1.0",
        "encoding": "UTF-8 with BOM",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "observation_id",
    }, "filename", mutable_fields={"row_count"})
    _ensure_utf8_bom(GROUP / "dataset_manifest.csv")

    relative_path = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
    _append_once(DATA / "global_audit_package" / "global_source_register.csv", {
        "dataset_path": relative_path,
        "dataset_group": "Feed BMP",
        "source_id": SOURCE_ID,
        "source_title": source_title,
        "authors": authors,
        "year": "2025",
        "doi_or_stable_id": DOI,
        "url": DOI_URL,
        "source_type": "peer-reviewed primary experimental article; direct transcription from accepted manuscript",
        "notes": "B-tier meadow-grass comparator for Phases 1, 2, 3, 5, and 7; alternate-route context for Phase 4 and raw-gas context only for Phase 6. Irish cultivated grass; no runtime activation.",
    }, "dataset_path")

    _append_once(DATA / "global_audit_package" / "global_dataset_manifest.csv", {
        "dataset_path": relative_path,
        "category": "Bigas production + upgrade",
        "subgroup": "Feed BMP",
        "filename": FILENAME,
        "row_count_observed": len(ROWS),
        "header_count": len(FIELDS),
        "headers": "; ".join(FIELDS),
        "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "B-tier source-located comparator; measured endpoints and lab conditions only; no GreenHub-specific supply, extraction, continuous AD, upgrading, or fertilizer substitution coefficients.",
    }, "dataset_path", mutable_fields={"row_count_observed", "header_count", "headers", "standardized_status_values", "detected_readiness", "notes"})

    numeric_rows = sum(bool(row["numeric_value"] or row["lower_bound"] or row["upper_bound"]) for row in ROWS)
    _append_once(DATA / "global_audit_package" / "global_dataset_readiness.csv", {
        "dataset_path": relative_path,
        "category": "Bigas production + upgrade",
        "subgroup": "Feed BMP",
        "readiness": "D3",
        "duplicate_ids": 0,
        "duplicate_rows": 0,
        "numeric_rows": numeric_rows,
        "unsourced_numeric_rows": 0,
        "numeric_rows_missing_exact_location": 0,
        "unit_conflicts": 0,
        "basis_conflicts": 0,
        "cross_reference_issues": 0,
        "equation_missing_inputs": 0,
        "equation_symbol_mismatches": 0,
        "notes": "DOI-linked; all numeric records have exact source section/table locations. Basis and transfer limitations are explicit. Reference-only; no runtime connection.",
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

    print(json.dumps({
        "dataset": CSV_PATH.relative_to(ROOT).as_posix(),
        "rows": len(ROWS),
        "numeric_rows": numeric_rows,
        "sha256": digest,
        "global_dataset_count": summary["dataset_count"],
        "quality_class": "B",
        "activation_state": "reference_only",
    }, indent=2))


if __name__ == "__main__":
    main()
