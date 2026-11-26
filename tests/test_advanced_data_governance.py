"""Checkpoint 1 tests for the read-only advanced-model dataset quality gate."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from Greenhub.data_governance import (
    INTEGRATION_ELIGIBILITY,
    build_checkpoint1_registries,
)
from scratch.audit_greenhub_datasets import identifier_columns_for_dataset


def _read_rows(path):
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_literature_candidate_audit_uses_candidate_id_not_reused_scenario_id():
    candidate_path = (
        Path(__file__).resolve().parents[1]
        / "Greenhub/data/Pre-treatment/Mechanical/literature_operating_candidates.csv"
    )
    with candidate_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        assert identifier_columns_for_dataset(reader.fieldnames or []) == ("candidate_id",)

    candidate_ids = [row["candidate_id"] for row in rows]
    assert len(candidate_ids) == len(set(candidate_ids))
    assert sum(row["scenario_id"] == "AD1" for row in rows) == 3


def test_checkpoint1_governance_outputs_are_complete_and_fail_closed(tmp_path):
    result = build_checkpoint1_registries(tmp_path)
    summary = result["summary"]

    datasets = result["dataset_activation"]
    dataset_count = len(datasets)
    assert summary["source_dataset_count"] == dataset_count
    assert summary["source_issue_count"] == sum(record.source_issue_count for record in result["quarantine"])
    assert summary["quarantine_row_count"] == len(result["quarantine"])
    assert summary["dataset_eligibility_counts"] == dict(Counter(record.integration_eligibility for record in datasets))
    assert summary["active_dataset_count"] == 0
    assert summary["default_eligible_dataset_count"] == 0
    assert summary["equation_count"] == 194
    assert summary["equation_eligibility_counts"] == {
        "blocked": 190,
        "reference_only": 4,
    }
    assert summary["active_equation_count"] == 0
    assert summary["cost_overlap_group_count"] == 24
    assert summary["resolved_cost_overlap_count"] == 0
    assert summary["source_checksum_count"] >= dataset_count
    assert summary["scientific_values_modified"] is False

    quarantine = result["quarantine"]
    assert len({record.quarantine_id for record in quarantine}) == len(quarantine)
    assert all(record.integration_eligibility == "blocked" for record in quarantine)
    assert all(record.required_correction for record in quarantine)
    assert all(record.calculation_pathways_affected for record in quarantine)

    assert len(datasets) == dataset_count
    assert all(record.integration_eligibility in INTEGRATION_ELIGIBILITY for record in datasets)
    assert not any(record.active for record in datasets)
    assert not any(record.default_eligibility for record in datasets)
    assert not any(record.calculation_connected for record in datasets)

    equations = result["equation_activation"]
    assert summary["equation_count"] == len(equations)
    assert sum(record.source_row_count for record in equations) == 511
    duplicate = next(
        record
        for record in equations
        if record.dataset_path == "Protein recovery/Membrane/energy_data.csv"
        and record.equation_id == "EQ-ENERGY-001"
    )
    assert duplicate.source_row_count == 5
    assert duplicate.integration_eligibility == "blocked"
    assert not any(record.active for record in equations)
    assert not any(record.typed_implementation_present for record in equations)

    costs = result["cost_ownership"]
    assert len(costs) == 24
    assert sum(record.dataset_count for record in costs) == 49
    assert all(record.resolution_status == "blocked" for record in costs)
    assert all(record.selected_state == "not_selected" for record in costs)


def test_checkpoint1_generation_is_deterministic_and_source_safe(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = build_checkpoint1_registries(first_dir)
    second = build_checkpoint1_registries(second_dir)

    assert first["summary"] == second["summary"]
    for key in (
        "quarantine",
        "dataset_activation",
        "equation_activation",
        "cost_ownership",
        "source_checksums",
        "summary",
    ):
        first_path = first["paths"][key]
        second_path = second["paths"][key]
        assert first_path.read_bytes() == second_path.read_bytes()

    dataset_count = first["summary"]["source_dataset_count"]
    checksum_rows = _read_rows(first["paths"]["source_checksums"])
    assert len(checksum_rows) == first["summary"]["source_checksum_count"]
    assert all(len(row["sha256"]) == 64 for row in checksum_rows)
    assert all(int(row["byte_size"]) > 0 for row in checksum_rows)
    assert any(
        row["dataset_path"] == "lca/source_data/wechselberger_et_al_2023_R_code_raw.Rmd"
        for row in checksum_rows
    )
    assert any(
        row["dataset_path"] == "Pre-treatment/Feedstock/roadside_cutting_field_decay_schaffers_1998_reference.csv"
        for row in checksum_rows
    )
    assert any(
        row["dataset_path"] == "Pre-treatment/Feedstock/greenhub_zuid_holland_dry_run_operational_evidence_2024_2026_reference.csv"
        for row in checksum_rows
    )
    assert any(
        row["dataset_path"] == "Bigas production + upgrade/AD kinetics/roadside_grass_juice_continuous_digestion_chopda_2026_abstract_reference.csv"
        for row in checksum_rows
    )
    assert any(
        row["dataset_path"] == "Pre-treatment/Mechanical/grassification_maldegem_site_access_observations_2019_reference.csv"
        for row in checksum_rows
    )
    assert any(
        row["dataset_path"] == "lca/grassification_flanders_roadside_grass_lca_2021_reference.csv"
        for row in checksum_rows
    )
    assert any(
        row["dataset_path"] == "Protein recovery/Isoelectric/pilot_fraction_protein_quality_nynas_2024_reference.csv"
        for row in checksum_rows
    )
