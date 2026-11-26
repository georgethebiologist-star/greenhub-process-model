import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"


def test_guo_abstract_values_are_comparator_only_and_keep_relative_basis():
    path = DATA / "grass_clover_pilot_press_PEF_protein_separation_guo_2022_abstract_reference.csv"
    sidecar = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (DATA / "source_register.csv").open(encoding="utf-8-sig", newline="") as handle:
        sources = {row["source_id"]: row for row in csv.DictReader(handle)}
    with (DATA / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        manifest = {row["filename"]: row for row in csv.DictReader(handle)}
    with (ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        global_manifest = {row["filename"]: row for row in csv.DictReader(handle)}

    by_id = {row["observation_id"]: row for row in rows}
    assert len(rows) == 8
    assert by_id["GUO2022_JUICE_INCREASE"]["value"] == "25"
    assert "relative to untreated control" in by_id["GUO2022_JUICE_INCREASE"]["basis_or_comparison"]
    assert by_id["GUO2022_CRUDE_PROTEIN_INCREASE"]["value"] == "31"
    assert by_id["GUO2022_PRODUCT_CRUDE_PROTEIN"]["unit"] == "g/100 g DM"
    assert {row["evidence_class"] for row in rows} == {"B_literature_abstract"}
    assert {row["activation_state"] for row in rows if row["activation_state"] != "reference_only"} == {"D4_opt_in_candidate"}
    assert sum(row["activation_state"] == "D4_opt_in_candidate" for row in rows) == 2
    assert sidecar["publication_doi"] == "10.1016/j.fufo.2022.100173"
    assert sidecar["calculation_connected"] is True
    assert sidecar["activation_state"] == "partial_D4_opt_in_runtime_candidate"
    assert sidecar["source_id"] in sources
    assert manifest[path.name]["row_count"] == str(len(rows))
    assert manifest[path.name]["integration_readiness"] == "D4_partial_opt_in_runtime_integration"
    assert global_manifest[path.name]["row_count_observed"] == str(len(rows))
    assert global_manifest[path.name]["detected_readiness"] == "D3"
