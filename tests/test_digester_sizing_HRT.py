import pytest

from Greenhub.phase5_specifications import calculate_digester_sizing


def test_HRT_sizing_uses_flow_and_time():
    result = calculate_digester_sizing(
        liquid_flow_m3_hr=2.0,
        cod_load_kg_hr=10.0,
        vs_load_kg_hr=5.0,
        hrt_days=20.0,
        target_cod_olr_kg_m3_day=2.0,
        target_vs_olr_kg_m3_day=1.0,
        sizing_mode="HRT_priority",
        working_volume_fraction=0.9,
        headspace_fraction=0.1,
        maximum_single_tank_volume_m3=None,
    )
    assert result.selected_working_volume_m3 == pytest.approx(960.0)
    assert result.actual_hrt_days == pytest.approx(20.0)
