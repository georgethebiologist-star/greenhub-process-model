"""EU/NL fertiliser rules are staged as traceable Phase 7 reference data only."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Greenhub" / "data" / "Resource recovery" / "Digestate_and_Separation"
AUDIT = ROOT / "Greenhub" / "data" / "global_audit_package"
FILENAME = "eu_digestate_fertiliser_regulatory_requirements_2019_1009_2026_reference.csv"
DATASET = f"Resource recovery/Digestate_and_Separation/{FILENAME}"
SOURCE_EU = "SRC-EU-REG-2019-1009-CONSOL-2026-07-01"
SOURCE_NL = "SRC-NL-BUSINESSGOV-FERTILISER-RESIDUE-ADMISSION"
SOURCE_RVO = "SRC-NL-RVO-ANNEX-AA-DIGESTATE-2026"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_phase7_requirements_are_traceable_and_not_runtime_defaults():
    path = PACKAGE / FILENAME
    rows = read_rows(path)
    by_id = {row["record_id"]: row for row in rows}
    assert len(rows) == 85
    assert len(by_id) == len(rows)
    assert {row["phase"] for row in rows} == {"7"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["data_status"] for row in rows} <= {
        "official_regulatory_requirement",
        "official_government_guidance",
    }
    assert {row["source_id"] for row in rows} == {SOURCE_EU, SOURCE_NL, SOURCE_RVO}

    # Guard key legal values and effective date against silent unit/value drift.
    assert by_id["EUFPR26-PFC1A_CADMIUM_CD"]["value"] == "1.5"
    assert by_id["EUFPR26-PFC1A_CADMIUM_CD"]["unit"] == "mg/kg dry matter"
    assert by_id["EUFPR26-PFC1A_HEXAVALENT_CHROMIUM_CR_VI"]["value"] == "2"
    assert by_id["EUFPR26-PFC1A_NICKEL_NI"]["value"] == "50"
    plastic = by_id["EUFPR26-CMC5_PLASTIC_2026"]
    assert plastic["value"] == "2.5"
    assert plastic["effective_from"] == "2026-07-16"
    assert "grown for biogas production" in by_id["EUFPR26-CMC4_INPUT_SCOPE"]["condition_text"]
    assert "not assumed" in by_id["EUFPR26-CMC4_INPUT_SCOPE"]["notes"]
    assert by_id["EUFPR26-CMC12_P2O5_MIN"]["value"] == "16"
    assert by_id["EUFPR26-CMC12_CORG_MAX"]["value"] == "3"
    assert by_id["EUFPR26-CMC12_MACRO_EACH_MAX"]["value"] == "3"
    assert by_id["EUFPR26-CMC12_MACRO_SUM_MAX"]["value"] == "5"
    assert by_id["EUFPR26-PFC1C_COMPOUND_SUM_MIN"]["value"] == "18"
    assert by_id["EUFPR26-NL_RVO_ANNEX_AA_GATE"]["source_id"] == SOURCE_RVO
    assert "does not establish" in by_id["EUFPR26-NL_RVO_ANNEX_AA_GATE"]["notes"]
    sidecar = json.loads((PACKAGE / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    assert sidecar["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert sidecar["dataset_version"] == "1.1.0"
    assert set(sidecar["source_ids"]) == {SOURCE_EU, SOURCE_NL, SOURCE_RVO}
    assert sidecar["runtime_policy"].startswith("Reference-only")

    sources = read_rows(PACKAGE / "source_register.csv")
    source_urls = {row["source_id"]: row["url"] for row in sources}
    assert SOURCE_EU in source_urls and "eur-lex.europa.eu" in source_urls[SOURCE_EU]
    assert SOURCE_NL in source_urls and "business.gov.nl" in source_urls[SOURCE_NL]
    assert SOURCE_RVO in source_urls and "rvo.nl" in source_urls[SOURCE_RVO]
    assert "struvite" in " ".join(sidecar["limitations"]).lower()


def test_phase7_dataset_is_indexed_but_still_blocked_and_gap_is_not_claimed_closed():
    manifest = read_rows(AUDIT / "global_dataset_manifest.csv")
    item = next(row for row in manifest if row["dataset_path"] == DATASET)
    assert item["row_count_observed"] == "85"
    assert item["detected_readiness"] == "D3"

    activation = read_rows(AUDIT / "dataset_activation_matrix.csv")
    item = next(row for row in activation if row["dataset_path"] == DATASET)
    assert item["active"] == "False"
    assert item["default_eligibility"] == "False"
    assert item["integration_eligibility"] == "reference_only"

    for relative in (
        "docs/missing_data_gap_analysis.csv",
        "Greenhub/data/Pre-treatment/Feedstock/expanded_process_data_register.csv",
        "Greenhub/data/Pre-treatment/Feedstock/complete_missing_data_with_traceability.csv",
    ):
        gap = next(row for row in read_rows(ROOT / relative) if row["gap_id"] == "NU-002")
        assert gap["status"] == "partially_implemented"
        assert "no revenue or LCA credit" in gap["effect_on_model_outputs"]
