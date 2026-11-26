import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_coburn_table5_recovery_benchmark_is_traceable_and_not_activated():
    path = DATA / "alfalfa_protein_recovery_methods_coburn_2021_reference.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA / "source_register.csv")
    manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 5
    assert len({row["record_id"] for row in rows}) == 5
    assert {row["source_id"] for row in rows} == {"COBURN2021"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["replicates"] for row in rows} == {"3"}
    assert {row["feedstock"] for row in rows} == {"UMN4624 biomass-type alfalfa herbage"}
    assert {row["apc_recovery_g_per_kg_herbage_DM"] for row in rows} == {"105", "109", "134", "138", "142"}
    acid = next(row for row in rows if row["recovery_method"] == "acid")
    assert acid["crude_protein_g_per_kg_APC"] == "458"
    assert acid["statistical_groups_crude_protein"] == "c"
    assert "reagent volume/dose is not reported" in acid["notes"].lower()
    base_acid = next(row for row in rows if row["recovery_method"] == "base_then_acid")
    assert "then adjusted to pH 4" in base_acid["reported_treatment"]
    assert metadata["doi"] == "10.1002/agg2.20184"
    assert metadata["source_location"] == "Table 5 and Section 2.3, APC recovery methods"
    assert metadata["activation"] == "reference_only"
    assert metadata["no_runtime_mapping"] is True
    assert any("not roadside grass" in item for item in metadata["limitations"])
    assert sum(row["source_id"] == "COBURN2021" for row in sources) == 1
    assert any(row["filename"] == path.name and row["row_count"] == "5" and row["integration_readiness"] == "reference_only" for row in manifest)

    asset = next(row for row in catalog if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "COBURN2021"
    assert asset["source_dois"] == "10.1002/agg2.20184"
    assert asset["readiness"] == "reference_only"

    source_code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert path.name not in source_code
