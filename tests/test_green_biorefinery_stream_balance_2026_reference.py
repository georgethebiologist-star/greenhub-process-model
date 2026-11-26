import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
FILE_NAME = "green_biorefinery_stream_balance_2026_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_pilot_stream_mass_and_nitrogen_table_is_traceable_and_hierarchical():
    rows = _rows(DATA_DIR / FILE_NAME)
    metadata = json.loads(
        (DATA_DIR / "green_biorefinery_stream_balance_2026_reference.source.json")
        .read_text(encoding="utf-8")
    )
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    sources = _rows(DATA_DIR / "source_register.csv")

    assert len(rows) == metadata["rows"] == 24
    assert len({row["observation_id"] for row in rows}) == 24
    assert {row["source_id"] for row in rows} == {"SRC-ELSHANI-2026"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sum(row["filename"] == FILE_NAME for row in manifest) == 1
    assert sum(row["source_id"] == "SRC-ELSHANI-2026" for row in sources) == 1

    lookup = {(row["stream_name"], row["parameter"]): row for row in rows}
    assert lookup[("green juice", "fresh_mass")]["stream_role"] == "intermediate"
    assert lookup[("unrecovered material", "nitrogen_concentration")]["reported_value"] == ""
    assert lookup[("unrecovered material", "nitrogen_concentration")]["data_status"] == "not_reported"

    final_streams = [row for row in rows if row["stream_role"] in {"final_product", "unrecovered_loss"}]
    fresh_output = sum(float(row["reported_value"]) for row in final_streams if row["parameter"] == "fresh_mass")
    dm_output = sum(float(row["reported_value"]) for row in final_streams if row["parameter"] == "dry_mass")
    assert fresh_output == 5264
    assert fresh_output - float(lookup[("forage biomass", "fresh_mass")]["reported_value"]) == 1
    assert dm_output == float(lookup[("forage biomass", "dry_mass")]["reported_value"]) == 1000
    assert metadata["balance_checks"]["nitrogen_balance_status"] == "incomplete"
