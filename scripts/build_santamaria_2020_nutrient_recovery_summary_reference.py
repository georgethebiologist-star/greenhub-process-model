from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Greenhub" / "data" / "Resource recovery" / "Digestate_and_Separation"
CSV_PATH = OUT / "clover_grass_nutrient_recovery_and_ad_balance_santamaria_2020_reference.csv"
SOURCE_ID = "SRC_SANTAMARIA_FERNANDEZ_2020"
DOI = "10.1007/s12649-019-00842-3"
RETRIEVAL_DATE = "2026-11-08"

FIELDS = [
    "record_id", "source_id", "evidence_class", "activation_state", "feedstock",
    "process_stage", "scale", "stream", "metric", "reported_value", "lower_bound",
    "upper_bound", "relation", "reported_uncertainty", "uncertainty_type", "reported_unit",
    "basis", "data_status", "source_location", "interpretation_note",
]


def row(record_id, *, feedstock, process_stage, scale, stream, metric, unit, basis,
        value="", low="", high="", relation="exact", uncertainty="", uncertainty_type="",
        status="reported_from_source_narrative", location="", note=""):
    return {
        "record_id": record_id,
        "source_id": SOURCE_ID,
        "evidence_class": "B_primary_literature_reported_result",
        "activation_state": "reference_only",
        "feedstock": feedstock,
        "process_stage": process_stage,
        "scale": scale,
        "stream": stream,
        "metric": metric,
        "reported_value": value,
        "lower_bound": str(low) if low != "" else "",
        "upper_bound": str(high) if high != "" else "",
        "relation": relation,
        "reported_uncertainty": str(uncertainty) if uncertainty != "" else "",
        "uncertainty_type": uncertainty_type,
        "reported_unit": unit,
        "basis": basis,
        "data_status": status,
        "source_location": location,
        "interpretation_note": note,
    }


