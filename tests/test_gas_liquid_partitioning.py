import pytest


def test_partition_ledger_conserves_each_gas(representative_phase5_separator):
    for row in representative_phase5_separator.partition_rows:
        allocated = row["raw_biogas_kg_hr"] + row["digestate_kg_hr"] + row["uncaptured_kg_hr"]
        assert allocated == pytest.approx(row["produced_or_entering_kg_hr"])
