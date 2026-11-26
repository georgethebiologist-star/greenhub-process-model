from pathlib import Path

from scratch.audit_greenhub_datasets import read_csv


def test_dataset_audit_preserves_and_flags_short_and_extra_csv_rows(tmp_path: Path):
    source = tmp_path / "shape.csv"
    source.write_text("left,right\n1,2\n3\n4,5,6\n", encoding="utf-8")

    headers, rows = read_csv(source)

    assert headers == ["left", "right"]
    assert rows[0] == {"left": "1", "right": "2"}
    assert "missing values for columns: right" in rows[1]["__csv_row_shape_issues__"]
    assert "extra unquoted fields" in rows[2]["__csv_row_shape_issues__"]
    assert '"6"' in rows[2]["__csv_row_shape_issues__"]
