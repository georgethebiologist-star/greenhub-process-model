from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
FILENAME = "nynas_2026_lucerne_second_press_water_dilution_reference.csv"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_nynas_2026_water_repress_rows_preserve_reported_basis_and_status() -> None:
    rows = _read(GROUP / FILENAME)
    sidecar = json.loads((GROUP / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    assert len(rows) == sidecar["rows"] == 63
    assert len({row["record_id"] for row in rows}) == 63
    assert {row["source_id"] for row in rows} == {"SRC-NYNAS-2026-SECOND-PRESS"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["source_doi"] == "10.1016/j.jafr.2026.102842"
    assert sidecar["license"] == "CC BY 4.0, as specified for the final published version by the Swedish University of Agricultural Sciences repository record."
    assert sidecar["calculation_connected"] is False
    assert sidecar["parameter_registry_mapping"] is None

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["NYNAS26-1-1-FRESH-N_FLOW_P_TO_GJR"]["reported_mean"] == "35"
    assert by_id["NYNAS26-1-1-FRESH-N_FLOW_GJR_TO_GPSOLUBLE"]["reported_mean"] == "15"
    assert by_id["NYNAS26-1-2-FRESH-N_FLOW_GJR_TO_GPSOLUBLE"]["reported_sd"] == "5"
    assert by_id["NYNAS26-1-2-FROZEN-N_IN_GPRP"]["reported_mean"] == "6.6"
    assert by_id["NYNAS26-TIME-5H-21C-FROZEN-N_FLOW_GJR_TO_GPSOLUBLE"]["reported_mean"] == "6"
    ice = by_id["NYNAS26-TIME-15MIN-ICE-FROZEN-N_IN_GJR"]
    assert ice["reported_mean"] == "4.34"
    assert ice["soaking_temperature_C"] == ""
    assert all(row["replicate_n"] == "3" for row in rows)
    assert all(row["pulp_to_water_mass_ratio"] in {"1:1", "1:2"} for row in rows)
    assert all("nitrogen" in row["basis"].lower() for row in rows)
    assert "not Dutch roadside grass" in sidecar["limitations"][0]


def test_nynas_2026_extract_is_registered_and_checksummed() -> None:
    source = next(row for row in _read(GROUP / "source_register.csv") if row["source_id"] == "SRC-NYNAS-2026-SECOND-PRESS")
    manifest = next(row for row in _read(GROUP / "dataset_manifest.csv") if row["filename"] == FILENAME)
    rel = f"Protein recovery/Isoelectric/{FILENAME}"
    readiness = next(row for row in _read(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_readiness.csv") if row["dataset_path"] == rel)
    checksum = next(row for row in _read(ROOT / "Greenhub" / "data" / "global_audit_package" / "source_dataset_checksums.csv") if row["dataset_path"] == rel)
    assert source["doi_or_stable_id"] == "10.1016/j.jafr.2026.102842"
    assert manifest["row_count"] == "63"
    assert manifest["integration_readiness"] == "reference_only_not_runtime_eligible"
    assert readiness["numeric_rows"] == "63"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert checksum["sha256"] == __import__("hashlib").sha256((GROUP / FILENAME).read_bytes()).hexdigest()
