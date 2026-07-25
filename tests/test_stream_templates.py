from Greenhub.stream_templates import STREAM_TEMPLATES


def test_required_process_stream_templates_exist():
    required = {
        "incoming_grass", "raw_liquid_fraction", "clarified_protein_liquid",
        "raw_biogas", "digestate", "biomethane", "struvite_product",
        "ammonium_sulfate_product", "potassium_concentrate", "treated_residual_water",
    }
    assert required <= set(STREAM_TEMPLATES)


def test_templates_validate():
    for template in STREAM_TEMPLATES.values():
        template.validate()
        assert template.canonical_reporting_units
