"""Tests for loading the versioned GreenHub master input workbook."""

from pathlib import Path

import pytest

from Greenhub.input_data import INPUT_WORKBOOK_PATH, ensure_input_workbook, load_feed_specification
from Greenhub.input_data import load_input_records_csv


def test_master_input_workbook_exists():
    assert ensure_input_workbook() == INPUT_WORKBOOK_PATH
    assert INPUT_WORKBOOK_PATH.exists()


def test_missing_master_workbook_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="master input workbook"):
        ensure_input_workbook(tmp_path / "missing.xlsx")


def test_feed_specification_loads_from_workbook():
    specification = load_feed_specification()
    assert specification.selected_month == "July"
    assert specification.sample_id == "baseline"
    assert specification.total_mass_flow_kg_hr > 0.0
    assert specification.records


def test_csv_input_records_are_supported(tmp_path: Path):
    path = tmp_path / "records.csv"
    path.write_text(
        "name,python_name,value,unit,basis,stream,sample_id,scenario,data_type,measurement_status,source_class,distribution,priority,allocation_target,active\n"
        "Glucose,glucose,1.0,g/L,compound mass,raw_liquid_fraction,s1,baseline,component,measured,A,none,10,Glucose,true\n",
        encoding="utf-8",
    )
    records = load_input_records_csv(path)
    assert records[0].allocation_target == "Glucose"
