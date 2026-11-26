from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "lca"
DATA_FILE = DATA_DIR / "biogas_chain_methane_emission_factors_wechselberger_2023_reference.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_methane_emission_extract_keeps_process_bases_and_scope() -> None:
    rows = _read_csv(DATA_FILE)
    metadata = json.loads(DATA_FILE.with_name(DATA_FILE.name + ".source.json").read_text(encoding="utf-8"))
    source_rows = _read_csv(DATA_DIR / "source_register.csv")

    assert len(rows) == metadata["record_count"] == 11
    assert all(len(row) == 20 and all(value is not None for value in row.values()) for row in rows)
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["article_doi"] for row in rows} == {"10.1016/j.wasman.2022.12.012"}
    assert {row["dataset_doi"] for row in rows} == {"10.5281/zenodo.7474206"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["WCH23-UPGRADING-WATER"]["n_reported"] == "2"
    assert by_id["WCH23-UPGRADING-WATER"]["median_value"] == "2.94"
    assert by_id["WCH23-UPGRADING-WATER"]["minimum_value"] == "1.98"
    assert by_id["WCH23-UPGRADING-WATER"]["maximum_value"] == "3.89"
    assert by_id["WCH23-UPGRADING-WATER"]["basis"] == "CH4 utilized"
    assert by_id["WCH23-DIGESTATE-STORAGE"]["basis"] == "CH4 produced"
    assert by_id["WCH23-DIGESTATE-STORAGE"]["n_reported"] == "8"
    assert by_id["WCH23-DIGESTATE-STORAGE"]["maximum_value"] == "5.62"
    assert by_id["WCH23-UPGRADING-PSA"]["source_location"] == "Table 2 Presented study footnote f"
    assert all(row["mean_value"] == "" for row in rows)

    source = [row for row in source_rows if row["source_id"] == "SRC-WECHSELBERGER-2023"]
    assert len(source) == 1
    assert "CC BY 4.0" in source[0]["quality_notes"]
    assert metadata["runtime_parameter_mapping"] is None
    assert "not probability distributions" in " ".join(metadata["limitations"])
