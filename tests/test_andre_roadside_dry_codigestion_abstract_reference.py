from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "Greenhub"
    / "data"
    / "Bigas production + upgrade"
    / "Feed BMP"
    / "andre_roadside_grass_dry_codigestion_2019_abstract_reference.csv"
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_andre_abstract_values_are_preserved_without_runtime_activation() -> None:
    rows = _rows(DATA)
    metadata = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["observation_id"]: row for row in rows}
    manifest = _rows(DATA.parent / "dataset_manifest.csv")
    sources = _rows(DATA.parent / "source_register.csv")
    ad_sources = _rows(DATA.parent / "ad_source_register.csv")

    assert len(rows) == 6
    assert len(by_id) == len(rows)
    assert all(row["source_id"] == "ANDRE2019" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["geography"] == "not specified in abstract" for row in rows)
    assert by_id["ANDRE2019-BMP-JUNE"]["reported_value"] == "202.9"
    assert by_id["ANDRE2019-BMP-JUNE"]["unit"] == "Nm3 CH4/t VS"
    assert by_id["ANDRE2019-BMP-OCTOBER"]["reported_value"] == "167.9"
    assert by_id["ANDRE2019-INHIBITION"]["reported_value"] == "34.8–44.4"
    assert "does not define" in by_id["ANDRE2019-INHIBITION"]["uncertainty_or_limit"]

    assert metadata["doi"] == "10.1016/j.biortech.2019.121737"
    assert metadata["rows"] == len(rows)
    assert metadata["runtime_parameter_mapping"] is None
    assert metadata["activation_state"] == "reference_only"
    assert "substrate-to-value mapping" in " ".join(metadata["limitations"])
    assert any(row["source_id"] == "ANDRE2019" for row in sources)
    assert any(row["source_id"] == "ANDRE2019" for row in ad_sources)
    assert any(
        row["filename"] == DATA.name
        and row["row_count"] == str(len(rows))
        and row["integration_status"] == "traceable_reference_only_not_runtime_eligible"
        for row in manifest
    )
