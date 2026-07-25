import pytest

from Greenhub.input_schema import InputRecord


def valid_row():
    return {
        "name": "Glucose", "python_name": "glucose", "value": 1.0, "unit": "g/L",
        "basis": "compound mass", "stream": "raw_liquid_fraction", "sample_id": "s1",
        "scenario": "baseline", "data_type": "component", "measurement_status": "measured",
        "source_class": "A", "distribution": "none", "priority": 10,
        "allocation_target": "Glucose", "active": True,
    }


def test_valid_input_record():
    record = InputRecord.from_mapping(valid_row())
    assert record.value == 1.0
    assert record.source_class == "A"


def test_missing_optional_value_is_preserved():
    row = valid_row()
    row.update(value=None, measurement_status="not_measured")
    assert InputRecord.from_mapping(row).value is None


def test_invalid_uncertainty_range_raises():
    row = valid_row()
    row.update(minimum=2.0, maximum=1.0)
    with pytest.raises(ValueError, match="minimum"):
        InputRecord.from_mapping(row)
