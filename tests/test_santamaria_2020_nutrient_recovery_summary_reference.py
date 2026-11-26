import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Resource recovery" / "Digestate_and_Separation"
CSV_PATH = DATA_DIR / "clover_grass_nutrient_recovery_and_ad_balance_santamaria_2020_reference.csv"


def _rows():
    with CSV_PATH.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_santamaria_summary_extract_is_traceable_and_kept_reference_only():
    rows = _rows()
    assert len(rows) == 48
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["source_id"] for row in rows} == {"SRC_SANTAMARIA_FERNANDEZ_2020"}

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["doi"] == "10.1007/s12649-019-00842-3"
    assert "no CC BY license was verified" in sidecar["license_and_reuse"]
    assert sidecar["row_count"] == 48
    assert sidecar["readiness"] == "D3"


def test_santamaria_recovery_ranges_and_censored_bounds_keep_their_semantics():
    by_id = {row["record_id"]: row for row in _rows()}
    cake_c = by_id["SF2020-REC-CLOVER-CAKE-C"]
    assert (cake_c["lower_bound"], cake_c["upper_bound"], cake_c["relation"]) == ("60", "79", "range")
    assert "fresh biomass input" in cake_c["basis"]

    grouped = by_id["SF2020-REC-CLOVER-CAKE-NPS"]
    assert grouped["metric"] == "N_P_S_recovery_grouped"
    assert (grouped["lower_bound"], grouped["upper_bound"]) == ("52", "63")
    assert "not resolved" in grouped["interpretation_note"]

    upper = by_id["SF2020-REC-CLOVER-BJ-P"]
    assert upper["lower_bound"] == ""
    assert upper["upper_bound"] == "27"
    assert upper["relation"] == "up_to"

    protein = by_id["SF2020-REC-PROTEIN-CLOVER-GRASS-NITROGEN"]
    assert protein["reported_value"] == "16"
    assert protein["basis"] == "nitrogen in fresh biomass input"


def test_santamaria_ad_narrative_does_not_merge_distinct_metrics_or_hide_conflict():
    by_id = {row["record_id"]: row for row in _rows()}
    carbon = by_id["SF2020-AD-C-CONVERSION"]
    organic_matter = by_id["SF2020-AD-OM-CONVERSION"]
    assert carbon["reported_value"] == "56"
    assert organic_matter["reported_value"] == "48"
    assert carbon["basis"] != organic_matter["basis"]

    ammonium = by_id["SF2020-AD-NH4-SHARE-IN"]
    assert "brown-juice constituent" in ammonium["stream"]
    assert ammonium["reported_uncertainty"] == "2.7"

    conflict = by_id["SF2020-AD-CN-CONFLICT-ALT"]
    assert conflict["data_status"] == "quarantined_source_conflict"
    assert conflict["relation"] == "quarantined_conflict"
    assert conflict["activation_state"] == "reference_only"

    manifest_path = DATA_DIR / "dataset_manifest.csv"
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    entry = next(row for row in manifest if row["filename"] == CSV_PATH.name)
    assert entry["row_count"] == "48"
    assert entry["integration_status"] == "traceable_reference_only_not_runtime_eligible"