def build_rows():
    rows = []
    # Wet-mass product shares reported in Results for the two small-scale trials.
    for crop, flows in {
        "red clover": {"press cake": 40.1, "brown juice": 53.2, "protein concentrate": 6.7},
        "clover grass": {"press cake": 39.5, "brown juice": 56.8, "protein concentrate": 3.7},
    }.items():
        for stream, share in flows.items():
            rows.append(row(
                f"SF2020-WET-SHARE-{crop.upper().replace(' ', '-')}-{stream.upper().replace(' ', '-')}",
                feedstock=crop, process_stage="small-scale fractionation and protein precipitation",
                scale="small-scale", stream=stream, metric="stream_wet_mass_share",
                value=share, unit="%", basis="fresh biomass input wet mass",
                location="Results, paragraph describing Figs. 1–2",
                note="Source-reported output share; the three shares sum to 100% within each crop in the paper. These are not GreenHub stream yields.",
            ))

    # Abstract-level nutrient distribution ranges; grouped ranges stay grouped.
    range_rows = [
        ("CLOVER-CAKE-C", "red clover and clover grass", "screw pressing", "press cake", "carbon_recovery", 60, 79, "range", "Abstract", "Range across the studied biomass; not crop-specific endpoints."),
        ("CLOVER-CAKE-NPS", "red clover and clover grass", "screw pressing", "press cake", "N_P_S_recovery_grouped", 52, 63, "range", "Abstract", "The abstract reports one shared range for N, P and S; it is not resolved into three analyte-specific endpoint pairs."),
        ("CLOVER-BJ-C", "red clover and clover grass", "protein precipitation", "brown juice", "carbon_recovery", 6, 10, "range", "Abstract", "Range across the studied biomass; not crop-specific endpoints."),
        ("CLOVER-BJ-N", "red clover and clover grass", "protein precipitation", "brown juice", "nitrogen_recovery", 8, 15, "range", "Abstract", "Range across the studied biomass; not crop-specific endpoints."),
        ("CLOVER-BJ-P", "red clover and clover grass", "protein precipitation", "brown juice", "phosphorus_recovery", "", 27, "up_to", "Abstract", "Only an upper limit is reported; lower bound is unknown, not zero."),
        ("CLOVER-BJ-S", "red clover and clover grass", "protein precipitation", "brown juice", "sulfur_recovery", "", 26, "up_to", "Abstract", "Only an upper limit is reported; lower bound is unknown, not zero."),
        ("CLOVER-BJ-K", "red clover and clover grass", "protein precipitation", "brown juice", "potassium_recovery", 19, 31, "range", "Abstract", "Range across the studied biomass; not crop-specific endpoints."),
        ("CLOVER-CAKE-K", "red clover and clover grass", "screw pressing", "press cake", "potassium_recovery", "", 45, "less_than", "Abstract", "The source states less than 45%; no lower limit is reported."),
    ]
    for suffix, crop, stage, stream, metric, low, high, relation, location, note in range_rows:
        rows.append(row(
            f"SF2020-REC-{suffix}", feedstock=crop, process_stage=stage,
            scale="small-scale; crop-specific results combined in source summary", stream=stream,
            metric=metric, low=low, high=high, relation=relation, unit="%",
            basis="analyte mass in stream divided by analyte mass in fresh biomass input",
            status="reported_range_or_bound", location=location,
            note=note + " Not suitable for closing a single-crop component balance.",
        ))

    # Combined residual-stream recoveries reported in the Discussion.
    for analyte, low, high in [
        ("carbon", 66, 89), ("nitrogen", 61, 78), ("phosphorus", 68, 83),
        ("potassium", 62, 71), ("sulfur", 58, 81),
    ]:
        rows.append(row(
            f"SF2020-REC-RESIDUAL-{analyte.upper()}",
            feedstock="red clover and clover grass", process_stage="whole biorefinery fractionation",
            scale="small-scale; aggregate across both crops", stream="press cake + brown juice",
            metric=f"{analyte}_recovery_combined_residual_streams", low=low, high=high,
            relation="range", unit="%",
            basis="analyte input in fresh biomass; combined press cake and brown juice",
            status="reported_range_or_bound", location="Discussion, nutrient recovery across fractions",
            note="Source-reported aggregate range; not attributable to either residual stream separately and not an exact mass-balance closure.",
        ))

    # Crop-specific nutrient fractions entering protein concentrate, as stated in the text.
    for crop, recoveries in {
        "red clover": {"carbon": ("", 10, "less_than"), "nitrogen": (15, 15, "about"), "phosphorus": ("", 10, "less_than"), "potassium": ("", 10, "less_than"), "sulfur": (16, 16, "reported_approximate")},
        "clover grass": {"carbon": ("", 10, "less_than"), "nitrogen": (16, 16, "reported"), "phosphorus": ("", 10, "less_than"), "potassium": ("", 10, "less_than"), "sulfur": (12, 12, "reported")},
    }.items():
        for analyte, (low, high, relation) in recoveries.items():
            value = ""
            if relation in {"reported", "reported_approximate", "about"}:
                value = str(high)
                low = ""
                high = ""
            rows.append(row(
                f"SF2020-REC-PROTEIN-{crop.upper().replace(' ', '-')}-{analyte.upper()}",
                feedstock=crop, process_stage="protein precipitation", scale="small-scale",
                stream="protein concentrate", metric=f"{analyte}_recovery_to_protein_concentrate",
                value=value, low=low, high=high, relation=relation, unit="%",
                basis=f"{analyte} in fresh biomass input",
                status="reported_approximate" if relation in {"about", "reported_approximate"} else "reported_or_upper_bound",
                location="Discussion, nutrient recovery across fractions; Conclusions",
                note="Text-level result; concentration in protein concentrate is not equivalent to product purity or protein mass recovery.",
            ))

    # Complement the already-staged Table 2 CSTR summary with values transcribed from the
    # Results narrative. Keep approximations and source-text conflicts explicit.
    ad_values = [
        ("AD-C-CONVERSION", "clover grass", "press cake + brown juice", "carbon_conversion_to_biogas", "56", "", "", "exact", "%", "influent total carbon", "Results, Fate of Nutrients During Anaerobic Co-digestion", "Source reports conversion of influent total C; not a measured methane leak or a carbon-neutrality credit."),
        ("AD-OM-CONVERSION", "clover grass", "press cake + brown juice", "organic_matter_conversion_to_biogas", "48", "", "", "exact", "%", "influent organic matter; source's COD:VS and theoretical-yield calculation", "Results, anaerobic reactor performance", "Source-calculated conversion; distinct denominator/method from the 56% total-carbon result."),
        ("AD-NH4-SHARE-IN", "clover grass", "brown-juice constituent of influent (source footnote)", "ammonium_nitrogen_share_of_total_nitrogen", "9.4", "", "", "approximate", "%", "total N; source value is annotated as measured in brown juice", "Table 2 footnote; Results, Fate of Nutrients During Anaerobic Co-digestion", "The table gives 9.4 ± 2.7% for brown-juice NH4-N/total-N; this is not a flow-weighted result for the whole feed blend."),
        ("AD-NH4-SHARE-OUT", "clover grass", "digestate", "ammonium_nitrogen_share_of_total_nitrogen", "42.6", "", "", "exact", "%", "total N", "Results, Fate of Nutrients During Anaerobic Co-digestion", "The abstract rounds this to 43%; the results discussion reports 42.6%."),
        ("AD-CN-FEED", "clover grass", "influent blend", "C_to_N_ratio", "17", "", "", "exact", "dimensionless", "mass ratio; Results narrative", "Results, Fate of Nutrients During Anaerobic Co-digestion", "Another Results sentence contains an incompatible C:N comparison; keep this source statement quarantined from runtime use."),
        ("AD-CN-DIGESTATE", "clover grass", "digestate", "C_to_N_ratio", "7.3", "", "", "exact", "dimensionless", "mass ratio; Results narrative", "Results, Fate of Nutrients During Anaerobic Co-digestion", "Another Results sentence contains an incompatible C:N comparison; keep this source statement quarantined from runtime use."),
        ("AD-TS-IN", "clover grass", "influent blend", "total_solids_concentration", "99.7", "", "", "exact", "g/kg", "fresh matter", "Table 2, text-layer table extraction", "Mean ± SD is 99.7 ± 7.0 g/kg; table layout is malformed in the proof PDF, so retain the source note and cross-check against narrative TS removal."),
        ("AD-TS-OUT", "clover grass", "digestate", "total_solids_concentration", "51.1", "", "", "exact", "g/kg", "fresh matter", "Table 2, text-layer table extraction", "Mean ± SD is 51.1 ± 7.4 g/kg; table layout is malformed in the proof PDF, so retain the source note and cross-check against narrative TS removal."),
        ("AD-VS-IN", "clover grass", "influent blend", "volatile_solids_concentration", "80.5", "", "", "exact", "g/kg", "fresh matter", "Table 2, text-layer table extraction", "Mean ± SD is 80.5 ± 7.0 g/kg; table layout is malformed in the proof PDF, so retain the source note."),
        ("AD-VS-OUT", "clover grass", "digestate", "volatile_solids_concentration", "34.6", "", "", "exact", "g/kg", "fresh matter", "Table 2, text-layer table extraction", "Mean ± SD is 34.6 ± 6.5 g/kg; table layout is malformed in the proof PDF, so retain the source note."),
        ("AD-C-IN", "clover grass", "influent blend", "total_carbon_concentration", "43.3", "", "", "exact", "g/kg", "fresh matter", "Results, digestate mass-balance paragraph", "The malformed Table 2 text layer contains a nearby 43.4 value; narrative value 43.3 is kept with its own source location, not silently reconciled."),
        ("AD-C-OUT", "clover grass", "digestate", "total_carbon_concentration", "19.1", "", "", "exact", "g/kg", "fresh matter", "Results, digestate mass-balance paragraph", "The source attributes the decrease to carbon transferred to biogas; not a complete elemental carbon balance because gas flow and carbon in other outputs are not fully available here."),
        ("AD-NTOT-APPROX", "clover grass", "influent and digestate (source says concentrations remain similar)", "total_nitrogen_concentration", "2.5", "", "", "approximately", "g/kg", "fresh matter", "Results, digestate mass-balance paragraph", "Approximate narrative value, not a separately verified inlet/outlet pair."),
        ("AD-P-APPROX", "clover grass", "influent and digestate (source says concentrations remain similar)", "total_phosphorus_concentration", "0.3", "", "", "approximately", "g/kg", "fresh matter", "Results, digestate mass-balance paragraph", "Approximate narrative value; source notes possible measurement error and start-up inoculum contribution."),
        ("AD-K-APPROX", "clover grass", "influent and digestate (source says concentrations remain similar)", "total_potassium_concentration", "3.3", "", "", "approximately", "g/kg", "fresh matter", "Results, digestate mass-balance paragraph", "Approximate narrative value, not a separately verified inlet/outlet pair."),
        ("AD-S-APPROX", "clover grass", "influent and digestate (source says concentrations remain similar)", "total_sulfur_concentration", "0.2", "", "", "approximately", "g/kg", "fresh matter", "Results, digestate mass-balance paragraph", "Approximate narrative value; source notes possible measurement error and start-up inoculum contribution."),
        ("AD-NPK-RATIO", "clover grass", "digestate", "N_to_P_to_K_ratio", "4:1:12", "", "", "source_reported_ratio", "ratio", "inorganic N basis; order N:P:K", "Discussion, fertilizer-value paragraph", "Not a guaranteed fertilizer specification or substitution factor."),
        ("AD-CN-CONFLICT-ALT", "clover grass", "influent/digestate; assignment unclear", "C_to_N_ratio_alternative_text_report", "19.2; 20.0; 12.8", "", "", "quarantined_conflict", "dimensionless", "article's Results prose; exact pairing unclear", "Results, digestate mass-balance paragraph", "The article also reports these C:N values in a sentence whose pairing/context is ambiguous relative to the separately reported 17 and 7.3. Preserved as a conflict marker; do not use numerically."),
    ]
    for suffix, crop, stream, metric, value, low, high, relation, unit, basis, location, note in ad_values:
        uncertainty = ""
        uncertainty_type = ""
        if suffix in {"AD-TS-IN", "AD-TS-OUT", "AD-VS-IN", "AD-VS-OUT"}:
            uncertainty = {"AD-TS-IN": "7.0", "AD-TS-OUT": "7.4", "AD-VS-IN": "7.0", "AD-VS-OUT": "6.5"}[suffix]
            uncertainty_type = "standard deviation as extracted from Table 2"
        elif suffix == "AD-NH4-SHARE-IN":
            uncertainty = "2.7"
            uncertainty_type = "standard deviation for brown-juice result"
        rows.append(row(
            f"SF2020-{suffix}", feedstock=crop,
            process_stage="anaerobic co-digestion", scale="3-L semi-continuous CSTR",
            stream=stream, metric=metric, value=value, low=low, high=high,
            relation=relation, uncertainty=uncertainty, uncertainty_type=uncertainty_type,
            unit=unit, basis=basis,
            status="quarantined_source_conflict" if relation == "quarantined_conflict" else "reported_with_basis_or_table_caveat" if "malformed" in note or "conflict" in note else "reported_from_source_narrative",
            location=location, note=note,
        ))

    # Source-calculated theoretical potential is distinct from measured reactor yield.
    rows.append(row(
        "SF2020-AD-THEORETICAL-CH4-MAX", feedstock="clover grass",
        process_stage="anaerobic co-digestion", scale="3-L semi-continuous CSTR",
        stream="press cake + brown juice influent", metric="theoretical_maximum_methane_yield",
        value="490", unit="mL CH4/g VS", basis="source-reported COD:VS ratio 1.4; Buswell equation",
        status="source_calculated_not_measured", location="Results, anaerobic reactor performance",
        note="Model-calculated theoretical maximum; not experimental BMP and not comparable to a measured yield without matching basis/conditions.",
    ))
    return rows


