from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "lca" / "grassification_flanders_roadside_grass_lca_2021_reference.csv"


def test_flanders_lca_results_keep_boundary_and_credits_explicit() -> None:
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(DATA.with_name(DATA.name + ".source.json").read_text(encoding="utf-8"))
    with (DATA.parent / "source_register.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))

    assert len(rows) == 22
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["source_id"] for row in rows} == {"SRC-GRASSIFICATION-LCA-FL-2021"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["GRASS-LCA-2021-SCOPE-FU"]["reported_value"] == "1"
    assert by_id["GRASS-LCA-2021-SCOPE-FU"]["unit"] == "tonne mowed grass"
    assert by_id["GRASS-LCA-2021-CC-AD"]["reported_value"] == "-277"
    assert by_id["GRASS-LCA-2021-CC-AD"]["record_type"] == "impact_result"
    assert by_id["GRASS-LCA-2021-CC-ENERGY"]["record_type"] == "impact_contribution"
    assert by_id["GRASS-LCA-2021-CC-ENERGY"]["reported_value"] == "-81"
    assert by_id["GRASS-LCA-2021-LCI-ACCESS"]["reported_value"] == "available on request from authors"
    assert metadata["runtime_mapping"] == "none"
    assert "not negative physical emissions" in metadata["provenance_note"].lower()
    assert any(row["source_id"] == "SRC-GRASSIFICATION-LCA-FL-2021" for row in sources)
