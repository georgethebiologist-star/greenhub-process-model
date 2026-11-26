from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AD = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "AD reactor"


def _rows(name: str) -> list[dict[str, str]]:
    with (AD / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_recent_roadside_grass_ad_paper_is_a_traceable_unresolved_lead() -> None:
    sources = _rows("source_register.csv")
    source = next(row for row in sources if row["source_id"] == "SRC012")
    assert source["doi_or_stable_id"] == "10.1007/s12649-025-03274-4"
    assert source["source_url"] == "https://doi.org/10.1007/s12649-025-03274-4"

    gap = next(row for row in _rows("assumption_and_missing_data_register.csv") if row["register_id"] == "AMR006")
    assert gap["data_status"] == "missing"
    assert gap["numerical_value"] == ""
    assert "denominator" in gap["current_coverage"]
    assert "Do not ingest" in gap["notes"]

    benchmarks = _rows("brown_juice_reactor_benchmarks.csv")
    assert all(row["source_id"] != "SRC012" for row in benchmarks)
