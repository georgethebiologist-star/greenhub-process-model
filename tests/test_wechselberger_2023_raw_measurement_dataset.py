from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "lca" / "source_data"
AUDIT = ROOT / "Greenhub" / "data" / "global_audit_package"
SOURCE_ID = "SRC-WECHSELBERGER-2023"
FILES = {
    "wechselberger_et_al_2023_measurement_data_raw.csv": "d35a0df634b1000bb936eee46aa7a3cb",
    "wechselberger_et_al_2023_glossary_raw.csv": "37d36bbf21a5ec651cf1459dc220804c",
    "wechselberger_et_al_2023_R_code_raw.Rmd": "47c53939bc683071d8cb35a0db41b430",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_zenodo_source_files_are_verbatim_registered_and_reference_only() -> None:
    data_path = GROUP / "wechselberger_et_al_2023_measurement_data_raw.csv"
    with data_path.open("r", encoding="cp1252", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames
    assert len(rows) == 294
    assert len(fields or []) == 32
    assert {row["process_stage"] for row in rows} == {
        "Biogas production", "Biogas utilization", "Miscellaneous", "Not specified",
        "Substrate receiving & storage",
    }
    country_values = {row["country"] for row in rows}
    assert {"Austria", "Germany", "Sweden", "Switzerland"} <= country_values
    assert {"Canada", "Denmark"} <= country_values  # cited secondary observations, not the 33-plant campaign

    for filename, expected_md5 in FILES.items():
        path = GROUP / filename
        payload = path.read_bytes()
        assert hashlib.md5(payload).hexdigest() == expected_md5
        assert len(payload) < 100_000_000
        sidecar = json.loads(Path(str(path) + ".source.json").read_text(encoding="utf-8"))
        assert sidecar["source_file"] == filename
        assert sidecar["source_file_md5"] == expected_md5
        assert sidecar["source_record_doi"] == "10.5281/zenodo.7474206"
        assert sidecar["source_v1_doi"] == "10.5281/zenodo.7422108"
        assert sidecar["runtime_parameter_mapping"] is None
        assert sidecar["activation_state"] == "reference_only"
        assert "not GreenHub or roadside-grass specific" in sidecar["transferability"]
        assert sidecar["primary_measurement_geography"] == "Austria, Germany, Sweden and Switzerland"

    manifest = {row["filename"]: row for row in _rows(GROUP / "dataset_manifest.csv")}
    global_sources = {row["dataset_path"]: row for row in _rows(AUDIT / "global_source_register.csv")}
    checksums = {row["dataset_path"]: row for row in _rows(AUDIT / "source_dataset_checksums.csv")}
    readiness = {row["dataset_path"]: row for row in _rows(AUDIT / "global_dataset_readiness.csv")}
    for filename in FILES:
        rel = f"lca/source_data/{filename}"
        assert manifest[filename]["integration_readiness"] == "traceable_reference_only_not_runtime_eligible"
        assert global_sources[rel]["source_id"] == SOURCE_ID
        assert checksums[rel]["sha256"] == hashlib.sha256((ROOT / "Greenhub" / "data" / rel).read_bytes()).hexdigest()
        assert readiness[rel]["readiness"] == "D3"

    source = next(row for row in _rows(ROOT / "Greenhub" / "data" / "lca" / "source_register.csv") if row["source_id"] == SOURCE_ID)
    assert "294 records" in source["quality_notes"]

