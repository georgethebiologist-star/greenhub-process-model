from Greenhub.state_engine import ProcessState, build_state_outputs


def test_process_state_is_explicit_and_serializable():
    fields = ProcessState.__dataclass_fields__
    assert {"flow_kg_hr", "temperature_k", "pressure_pa", "pH", "moisture_fraction", "solids_kg_hr", "density_kg_m3", "viscosity_pa_s", "particle_size_um", "storage_age_h"}.issubset(fields)


def test_state_outputs_preserve_structural_fallback_for_missing_equations():
    class Model:
        streams = {}
        units = {}

    result = build_state_outputs(Model())
    assert result["process_state_history"][0]["time"] == 0.0
    assert any(item["fallback"] for item in result["equation_usage"])
    assert result["inventory_evolution"][0]["status"] == "structural_fallback"
