import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
FILE_NAME = "green_biorefinery_energy_scale_and_storage_benchmarks_2026_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_pilot_energy_and_design_values_keep_distinct_evidence_classes():
    rows = _rows(DATA_DIR / FILE_NAME)
    metadata = json.loads(
        (DATA_DIR / "green_biorefinery_energy_scale_and_storage_benchmarks_2026_reference.source.json")
        .read_text(encoding="utf-8")
    )
    sources = _rows(DATA_DIR / "source_register.csv")
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")

    assert len(rows) == metadata["rows"] == 18
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert {row["source_id"] for row in rows} == {"SRC-ELSHANI-2026"}
    assert sum(row["evidence_class"] == "B_reported_pilot_measurement" for row in rows) == 3
    assert sum(row["evidence_class"] == "C_study_design_assumption" for row in rows) == 5
    assert sum(row["evidence_class"] == "C_literature_based_factor" for row in rows) == 9
    assert sum(row["evidence_class"] == "C_derived_from_reported_values" for row in rows) == 1
    assert sum(row["source_id"] == "SRC-ELSHANI-2026" for row in sources) == 1
    assert sum(row["filename"] == FILE_NAME for row in manifest) == 1

    lookup = {row["parameter"]: row["reported_value"] for row in rows}
    assert lookup["total_energy_demand"] == "1489"
    assert lookup["electricity_demand"] == "375"
    assert lookup["propane_heat_demand"] == "138"
    assert lookup["reported_energy_rounding_check"] == "1488"


def test_phase6_h2s_equation_provenance_row_is_well_formed_and_unique():
    path = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Water_Scrubbing" / "equation_registry.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    ids = [row["equation_id"] for row in rows]
    h2s = next(row for row in rows if row["equation_name"] == "h2s_solubility_temperature_correction")

    assert len(ids) == len(set(ids))
    assert h2s["equation_id"] == "WS_EQN_008"
    assert h2s["source_id"] == "SRC007"
    assert h2s["authors"] == "Peter G. T. Fogg"
    assert h2s["year"] == "1987"
    assert h2s["doi_or_stable_identifier"] == "10.1016/C2009-0-00348-1"
    assert "WS_EQN_005" in h2s["transferability"]

