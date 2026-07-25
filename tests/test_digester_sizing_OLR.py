from Greenhub.phase5_specifications import calculate_digester_sizing


def test_OLR_sizing_and_inconsistency_are_visible():
    result = calculate_digester_sizing(
        liquid_flow_m3_hr=0.1,
        cod_load_kg_hr=10.0,
        vs_load_kg_hr=1.0,
        hrt_days=1.0,
        target_cod_olr_kg_m3_day=1.0,
        target_vs_olr_kg_m3_day=5.0,
        sizing_mode="maximum_required_volume",
        working_volume_fraction=0.85,
        headspace_fraction=0.15,
        maximum_single_tank_volume_m3=100.0,
    )
    assert result.selected_working_volume_m3 == result.volume_by_cod_olr_m3
    assert result.maximum_sizing_disagreement_fraction > 0.5
    assert result.number_of_digesters > 1
