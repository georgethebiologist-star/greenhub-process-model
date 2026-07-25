from Greenhub.characterization import characterize_feed


def test_aggregate_measurement_is_compared_not_allocated(simple_input_mapping):
    cod = next(row for row in simple_input_mapping["records"] if row["python_name"] == "cod")
    cod.update(value=13000.0, measurement_status="measured", source_class="A")
    result = characterize_feed(simple_input_mapping, ID="reconciliation_feed")
    row = next(item for item in result.reconciliation if item.measurement == "cod")
    assert row.calculated_value is not None
    assert "COD" not in result.component_flows_kg_hr
    assert result.stream.F_mass == 100.0
