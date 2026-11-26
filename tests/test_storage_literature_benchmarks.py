from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage" / "storage_loss_literature_benchmarks.csv"


def test_storage_benchmarks_are_traceable_and_reference_only() -> None:
    with DATA.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    assert len(rows) == 26
    assert len({row["benchmark_id"] for row in rows}) == len(rows)
    assert {row["storage_regime"] for row in rows} == {"aerobic", "anaerobic", "wrapped_silage", "fresh_grass", "ensiled_bale", "unensiled_control"}
    for row in rows:
        assert row["evidence_class"].startswith("B_")
        assert row["status"] == "reference_only"
        assert row["uncertainty_and_transferability"]
        assert row["activation_note"]

    yang_rows = [row for row in rows if row["source_id"] == "SRC-ENERGY-CROP-STORAGE-2026"]
    crook_rows = [row for row in rows if row["source_id"] == "SRC-GRASS-RYEGRASS-STORAGE-2020"]
    assert len(yang_rows) == 10
    assert all(row["source_url_or_doi"] == "https://doi.org/10.1038/s41598-025-34190-1" for row in yang_rows)
    assert len(crook_rows) == 8
    assert all(row["source_url_or_doi"] == "https://doi.org/10.1002/cft2.20015" for row in crook_rows)
    recovery = {row["benchmark_id"]: row for row in crook_rows if "DM-RECOVERY" in row["benchmark_id"]}
    assert recovery["CROOK2020-DM-RECOVERY-DRY"]["value"] == "97.8"
    assert recovery["CROOK2020-DM-RECOVERY-WET"]["value"] == "92.7"
    assert all("85 d" in row["basis"] for row in crook_rows)
    assert all(
        any(token in row["uncertainty_and_transferability"].lower() for token in ("roadside", "process", "livestock"))
        for row in crook_rows
    )

    roadside_rows = [row for row in rows if row["source_id"] == "SRC-ROAD-VERGE-GRASS-ENSILING-2020"]
    assert len(roadside_rows) == 8
    assert all(row["source_url_or_doi"] == "https://doi.org/10.1016/j.biombioe.2020.105570" for row in roadside_rows)
    roadside_bmp = {row["benchmark_id"]: row for row in roadside_rows if row["parameter_or_metric"] == "experimental_methane_potential"}
    assert roadside_bmp["BROWN2020-FRESH-S2-BMP"]["value"] == "260"
    assert roadside_bmp["BROWN2020-ENSILED-S2-BMP"]["value"] == "276"
    assert all(
        "storage" in row["uncertainty_and_transferability"].lower()
        and "not" in row["uncertainty_and_transferability"].lower()
        for row in roadside_bmp.values()
    )

    equations = {
        row["storage_regime"]: row
        for row in yang_rows
        if row["parameter_or_metric"] == "dry_matter_loss_exponent_c"
    }
    assert equations["aerobic"]["value"] == "0.6364"
    assert equations["anaerobic"]["value"] == "0.6494"
    assert all(row["model_fit_n"] == "1344" for row in equations.values())
