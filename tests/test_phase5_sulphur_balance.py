import pytest


def test_phase5_total_sulphur_closes(phase5_snapshot):
    validation = phase5_snapshot.validation
    assert abs(validation.element_errors_kg_hr["sulfur"]) < 1e-8
    assert validation.element_out_kg_hr["sulfur"] == pytest.approx(validation.element_in_kg_hr["sulfur"], abs=1e-12)
