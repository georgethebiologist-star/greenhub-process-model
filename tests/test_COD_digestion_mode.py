import biosteam as bst
import pytest

from Greenhub.phase5_units import AnaerobicDigester, digestion_parameters_from_mapping


def test_COD_yield_mode_runs_without_component_double_counting(phase5_values):
    values = dict(
        phase5_values,
        digestion_calculation_mode="COD_yield",
        methane_yield_nm3_kg_cod_converted=0.20,
    )
    feed = bst.Stream("cod_mode_feed", Water=90.0, Glucose=10.0, units="kg/hr")
    reactor = AnaerobicDigester(
        "R589",
        ins=feed,
        outs="cod_mode_broth",
        parameters=digestion_parameters_from_mapping(values, enabled=True),
    )
    reactor.simulate()
    assert reactor.parameters.calculation_mode == "COD_yield"
    assert reactor.generated_kg_hr["Methane"] > 0.0
    assert reactor.converted_cod_kg_hr > reactor.methane_cod_kg_hr


def test_zero_COD_and_zero_biodegradability_are_safe(phase5_values):
    parameters = digestion_parameters_from_mapping(phase5_values, enabled=True)
    water_feed = bst.Stream("zero_cod_feed", Water=100.0, units="kg/hr")
    reactor = AnaerobicDigester("R590", ins=water_feed, outs="zero_cod_broth", parameters=parameters)
    reactor.simulate()
    assert reactor.generated_kg_hr.get("Methane", 0.0) == 0.0

    zero_values = dict(phase5_values)
    for name in (
        "carbohydrate_biodegradable_fraction",
        "protein_biodegradable_fraction",
        "lipid_biodegradable_fraction",
        "other_cod_biodegradable_fraction",
    ):
        zero_values[name] = 0.0
    zero_parameters = digestion_parameters_from_mapping(zero_values, enabled=True)
    glucose_feed = bst.Stream("zero_biodegradable_feed", Water=90.0, Glucose=10.0, units="kg/hr")
    zero_reactor = AnaerobicDigester("R591", ins=glucose_feed, outs="zero_biodegradable_broth", parameters=zero_parameters)
    zero_reactor.simulate()
    assert zero_reactor.converted_cod_kg_hr == 0.0
    assert zero_reactor.outs[0].imass["Methane"] == 0.0


def test_impossible_COD_methane_yield_fails(phase5_values):
    values = dict(
        phase5_values,
        digestion_calculation_mode="COD_yield",
        methane_yield_nm3_kg_cod_converted=1.0,
    )
    parameters = digestion_parameters_from_mapping(values, enabled=True)
    feed = bst.Stream("impossible_yield_feed", Water=90.0, Glucose=10.0, units="kg/hr")
    reactor = AnaerobicDigester("R592", ins=feed, outs="impossible_yield_broth", parameters=parameters)
    with pytest.raises(ValueError, match="theoretical"):
        reactor.simulate()
