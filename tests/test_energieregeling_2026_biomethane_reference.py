"""The current Dutch G-gas requirements are traceable reference data, not defaults."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Common_Conditioning"
AUDIT = ROOT / "Greenhub" / "data" / "global_audit_package"
DATASET = "Bigas production + upgrade/Common_Conditioning/biomethane_specifications.csv"
SOURCE_ID = "SRC-NL-ENERGIEREGELING-G-QUALITY-2026"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_dutch_2026_gas_quality_is_separately_scoped_and_reference_only():
    rows = read_rows(PACKAGE / "biomethane_specifications.csv")
    dutch = [row for row in rows if row["source_id"] == SOURCE_ID]
    by_id = {row["parameter_id"]: row for row in dutch}

    assert len(rows) == 58
    assert len(dutch) == 35
    assert len(by_id) == len(dutch)
    assert {row["country"] for row in dutch} == {"Netherlands"}
    assert {row["specification_year"] for row in dutch} == {"2026"}
    assert {row["data_status"] for row in dutch} == {"official_regulatory_requirement"}
    assert all(row["doi_or_stable_id"] == "Staatscourant 2025, 37730" for row in dutch)
    assert all(row["exact_location"].startswith("Annex 1, Part B") for row in dutch)

    assert by_id["BMS_NL_2026_GGAS_WOBBE_MIN_STANDARD"]["value"] == "43.46"
    assert by_id["BMS_NL_2026_GGAS_WOBBE_MAX_STANDARD"]["value"] == "44.41"
    assert by_id["BMS_NL_2026_GGAS_CO2_RTL_DISTRIBUTION_TABLE_MAX"]["value"] == "10.34"
    assert "footnote 4" in by_id["BMS_NL_2026_GGAS_CO2_RTL_DISTRIBUTION_TABLE_MAX"]["exact_location"]
    assert not any("CH4_MIN" in row["parameter_id"] for row in dutch)
    assert all("Reference-only" in row["notes"] for row in dutch)

    old = {row["parameter_id"] for row in rows if row["source_id"] in {"SRC001", "SRC002"}}
    assert "BMS_DK_2020_CO2_MAX" in old
    assert "BMS_HIST_2009_NE_METHANE_MIN_22" in old


def test_conditional_co2_rule_is_registered_but_blocked_without_project_inputs():
    equation_id = "EQ_CC_NL_2026_G_GAS_CO2_CONDITIONAL_MAX"
    expected_paths = {
        "Bigas production + upgrade/Common_Conditioning/conditioning_equation_registry.csv",
        "Bigas production + upgrade/Common_Conditioning/equation_registry.csv",
    }
    for name in ("conditioning_equation_registry.csv", "equation_registry.csv"):
        equations = read_rows(PACKAGE / name)
        match = next(row for row in equations if row["equation_id"] == equation_id)
        assert "10.32 - 0.72*N2 - 0.87*O2" in match["exact_source_equation"]
        assert "10.56 - 0.746*N2 - 1.01*O2" in match["exact_source_equation"]
        assert "CO2 > 6 mol%" in match["applicability"]
        assert match["data_status"] == "official_regulatory_requirement"
        assert "Reference formula only" in match["limitations"]

    global_equations = read_rows(AUDIT / "global_equation_registry.csv")
    matches = [row for row in global_equations if row["equation_id"] == equation_id]
    assert {row["dataset_path"] for row in matches} == expected_paths
    assert all("connection category" in row["likely_missing_inputs"] for row in matches)

    issues = read_rows(AUDIT / "global_validation_issues.csv")
    equation_issues = [row for row in issues if row["row_id"] == equation_id]
    assert len(equation_issues) == 2
    assert all(row["issue_type"] == "equation_required_inputs_unavailable" for row in equation_issues)


def test_fair_catalog_metadata_and_gap_status_are_current_without_activation():
    sidecar = json.loads((PACKAGE / "biomethane_specifications.csv.source.json").read_text(encoding="utf-8"))
    dataset = PACKAGE / "biomethane_specifications.csv"
    assert sidecar["sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert SOURCE_ID in sidecar["source_ids"]
    assert sidecar["runtime_policy"].startswith("Reference-only")
    assert "No single minimum methane fraction" in " ".join(sidecar["limitations"])

    for relative in (
        "docs/missing_data_gap_analysis.csv",
        "Greenhub/data/Pre-treatment/Feedstock/expanded_process_data_register.csv",
        "Greenhub/data/Pre-treatment/Feedstock/complete_missing_data_with_traceability.csv",
    ):
        row = next(item for item in read_rows(ROOT / relative) if item["gap_id"] == "BG-001")
        assert row["status"] == "partially_implemented"
        assert "operator" in row["effect_on_model_outputs"]

    manifest = read_rows(AUDIT / "global_dataset_manifest.csv")
    found = next(row for row in manifest if row["dataset_path"] == DATASET)
    assert found["row_count_observed"] == "58"
    activation = read_rows(AUDIT / "dataset_activation_matrix.csv")
    item = next(row for row in activation if row["dataset_path"] == DATASET)
    assert item["integration_eligibility"] == "blocked"
    assert item["active"] == "False"
    assert item["default_eligibility"] == "False"

