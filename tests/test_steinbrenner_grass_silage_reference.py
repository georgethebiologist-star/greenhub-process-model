import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/storage/grass_silage_storage_pressjuice_bmp_steinbrenner_2022_reference.csv"
SIDECAR = DATA.with_suffix(".source.json")
SOURCE_REGISTER = DATA.parent / "source_register.csv"
CATALOG = ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_steinbrenner_reference_dataset_is_complete_and_traceable():
    rows = _rows(DATA)
    sidecar = json.loads(SIDECAR.read_text(encoding="utf-8"))
    sources = _rows(SOURCE_REGISTER)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    assert len(rows) == 147
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"SRC-STEINBRENNER-2022"}
    assert sum(row["source_location"].startswith("Table 3") for row in rows) == 80
    assert sum(row["source_location"].startswith("Table 4") for row in rows) == 64
    assert sum(row["measurement"] == "press_cake_specific_methane_yield" for row in rows) == 3

    source = next(row for row in sources if row["source_id"] == "SRC-STEINBRENNER-2022")
    assert source["doi_or_stable_identifier"] == "10.1007/s12649-021-01626-4"
    assert sidecar["persistent_identifier"] == "doi:10.1007/s12649-021-01626-4"
    assert "CC BY 4.0" in sidecar["license"]
    assert sidecar["dataset_id"].startswith("urn:greenhub:")
    assert sidecar["activation_state"] == "reference_only"
    asset = next(
        row for row in catalog["assets"]
        if row["relative_path"].endswith(DATA.name)
    )
    assert asset["source_metadata_status"] == "linked_to_source_register"
    assert "10.1007/s12649-021-01626-4" in asset["source_dois"]
    assert asset["readiness"] == "reference_only"


def test_steinbrenner_basis_censoring_and_nonactivation_are_preserved():
    rows = _rows(DATA)
    by_id = {row["observation_id"]: row for row in rows}

    assert by_id["STB22-C20-LA"]["reported_mean"] == "114.9"
    assert by_id["STB22-C20-LA"]["unit"] == "g/kg TS"
    assert by_id["STB22-WB37-PJ-BA"]["reported_mean"] == "20.1"
    assert by_id["STB22-WB37-PJ-BA"]["basis"] == "press juice fresh-matter basis"
    assert by_id["STB22-C20-ISOBA"]["reported_mean"] == "<0.1"
    assert by_id["STB22-C20-ISOBA"]["reported_sd"] == ""
    assert by_id["STB22-C20-PC-SMY"]["reported_mean"] == "0.353"
    assert by_id["STB22-C20-PC-SMY"]["unit"] == "Nm3 CH4/kg VS"
    assert all(row["activation_state"] == "reference_only" for row in rows)
