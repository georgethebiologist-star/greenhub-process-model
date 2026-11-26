from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "gr4ss_leeuwarden_project_design_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_gr4ss_permit_and_project_targets_remain_distinct_reference_evidence() -> None:
    rows = _rows(DATA / FILENAME)
    metadata = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 7
    by_id = {row["record_id"]: row for row in rows}
    assert by_id["GR4SS-LEEWARDEN-PERMITTED-VERGE-FEED-36000"]["reported_value"] == "36000"
    assert by_id["GR4SS-LEEWARDEN-PERMITTED-PLANT-RESIDUES-24000"]["reported_value"] == "24000"
    capacity = by_id["GR4SS-LEEWARDEN-DESIGN-CAPACITY-60000"]
    assert capacity["reported_value"] == "60000" and capacity["unit"] == "t/year"
    assert "not measured throughput" in capacity["limitations"]
    biomethane = by_id["GR4SS-LEEWARDEN-TARGET-BIOMETHANE-10000000"]
    assert biomethane["reported_value"] == "10000000"
    assert "period not stated" in biomethane["unit"]
    assert all(row["quality_class"] == "B" and row["activation_state"] == "reference_only" for row in rows)
    assert metadata["calculation_connected"] is False
    assert metadata["runtime_parameter_mapping"] is None
    assert any(row["file_name"] == FILENAME and row["row_count"] == "7" for row in manifest)
    expected_sources = {
        "SRC-GR4SS-PERMIT-2025",
        "SRC-GR4SS-OPERATOR-2025",
        "SRC-GR4SS-PROJECT-WEBSITE",
    }
    assert expected_sources <= {row["source_id"] for row in sources}
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert set(asset["source_ids"].split(";")) == expected_sources
    assert asset["readiness"] == "reference_only"
    assert asset["maturity"] == "D3"
    assert asset["activation_state"] == "reference_only"

    package_code = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "Greenhub").rglob("*.py")
    )
    assert FILENAME not in package_code
