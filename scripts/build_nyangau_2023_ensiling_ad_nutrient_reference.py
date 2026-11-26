from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"
CSV_PATH = OUT / "nyangau_2023_brown_juice_ensiling_ad_digestate_nutrient_reference.csv"
SOURCE_ID = "SRC-NYANGAU-2023-BJ-ENSILING-AD-NUTRIENT"
DOI = "10.1016/j.eti.2023.103248"
RETRIEVAL_DATE = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "evidence_class", "activation_state", "table_id",
    "experiment_scale", "material", "treatment", "condition", "metric",
    "reported_mean", "reported_uncertainty", "uncertainty_type", "significance_group",
    "reported_unit", "basis", "replicate_n", "data_status", "source_location", "notes",
]


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.upper()).strip("-")


def _add(
    rows: list[dict[str, str]], *, table: str, scale: str, material: str,
    treatment: str, condition: str, metric: str, value, unit: str, basis: str,
    n: str = "", uncertainty_type: str = "", group: str = "",
    location: str = "", note: str = "", status: str = "reported",
) -> None:
    mean = ""
    uncertainty = ""
    qualifier = ""
    if isinstance(value, tuple):
        mean, uncertainty = (str(part) for part in value[:2])
        if len(value) > 2:
            group = str(value[2])
    elif value == "bdl":
        status, qualifier = "below_detection_limit", "bdl"
    elif value is None or value == "—":
        status = "not_reported_or_not_applicable"
    else:
        mean = str(value)
    if qualifier:
        note = (note + "; " if note else "") + f"Source qualifier: {qualifier}; not converted to zero."
    rows.append({
        "record_id": f"NYANGAU23-{_slug(table)}-{_slug(scale)}-{_slug(material)}-{_slug(metric)}-{_slug(condition)}",
        "source_id": SOURCE_ID,
        "evidence_class": "B_measured_primary_literature",
        "activation_state": "reference_only",
        "table_id": table,
        "experiment_scale": scale,
        "material": material,
        "treatment": treatment,
        "condition": condition,
        "metric": metric,
        "reported_mean": mean,
        "reported_uncertainty": uncertainty,
        "uncertainty_type": uncertainty_type,
        "significance_group": group,
        "reported_unit": unit,
        "basis": basis,
        "replicate_n": n,
        "data_status": status,
        "source_location": location,
        "notes": note,
    })


