from Greenhub.characterization import characterize_feed


def test_missing_optional_values_do_not_add_mass_or_break_simulation(simple_input_mapping):
    simple_input_mapping["records"].append(
        {
            "name": "Potassium", "python_name": "potassium", "value": None,
            "unit": "mg/L", "basis": "K", "stream": "raw_liquid_fraction",
            "sample_id": "test", "scenario": "baseline", "month": "All",
            "data_type": "component", "measurement_status": "not_measured",
            "source_class": "E", "distribution": "none", "priority": 10,
            "allocation_target": "PotassiumIon", "active": True,
        }
    )
    result = characterize_feed(simple_input_mapping, ID="partial_feed")
    assert "PotassiumIon" not in result.component_flows_kg_hr
    assert result.stream.F_mass == 100.0
    quality = next(row for row in result.data_quality_rows if row["python_name"] == "potassium")
    assert "preserved as missing" in quality["warning"]
