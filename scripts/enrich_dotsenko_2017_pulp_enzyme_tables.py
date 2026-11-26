"""Transcribe the open-access Dotsenko & Lange (2017) pulp-response tables.

This enriches the existing Thermal_Enzymatic evidence table only. It does not
enable the optional enzyme scenarios or map observations to runtime parameters.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub/data/Pre-treatment/Thermal_Enzymatic"
DATA_PATH = GROUP / "enzymatic_treatment_response.csv"
SIDECAR_PATH = Path(str(DATA_PATH) + ".source.json")
SOURCE_ID = "SRC-ENZ-002"
DOI = "10.1007/s12649-016-9718-7"
DOI_URL = f"https://doi.org/{DOI}"
ARTICLE_URL = "https://link.springer.com/article/10.1007/s12649-016-9718-7"
PDF_URL = "https://link.springer.com/content/pdf/10.1007/s12649-016-9718-7.pdf"
AUTHORS = "Gleb Dotsenko; Lene Lange"
TITLE = "Enzyme Enhanced Protein Recovery from Green Biomass Pulp"
RETRIEVED = "2026-11-08"
GENERATED_PREFIX = "ENZR-DOT17-"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def observation(
    sequence: int,
    *,
    table: str,
    species: str,
    metric: str,
    value: float | int | str = "",
    unit: str = "",
    basis: str,
    location: str,
    experiment_suffix: str,
    enzyme_name: str = "",
    enzyme_dose: float | int | str = "",
    enzyme_dose_unit: str = "",
    time: float | int | str = "",
    time_unit: str = "h",
    temp: float | int | str = 50,
    ph: float | int | str = 8,
    solids: float | int | str = 20,
    solids_unit: str = "mg dry matter/mL",
    mixing: str = "continuous shaking, 200 rpm",
    pm: float | int | str = "",
    replicate_count: int | None = None,
    uncertainty_note: str = "",
    control: str = "treated",
    quality_note: str = "",
    data_status: str = "literature-reported",
    protein_release: float | int | str = "",
    protein_release_unit: str = "",
    process: str = "protein recovery from screw-press pulp",
    source_location: str | None = None,
) -> dict[str, str]:
    material = "white clover" if species == "white_clover" else "perennial ryegrass"
    uncertainty = uncertainty_note
    if pm != "":
        uncertainty = f"mean ± {pm}; SD"
        if replicate_count is not None:
            uncertainty += f"; n={replicate_count}"
    condition_parts = [f"Table {table}"]
    if temp != "":
        condition_parts.append(f"{temp} °C")
    if time != "":
        condition_parts.append(f"{time} {time_unit}")
    if ph != "":
        condition_parts.append(f"pH {ph}")
    if solids != "":
        condition_parts.append(f"{solids} {solids_unit}")
    if mixing:
        condition_parts.append(mixing)
    conditions = "; ".join(condition_parts) + ". "
    conditions += "Fresh-plant screw-press pulp stored at -20 °C before experiments."
    if table in {"2", "3", "4", "5"}:
        conditions += " Sodium azide was added at 3 mM to prevent microbial growth."
    if table == "5":
        conditions += (
            " Cellulase/hemicellulase pre-hydrolysis was 24 h at pH 5, followed by "
            "Savinase proteolysis at pH 8; reported proteolysis timepoints are 24, 48, and 72 h."
        )
    if quality_note:
        conditions += " " + quality_note
    row = {
        "parameter_id": f"{GENERATED_PREFIX}{sequence:03d}",
        "observation_id": f"OBS-{GENERATED_PREFIX}{sequence:03d}",
        "python_variable": "",
        "value": str(value),
        "unit": unit,
        "normalized_si_value": "",
        "normalized_si_unit": "",
        "basis": basis,
        "process": process,
        "material_feed_type": f"{material} screw-press pulp",
        "material_state": "fresh-plant pulp, stored at -20 °C before lab extraction",
        "operating_conditions": conditions,
        "valid_range": f"Source-reported condition; experiment {experiment_suffix}",
        "data_status": data_status,
        "source_id": SOURCE_ID,
        "source_title": TITLE,
        "authors": AUTHORS,
        "year": "2017",
        "doi_or_stable_identifier": DOI,
        "exact_source_location": source_location or location,
        "source_url": DOI_URL,
        "notes": (
            "Direct transcription; no conversion, fit, or GreenHub parameter mapping. "
            "This is cultivated ryegrass/clover pulp, not roadside-grass/GreenHub pulp. "
            "The enzyme-assisted results are laboratory extraction experiments and are "
            "not an enabled GreenHub route. " + quality_note
        ).strip(),
        "uncertainty": uncertainty,
        "transferability_to_fresh_grass": "related_material_not_greenhub_feed",
        "scenario_id": "",
        "experiment_id": f"DOT17-{table}-{experiment_suffix}",
        "enzyme_id": "",
        "enzyme_name": enzyme_name,
        "enzyme_dose": str(enzyme_dose),
        "enzyme_dose_unit": enzyme_dose_unit,
        "treatment_time": str(time),
        "treatment_time_unit": time_unit,
        "temperature": str(temp),
        "temperature_unit": "degC",
        "pH": str(ph),
        "solids_loading": str(solids),
        "solids_loading_unit": solids_unit,
        "mixing": mixing,
        "protein_release": str(protein_release),
        "protein_release_unit": protein_release_unit,
        "sugar_release": "",
        "sugar_release_unit": "",
        "fibre_degradation": "",
        "fibre_degradation_unit": "",
        "viscosity": "",
        "viscosity_unit": "",
        "downstream_separation_response": "",
        "control_or_treated": control,
        "response_definition": metric,
    }
    if value == "" and data_status == "qualitative-reported":
        row["notes"] += " No numerical detection limit is reported; blank is not zero."
    return row


def build_observations() -> list[dict[str, str]]:
    observations: list[dict[str, str]] = []
    seq = 1

    def add(**kwargs: object) -> None:
        nonlocal seq
        observations.append(observation(seq, **kwargs))  # type: ignore[arg-type]
        seq += 1

    # Pulp properties and the inter-assay method comparison (Table 1).
    for species, dm, dm_sd, cp, cp_sd in (
        ("white_clover", 32, 1, 16, 1),
        ("ryegrass", 33, 1, 10, 1),
    ):
        add(table="Methods", species=species, metric="pulp total solids", value=dm,
            unit="% wet pulp", basis="mass fraction of stored screw-press pulp",
            location="Materials and Methods, p.1258", experiment_suffix="PULP",
            pm=dm_sd, time="", temp="", ph="", solids="", solids_unit="",
            time_unit="", mixing="", uncertainty_note="Reported ±1 percentage point; statistic/replicate count not stated.",
            quality_note="Total solids as reported; pulp stored at -20 °C.")
        add(table="Methods", species=species, metric="pulp crude protein", value=cp,
            unit="% dry matter", basis="Kjeldahl crude protein relative to pulp DM",
            location="Materials and Methods, p.1258", experiment_suffix="PULP",
            pm=cp_sd, time="", temp="", ph="", solids="", solids_unit="",
            time_unit="", mixing="", uncertainty_note="Reported ±1 percentage point; statistic/replicate count not stated.",
            quality_note="Kjeldahl nitrogen multiplied by 6.25.")

    assay_values = {
        "white_clover": {"UV absorbance assay (280 nm)": (1.9, 0.2),
                         "Pierce bicinchoninic acid assay": (2.0, 0.2),
                         "Bradford assay": (1.9, 0.2),
                         "Kjeldahl assay (crude protein)": (1.4, 0.1)},
        "ryegrass": {"UV absorbance assay (280 nm)": (0.7, 0.1),
                     "Pierce bicinchoninic acid assay": (1.0, 0.1),
                     "Bradford assay": (0.7, 0.1),
                     "Kjeldahl assay (crude protein)": (0.6, 0.1)},
    }
    for species, methods in assay_values.items():
        for method, (mean, sd) in methods.items():
            add(table="1", species=species, metric="protein concentration by " + method,
                value=mean, unit="mg/mL", basis="72-h supernatant concentration",
                location="Table 1, p.1259", experiment_suffix=f"{species}-pH8",
                enzyme_name="No added enzyme", enzyme_dose=0, enzyme_dose_unit="mg/g DM",
                time=72, pm=sd,
                quality_note="pH 8.0 aqueous pulp extraction; assay methods are not interchangeable; Table 1 replicate count not stated.")

    # Tables 2 and 3: concentrations and reported 72-h recovery yields.
    t2 = {
        ("white_clover", "no detergent"): ([ (1.6,.1),(1.8,.2),(1.9,.2) ], (1.4,.1), 43),
        ("ryegrass", "no detergent"): ([ (.5,.1),(.7,.1),(.7,.1) ], (.6,.1), 31),
        ("white_clover", "Tween 80 0.5% w/w"): ([ (1.7,.2),(1.9,.2),(2.0,.2) ], (1.7,.1), 53),
        ("ryegrass", "Tween 80 0.5% w/w"): ([ (.7,.1),(.9,.1),(.8,.1) ], (.8,.1), 40),
    }
    t3 = {
        ("white_clover", "no detergent"): ([ (2.8,.2),(2.9,.2),(2.8,.2) ], (2.5,.2), 79),
        ("ryegrass", "no detergent"): ([ (1.5,.1),(1.7,.2),(1.7,.2) ], (1.5,.1), 76),
        ("white_clover", "Tween 80 0.5% w/w"): ([ (2.7,.2),(3.1,.2),(3.1,.2) ], (2.7,.2), 84),
        ("ryegrass", "Tween 80 0.5% w/w"): ([ (1.6,.1),(1.9,.2),(2.0,.2) ], (1.6,.2), 79),
    }

    def add_kinetics(table: str, cases: dict, enzyme: str, dose: str, dose_unit: str) -> None:
        for (species, additive), (uv, kjeldahl, yield_pct) in cases.items():
            exp = f"{species}-{additive.lower().replace(' ', '-').replace('%', 'pct')}"
            for hour, (mean, sd) in zip((24, 48, 72), uv):
                add(table=table, species=species, metric="UV absorbance protein concentration",
                    value=mean, unit="mg/mL", basis="supernatant concentration by UV absorbance at 280 nm",
                    location=f"Table {table}, p.{1259 if table == '2' else 1260}", experiment_suffix=exp,
                    enzyme_name=enzyme, enzyme_dose=dose, enzyme_dose_unit=dose_unit,
                    time=hour, pm=sd, replicate_count=3, quality_note=f"Additive: {additive}.")
            mean, sd = kjeldahl
            add(table=table, species=species, metric="Kjeldahl crude protein concentration at 72 h",
                value=mean, unit="mg/mL", basis="supernatant crude protein by Kjeldahl at 72 h",
                location=f"Table {table}, p.{1259 if table == '2' else 1260}", experiment_suffix=exp,
                enzyme_name=enzyme, enzyme_dose=dose, enzyme_dose_unit=dose_unit,
                time=72, pm=sd, replicate_count=3, quality_note=f"Additive: {additive}.")
            add(table=table, species=species, metric="protein recovery yield at 72 h",
                value=yield_pct, unit="% pulp protein", basis="solubilized protein / total Kjeldahl crude protein in pulp",
                location=f"Table {table}, p.{1259 if table == '2' else 1260}", experiment_suffix=exp,
                enzyme_name=enzyme, enzyme_dose=dose, enzyme_dose_unit=dose_unit,
                time=72, protein_release=yield_pct, protein_release_unit="% of pulp crude protein",
                pm="", quality_note=f"Additive: {additive}; table does not report SD for yield.")

    add_kinetics("2", t2, "No added enzyme; endogenous pulp extraction", 0, "mg/g DM")
    add_kinetics("3", t3, "Savinase 16.0L protease", 5, "mg protein/g dry pulp")

    # Table 4 dose response for Savinase, with no-enzyme condition retained.
    t4 = {
        "white_clover": {
            20: ((2.8,.2),(2.9,.2),(2.9,.2),(2.5,.2),79),
            10: ((2.8,.2),(2.8,.2),(2.9,.2),(2.5,.2),79),
            5: ((2.7,.2),(2.8,.2),(2.8,.2),(2.5,.2),79),
            2.5: ((2.7,.2),(2.8,.2),(2.9,.2),(2.4,.2),75),
            1.25: ((2.6,.2),(2.7,.2),(2.7,.2),(2.4,.2),75),
            0: ((1.6,.1),(1.8,.2),(1.9,.2),(1.4,.1),43),
        },
        "ryegrass": {
            20: ((1.5,.2),(1.7,.2),(1.6,.2),(1.5,.1),76),
            10: ((1.5,.2),(1.7,.2),(1.7,.2),(1.5,.1),76),
            5: ((1.5,.2),(1.6,.2),(1.7,.2),(1.5,.1),76),
            2.5: ((1.3,.1),(1.6,.1),(1.6,.1),(1.4,.1),70),
            1.25: ((1.4,.1),(1.5,.1),(1.6,.1),(1.4,.1),70),
            0: ((.5,.1),(.7,.1),(.7,.1),(.6,.1),31),
        },
    }
    for species, doses in t4.items():
        for dose, (uv24, uv48, uv72, kjeldahl, yield_pct) in doses.items():
            exp = f"{species}-dose-{dose:g}-mg-g"
            enzyme = "Savinase 16.0L protease" if dose else "No added Savinase (control)"
            for hour, (mean, sd) in zip((24,48,72), (uv24,uv48,uv72)):
                add(table="4", species=species, metric="UV absorbance protein concentration",
                    value=mean, unit="mg/mL", basis="supernatant concentration by UV absorbance at 280 nm",
                    location="Table 4, p.1261", experiment_suffix=exp,
                    enzyme_name=enzyme, enzyme_dose=dose,
                    enzyme_dose_unit="mg/g DM as Table 4 heading; exact enzyme-mass basis not further specified",
                    time=hour, pm=sd, replicate_count=3,
                    quality_note="Savinase dosage dependence; dose basis as table heading.")
            mean, sd = kjeldahl
            add(table="4", species=species, metric="Kjeldahl crude protein concentration at 72 h",
                value=mean, unit="mg/mL", basis="supernatant crude protein by Kjeldahl at 72 h",
                location="Table 4, p.1261", experiment_suffix=exp,
                enzyme_name=enzyme, enzyme_dose=dose,
                enzyme_dose_unit="mg/g DM as Table 4 heading; exact enzyme-mass basis not further specified",
                time=72, pm=sd, replicate_count=3,
                quality_note="Savinase dosage dependence; dose basis as table heading.")
            add(table="4", species=species, metric="protein recovery yield at 72 h",
                value=yield_pct, unit="% pulp protein", basis="solubilized protein / total Kjeldahl crude protein in pulp",
                location="Table 4, p.1261", experiment_suffix=exp,
                enzyme_name=enzyme, enzyme_dose=dose,
                enzyme_dose_unit="mg/g DM as Table 4 heading; exact enzyme-mass basis not further specified",
                time=72, protein_release=yield_pct, protein_release_unit="% of pulp crude protein",
                quality_note="Table does not report SD for yield; no optimum is inferred.")

    # Table 5: carbohydrase pretreatment followed by Savinase proteolysis.
    t5 = {
        ("white_clover", "modest", 2.5): ((2.9,.2),(3.0,.2),(3.0,.2),(2.6,.2),81),
        ("ryegrass", "modest", 2.5): ((1.7,.1),(1.9,.2),(1.8,.2),(1.6,.1),79),
        ("white_clover", "exhaustive", 30): ((2.9,.2),(3.3,.2),(3.4,.2),(3.0,.2),94),
        ("ryegrass", "exhaustive", 30): ((1.9,.2),(2.1,.2),(2.1,.2),(1.9,.1),95),
    }
    for (species, extent, carb_dose), (uv24,uv48,uv72,kjeldahl,yield_pct) in t5.items():
        exp=f"{species}-{extent}"
        enzymes="Cellic CTec2 + HTec2, then Savinase 16.0L"
        dose_note=(f"Cellic CTec2/HTec2 dose {carb_dose:g} mg/g DM as reported for {extent} pretreatment; "
                   "subsequent Savinase dose 5 mg protein/g dry pulp. The source does not state "
                   "the individual CTec2 versus HTec2 dose allocation.")
        for hour,(mean,sd) in zip((24,48,72),(uv24,uv48,uv72)):
            add(table="5",species=species,metric="UV absorbance protein concentration after sequential enzyme treatment",
                value=mean,unit="mg/mL",basis="supernatant concentration by UV absorbance at 280 nm",
                location="Table 5, p.1262",experiment_suffix=exp,enzyme_name=enzymes,
                enzyme_dose=carb_dose,enzyme_dose_unit="mg/g DM; CTec2/HTec2 allocation not reported",
                time=hour,pm=sd,replicate_count=3,ph="8",quality_note=dose_note)
        mean,sd=kjeldahl
        add(table="5",species=species,metric="Kjeldahl crude protein concentration at 72 h after sequential enzyme treatment",
            value=mean,unit="mg/mL",basis="supernatant crude protein by Kjeldahl at 72 h",
            location="Table 5, p.1262",experiment_suffix=exp,enzyme_name=enzymes,
            enzyme_dose=carb_dose,enzyme_dose_unit="mg/g DM; CTec2/HTec2 allocation not reported",
            time=72,pm=sd,replicate_count=3,ph="8",quality_note=dose_note)
        add(table="5",species=species,metric="protein recovery yield at 72 h after sequential enzyme treatment",
            value=yield_pct,unit="% pulp protein",basis="solubilized protein / total Kjeldahl crude protein in pulp",
            location="Table 5, p.1262",experiment_suffix=exp,enzyme_name=enzymes,
            enzyme_dose=carb_dose,enzyme_dose_unit="mg/g DM; CTec2/HTec2 allocation not reported",
            time=72,protein_release=yield_pct,protein_release_unit="% of pulp crude protein",
            ph="8",quality_note=dose_note+" Table does not report SD for yield.")

    # Carbohydrases alone: measured qualitative non-detects, not zero protein.
    for species in ("white_clover", "ryegrass"):
        add(table="Results",species=species,metric="protein in cellulase/hemicellulase-only supernatant",
            value="",unit="",basis="qualitative assay result; no numerical detection limit reported",
            location="Results, p.1262",experiment_suffix=f"{species}-carbohydrases-only",
            enzyme_name="Cellic CTec2 + Cellic HTec2",enzyme_dose=30,
            enzyme_dose_unit="mg enzyme/g DM as reported",time=72,ph=5,
            data_status="qualitative-reported",control="treated",
            quality_note="No plant protein detected by Bradford or Kjeldahl after cellulase/hemicellulase hydrolysis; source says glucose release was almost quantitative but gives no numeric value.")
    return observations


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]], *, bom: bool = True) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def upsert(path: Path, key: str, row: dict[str, str], mutable_fields: set[str]) -> None:
    fields, rows = read_rows(path)
    matched = [item for item in rows if item.get(key) == row.get(key)]
    if len(matched) > 1:
        raise ValueError(f"Duplicate key {row.get(key)} in {path}")
    if matched:
        item = matched[0]
        changed = {field for field in fields if item.get(field, "") != row.get(field, "")}
        if not changed.issubset(mutable_fields):
            raise ValueError(f"Unexpected fields would change in {path}: {sorted(changed - mutable_fields)}")
        item.update({field: row.get(field, "") for field in changed})
    else:
        rows.append({field: row.get(field, "") for field in fields})
    write_csv(path, fields, rows, bom=path.read_bytes().startswith(b"\xef\xbb\xbf"))


def main() -> None:
    fields, current = read_rows(DATA_PATH)
    if not fields or "parameter_id" not in fields:
        raise ValueError("Unexpected response-data schema")
    generated = build_observations()
    # Replace only the two known abstract-only placeholders and previous rows
    # generated by this exact source extractor; preserve every other source row.
    retained = [row for row in current if row["parameter_id"] not in {"ENZR-PULP-1", "ENZR-PULP-2"}
                and not row["parameter_id"].startswith(GENERATED_PREFIX)]
    pulp_index = next((i for i, row in enumerate(retained) if row["parameter_id"] == "ENZR-RANGE-2"), len(retained)-1) + 1
    current = retained[:pulp_index] + generated + retained[pulp_index:]
    if len({row["parameter_id"] for row in current}) != len(current):
        raise ValueError("parameter_id values must be unique")
    if len({row["observation_id"] for row in current}) != len(current):
        raise ValueError("observation_id values must be unique")
    write_csv(DATA_PATH, fields, current)
    digest = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()

    source_rows = read_rows(GROUP / "source_register.csv")[1]
    src = next(item for item in source_rows if item["source_id"] == SOURCE_ID)
    src["authors"] = AUTHORS
    src["access_date"] = RETRIEVED
    src["notes"] = (
        "Full open-access article tables 1–5 transcribed at condition level: pulp composition, "
        "assay comparison, aqueous extraction, Savinase dose/time response, and sequential "
        "carbohydrase/protease treatment. CC BY 4.0. All evidence-only; no enzyme route/default activation."
    )
    write_csv(GROUP / "source_register.csv", list(source_rows[0]), source_rows)

    sidecar = {
        "dataset_id": "urn:greenhub:dataset:thermal-enzymatic:dotsenko-lange-2017-pulp-response:v1",
        "dataset_version": "1.1.0",
        "dataset_file": DATA_PATH.name,
        "record_count": len(current),
        "source_record_count": len(generated),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "citation": "Dotsenko, G., & Lange, L. (2017). Enzyme Enhanced Protein Recovery from Green Biomass Pulp. Waste and Biomass Valorization, 8, 1257–1264. https://doi.org/10.1007/s12649-016-9718-7",
        "doi": DOI,
        "source_url": ARTICLE_URL,
        "full_text_pdf": PDF_URL,
        "retrieval_date": RETRIEVED,
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0), as stated in the published article.",
        "geography": "Cultivated perennial ryegrass and white clover pulp supplied by Aarhus University, Denmark; not roadside grass.",
        "material_scope": "Screw-press pulps from fresh ryegrass and white clover. Laboratory aqueous extraction and enzyme-assisted protein solubilization.",
        "quality_class": "B_measured_literature_observations",
        "data_structure": "Long-form transcriptions from Tables 1–5: each row is one response metric at one assay time/condition. Mean ± SD is preserved for concentration data; triplicate count is stated for Tables 2–5, but Table 1 replicate count and the statistic behind pulp-composition ± values are not specified. Protein-yield SD is not printed. Qualitative non-detects have blank numeric values.",
        "phase_coverage": {
            "3": "Direct screw-press pulp characterization and cell-wall/protein extraction response comparator; no pressing mass balance or GreenHub feed calibration.",
            "4": "Condition-resolved aqueous pulp protein recovery, assay-method comparison, Savinase dose/time response, and sequential carbohydrase/protease recovery.",
            "5": "No digestion or residual biodegradability data.",
            "7": "No nutrient recovery or fertilizer-product results."
        },
        "limitations": [
            "Feed is cultivated ryegrass and white clover, not GreenHub roadside/VARTA biomass.",
            "Pulp is from fresh-plant screw pressing and was stored at -20 °C before laboratory experiments.",
            "Experiments are 20 mL lab reactions, 20 mg DM/mL, 50 °C, 200 rpm, with triplicate reactions; no scale-up, water/reagent/energy balance, equipment productivity, or continuous operation is reported.",
            "Protein yield is the solubilized fraction of crude Kjeldahl protein already in pulp, not total-feed protein recovery or precipitated saleable protein.",
            "Carbohydrase-only protein non-detection has no numeric detection limit; blanks are not treated as zero.",
            "Table 5 reports cellulase/hemicellulase doses for modest/exhaustive hydrolysis but does not allocate dose between CTec2 and HTec2 individually; do not interpret the reported dose as a verified total blend mass.",
            "The reported proteolysis products are low-molecular-weight peptides; nutritional/feed product quality and downstream separation are not established by recovery yield alone.",
            "No GreenHub model parameter, default, route, TEA/LCA factor, scenario, or Pareto setting is activated."
        ],
        "conversion_or_processing": "Direct table transcription only; no unit conversion, interpolation, regression, optimum selection, or mass-balance inference.",
        "uncertainty": "Concentration columns report mean ± SD (n=3); yield columns have no SD shown. No new uncertainty distribution is fitted.",
        "runtime_policy": "Evidence-only. Enzyme scenarios remain disabled and structurally blocked for predictive use without GreenHub-specific response, dose normalization, economics, and scale-up evidence.",
        "fair_metadata": {
            "findable": "Local URN, DOI, source ID and FAIR catalog entry.",
            "accessible": "Publisher full text is available at HTTPS; the published article states CC BY 4.0.",
            "interoperable": "Existing UTF-8 long-form response schema; units, basis, table location, species and conditions are explicit.",
            "reusable": "Citation, retrieval date, license, row-level source location, uncertainty and transfer limits recorded."
        }
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest_path = GROUP / "dataset_manifest.csv"
    manifest = read_rows(manifest_path)[1]
    manifest_row = next(row for row in manifest if row["filename"] == DATA_PATH.name)
    manifest_row["row_count"] = str(len(current))
    manifest_row["purpose"] = "Source-located enzyme and thermal response observations; Dotsenko & Lange Tables 1–5 are laboratory reference evidence only; model remains blocked for predictive enzyme activation."
    write_csv(manifest_path, list(manifest[0]), manifest)

    validation_path = GROUP / "validation_report.csv"
    validation = read_rows(validation_path)[1]
    vrow = next(row for row in validation if row["filename"] == DATA_PATH.name)
    vrow["row_count"] = str(len(current))
    vrow["unique_nonblank_primary_keys"] = "pass"
    vrow["populated_numeric_traceability"] = "pass"
    vrow["notes"] = "Direct source/table locations and uncertainty retained; numerical assay data remain evidence-only, not runtime-active."
    write_csv(validation_path, list(validation[0]), validation)

    missing_path = GROUP / "assumption_and_missing_data_register.csv"
    missing = read_rows(missing_path)[1]
    item = next(row for row in missing if row["register_id"] == "AMR-TE-006")
    item.update({
        "item_type": "transferability_scaleup_gap",
        "required_variable": "GreenHub roadside-pulp validation, enzyme activity normalization, and scale-up response",
        "reason_missing_or_assumed": "The lab-scale ryegrass/clover pulp response tables are now transcribed from Dotsenko & Lange (2017); GreenHub roadside-pulp response, enzyme activity basis/lot data, scale-up, and plant energy/reagent costs remain unavailable.",
        "recommended_measurement_or_source": "Use the paper only as a lab comparator; obtain matched GreenHub pulp trials, supplier activity certificates, and scale-up energy/separation measurements before predictive activation.",
        "model_consequence": "Literature response is discoverable, but the GreenHub enzyme scenario remains blocked from predictive use and default activation.",
        "status": "reference_staged_only; model validation open",
    })
    write_csv(missing_path, list(missing[0]), missing)

    global_manifest_path = ROOT / "Greenhub/data/global_audit_package/global_dataset_manifest.csv"
    global_manifest = read_rows(global_manifest_path)[1]
    gm = next(row for row in global_manifest if row["dataset_path"] == "Pre-treatment/Thermal_Enzymatic/enzymatic_treatment_response.csv")
    gm["row_count_observed"] = str(len(current))
    gm["standardized_status_values"] = "literature-reported;qualitative-reported;missing"
    gm["notes"] = "Source data improved for Dotsenko & Lange Tables 1–5; cross-study observations remain reference-only. Predictive enzyme activation is still blocked; existing row identifiers/condition grouping still require audit review."
    write_csv(global_manifest_path, list(global_manifest[0]), global_manifest)

    global_readiness_path = ROOT / "Greenhub/data/global_audit_package/global_dataset_readiness.csv"
    global_readiness = read_rows(global_readiness_path)[1]
    gr = next(row for row in global_readiness if row["dataset_path"] == "Pre-treatment/Thermal_Enzymatic/enzymatic_treatment_response.csv")
    gr["numeric_rows"] = str(sum(bool(row["value"]) for row in current))
    gr["notes"] = "B-tier literature table values now source-located; no unsourced numbers. D1 remains due the audit's duplicate scenario-group identifiers (not duplicated parameter_id/observation_id); blocked from activation pending audit-key review."
    write_csv(global_readiness_path, list(global_readiness[0]), global_readiness)

    global_source_path = ROOT / "Greenhub/data/global_audit_package/global_source_register.csv"
    global_sources = read_rows(global_source_path)[1]
    gs = next(row for row in global_sources if row["source_id"] == SOURCE_ID)
    gs["authors"] = AUTHORS
    gs["notes"] = "Open-access CC BY 4.0 paper; Tables 1–5 are now transcribed at condition level. Cultivated ryegrass/clover pulp, lab-only, reference data; no GreenHub runtime activation."
    write_csv(global_source_path, list(global_sources[0]), global_sources)

    print(json.dumps({
        "dataset": DATA_PATH.relative_to(ROOT).as_posix(),
        "record_count": len(current),
        "source_rows": len(generated),
        "new_numeric_rows": sum(bool(row["value"]) for row in generated),
        "sha256": digest,
        "source_id": SOURCE_ID,
        "activation": "blocked/reference-only",
    }, indent=2))


if __name__ == "__main__":
    main()
