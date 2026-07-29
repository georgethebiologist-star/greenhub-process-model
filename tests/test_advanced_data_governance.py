"""Checkpoint 1 tests for the read-only advanced-model dataset quality gate."""

from __future__ import annotations

import csv

from Greenhub.data_governance import (
    INTEGRATION_ELIGIBILITY,
    build_checkpoint1_registries,
)


def _read_rows(path):
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_checkpoint1_governance_outputs_are_complete_and_fail_closed(tmp_path):
    result = build_checkpoint1_registries(tmp_path)
    summary = result["summary"]

    assert summary["source_dataset_count"] == 301
    assert summary["source_issue_count"] == 443
    assert summary["quarantine_row_count"] == 278
    assert summary["dataset_eligibility_counts"] == {
        "blocked": 52,
        "reference_only": 249,
    }
    assert summary["active_dataset_count"] == 0
    assert summary["default_eligible_dataset_count"] == 0
    assert summary["equation_count"] == 179
    assert summary["equation_eligibility_counts"] == {
        "blocked": 169,
        "reference_only": 10,
    }
    assert summary["active_equation_count"] == 0
    assert summary["cost_overlap_group_count"] == 24
    assert summary["resolved_cost_overlap_count"] == 0
    assert summary["source_checksum_count"] == 301
    assert summary["scientific_values_modified"] is False

    quarantine = result["quarantine"]
    assert len({record.quarantine_id for record in quarantine}) == len(quarantine)
    assert sum(record.source_issue_count for record in quarantine) == 443
    assert all(record.integration_eligibility == "blocked" for record in quarantine)
    assert all(record.required_correction for record in quarantine)
    assert all(record.calculation_pathways_affected for record in quarantine)

    datasets = result["dataset_activation"]
    assert len(datasets) == 301
    assert all(record.integration_eligibility in INTEGRATION_ELIGIBILITY for record in datasets)
    assert not any(record.active for record in datasets)
    assert not any(record.default_eligibility for record in datasets)
    assert not any(record.calculation_connected for record in datasets)

    equations = result["equation_activation"]
    assert sum(record.source_row_count for record in equations) == 183
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

    checksum_rows = _read_rows(first["paths"]["source_checksums"])
    assert len(checksum_rows) == 301
    assert all(len(row["sha256"]) == 64 for row in checksum_rows)
    assert all(int(row["byte_size"]) > 0 for row in checksum_rows)
