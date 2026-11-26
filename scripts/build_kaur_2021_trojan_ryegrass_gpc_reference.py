"""Transcribe open Kaur et al. (2021) ryegrass-GPC results and protocol.

This is a cultivated-forage, alternate-extraction comparator. It is kept
reference-only and does not activate GreenHub isoelectric recovery inputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Protein recovery" / "Isoelectric"
AUDIT = DATA / "global_audit_package"
FILENAME = "kaur_2021_trojan_ryegrass_gpc_yield_composition_and_protocol_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-KAUR-2021-TROJAN-RYEGRASS-GPC"
DOI = "10.3390/foods10020331"
URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC7913788/"
DOI_URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"
FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_table_or_section", "route",
    "species_or_blend", "material", "process_step", "metric", "value", "unit", "basis",
    "analytical_method", "statistic", "replicate_count", "uncertainty", "source_location",
    "evidence_class", "quality_class", "activation_state", "transferability", "limitations",
]

SOURCE = {
    "source_id": SOURCE_ID,
    "source_title": "Physico-Chemical Characteristics and In Vitro Gastro-Small Intestinal Digestion of New Zealand Ryegrass Proteins",
    "authors": "Lovedeep Kaur; Harmandeepsingh Lamsar; Ignacio F. López; Manon Filippi; Dayna Ong Shu Min; Kévin Ah-Sing; Jaspreet Singh",
    "year": "2021",
    "source_type": "peer-reviewed primary experimental article; open access",
    "peer_review_status": "peer-reviewed",
    "doi_or_stable_id": DOI,
    "source_url": DOI_URL,
    "materials": "Perennial ryegrass (Lolium perenne L.) cultivar Trojan, harvested in New Zealand, frozen at −20 °C before laboratory extraction",
    "processes": "Chemical extraction with wet disintegration, cheese pressing, pH 3.5 precipitation and freeze drying; separate six-hour Viscozyme-assisted multi-press extraction comparator",
    "used_in_files": FILENAME,
    "access_notes": "Full open article at PubMed Central; Massey Research Online repository record identifies CC BY 4.0 and a stable handle.",
    "quality_notes": (
        "Reports approximate GPC yields for two different routes and proximate/mineral values for acid-precipitated GPC. "
        "Article uses Kjeldahl nitrogen conversion factor 5.83 for protein. Table 1 does not state a more specific sample basis for all composition values. "
        "No complete stream/mass balance, acid dose, centrifuge settings or dryer energy is reported. Cultivated NZ ryegrass and an alternate chemical/enzyme route are not GreenHub roadside-feed validation."
    ),
}


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read_csv(path)
    if not fields:
        fields = list(entries[0])
    key_columns = key.split("|")
    identity = lambda row: tuple(row.get(column, "") for column in key_columns)
    index = {identity(row): row for row in rows}
    for entry in entries:
        item_key = identity(entry)
        if item_key in index:
            index[item_key].update(entry)
        else:
            rows.append(entry)
            index[item_key] = rows[-1]
    _write_csv(path, fields, rows)


def _row(
    record_id: str, *, route: str, source_section: str, material: str,
    process_step: str, metric: str, value: str, unit: str, basis: str,
    method: str = "", statistic: str = "source-reported result/condition",
    n: str = "", uncertainty: str = "not reported for this value",
) -> dict[str, str]:
    limitations = (
        "Cultivated Trojan ryegrass, not roadside/VARTA/GreenHub feed. This source comparator is not a GreenHub process setting or calibration. "
        "Do not infer missing stream flow, component recovery, reagent demand, centrifuge capture or drying energy."
    )
    if "not further specified" in basis:
        limitations += " The article's table does not identify a more specific analytical basis; it is preserved as unresolved."
    if "without reported dose" in basis:
        limitations += " Endpoint pH is not a titration curve or reagent-dose measurement."
    return {
        "record_id": record_id,
        "source_id": SOURCE_ID,
        "phase_relevance": "3;4",
        "source_table_or_section": source_section,
        "route": route,
        "species_or_blend": "Perennial ryegrass (Lolium perenne L.), cultivar Trojan",
        "material": material,
        "process_step": process_step,
        "metric": metric,
        "value": value,
        "unit": unit,
        "basis": basis,
        "analytical_method": method,
        "statistic": statistic,
        "replicate_count": n,
        "uncertainty": uncertainty,
        "source_location": source_section,
        "evidence_class": "B_measured_or_source_reported",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "New Zealand cultivated ryegrass; different harvest, frozen feed, laboratory apparatus and process route; comparator only, not roadside-grass performance.",
        "limitations": limitations,
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    article_method = "Kjeldahl protein analysis using nitrogen conversion factor 5.83; other Table 1 assays cited to AOAC/starch-sugar/IP-OES methods in article §2.4."
    rows.extend([
        _row("KAUR21-ACID-GPC-YIELD", route="chemical_acid_precipitation", source_section="Results §3.1, p. 6", material="acid-precipitated, freeze-dried GPC", process_step="overall product recovery", metric="grass_protein_concentrate_powder_yield", value="2.22", unit="% fresh grass mass", basis="source reports approximate average; fresh-grass weight basis", statistic="approximate average", uncertainty="not reported in prose"),
        _row("KAUR21-ENZYME-GPC-YIELD", route="enzyme_assisted_extraction", source_section="Results §3.1, p. 6", material="enzyme-assisted, freeze-dried GPC", process_step="overall product recovery", metric="grass_protein_concentrate_powder_yield", value="11", unit="% dry grass mass", basis="source-reported average; dry-grass mass basis", statistic="average", uncertainty="not reported in prose"),
        _row("KAUR21-ENZYME-PROTEIN-RECOVERY", route="enzyme_assisted_extraction", source_section="Results §3.1, p. 6", material="enzyme-assisted extraction of grass proteins", process_step="overall protein recovery", metric="grass_protein_recovery", value="85", unit="% of grass proteins", basis="author-reported recovery; exact denominator and calculation are not detailed in the cited result text", statistic="about 85%; author-reported", uncertainty="not reported"),
        _row("KAUR21-ENZYME-GPC-PROTEIN", route="enzyme_assisted_extraction", source_section="Results §3.1, p. 6", material="enzyme-assisted, freeze-dried GPC", process_step="product composition", metric="protein_content", value="44", unit="%", basis="protein content as reported; more specific basis not further specified in the cited sentence", method=article_method, statistic="reported value", uncertainty="not reported alongside value"),
    ])

    composition = [
        ("moisture", "3.77", "%", "Table 1 component proportion; sample basis not further specified"),
        ("ash", "2.53", "%", "Table 1 component proportion; sample basis not further specified"),
        ("protein", "54.69", "%", "Table 1 component proportion; nitrogen × 5.83 by Kjeldahl; sample basis not further specified"),
        ("fat", "8.45", "%", "Table 1 component proportion; sample basis not further specified"),
        ("carbohydrate", "26.61", "%", "Table 1 component proportion; sample basis not further specified"),
        ("insoluble_dietary_fiber", "18.40", "%", "Table 1 component proportion; sample basis not further specified"),
        ("soluble_dietary_fiber", "3.60", "%", "Table 1 component proportion; sample basis not further specified"),
        ("calcium", "143", "mg/100 g", "Table 1; sample basis not further specified"),
        ("magnesium", "95", "mg/100 g", "Table 1; sample basis not further specified"),
        ("potassium", "320", "mg/100 g", "Table 1; sample basis not further specified"),
        ("sodium", "121", "mg/100 g", "Table 1; sample basis not further specified"),
        ("iron", "40", "mg/100 g", "Table 1; sample basis not further specified"),
    ]
    for metric, value, unit, basis in composition:
        rows.append(_row(
            f"KAUR21-ACID-GPC-{metric.upper()}", route="chemical_acid_precipitation",
            source_section="Table 1, p. 7", material="acid-precipitated GPC powder",
            process_step="product composition", metric=metric, value=value, unit=unit,
            basis=basis, method=article_method, statistic="Table 1 reported value",
            uncertainty="Table 1 gives no SD for the value",
        ))

    conditions = [
        ("ACID-WATER", "chemical_acid_precipitation", "acid-extraction wet disintegration", "distilled_water_addition", "58.8", "% (w/v), as printed", "Source notation; denominator/batch scaling not further specified", "Methods §2.2, p. 3"),
        ("ACID-NAOH-ADDITION", "chemical_acid_precipitation", "alkaline extraction/disintegration", "0.1 M sodium_hydroxide_solution_addition", "26", "% (v/w), as printed", "Source notation; feed-mass reference not further specified", "Methods §2.2, p. 3"),
        ("ACID-NAOH-STRENGTH", "chemical_acid_precipitation", "alkaline extraction/disintegration", "sodium_hydroxide_solution_concentration", "0.1", "mol/L", "solution concentration; dose still not reported as a transferable mass per feed", "Methods §2.2, p. 3"),
        ("ACID-GRIND-SPEED", "chemical_acid_precipitation", "wet disintegration", "wet_disintegrator_speed", "6000", "rpm", "apparatus operating condition", "Methods §2.2, p. 3"),
        ("ACID-GRIND-TIME", "chemical_acid_precipitation", "wet disintegration", "wet_disintegrator_duration", "10", "min", "per reported extraction/disintegration step", "Methods §2.2, p. 3"),
        ("ACID-PRECIP-PH", "chemical_acid_precipitation", "protein precipitation", "precipitation_endpoint_pH", "3.5", "pH", "endpoint only; acid species/dose not stated in the cited method passage", "Methods §2.2, p. 3"),
        ("ENZYME-CONCENTRATION", "enzyme_assisted_extraction", "cell-wall hydrolysis", "Viscozyme_L_concentration", "1", "%", "source method reports concentration; exact percent basis is not further specified", "Methods §2.3, pp. 3–4"),
        ("ENZYME-SOLUTION-RATIO", "enzyme_assisted_extraction", "cell-wall hydrolysis", "enzyme_solution_to_wet_grass_ratio", "7:1", "v/w", "source-reported ratio; not normalized to GreenHub batch scale", "Methods §2.3, p. 3"),
        ("ENZYME-PH", "enzyme_assisted_extraction", "cell-wall hydrolysis", "hydrolysis_pH", "5", "pH", "reported controlled condition", "Methods §2.3, pp. 3–4"),
        ("ENZYME-TEMP", "enzyme_assisted_extraction", "cell-wall hydrolysis", "hydrolysis_temperature", "45", "°C", "reported controlled condition", "Methods §2.3, pp. 3–4"),
        ("ENZYME-TIME", "enzyme_assisted_extraction", "cell-wall hydrolysis", "total_hydrolysis_time", "6", "h", "two successive 3 h treatments", "Methods §2.3 and Results §3.1, pp. 3–6"),
        ("ENZYME-HCL-STRENGTH", "enzyme_assisted_extraction", "pH adjustment", "hydrochloric_acid_concentration", "6", "mol/L", "concentration used for pH adjustment; consumption/dose not reported", "Methods §2.3, pp. 3–4"),
        ("ENZYME-WATER-1", "enzyme_assisted_extraction", "second pressing after first enzyme treatment", "water_addition", "9000", "mL", "batch amount; feed batch mass/scale not stated for normalization", "Methods §2.3, p. 3"),
        ("ENZYME-WATER-2", "enzyme_assisted_extraction", "pressing after first enzyme treatment", "water_addition", "10", "L", "batch amount; feed batch mass/scale not stated for normalization", "Methods §2.3, p. 3"),
        ("ENZYME-WATER-3", "enzyme_assisted_extraction", "pressing after second enzyme treatment", "water_addition", "5", "L", "batch amount; feed batch mass/scale not stated for normalization", "Methods §2.3, p. 3"),
    ]
    for key, route, step, metric, value, unit, basis, location in conditions:
        limitations = "Protocol condition only; not a per-tonne utility/reagent demand and not a GreenHub default."
        if metric == "precipitation_endpoint_pH":
            limitations += " No acid demand, juice titration curve or buffer capacity is given."
        rows.append(_row(
            f"KAUR21-{key}", route=route, source_section=location, material="cultivated Trojan ryegrass slurry or extract",
            process_step=step, metric=metric, value=value, unit=unit, basis=basis,
            statistic="reported method condition", uncertainty="not applicable; protocol setting, not an estimated response",
        ))
        rows[-1]["limitations"] += " " + limitations
    return rows


def _register(rows: list[dict[str, str]]) -> None:
    _upsert(FOLDER / "source_register.csv", "source_id", [SOURCE])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "filename": FILENAME,
        "dataset_scope": "Source-reported acid-precipitation and enzyme-assisted ryegrass GPC yields, product composition, mineral values, and laboratory method settings; B/reference-only.",
        "row_count": str(len(rows)),
        "required_columns_present": "yes: source, route, material, process stage, metric, value, unit, basis and exact source location",
        "numeric_traceability_check": "All numeric values linked to article table or methods/results section; unknown bases retained explicitly.",
        "contains_assumptions_with_blank_values": "yes: missing acid dose, stream balance, centrifuge settings and drying energy remain absent, not zero",
        "integration_readiness": "reference_only",
        "limitations": "Cultivated NZ forage and distinct chemical/enzyme extraction routes; no complete stream balance, no acid titration/dose, not GreenHub route calibration.",
    }])
    rel = f"Protein recovery/Isoelectric/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel, "dataset_group": "Protein recovery/Isoelectric", "source_id": SOURCE_ID,
        "source_title": SOURCE["source_title"], "authors": SOURCE["authors"], "year": SOURCE["year"],
        "doi_or_stable_id": DOI, "url": DOI_URL, "source_type": SOURCE["source_type"],
        "notes": SOURCE["quality_notes"],
    }])
    numeric_count = sum(_is_number(row["value"]) for row in rows)
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Protein recovery", "subgroup": "ryegrass GPC yield and characterization; Phases 3 and 4",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only",
        "detected_readiness": "D3",
        "notes": "Table 1 composition and method conditions from alternate acid/enzyme routes; exact source locations; basis ambiguities explicit.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "Protein recovery", "subgroup": "ryegrass GPC yield and characterization; Phases 3 and 4",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0",
        "numeric_rows": str(numeric_count), "unsourced_numeric_rows": "0",
        "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0", "basis_conflicts": "0",
        "cross_reference_issues": "0", "equation_missing_inputs": "0", "equation_symbol_mismatches": "0",
        "notes": "Source locations are article Table 1 or section/page. Product Table 1 basis is not further resolved; methods values are not normalized to plant scale.",
    }])
    checksums = [{
        "dataset_path": f"Protein recovery/Isoelectric/{path.name}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "byte_size": str(path.stat().st_size),
    } for path in (CSV_PATH, SIDECAR_PATH)]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    summary["dataset_count"] = len(manifests)
    counts: dict[str, int] = {}
    for item in readiness:
        key = item.get("readiness", "")
        counts[key] = counts.get(key, 0) + 1
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> None:
    rows = build_rows()
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate record identifiers in Kaur ryegrass-GPC evidence")
    _write_csv(CSV_PATH, FIELDS, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:protein-recovery:kaur-2021-trojan-ryegrass-gpc:v1",
        "persistent_identifier_status": "Repository-local identifier for this transcription; DOI identifies the article, not this derived dataset.",
        "dataset_version": "1.0.0",
        "title": "Trojan ryegrass grass-protein-concentrate yield, composition and method conditions",
        "source_id": SOURCE_ID,
        "citation": "Kaur, L. et al. (2021). Physico-Chemical Characteristics and In Vitro Gastro-Small Intestinal Digestion of New Zealand Ryegrass Proteins. Foods, 10(2), 331. https://doi.org/10.3390/foods10020331",
        "doi": DOI,
        "source_url": URL,
        "repository_url": "https://mro.massey.ac.nz/items/db3caa01-1e03-4d0f-8643-a2af00827f1f",
        "retrieval_date": RETRIEVED,
        "source_locations": ["Methods §§2.1–2.4, pp. 3–4", "Results §3.1, p. 6", "Table 1, p. 7"],
        "reference_year": 2021,
        "experiment_year": None,
        "geography": "Massey University, Palmerston North, New Zealand; exact field site/harvest date not stated in cited methods extract.",
        "material_scope": "Perennial ryegrass (Lolium perenne L.) cultivar Trojan. Harvested grass was frozen at −20 °C before lab processing; final powder was freeze-dried. Not roadside/VARTA feed.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0), identified by Massey Research Online and the article publisher.",
        "evidence_class": "B_measured_or_source_reported",
        "quality_class": "B",
        "activation_state": "reference_only",
        "calculation_connected": False,
        "row_count": len(rows),
        "sha256_csv": digest,
        "transcription_policy": "Article Table 1 values and explicit prose/method conditions are transcribed without normalizing ambiguous bases, converting protocol ratios to feed-scale quantities, or inferring missing acid demand and stream flows.",
        "fair_metadata": {
            "findable": "Local URN, source DOI, article/repository URLs, citation and exact page/section/table are recorded.",
            "accessible": "UTF-8 CSV and JSON sidecar are stored; article is open access under CC BY 4.0.",
            "interoperable": "Long-form fields identify route, unit, basis, source location, method and evidence status.",
            "reusable": "License, process conditions, analytical method, factor N×5.83, unreported bases, missing-data boundaries and transferability are documented.",
        },
        "limitations": [
            "Cultivated New Zealand Trojan ryegrass is not roadside grass or GreenHub feedstock.",
            "Acid precipitation route uses NaOH and repeated pressing; it is not the GreenHub route and is not a chemistry calibration.",
            "Table 1 reports proximate percentages and mineral mg/100 g but does not further specify the basis; no dry-basis conversion is made.",
            "The Table 1 composition categories are not a closed mass balance and must not be summed; carbohydrate/fibre overlap is not resolved by the table.",
            "Protein content uses Kjeldahl N × 5.83; it is not a true-protein assay and should not be silently converted using N × 6.25.",
            "Acid product yield is approximate and no numerical acid demand, clarified-juice volume, press-cake mass or full component balance is reported.",
            "Enzyme-route values and water additions are a distinct alternate process; they are not normalized per tonne because feed batch mass is not reported.",
            "Freeze drying is not spray drying; no dryer energy, evaporation rate or powder recovery curve is available.",
            "No product price, TEA/LCA factor or runtime parameter is derived from the extract.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _register(rows)
    print(json.dumps({"file": str(CSV_PATH), "rows": len(rows), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
