from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Greenhub" / "data" / "Protein recovery" / "Membrane"
DATA = PACKAGE / "clover_grass_pilot_membrane_protein_quality_badfar_2027_reference.csv"
SOURCE_ID = "BADFAR-CLOVER-GRASSPILOT-2027"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows), f"Malformed CSV row in {path.name}"
        return rows


def test_badfar_pilot_observations_keep_reported_denominators_and_reference_only_scope() -> None:
    rows = _read_csv(DATA)
    assert len(rows) == 21
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["quality_class"] == "B" for row in rows)

    index = {row["property"]: row for row in rows}
    assert index["enzyme_activity"]["reported_value"] == "140"
    assert index["trypsin_dose"]["basis_status"] == "basis unresolved"
    assert "denominator not expanded" in index["trypsin_dose"]["reported_basis"]
    green_juice_cp = next(row for row in rows if row["observation_id"] == "BADFAR27-GJ-CP")
    assert "percentage denominator not specified" in green_juice_cp["basis_status"]
    centrifuge = next(row for row in rows if row["observation_id"] == "BADFAR27-DCH-CENTRIFUGE")
    assert centrifuge["source_id"] == SOURCE_ID
    assert centrifuge["activation_state"] == "reference_only"


def test_badfar_dataset_is_registered_and_cannot_be_used_as_a_runtime_default() -> None:
    metadata = json.loads(DATA.with_suffix(DATA.suffix + ".source.json").read_text(encoding="utf-8"))
    assert metadata["persistent_identifier"] == "doi:10.1016/j.foodhyd.2026.113048"
    assert metadata["license"] == "CC BY, verified on the DTU Research Database record for the final published version. The earlier bioRxiv preprint has a separate CC BY-NC-ND 4.0 license and is not the basis for this extract."
    assert metadata["data_scope"].startswith("21 reference observations")
    assert metadata["activation_state"] == "reference_only"
    assert metadata["calculation_connected"] is False
    assert metadata["runtime_parameter_mapping"] is None

    manifest = {row["filename"]: row for row in _read_csv(PACKAGE / "dataset_manifest.csv")}
    assert manifest[DATA.name]["row_count"] == "21"
    assert manifest[DATA.name]["integration_readiness"] == "reference_only"
    sources = {row["source_id"]: row for row in _read_csv(PACKAGE / "source_register.csv")}
    assert sources[SOURCE_ID]["doi_or_stable_id"] == "10.1016/j.foodhyd.2026.113048"
