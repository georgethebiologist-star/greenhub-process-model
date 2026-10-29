from pathlib import Path

from Greenhub.complete_missing_data import (
    completed_input_summary,
    load_completed_input_register,
)


def test_completed_register_is_available_and_traceable():
    path = Path("Greenhub/data/Pre-treatment/Feedstock/expanded_process_data_register.csv")
    records = load_completed_input_register(path)
    assert len(records) == 110
    assert records[0].gap_id == "FD-001"
    assert records[0].source_reference
    assert records[0].numeric_lower == 3.0
    assert records[0].numeric_upper == 5.0


def test_unresolved_rows_are_not_promoted_to_screening_inputs():
    summary = completed_input_summary()
    assert summary["record_count"] == 110
    assert summary["screening_input_count"] < summary["record_count"]
    records = {record.gap_id: record for record in load_completed_input_register()}
    assert not records["FD-010"].usable_as_screening_input
    assert not records["TEA-001"].usable_as_screening_input