def _register_manifest(row_data):
    manifest_path = OUT / "dataset_manifest.csv"
    fields = ["filename", "purpose", "row_count", "populated_numeric_rows", "missing_rows", "integration_status", "schema"]
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != fields:
                raise ValueError(f"Unexpected manifest columns: {reader.fieldnames}")
            manifest = list(reader)
    else:
        manifest = []
    if not any(item.get("filename") == row_data["filename"] for item in manifest):
        manifest.append(row_data)
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    sidecar = {
        "dataset_identifier": "urn:greenhub:dataset:santamaria-fernandez-clover-grass-nutrient-recovery-ad-summary-2020:v1",
        "persistent_identifier_status": "The DOI identifies the article, not this GreenHub extract.",
        "source_file": CSV_PATH.name,
        "dataset_version": "1.0.0",
        "title": "Reported fraction yields, nutrient recovery ranges and residual anaerobic-digestion outcomes from a clover-grass biorefinery",
        "citation": "Santamaria-Fernandez, M., Ytting, N. K., Lübeck, M., & Uellendahl, H. (2020). Potential Nutrient Recovery in a Green Biorefinery for Production of Feed, Fuel and Fertilizer for Organic Farming. Waste and Biomass Valorization, 11, 5901–5911. https://doi.org/10.1007/s12649-019-00842-3",
        "doi": DOI,
        "source_url": f"https://doi.org/{DOI}",
        "full_text_url": "https://vbn.aau.dk/ws/files/450867530/e.Proofing.pdf",
        "retrieval_date": RETRIEVAL_DATE,
        "geography": "Denmark; red clover and clover-grass small-scale trials and a Foulum pilot-derived CSTR feed.",
        "evidence_class": "B_primary_literature_reported_and_source_calculated_values",
        "license_and_reuse": "The Aalborg University accepted-manuscript record carries a private-study/source-URL redistribution notice; no CC BY license was verified for this source. This CSV is a factual transcription/summary, not a copy of the article. Verify publisher reuse terms before redistributing the extract externally.",
        "source_data_availability": "The article reports experimental analyses and process-flow data in the paper; no machine-readable raw-data package was identified in the repository record during this pass.",
        "row_count": len(rows),
        "source_scope": "Small-scale red-clover and clover-grass fractionation, plus pilot-derived clover-grass press-cake/brown-juice anaerobic co-digestion. Cultivated Danish forage, not roadside/VARTA grass.",
        "extraction_scope": "The companion 69-row dataset already contains Table 1 composition and Table 2 operating summaries. This additional extract captures wet product-share values and recovery ranges/outcomes stated in the abstract and narrative, plus selected Table 2 inlet/effluent values recovered from the article text layer.",
        "basis_and_conversion": "Direct source transcription. Percentage recovery ranges refer to source-defined nutrient mass in the named fraction relative to input; grouped analyte ranges remain grouped. No cross-feedstock averaging, missing-value imputation, conversion, or mass-balance closure was performed.",
        "quality_notes": [
            "Ranges are source-reported across crop types; range endpoints are not assigned to an individual crop unless the source explicitly does so.",
            "The source's Table 2 text layer is malformed. TS/VS and other narrative values are flagged; no uncertain table cells are repaired by inference.",
            "The paper contains incompatible/ambiguous C:N statements (17 to 7.3 versus a separate 19.2/20.0/12.8 passage). The alternate passage is retained as quarantined text and not reconciled.",
            "P and S concentrations in digestate may be influenced by measurement error and inoculum during start-up, as the authors note.",
            "Digestate composition is not a nutrient-recovery efficiency, plant uptake, legal product grade, or fertilizer-substitution factor.",
            "All rows are reference-only; no parameter, model default, TEA/LCA credit, process route, or Pareto scenario consumes them."
        ],
        "activation_state": "reference_only",
        "readiness": "D3",
        "phase_tags": ["Phase 3: fractionation stream flows and nutrient partition", "Phase 4: protein concentrate nutrient recovery", "Phase 5: residual AD", "Phase 7: digestate composition and fertilizer-use context"],
        "fair_metadata": {
            "findable": "Repository-local URN, title, article DOI, source ID and direct full-text URL are recorded.",
            "accessible": "CSV and JSON sidecar are local; the source article is linked at the Aalborg University repository.",
            "interoperable": "Long-form UTF-8 CSV uses stable record/source IDs, explicit bounds/operators, process stream, basis, unit, source location and status.",
            "reusable": "Citation, retrieval date, extraction method, rights caveat, uncertainty, source conflicts and transfer limits are included."
        }
    }
    CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    _register_manifest({
        "filename": CSV_PATH.name,
        "purpose": "Source-narrative wet product shares and nutrient-recovery ranges plus residual CSTR digestate outcomes; reference-only and with source conflicts flagged.",
        "row_count": str(len(rows)),
        "populated_numeric_rows": str(sum(bool(item["reported_value"] or item["lower_bound"] or item["upper_bound"]) for item in rows)),
        "missing_rows": str(sum(not (item["reported_value"] or item["lower_bound"] or item["upper_bound"]) for item in rows)),
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "schema": "stable record/source IDs; stream; recovery or assay metric; reported value or bounds/operator; unit/basis; source location; caveats",
    })


if __name__ == "__main__":
    build()
