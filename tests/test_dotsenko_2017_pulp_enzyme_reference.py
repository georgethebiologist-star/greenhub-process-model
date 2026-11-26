import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub/data/Pre-treatment/Thermal_Enzymatic"
DATA_PATH = DATA_DIR / "enzymatic_treatment_response.csv"
SIDECAR_PATH = Path(str(DATA_PATH) + ".source.json")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _single(rows: list[dict[str, str]], predicate, label: str) -> dict[str, str]:
    matched = [row for row in rows if predicate(row)]
    assert len(matched) == 1, f"expected one {label}, found {len(matched)}"
    return matched[0]


def test_dotsenko_tables_are_transcribed_with_traceability_and_no_activation():
    rows = _rows(DATA_PATH)
    generated = [row for row in rows if row["parameter_id"].startswith("ENZR-DOT17-")]
    sidecar = json.loads(SIDECAR_PATH.read_text(encoding="utf-8"))

    assert len(rows) == 151
    assert len(generated) == 134
    assert sum(bool(row["value"]) for row in generated) == 132
    assert len({row["parameter_id"] for row in rows}) == len(rows)
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert all(row["source_id"] == "SRC-ENZ-002" for row in generated)
    assert all(row["doi_or_stable_identifier"] == "10.1007/s12649-016-9718-7" for row in generated)
    assert all(row["exact_source_location"] and row["source_url"].startswith("https://doi.org/") for row in generated)
    assert all(not row["python_variable"] and not row["scenario_id"] for row in generated)

    aqueous_wc = _single(
        generated,
        lambda row: row["exact_source_location"].startswith("Table 2")
        and row["material_feed_type"].startswith("white clover")
        and "Tween 80 0.5%" in row["operating_conditions"]
        and row["response_definition"] == "protein recovery yield at 72 h",
        "white-clover Table 2 Tween yield",
    )
    assert aqueous_wc["value"] == "53"
    assert aqueous_wc["unit"] == "% pulp protein"
    assert not aqueous_wc["uncertainty"]

    dose_response = _single(
        generated,
        lambda row: row["exact_source_location"].startswith("Table 4")
        and row["material_feed_type"].startswith("white clover")
        and row["enzyme_dose"] == "1.25"
        and row["response_definition"] == "protein recovery yield at 72 h",
        "white-clover Table 4 1.25-dose yield",
    )
    assert dose_response["value"] == "75"
    assert "basis not further specified" in dose_response["enzyme_dose_unit"]

    exhaustive = _single(
        generated,
        lambda row: row["exact_source_location"].startswith("Table 5")
        and row["material_feed_type"].startswith("perennial ryegrass")
        and "exhaustive" in row["experiment_id"]
        and row["response_definition"] == "protein recovery yield at 72 h after sequential enzyme treatment",
        "ryegrass Table 5 exhaustive yield",
    )
    assert exhaustive["value"] == "95"
    assert "allocation not reported" in exhaustive["enzyme_dose_unit"]
    assert "Savinase dose 5 mg protein/g dry pulp" in exhaustive["operating_conditions"]

    nondetect = _single(
        generated,
        lambda row: row["data_status"] == "qualitative-reported"
        and row["material_feed_type"].startswith("perennial ryegrass"),
        "ryegrass carbohydrase-only non-detect",
    )
    assert nondetect["value"] == ""
    assert "not zero" in nondetect["notes"]

    assert sidecar["record_count"] == len(rows)
    assert sidecar["source_record_count"] == len(generated)
    assert sidecar["sha256"] == hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    assert "CC BY 4.0" in sidecar["license"]
    assert "not GreenHub roadside/VARTA" in sidecar["limitations"][0]
    assert "No GreenHub model parameter" in sidecar["limitations"][-1]

    activation = _single(
        _rows(ROOT / "Greenhub/data/global_audit_package/dataset_activation_matrix.csv"),
        lambda row: row["dataset_path"] == "Pre-treatment/Thermal_Enzymatic/enzymatic_treatment_response.csv",
        "enzyme-response activation record",
    )
    assert activation["integration_eligibility"] == "blocked"
    assert activation["default_eligibility"].lower() == "false"
    assert activation["active"].lower() == "false"

    gap = _single(
        _rows(DATA_DIR / "assumption_and_missing_data_register.csv"),
        lambda row: row["register_id"] == "AMR-TE-006",
        "remaining GreenHub validation gap",
    )
    assert gap["status"] == "reference_staged_only; model validation open"
    assert "roadside-pulp response" in gap["reason_missing_or_assumed"]
