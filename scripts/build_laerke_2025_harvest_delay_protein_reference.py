from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Greenhub" / "data" / "storage"
CSV_PATH = OUT / "grass_clover_harvest_delay_digestible_protein_laerke_2025_abstract_reference.csv"
SOURCE_ID = "SRC-LAERKE-2025-HARVEST-DELAY"
DOI = "10.1016/j.anifeedsci.2025.116336"
RETRIEVAL_DATE = "2026-11-08"

FIELDS = [
    "observation_id",
    "source_id",
    "evidence_class",
    "activation_state",
    "feedstock",
    "harvest_method",
    "delay_after_harvest_h",
    "metric",
    "reported_value",
    "reported_unit",
    "basis",
    "value_type",
    "data_status",
    "source_location",
    "interpretation_note",
]


def _record(
    observation_id: str,
    *,
    method: str = "",
    delay_h: str = "",
    metric: str,
    value: str = "",
    unit: str,
    basis: str,
    value_type: str,
    status: str = "reported",
    note: str = "",
) -> dict[str, str]:
    return {
        "observation_id": observation_id,
        "source_id": SOURCE_ID,
        "evidence_class": "B_abstract_only_primary_literature",
        "activation_state": "reference_only",
        "feedstock": "Danish grass-clover mixture; exact species proportions not reported in the accessible abstract",
        "harvest_method": method,
        "delay_after_harvest_h": delay_h,
        "metric": metric,
        "reported_value": value,
        "reported_unit": unit,
        "basis": basis,
        "value_type": value_type,
        "data_status": status,
        "source_location": "Publisher abstract; Aarhus University repository record",
        "interpretation_note": note,
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sid_values = {("mowed", "0"): "71.0", ("chopped", "0"): "69.2"}
    digestible_cp_yield = {
        ("mowed", "0"): "56.8",
        ("mowed", "12"): "43.4",
        ("chopped", "12"): "29.4",
    }

    # The abstract states that both methods were processed immediately and after
    # 6 and 12 h. It reports exact SID values only for immediate processing.
    for method in ("mowed", "chopped"):
        for delay in ("0", "6", "12"):
            value = sid_values.get((method, delay), "")
            rows.append(
                _record(
                    f"LAERKE25-SIDCP-{method.upper()}-{delay}H",
                    method=method,
                    delay_h=delay,
                    metric="standardized ileal digestibility of crude protein in concentrate",
                    value=value,
                    unit="%",
                    basis="protein concentrate crude protein",
                    value_type="experimental outcome summarized in abstract",
                    status="reported" if value else "tested_value_not_reported_in_abstract",
                    note=(
                        "Immediate processing is encoded as 0 h for comparison; this is a condition label, not a measured transport duration."
                        if delay == "0"
                        else "The delay condition was tested, but its exact SID value is not reported in the accessible abstract."
                    ),
                )
            )

    # The paper describes these as calculated digestible-protein yields, not
    # directly measured stream mass balances.
    for method in ("mowed", "chopped"):
        for delay in ("0", "6", "12"):
            value = digestible_cp_yield.get((method, delay), "")
            rows.append(
                _record(
                    f"LAERKE25-DCPYIELD-{method.upper()}-{delay}H",
                    method=method,
                    delay_h=delay,
                    metric="calculated yield of digestible crude protein",
                    value=value,
                    unit="kg digestible CP/ha",
                    basis="per hectare of harvested grass-clover biomass",
                    value_type="source-calculated yield",
                    status="reported" if value else "tested_value_not_reported_in_abstract",
                    note=(
                        "Immediate processing is encoded as 0 h for comparison; this is a condition label, not a measured transport duration."
                        if delay == "0"
                        else "The delay condition was tested, but its exact yield is not reported in the accessible abstract."
                    ),
                )
            )

    rows.extend(
        [
            _record(
                "LAERKE25-SIDCP-IMMEDIATE-METHOD-COMPARISON-P",
                metric="between-method comparison of immediate SID crude protein",
                value=">0.05",
                unit="p-value",
                basis="mowed versus chopped biomass, immediate processing",
                value_type="reported statistical result",
                note="The abstract reports no significant difference at immediate processing.",
            ),
            _record(
                "LAERKE25-SIDCP-DELAY-EFFECT-P",
                metric="effect of processing delay on SID crude protein",
                value="0.005",
                unit="p-value",
                basis="mowed and chopped treatments; abstract does not provide the full model or contrasts",
                value_type="reported statistical result",
                note="The abstract states delayed processing diminished SID of crude protein.",
            ),
            _record(
                "LAERKE25-SIDCP-HARVEST-METHOD-EFFECT-P",
                metric="effect of harvest method on SID crude protein",
                value="0.006",
                unit="p-value",
                basis="mowed versus chopped biomass; abstract does not provide the full model or contrasts",
                value_type="reported statistical result",
                note="The abstract reports lower SID for chopped biomass overall.",
            ),
            _record(
                "LAERKE25-AA-DELAY-EFFECT-P",
                metric="processing-delay effect across amino-acid SID outcomes",
                value="<0.05",
                unit="p-value threshold",
                basis="all amino acids, as reported in the abstract",
                value_type="reported statistical result",
                note="Amino-acid-specific values and exact p-values are not reported in the accessible abstract.",
            ),
        ]
    )
    return rows


def _append_csv_row(path: Path, row: dict[str, str], fields: list[str], key: str, value: str) -> None:
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if any(existing.get(key) == value for existing in reader):
                return
            fieldnames = reader.fieldnames
        if fieldnames != fields:
            raise ValueError(f"Unexpected columns in {path}: {fieldnames}")
        if path.read_bytes() and not path.read_bytes().endswith(b"\n"):
            with path.open("a", encoding="utf-8", newline="") as stream:
                stream.write("\n")
        mode = "a"
    else:
        fieldnames = fields
        mode = "w"
    with path.open(mode, encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        if mode == "w":
            writer.writeheader()
        writer.writerow(row)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    with CSV_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:laerke-grass-clover-harvest-delay-digestible-protein-2025-abstract:v1",
        "persistent_identifier_status": "Repository-local dataset identifier; the DOI identifies the cited article, not this extract.",
        "dataset_version": "1.0.0",
        "source_file": CSV_PATH.name,
        "title": "Harvest-method and processing-delay effects on digestible protein yield and quality in grass-clover biorefining",
        "citation": "Lærke, H. N., Jensen, S. K., Andrade, T. A., Ambye-Jensen, M., Jørgensen, E. T., & Stødkilde, L. (2025). Towards efficient grass-clover biorefining: Influence of harvesting methods and delayed processing. Animal Feed Science and Technology, 324, 116336. https://doi.org/10.1016/j.anifeedsci.2025.116336",
        "persistent_identifier": f"doi:{DOI}",
        "source_url": "https://doi.org/10.1016/j.anifeedsci.2025.116336",
        "repository_record": "https://pure.au.dk/portal/en/publications/towards-efficient-grass-clover-biorefining-influence-of-harvestin/",
        "retrieval_date": RETRIEVAL_DATE,
        "publication_year": 2025,
        "experimental_geography": "Denmark; exact field site is not stated in the accessible abstract.",
        "evidence_class": "B_measured_primary_literature_abstract_only",
        "license": "CC BY 4.0, as stated for the published version in the Aarhus University record.",
        "source_data_availability": "Underlying data are stated as available on request; this extract contains only values and statistical summaries explicitly reported in the accessible abstract.",
        "material_scope": "Grass-clover biomass harvested by mowing or chopping and processed immediately or after 6 or 12 hours; Danish cultivated forage, not roadside grass.",
        "rows": len(rows),
        "data_scope": "Immediate SID of crude protein for both harvest methods; calculated digestible CP yields for selected immediate/12-hour cases; abstract-reported statistical tests; and explicit blank rows for tested outcomes whose exact values are not present in the accessible abstract.",
        "conversion_or_processing": "Direct transcription. ‘Immediate’ is encoded as a 0 h condition label only. No interpolation, effect-size calculation, conversion to GreenHub feed basis, or kinetic fit was performed.",
        "uncertainty": "The abstract provides no replicate-level values, standard errors, confidence intervals, exact 6-hour outcomes, or exact SID values after delay.",
        "activation_state": "reference_only",
        "readiness": "D3",
        "phase_tags": ["Phase 1: harvest method and time to processing", "Phase 4: protein yield and quality"],
        "applicability_limit": "Do not transfer as a roadside-grass or GreenHub default: feedstock is cultivated Danish grass-clover, harvesting/equipment and field context differ, and the abstract does not report species proportions or a matched full process balance.",
        "limitations": [
            "Reference-only; no parameter, equation, runtime calculation, process default, UI input, TEA/LCA factor, or Pareto scenario consumes these rows.",
            "Underlying experimental data are available on request, but were not publicly included with the accessible abstract.",
            "Exact outcomes at 6 h are not reported in the abstract; delayed SID values and several tested digestible-protein yields are explicitly blank, not zero.",
            "Digestible CP per hectare is described by the authors as a calculated yield, not a directly measured unit-operation stream flow.",
            "No feed species proportions, batch-level flow balance, cutting dimensions, transport temperature, or replicate uncertainty is given in the abstract.",
            "Immediate processing is encoded as 0 h only to normalize the reported experimental condition; it is not an observed zero-duration logistics event."
        ],
        "fair_metadata": {
            "findable": "Local dataset URN, descriptive name, article DOI and institutional record are recorded.",
            "accessible": "CSV and JSON sidecar are stored in the repository; article abstract is publicly accessible and underlying data are available on request.",
            "interoperable": "UTF-8 CSV with explicit method, delay, endpoint, unit, basis, value type and missingness fields.",
            "reusable": "Citation, CC BY 4.0 notice, extraction scope, processing convention, uncertainty and transfer limitations are documented."
        }
    }
    CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").write_text(
        json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    source_path = OUT / "source_register.csv"
    source_row = {
        "source_id": SOURCE_ID,
        "source_title": "Towards efficient grass-clover biorefining: Influence of harvesting methods and delayed processing",
        "authors": "Helle Nygaard Lærke; Søren Krogh Jensen; Thalles Allan Andrade; Morten Ambye-Jensen; Emma Tøfting Jørgensen; Lene Stødkilde",
        "year": "2025",
        "source_type": "peer-reviewed primary experimental article; abstract-level data extract",
        "doi_or_stable_identifier": DOI,
        "stable_url": "https://doi.org/10.1016/j.anifeedsci.2025.116336",
        "material": "Danish cultivated grass-clover biomass harvested by mowing or chopping and processed immediately or after 6/12 hours; digestible CP yield and concentrate SID",
        "quality_notes": "CC BY 4.0 article per Aarhus University record. Only explicit abstract-level values and statistics are transcribed; exact 6-hour outcomes and several delayed SID values are not reported in the abstract. Reference-only, D3; not roadside/GreenHub parameter data.",
        "accessed_date": RETRIEVAL_DATE,
    }
    _append_csv_row(source_path, source_row, list(source_row), "source_id", SOURCE_ID)

    manifest_path = OUT / "dataset_manifest.csv"
    manifest_row = {
        "filename": CSV_PATH.name,
        "description": "Abstract-level harvest-method and processing-delay outcomes for grass-clover digestible protein yield and SID; unreported tested values remain blank.",
        "row_count": str(len(rows)),
        "schema_version": "1.0",
        "encoding": "UTF-8",
        "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible",
        "primary_key": "observation_id",
    }
    _append_csv_row(manifest_path, manifest_row, list(manifest_row), "filename", CSV_PATH.name)


if __name__ == "__main__":
    build()
