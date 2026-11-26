from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "greenhub_zuid_holland_dry_run_operational_evidence_2024_2026_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert all(None not in row for row in rows)
    return rows


def test_greenhub_dry_run_observations_are_traceable_and_not_activated() -> None:
    rows = _rows(DATA / FILENAME)
    sidecar = json.loads((DATA / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA / "source_register.csv")
    manifest = _rows(DATA / "dataset_manifest.csv")

    assert len(rows) == sidecar["rows"] == 25
    assert {row["quality_class"] for row in rows} == {"A", "B", "NOT_APPLICABLE"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["phase"] for row in rows} == {"1", "2", "3", "4", "5", "7"}
    assert {row["source_id"] for row in rows} == {
        "SRC-GHZH-DRYRUN-2024",
        "SRC-GHZH-PROCESS-2024",
        "SRC-GHZH-DRYRUN-2025-AMBIGUOUS",
        "SRC-GHZH-RESULTS-UNDATED",
        "SRC-GHZH-SECONDARY-150T-2025",
        "SRC-GHZH-AQUAMINERALS-INTENT-2026",
    }

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["GHZH24-COLLECTED-MASS"]["value"] == "117"
    assert "basis not stated" in by_id["GHZH24-COLLECTED-MASS"]["measurement_basis"]
    assert by_id["GHZH25-BOKASHI-MASS"]["value"] == "600"
    assert "Not identified as roadside cuttings" in by_id["GHZH25-BOKASHI-MASS"]["limitations"]
    assert "year unverified" in by_id["GHZH25-PAPER-MASS"]["campaign_year_label"]
    undated = by_id["GHZH-COLLECTED-MASS-UNDATED"]
    assert undated["value"] == "120"
    assert "Timeframe not stated" in undated["campaign_year_label"]
    assert "Do not annualize or reconcile" in undated["limitations"]
    secondary = by_id["GHZH25-ANNUAL-COLLECTION-CLAIM"]
    assert secondary["value"] == "150"
    assert secondary["unit"] == "t/year"
    assert secondary["quality_class"] == "B"
    assert "lower-bound threshold" in secondary["measurement_basis"]
    assert "Do not use as a point estimate" in secondary["limitations"]
    bokashi = by_id["GHZH-RESULTS-BOKASHI-USE-UNDATED"]
    assert bokashi["value"] == "100" and bokashi["phase"] == "7"
    assert bokashi["quality_class"] == "B"
    assert "Do not use as digestate yield" in bokashi["limitations"]
    inventory_plan = by_id["GHZH26-AQUAMINERALS-DATA-INVENTORY-PLAN"]
    assert not inventory_plan["value"]
    assert inventory_plan["quality_class"] == "NOT_APPLICABLE"
    assert inventory_plan["activation_state"] == "reference_only"
    assert sidecar["calculation_connected"] is False
    assert any("temporal inconsistency" in item for item in sidecar["limitations"])
    expected_source_ids = {
        "SRC-GHZH-DRYRUN-2024",
        "SRC-GHZH-PROCESS-2024",
        "SRC-GHZH-DRYRUN-2025-AMBIGUOUS",
        "SRC-GHZH-RESULTS-UNDATED",
        "SRC-GHZH-SECONDARY-150T-2025",
        "SRC-GHZH-AQUAMINERALS-INTENT-2026",
    }
    assert expected_source_ids <= {row["source_id"] for row in sources}
    assert all(sum(row["source_id"] == source_id for row in sources) == 1
               for source_id in expected_source_ids)
    assert any(row["file_name"] == FILENAME and row["row_count"] == "25" for row in manifest)
