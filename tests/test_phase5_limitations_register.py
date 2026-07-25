from Greenhub.phase5_limitations import LIMITATION_CATEGORIES


def test_limitations_register_is_structured_and_phase_complete(phase5_snapshot):
    limitations = phase5_snapshot.limitations
    assert {1, 2, 3, 4, 5}.issubset({item.phase for item in limitations})
    assert all(item.category in LIMITATION_CATEGORIES for item in limitations)
    assert all(item.data_needed and item.impact_on_results for item in limitations)
    assert any(item.unit_or_stream == "R501" for item in limitations)
    assert any(item.unit_or_stream == "AD4/AD5" for item in limitations)