def _add_matrix(rows, *, table, scale, records, metrics, units, bases, n, uncertainty_type, location, note=""):
    for material, treatment, values in records:
        for metric, unit, basis, value in zip(metrics, units, bases, values, strict=True):
            _add(
                rows, table=table, scale=scale, material=material, treatment=treatment,
                condition=treatment, metric=metric, value=value, unit=unit, basis=basis,
                n=n, uncertainty_type=uncertainty_type, location=location, note=note,
            )


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    # Table 1, first panel: direct transcription of means ± SD (n=3).
    t1_top_metrics = ["dry_matter", "volatile_solids", "ash", "pH", "carbon", "nitrogen", "oxygen", "sulfur", "hydrogen", "C_to_N_ratio", "ammonium_nitrogen"]
    t1_top_units = ["%", "%", "%", "dimensionless", "%", "%", "%", "%", "%", "ratio", "mg/kg"]
    t1_top_bases = ["fresh matter", "dry matter", "dry matter", "as measured", "dry matter", "dry matter", "dry matter", "dry matter", "dry matter", "elemental mass ratio", "fresh matter"]
    t1_top = [
        ("StrawField", "field-scale raw straw", [(53.8, .20), (94.6, .20), (5.4, .01), 7.89, 45.8, .41, 44.7, .06, 6.4, 117.0, None]),
        ("Strawfieldsilage", "field-scale straw silage", [(74.1, .08), (95.2, .13), (4.8, .04), 7.92, 42.6, .40, 46.8, .09, 6.7, 107.7, 120]),
        ("Straw+BJfieldsilage", "field-scale brown-juice-assisted straw silage", [(75.1, .08), (93.5, .11), (6.5, .11), 7.81, 42.8, .40, 44.9, .08, 6.8, 105.8, 200]),
        ("StrawLab", "lab-scale raw straw", [(87.7, .28), (95.2, .70), (4.8, .70), 6.67, 44.0, .40, 44.9, .13, 6.5, 106.4, 280]),
        ("Straw+BJLab", "lab-scale straw mixed with brown juice, not ensiled", [(32.0, .63), (95.1, .01), (4.9, .01), 5.97, 42.6, .55, 48.5, .08, 6.9, 95.1, 160]),
        ("Straw+BJLabsilage", "lab-scale brown-juice-assisted straw silage", [(30.2, .29), (94.1, .27), (5.9, .03), 3.81, 44.8, 1.02, 44.9, .10, 7.4, 43.8, 400]),
        ("Press cake", "lab-scale raw grass-biorefinery press cake", [(37.1, .49), (94.7, 3.05), (5.3, 3.05), 4.38, 44.3, 2.90, 43.2, .14, 7.5, 15.4, None]),
        ("Press cake+BJlabsilage", "lab-scale press-cake/brown-juice silage", [(27.7, .05), (94.9, .03), (5.1, .03), 3.51, 46.2, 3.04, 42.6, .16, 8.0, 15.2, None]),
    ]
    _add_matrix(rows, table="Table 1", scale="field and laboratory; per treatment", records=t1_top,
                metrics=t1_top_metrics, units=t1_top_units, bases=t1_top_bases, n="3",
                uncertainty_type="standard deviation", location="Table 1, first panel",
                note="Elemental analyses and NH4-N are source-reported; no mass-balance reconstruction performed.")

    # Table 1, second panel: fibre, fermentation chemistry and ensiling DM-loss values.
    t1_bottom_metrics = ["neutral_detergent_fiber", "acid_detergent_fiber", "hemicellulose", "cellulose", "lignin", "neutral_detergent_soluble_fiber", "citric_acid", "lactic_acid", "acetic_acid", "total_sugars", "dry_matter_loss"]
    t1_bottom_units = ["%", "%", "%", "%", "%", "%", "g/kg", "g/kg", "g/kg", "g/kg", "%"]
    t1_bottom_bases = ["dry matter"] * 6 + ["fresh matter"] * 4 + ["dry matter basis; source-reported loss"]
    t1_bottom = [
        ("StrawField", "field-scale raw straw", [(85.6, .68), (47.1, 1.22), (38.5, .76), (34.1, .58), (13.0, 4.43), (14.4, .56), "bdl", "bdl", "bdl", "bdl", None]),
        ("Strawfieldsilage", "field-scale straw silage", [(83.1, .43), (53.2, 1.59), (29.9, 1.07), (43.6, .61), (9.7, 3.93), (16.9, .36), "bdl", "bdl", "bdl", "bdl", 15.5]),
        ("Straw+BJfieldsilage", "field-scale brown-juice-assisted straw silage", [(81.5, .92), (52.3, .84), (29.2, .45), (43.6, .54), (8.7, 4.92), (18.5, .75), "bdl", "bdl", "bdl", "bdl", 14.4]),
        ("StrawLab", "lab-scale raw straw", [(82.6, .90), (49.6, .17), (33.1, .71), (42.3, .27), (7.2, 1.46), (17.4, .75), 1.15, "bdl", 1.95, 1.5, None]),
        ("Straw+BJLab", "lab-scale straw mixed with brown juice, not ensiled", [(82.3, .43), (50.0, .86), (32.4, .12), (42.4, .49), (7.6, 2.85), (17.7, .35), .24, .74, .37, 3.3, 0]),
        ("Straw+BJLabsilage", "lab-scale brown-juice-assisted straw silage", [(74.8, .53), (45.8, .21), (29.0, .48), (38.7, .06), (7.1, .70), (25.5, .39), "bdl", 21.3, 3.08, 1.3, 5.6]),
        ("Press cake", "lab-scale raw grass-biorefinery press cake", [(64.0, .29), (37.2, 2.13), (26.9, .97), (34.5, .74), (2.7, 2.84), (36.0, .18), "bdl", 6.83, 1.56, 6.6, 0]),
        ("Press cake+BJlabsilage", "lab-scale press-cake/brown-juice silage", [(64.0, 1.79), (39.2, 3.56), (24.8, 1.24), (36.6, 1.31), (2.6, 3.99), (36.0, 1.15), "bdl", None, None, None, 4.5]),
    ]
    _add_matrix(rows, table="Table 1", scale="field and laboratory; per treatment", records=t1_bottom,
                metrics=t1_bottom_metrics, units=t1_bottom_units, bases=t1_bottom_bases, n="3",
                uncertainty_type="standard deviation", location="Table 1, second panel",
                note="bdl is preserved as censored below-detection status, not zero; em dash/missing cells stay blank.")

    # Table 2 digestate/manure chemistry; report means and only table-provided SDs.
    t2_metrics = ["dry_matter", "volatile_solids", "ash", "pH", "total_nitrogen", "ammonium_nitrogen_to_total_nitrogen", "total_carbon", "total_sulfur", "sulfate_sulfur", "C_to_N_ratio", "C_to_S_ratio", "N_to_S_ratio", "CSTR_methane_yield", "sulfate_sulfur_to_total_sulfur", "sulfate_plus_sulfide_sulfur_to_total_sulfur"]
    t2_units = ["%", "%", "%", "dimensionless", "g/kg", "%", "g/kg", "g/kg", "g/kg", "ratio", "ratio", "ratio", "NL CH4/kg VS", "%", "%"]
    t2_bases = ["fresh matter", "dry matter", "dry matter", "as measured", "fresh matter", "of total nitrogen", "fresh matter", "fresh matter", "fresh matter", "elemental mass ratio", "elemental mass ratio", "elemental mass ratio", "volatile solids; CSTR, last 25-day HRT", "of total sulfur", "of total sulfur"]
    t2 = [
        ("Cattle Manure 1 (CM1)", "field-scale experiment; raw manure", [(6.18,.09),(78.6,.35),(21.4,.35),7.34,(2.77,.03),49.1,(25.2,.72),(.36,.009),.063,9.1,70.1,7.7,None,17.5,30.0]),
        ("Digested CM1", "field-scale experiment; mono-digested manure", [(3.51,.02),(69.1,.30),(30.9,.30),8.07,(2.79,.01),62.2,(13.3,.21),(.22,.005),.011,4.8,59.6,12.5,(209,5.0),4.9,8.7]),
        ("Co-dig CM1+Strawfield", "field-scale experiment; non-ensiled straw", [(7.19,.06),(82.4,.33),(17.6,.33),7.64,(2.81,.08),54.0,(22.9,.99),(.28,.006),.011,8.2,82.4,10.1,(179,3.6),4.0,8.5]),
        ("Co-dig CM1+Strawfieldsilage", "field-scale experiment; straw silage", [(6.96,.03),(80.5,.07),(19.5,.07),7.76,(3.00,.05),54.3,(18.7,.38),(.26,.009),.012,6.2,72.3,11.6,(186,2.4),4.6,10.0]),
        ("Co-dig CM1+Straw+BJfieldsilage", "field-scale experiment; brown-juice-assisted straw silage", [(7.04,.14),(80.2,.56),(19.8,.56),7.80,(2.97,.03),54.4,(13.6,.26),(.23,.009),.012,4.6,58.1,12.7,(190,3.2),5.1,10.7]),
        ("Cattle manure 2 (CM2)", "laboratory-scale experiment; raw manure", [(6.73,.13),(80.3,.52),(19.7,.52),6.94,(2.50,.02),45.3,(28.8,.27),(.38,.007),.045,11.5,76.4,6.6,None,11.9,24.9]),
        ("Co-dig CM2+Straw+BJlab", "laboratory-scale experiment; brown juice added, not ensiled", [(7.09,.20),(83.0,.32),(17.0,.32),7.48,(2.52,.06),51.1,(29.6,.45),(.33,.006),.012,11.7,89.6,7.6,(196,9.0),3.6,8.2]),
        ("Co-dig CM2+straw+BJlabsilage", "laboratory-scale experiment; brown-juice-assisted straw silage", [(6.85,.17),(81.6,.22),(18.4,.22),7.48,(2.58,.03),51.1,(20.3,.71),(.34,.021),.015,7.9,59.5,7.6,(204,9.9),4.4,8.3]),
        ("Co-dig CM2+Press cake", "laboratory-scale experiment; non-ensiled press cake", [(5.33,.10),(76.6,.15),(23.4,.15),7.59,(3.17,.03),47.6,(20.2,.25),(.31,.005),.013,6.4,66.2,10.4,(216,9.0),4.3,12.4]),
        ("Co-dig CM2+Press cake+BJlabsilage", "laboratory-scale experiment; brown-juice-assisted press-cake silage", [(5.34,.04),(76.7,.14),(23.3,.14),7.57,(3.26,.03),48.6,(16.0,.21),(.33,.008),.013,4.9,49.0,10.0,(221,7.2),4.0,11.3]),
    ]
    _add_matrix(rows, table="Table 2", scale="continuous stirred-tank digestion; manure and co-digestates", records=t2,
                metrics=t2_metrics, units=t2_units, bases=t2_bases, n="3",
                uncertainty_type="standard deviation when printed", location="Table 2",
                note="CSTR methane yield is the source-reported mean in the final 25-day HRT; blank manure-only yields are not zeros.")

    # Table 3 BMP and model fit metrics; means ± SE, n=3. Preserve table's k unit as printed.
    t3_metrics = ["batch_BMP", "Gompertz_B0", "Gompertz_maximum_methane_rate", "Gompertz_R2", "Gompertz_RMSE", "first_order_B0", "first_order_k", "first_order_R2", "first_order_RMSE"]
    t3_units = ["mL CH4/g VS", "mL CH4/g VS", "mL CH4/g VS/day", "dimensionless", "mL CH4/g VS", "mL CH4/g VS", "day (as printed)", "dimensionless", "mL CH4/g VS"]
    t3_bases = ["volatile solids", "volatile solids; fitted modified Gompertz model", "volatile solids per day; fitted modified Gompertz model", "model fit", "model fit", "volatile solids; fitted first-order model", "first-order model rate constant; equation defines rate per time", "model fit", "model fit"]
    t3 = [
        ("StrawLab", [(290.2,4.7,"a"),(265.3,3.9,"ab"),(11.8,.22,"bc"),.98,14.83,(291.3,3.7,"ab"),(.051,.0,"ab"),.98,13.77]),
        ("Straw+BJlab", [(287.8,3.3,"a"),(266.6,4.7,"ab"),(11.9,.02,"c"),.98,13.37,(291.8,4.0,"ab"),(.051,.0,"ab"),.98,13.83]),
        ("Straw+BJlabsilage", [(329.9,3.4,"b"),(297.2,1.9,"b"),(14.6,.16,"d"),.98,17.07,(325.7,1.8,"b"),(.055,.0,"b"),.98,16.47]),
        ("StrawField", [(280.7,7.3,"a"),(249.3,5.1,"a"),(10.1,.38,"ab"),.92,22.74,(249.6,4.5,"a"),(.092,.0,"c"),.95,17.87]),
        ("Strawfieldsilage", [(281.0,14.3,"a"),(258.0,14.9,"ab"),(10.5,.07,"abc"),.97,15.62,(284.2,12.0,"ab"),(.047,.0,"ab"),.98,13.87]),
        ("Straw+BJfieldsilage", [(291.0,11.8,"a"),(270.9,15.4,"ab"),(9.7,.50,"a"),.97,16.56,(297.8,13.2,"b"),(.043,.0,"a"),.98,12.75]),
    ]
    for treatment, values in t3:
        for metric, unit, basis, value in zip(t3_metrics, t3_units, t3_bases, values, strict=True):
            _add(rows, table="Table 3", scale="batch BMP experiment; field- and lab-scale substrate preparation",
                 material="wheat straw", treatment=treatment, condition=treatment, metric=metric,
                 value=value, unit=unit, basis=basis, n="3", uncertainty_type="standard error when printed",
                 location="Table 3", note="Model-fit results are not direct measurements. The paper's equation defines k as a rate per time although the table header prints 'day'; original table unit is preserved.")

    # Table 4 soil incubation: concentration series, not fertilizer substitution or nutrient recovery.
    soil_times = [0, 2, 7, 14, 28, 50, 80]
    soil_series = [
        ("field-scale", "Control", [ (25.4,.78,"a"),(26.1,.32,"a"),(26.3,.21,"a"),(26.6,.17,"a"),(27.7,.64,"a"),(29.4,.06,"a"),(32.6,.99,"a") ]),
        ("field-scale", "Cattle Manure 1 (CM1)", [ (113.9,7.64,"bc"),(79.5,.52,"b"),(97.6,1.40,"b"),(108.6,9.02,"b"),(112.5,5.82,"b"),(119.3,2.43,"b"),(130.2,1.90,"c") ]),
        ("field-scale", "Digested CM1", [ (141.8,13.83,"c"),(136.4,2.26,"e"),(145.4,2.13,"d"),(145.3,1.70,"d"),(148.6,2.14,"e"),(155.6,2.69,"d"),(163.6,1.41,"d") ]),
        ("field-scale", "Co-dig CM1+Strawfield", [ (105.7,1.91,"b"),(123.5,3.18,"c"),(128.4,2.91,"c"),(125.3,3.47,"c"),(116.6,1.99,"bc"),(116.9,6.20,"b"),(120.1,6.47,"b") ]),
        ("field-scale", "Co-dig CM1+Strawfieldsilage", [ (122.0,11.99,"b"),(134.5,5.89,"de"),(130.4,1.43,"c"),(129.9,1.11,"c"),(125.3,1.45,"cd"),(124.6,1.55,"bc"),(135.3,.26,"c") ]),
        ("field-scale", "Co-dig CM1+Straw+BJfieldsilage", [ (121.4,13.51,"bc"),(126.2,2.33,"cd"),(129.0,1.56,"c"),(127.5,1.12,"c"),(128.2,4.66,"d"),(129.2,.99,"c"),(131.5,1.30,"c") ]),
        ("laboratory-scale", "Control", [ (25.4,.78,"A"),(26.1,.32,"A"),(26.3,.21,"A"),(26.6,.17,"A"),(27.7,.64,"A"),(29.4,.06,"A"),(32.6,.99,"A") ]),
        ("laboratory-scale", "Cattle manure 2 (CM2)", [ (103.9,4.86,"B"),(73.8,1.69,"B"),(85.3,1.37,"B"),(88.7,1.53,"B"),(102.1,2.78,"B"),(107.2,2.39,"B"),(117.5,3.11,"B") ]),
        ("laboratory-scale", "Co-dig CM2+Straw+BJlab", [ (121.4,10.61,"B"),(122.2,2.75,"DE"),(120.2,2.59,"CD"),(119.6,2.75,"C"),(119.6,1.63,"CD"),(122.3,4.07,"C"),(123.3,1.66,"BC") ]),
        ("laboratory-scale", "Co-dig CM2+straw+BJlabsilage", [ (120.4,10.29,"B"),(124.2,3.85,"E"),(128.1,6.66,"D"),(126.9,1.89,"C"),(120.6,1.72,"C"),(122.1,1.01,"C"),(129.6,.28,"CD") ]),
        ("laboratory-scale", "Co-dig CM2+Press cake", [ (109.7,11.72,"B"),(110.7,8.29,"CD"),(115.3,3.65,"C"),(118.3,3.01,"C"),(125.9,.87,"DE"),(130.3,1.72,"D"),(139.3,4.17,"D") ]),
        ("laboratory-scale", "Co-dig CM2+Press cake+BJlabsilage", [ (99.5,13.86,"B"),(108.4,3.56,"C"),(118.7,4.21,"CD"),(121.4,6.06,"C"),(127.1,1.07,"E"),(132.5,1.45,"D"),(138.3,3.97,"D") ]),
    ]
    for scale, material, values in soil_series:
        for day, value in zip(soil_times, values, strict=True):
            _add(rows, table="Table 4", scale=scale, material=material, treatment=material,
                 condition=f"{day} days after amendment", metric="soil_inorganic_nitrogen_concentration",
                 value=value, unit="mg N/kg soil", basis="soil; digestate/manure application at 200 mg N/kg soil; 10 °C incubation",
                 n="3", uncertainty_type="standard deviation", location="Table 4",
                 note="Soil incubation concentration, not a direct fertilizer-substitution factor or plant uptake. Significance letters are source-reported.")

    return rows


