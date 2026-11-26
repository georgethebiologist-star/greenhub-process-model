import csv
import json
from pathlib import Path

import pytest

from Greenhub.application.contracts.requests import _default_feed_composition


ROOT = Path(__file__).resolve().parents[1]
FEED_DIR = ROOT / "Greenhub/data/Pre-treatment/Feedstock"
DATASET = FEED_DIR / "ryegrass_nitrogen_fractionation_hoekstra_2008_reference.csv"
RELATIVE_DATASET = "Pre-treatment/Feedstock/ryegrass_nitrogen_fractionation_hoekstra_2008_reference.csv"


def test_hoekstra_nitrogen_fractions_support_only_a_class_c_protein_partition():
    with DATASET.open(encoding="utf-8-sig", newline="") as source_file:
        rows = list(csv.DictReader(source_file))
    by_tissue = {
        tissue: {
            row["parameter"]: float(row["nitrogen_fraction_g_per_kg_total_N"])
            for row in rows
            if row["material_fraction"] == tissue
        }
        for tissue in ("lamina", "sheath")
    }

    soluble_b1n = sum(by_tissue[tissue]["Buffer-soluble true protein nitrogen (B1N)"] for tissue in by_tissue) / 2
    nonsoluble = sum(
        sum(
            by_tissue[tissue][parameter]
            for parameter in (
                "Buffer-insoluble true protein nitrogen (B2N)",
                "Potentially available cell-wall nitrogen (B3N)",
                "Unavailable cell-wall nitrogen (CN)",
            )
        )
        for tissue in by_tissue
    ) / 2
    soluble_share = soluble_b1n / (soluble_b1n + nonsoluble)

    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    compounds = profile["compounds"]
    total_protein_dry = compounds["SolubleProtein"]["source"]["reported_total_protein_dry_basis"]
    soluble_expected = total_protein_dry * profile["dry_matter_fraction"] * soluble_share
    suspended_expected = total_protein_dry * profile["dry_matter_fraction"] * (1 - soluble_share)

    assert len(rows) == 10
    assert by_tissue["lamina"]["Non-protein nitrogen (AN)"] == pytest.approx(186.0)
    assert by_tissue["sheath"]["Non-protein nitrogen (AN)"] == pytest.approx(280.0)
    assert soluble_b1n == pytest.approx(175.0)
    assert nonsoluble == pytest.approx(592.0)
    assert soluble_share == pytest.approx(0.22816166883963496)
    assert by_tissue["lamina"]["Buffer-soluble true protein nitrogen (B1N)"] == pytest.approx(164.0)
    assert by_tissue["sheath"]["Buffer-soluble true protein nitrogen (B1N)"] == pytest.approx(186.0)
    for tissue in by_tissue:
        assert sum(by_tissue[tissue].values()) == pytest.approx(1000.0, abs=1.0)

    for component, expected in (("SolubleProtein", soluble_expected), ("SuspendedProtein", suspended_expected)):
        record = compounds[component]
        source = record["source"]
        assert record["data_class"] == "C"
        assert record["wet_mass_fraction"] == pytest.approx(expected)
        assert source["partition_source_id"] == "SRC-HOEKSTRA-2008-NFRAC"
        assert source["partition_source_doi"] == "10.1016/S1573-5214(08)80035-8"
        assert source["partition_source_observations"]["soluble_true_protein_n_g_per_kg_total_n"] == 175.0
        assert source["partition_source_observations"]["non_soluble_protein_associated_n_g_per_kg_total_n"] == 592.0
        assert source["partition_source_observations"]["soluble_fraction_code"] == "B1N"
        assert "not measured in greenhub" in source["partition_assumption"].lower()
        assert "class-C split" in source["basis"]

    assert compounds["SolubleProtein"]["wet_mass_fraction"] + compounds["SuspendedProtein"]["wet_mass_fraction"] == pytest.approx(
        total_protein_dry * profile["dry_matter_fraction"]
    )
    assert _default_feed_composition()["SolubleProtein"] == pytest.approx(soluble_expected)
    assert _default_feed_composition()["SuspendedProtein"] == pytest.approx(suspended_expected)
    assert sum(record["wet_mass_fraction"] for record in compounds.values()) == pytest.approx(1.0)

    sidecar = json.loads(DATASET.with_suffix(DATASET.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["source_id"] == "SRC-HOEKSTRA-2008-NFRAC"
    assert sidecar["doi"] == "10.1016/S1573-5214(08)80035-8"
    assert sidecar["readiness_state"] == "D4_partial_calculation_connected"
    assert "not the GreenHub Dutch roadside grass" in sidecar["limitations"][0]

    audit = ROOT / "Greenhub/data/global_audit_package"
    with (audit / "global_dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as manifest_file:
        manifest = {row["dataset_path"]: row for row in csv.DictReader(manifest_file)}
    with (audit / "global_source_register.csv").open(encoding="utf-8-sig", newline="") as source_file:
        sources = {row["dataset_path"]: row for row in csv.DictReader(source_file)}
    assert manifest[RELATIVE_DATASET]["detected_readiness"] == "D4"
    assert sources[RELATIVE_DATASET]["source_id"] == "SRC-HOEKSTRA-2008-NFRAC"
