from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "ovam_2017_gr3_flanders_mowing_supply_inventory_reference.csv"
REL = f"Pre-treatment/Feedstock/{FILENAME}"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ovam_gr3_table36_keeps_scope_bases_and_estimate_caveats() -> None:
    rows = _read(GROUP / FILENAME)
    sidecar = json.loads((GROUP / f"{FILENAME}.source.json").read_text(encoding="utf-8"))
    assert len(rows) == sidecar["rows"] == 17
    assert len({row["record_id"] for row in rows}) == 17
    assert {row["source_id"] for row in rows} == {"SRC-OVAM-GR3-2017-TABLE36"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    # This DOI identifies separate grass hydrothermal-carbonisation support
    # data, not the OVAM inventory report. No DOI was identified for the report.
    assert sidecar["dataset_doi"] is None
    assert sidecar["dataset_url"] is None
    assert "printed p. 6" in sidecar["permission_or_rights"]
    assert sidecar["runtime_parameter_mapping"] is None

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["OVAM17-VERGE-AWV"]["annual_dry_matter_tonnes"] == "9,381"
    assert by_id["OVAM17-VERGE-AWV"]["annual_fresh_matter_tonnes"] == "34,744"
    assert by_id["OVAM17-ALL-GRASS-AND-VERGES"]["managed_area_ha"] == "33,311"
    assert by_id["OVAM17-NATUURPUNT-UPDATE-GRASS-DM"]["annual_dry_matter_tonnes"] == "5,000"
    assert by_id["OVAM17-NATUURPUNT-UPDATE-GRASS-DM"]["record_scope"] == "separate_manager_reported_update"
    assert by_id["OVAM17-VERGE-MUNICIPALITIES"]["reported_dm_yield_tonnes_per_ha"] == "1.38"
    assert all("27%" in row["fresh_mass_basis"] or row["fresh_mass_basis"] == "not reported" for row in rows)

    verge_actor_dm = sum(int(by_id[f"OVAM17-VERGE-{suffix}"]["annual_dry_matter_tonnes"].replace(",", "")) for suffix in ["AWV", "NAVIGABLE-WATERWAYS", "MUNICIPALITIES", "RAILWAYS"])
    assert verge_actor_dm == 34_884
    assert int(by_id["OVAM17-ALL-GRASS-AND-VERGES"]["annual_dry_matter_tonnes"].replace(",", "")) == 61_438
    grassland_actor_dm = sum(
        int(by_id[f"OVAM17-{suffix}"]["annual_dry_matter_tonnes"].replace(",", ""))
        for suffix in [
            "GRASSLAND-ANB", "GRASSLAND-NATUURPUNT", "GRASSLAND-RECOGNISED-MANAGERS",
            "GRASSLAND-AIRPORTS", "GRASSLAND-PORTS", "GRASSLAND-GOLF", "GRASSLAND-LNE-EROSION",
        ]
    )
    grassland_subtotal_dm = int(by_id["OVAM17-GRASSLAND-SUBTOTAL"]["annual_dry_matter_tonnes"].replace(",", ""))
    assert grassland_actor_dm == 26_554
    assert grassland_subtotal_dm == 26_553
    assert grassland_actor_dm - grassland_subtotal_dm == 1
    actor_rows_dm = grassland_actor_dm + verge_actor_dm
    assert actor_rows_dm == 61_438
    assert actor_rows_dm == int(by_id["OVAM17-ALL-GRASS-AND-VERGES"]["annual_dry_matter_tonnes"].replace(",", ""))


def test_ovam_gr3_extract_is_source_registered_checksummed_and_reference_only() -> None:
    source = next(row for row in _read(GROUP / "source_register.csv") if row["source_id"] == "SRC-OVAM-GR3-2017-TABLE36")
    manifest = next(row for row in _read(GROUP / "dataset_manifest.csv") if row["file_name"] == FILENAME)
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_source = next(row for row in _read(audit / "global_source_register.csv") if row["dataset_path"] == REL)
    readiness = next(row for row in _read(audit / "global_dataset_readiness.csv") if row["dataset_path"] == REL)
    checksum = next(row for row in _read(audit / "source_dataset_checksums.csv") if row["dataset_path"] == REL)
    assert source["doi_or_stable_identifier"] == ""
    assert "Table 36, printed p. 79" in source["quality_notes"]
    assert manifest["row_count"] == "17"
    assert manifest["integration_readiness"] == "traceable_reference_only_not_runtime_eligible"
    assert global_source["source_id"] == "SRC-OVAM-GR3-2017-TABLE36"
    assert readiness["numeric_rows"] == "17"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert checksum["sha256"] == hashlib.sha256((GROUP / FILENAME).read_bytes()).hexdigest()