def _append_unique(path: Path, row: dict[str, str], key: str) -> None:
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            existing = list(reader)
        if key in (fields or []) and any(item.get(key) == row[key] for item in existing):
            return
        if list(row) != fields:
            raise ValueError(f"Unexpected columns in {path}: {fields}")
        existing.append(row)
    else:
        fields = list(row)
        existing = [row]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    citation = "Nyang’au, J. O., Møller, H. B., Larsen, S. U., & Sørensen, P. (2023). Brown juice assisted ensiling of straw and press cake for enhanced biogas production and nutrient availability in digestates. Environmental Technology & Innovation, 32, 103248. https://doi.org/10.1016/j.eti.2023.103248"
    source_url = "https://doi.org/10.1016/j.eti.2023.103248"
    pdf_url = "https://pure.au.dk/portal/files/328744571/Nyang_au_et_al_2023b_Brown_juice_assisted_ensiling_of_straw_and_press_cake_for_enhanced_biogas_production_and_nutrient_availability_in_digestates.pdf"
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:ad:nyangau-brown-juice-ensiling-ad-digestate-nutrient-2023:v1",
        "persistent_identifier_status": "Repository-local URN identifies this extract; DOI identifies the cited article, not this transcription.",
        "dataset_version": "1.0.0",
        "source_file": CSV_PATH.name,
        "title": "Brown-juice ensiling, anaerobic digestion, digestate chemistry and soil inorganic nitrogen reference observations",
        "citation": citation,
        "persistent_identifier": f"doi:{DOI}",
        "source_url": source_url,
        "open_full_text_url": pdf_url,
        "retrieval_date": RETRIEVAL_DATE,
        "publication_year": 2023,
        "geography": "Denmark; winter wheat straw harvested near Thisted and Hanstholm; grass-biorefinery press cake and brown juice produced at Aarhus University Foulum.",
        "evidence_class": "B_measured_primary_literature",
        "license": "CC BY 4.0, stated in the published article.",
        "source_data_availability": "The article states that data are available on request; this extract transcribes values explicitly reported in Tables 1–4 of the open full text.",
        "material_scope": "Wheat straw, grass-biorefinery press cake and brown juice co-ensiled or not ensiled, anaerobically co-digested with cattle manure; CSTR digestates tested in a Danish soil incubation.",
        "row_count": len(rows),
        "source_tables": {
            "Table 1": "Feed/silage composition, fibre, acids, sugars and DM loss; means ± SD, n=3.",
            "Table 2": "Raw manure and CSTR digestate composition and last-HRT methane yields; means and SD where shown, n=3.",
            "Table 3": "Batch BMP and Gompertz/first-order model fit parameters; means ± SE, n=3.",
            "Table 4": "Soil inorganic-N concentration on days 0, 2, 7, 14, 28, 50 and 80; means ± SD, n=3.",
        },
        "processing": "Direct table transcription into a long-form CSV. No unit conversion, interpolation, digitization from figures, balance closure, averaging across materials, or fitting beyond models already reported in the source.",
        "uncertainty": "Source table uncertainties and significance letters are preserved where printed. Cells marked below detection remain censored; dashes and unreported cells are blank and status-coded, never converted to zero.",
        "activation_state": "reference_only",
        "readiness": "D3",
        "phase_tags": ["Phase 2: ensiling", "Phase 5: anaerobic digestion", "Phase 7: digestate nutrient availability"],
        "applicability_limit": "Not Dutch roadside grass and not a GreenHub operating dataset. Wheat straw and manure dominate several treatments; brown juice came from a grass-biorefinery route with heated protein precipitation and differs from GreenHub isoelectric supernatant. Use only as a comparability source, not as a runtime default or fertilizer-substitution credit.",
        "limitations": [
            "The experiment is Denmark-specific and includes wheat straw, cattle manure, cultivated forage-derived brown juice, and grass-biorefinery press cake; it does not test Dutch roadside grass as the principal feedstock.",
            "Soil inorganic-N concentrations are not nutrient recovery from feed, crop uptake, regulatory fertilizer value, or a substitution credit.",
            "CSTR methane yields and batch BMP values have different methods and boundaries; do not merge them.",
            "Table 3 prints the first-order k unit as day while the paper's equation defines a rate per time; the table unit is kept and flagged rather than silently corrected.",
            "The dataset omits supplementary tables/figures and any observations not explicitly present in Tables 1–4.",
            "No GreenHub parameter, default, calculation, route, API/UI behavior, TEA/LCA factor, or Pareto scenario consumes these rows."
        ],
        "fair_metadata": {
            "findable": "Repository-local dataset URN, descriptive title, DOI, full-text URL and source table references are recorded.",
            "accessible": "CSV and JSON sidecar are stored in the repository; the cited full-text article is open access.",
            "interoperable": "UTF-8 long-form CSV provides stable record/source IDs, table, metric, reported unit, basis, uncertainty, missingness and experiment context.",
            "reusable": "Citation, CC BY 4.0, source scope, retrieval date, transcription method, uncertainty, limits and non-activation are documented."
        }
    }
    CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    source_row = {
        "source_id": SOURCE_ID,
        "source_title": "Brown juice assisted ensiling of straw and press cake for enhanced biogas production and nutrient availability in digestates",
        "authors": "Jared Onyango Nyang’au; Henrik Bjarne Møller; Søren Ugilt Larsen; Peter Sørensen",
        "year": "2023",
        "doi_or_stable_id": DOI,
        "source_type": "peer-reviewed primary experimental article; Tables 1–4 transcribed",
        "url": source_url,
        "material_scope": "Wheat straw, green-biorefinery press cake and brown juice, cattle manure, CSTR digestates and soil incubation",
        "quality_notes": "CC BY 4.0. Tables 1–4 transcribed with source bases, uncertainty and missingness. Reference-only D3; not Dutch roadside grass, not direct GreenHub stream data, and not a fertilizer-substitution factor.",
    }
    for register_name in ("source_register.csv", "ad_source_register.csv"):
        _append_unique(OUT / register_name, source_row, "source_id")

    manifest_row = {
        "filename": CSV_PATH.name,
        "description": "Tables 1–4: straw/press-cake/brown-juice properties, reported BMP/model metrics, CSTR digestate chemistry, and 80-day soil inorganic-N concentrations; reference-only.",
        "row_count": str(len(rows)),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "record_id",
    }
    _append_unique(OUT / "dataset_manifest.csv", manifest_row, "filename")


if __name__ == "__main__":
    build()
