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
    / "grassification_roadside_codigestion_pilot_2020_reference.csv"
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_grassification_codigestion_observations_are_traceable_and_quarantined() -> None:
    rows = _read_csv(DATA)
    metadata = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))
    feed_bmp_dir = DATA.parent
    package_sources = _read_csv(feed_bmp_dir / "source_register.csv")
    ad_sources = _read_csv(feed_bmp_dir / "ad_source_register.csv")
    manifest = _read_csv(feed_bmp_dir / "dataset_manifest.csv")
    global_manifest = _read_csv(
        ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv"
    )
    fair_catalog = _read_csv(
        ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv"
    )

    assert len(rows) == 100
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert all(row["source_id"] == "SRC-GRASSIFICATION-D141-2020" for row in rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all(row["evidence_class"].strip().startswith("B_") for row in rows)
    assert all(row["evidence_class"] == row["evidence_class"].strip() for row in rows)

    feed_rows = [row for row in rows if row["material"] == "roadside_grass"]
    digestate_rows = [row for row in rows if row["material"] == "digestate"]
    assert len(feed_rows) == 16
    assert len(digestate_rows) == 84
    assert sum(row["measurement_or_test"] == "feed characterization" for row in feed_rows) == 10
    assert {row["sampling_date_reported"] for row in digestate_rows} == {
        "2020-04-09",
        "2020-04-15",
        "2020-04-23",
        "2020-05-05 or 2020-05-25",
    }

    by_id = {row["observation_id"]: row for row in rows}
    anomaly = by_id["GRASSIF-D141-GRASS-TAN"]
    assert anomaly["evidence_class"] == "B_measured_source_anomaly"
    assert anomaly["reported_value"] == "0.73 ± 13.13"
    assert "Do not use quantitatively" in anomaly["limitations"]
    assert by_id["GRASSIF-D141-GRASS-DM"]["value"] == "31.94"
    assert by_id["GRASSIF-D141-DIG-BIOGAS-2020LAST"]["value"] == "39"
    bmp_60 = by_id["GRASSIF-D141-GRASS-BMP-60PCT-D3"]
    bmp_90 = by_id["GRASSIF-D141-GRASS-BMP-90PCT-D8"]
    assert bmp_60["value"] == "60" and bmp_90["value"] == "90"
    assert "Figure 9" in bmp_90["source_location"]
    assert "not continuous-reactor HRT" in bmp_90["limitations"]

    assert metadata["source_id"] == "SRC-GRASSIFICATION-D141-2020"
    assert metadata["rows"] == len(rows)
    assert metadata["activation_state"] == "reference_only"
    assert metadata["runtime_parameter_mapping"] is None
    assert metadata["doi"] is None
    assert "license identified" in metadata["license"].lower()
    assert "manure" in " ".join(metadata["limitations"]).lower()
    assert any(row["source_id"] == metadata["source_id"] for row in package_sources)
    assert any(row["source_id"] == metadata["source_id"] for row in ad_sources)
    assert any(
        row["filename"] == DATA.name
        and row["row_count"] == str(len(rows))
        and row["integration_status"] == "traceable_reference_only_not_runtime_eligible"
        for row in manifest
    )
    global_entry = next(row for row in global_manifest if row["filename"] == DATA.name)
    assert global_entry["row_count_observed"] == str(len(rows))
    fair_entry = next(row for row in fair_catalog if row["relative_path"].endswith(DATA.name))
    assert fair_entry["observed_rows"] == str(len(rows))
    assert fair_entry["source_ids"] == "SRC-GRASSIFICATION-D141-2020"
