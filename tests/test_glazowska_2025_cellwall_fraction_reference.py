import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Protein recovery/Lactic_Acid/grass_clover_alfalfa_cellwall_sugar_fractionation_glazowska_2025_reference.csv"
SIDECAR = DATA.with_suffix(".source.json")
CATALOG = ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json"


def test_cellwall_fraction_values_are_traceable_and_not_activated():
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 132
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["feedstock"] for row in rows} == {"alfalfa", "grass_clover"}
    assert {row["fraction_code"] for row in rows} == {"FM", "PC", "GJ", "FF", "BJ", "LPC"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["source_id"] for row in rows} == {"SRC-GLAZOWSKA-2025-CELLWALL"}

    groups = {}
    for row in rows:
        groups.setdefault((row["feedstock"], row["fraction_code"]), []).append(row)
        assert "conflict" in row["unit_basis_status"]
        assert "component mass balance" in row["limitations"]
        assert row["doi"] == "10.1007/s13399-023-05125-5"
    assert len(groups) == 12

    for group in groups.values():
        values = {row["metric"]: float(row["reported_value"]) for row in group}
        sugar_total = sum(values[name] for name in (
            "glucose", "xylose", "galactose", "arabinose", "mannose", "rhamnose",
            "fucose", "glucuronic_acid", "galacturonic_acid",
        ))
        # Published components are rounded independently, so their sum may differ slightly.
        assert math.isclose(sugar_total, values["total_non_cellulosic_monosaccharides"], abs_tol=1.5)
        assert 0 < values["total_non_cellulosic_monosaccharides_percent"] < 100

    metadata = SIDECAR.read_text(encoding="utf-8")
    assert "source_unit_conflict" in metadata
    assert "CC BY 4.0" in metadata
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    asset_path = "Greenhub/data/Protein recovery/Lactic_Acid/" + DATA.name
    asset = next(row for row in catalog["assets"] if row["relative_path"] == asset_path)
    assert asset["source_dois"] == "10.1007/s13399-023-05125-5"
    assert asset["readiness"] == "reference_only"
