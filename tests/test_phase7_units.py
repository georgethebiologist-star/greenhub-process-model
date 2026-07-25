"""Mechanism, stoichiometry, and conservation tests for Phase 7 units."""

from __future__ import annotations

from dataclasses import replace

import biosteam as bst
import pytest

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.phase4_validation import sum_stream_component_flows
from Greenhub.phase7_units import (
    AcidAbsorber,
    AmmoniaStripper,
    CalciumPhosphateReactor,
    DigestateSolidLiquidSeparator,
    IonExchangeBed,
    IonExchangeRegeneration,
    PotassiumEvaporator,
    PotassiumMembraneConcentrator,
    StruviteCrystallizer,
    acid_parameters_from_mapping,
    calcium_parameters_from_mapping,
    ion_exchange_parameters_from_mapping,
    potassium_parameters_from_mapping,
    separation_parameters_from_mapping,
    stripping_parameters_from_mapping,
    struvite_parameters_from_mapping,
)


def _assert_elements_close(inputs, outputs, tolerance=1e-8):
    inlet = calculate_elemental_flows(sum_stream_component_flows(inputs))
    outlet = calculate_elemental_flows(sum_stream_component_flows(outputs))
    for element in inlet:
        assert inlet[element] == pytest.approx(outlet[element], abs=tolerance)


@pytest.fixture
def digestate_separator(phase7_values):
    feed = bst.Stream(
        "p7_separator_feed",
        Water=90.0,
        SuspendedSolids=4.0,
        InertSolids=1.0,
        MicrobialBiomass=1.0,
        ParticulatePhosphorus=0.2,
        Ammonium=1.0,
        PotassiumIon=0.5,
        Orthophosphate=0.4,
        units="kg/hr",
    )
    unit = DigestateSolidLiquidSeparator(
        "S790",
        ins=feed,
        outs=("p7_test_solids", "p7_test_centrate"),
        parameters=separation_parameters_from_mapping(phase7_values),
    )
    unit.simulate()
    return unit


def test_digestate_separator_mass_balance(digestate_separator):
    assert digestate_separator.ins[0].F_mass == pytest.approx(
        sum(stream.F_mass for stream in digestate_separator.outs), abs=1e-9
    )


def test_digestate_separator_soluble_species_partition(digestate_separator):
    feed = digestate_separator.ins[0]
    centrate = digestate_separator.outs[1]
    for component_id in ("Ammonium", "PotassiumIon", "Orthophosphate"):
        assert centrate.imass[component_id] / feed.imass[component_id] > 0.5


def test_digestate_separator_solid_capture(digestate_separator):
    feed = digestate_separator.ins[0]
    solids = digestate_separator.outs[0]
    assert solids.imass["SuspendedSolids"] / feed.imass["SuspendedSolids"] > 0.5
    assert solids.imass["InertSolids"] / feed.imass["InertSolids"] > 0.5


@pytest.fixture
def struvite_reactor(phase7_values):
    feed = bst.Stream(
        "p7_struvite_feed",
        Water=100.0,
        Ammonium=2.0,
        Orthophosphate=2.0,
        CalciumIon=0.2,
        CarbonateIon=0.2,
        units="kg/hr",
    )
    unit = StruviteCrystallizer(
        "R790",
        ins=(feed, bst.Stream("p7_mg"), bst.Stream("p7_base"), bst.Stream("p7_seed")),
        outs="p7_struvite_slurry",
        parameters=struvite_parameters_from_mapping(phase7_values),
    )
    unit.simulate()
    return unit


def test_struvite_phosphorus_balance(struvite_reactor):
    _assert_elements_close(struvite_reactor.ins, struvite_reactor.outs)
    assert struvite_reactor.formed_struvite_kmol_hr > 0.0


def test_struvite_magnesium_balance(struvite_reactor):
    inlet = calculate_elemental_flows(sum_stream_component_flows(struvite_reactor.ins))
    outlet = calculate_elemental_flows(sum_stream_component_flows(struvite_reactor.outs))
    assert inlet["magnesium"] == pytest.approx(outlet["magnesium"], abs=1e-9)


def test_struvite_crystal_water_balance(struvite_reactor):
    delta = struvite_reactor.reaction_delta_kg_hr
    water_kmol = delta["Water"] / chemicals.Water.MW
    assert water_kmol == pytest.approx(-6.0 * struvite_reactor.formed_struvite_kmol_hr, abs=1e-9)


def test_struvite_competing_precipitation(struvite_reactor):
    assert struvite_reactor.competing_calcium_phosphate_kmol_hr >= 0.0
    assert struvite_reactor.magnesium_hydroxide_kmol_hr >= 0.0
    assert struvite_reactor.calcium_carbonate_kmol_hr >= 0.0


@pytest.fixture
def calcium_reactor(phase7_values):
    feed = bst.Stream(
        "p7_calcium_feed",
        Water=100.0,
        Orthophosphate=2.0,
        CarbonateIon=0.1,
        units="kg/hr",
    )
    unit = CalciumPhosphateReactor(
        "R791",
        ins=(feed, bst.Stream("p7_ca"), bst.Stream("p7_ca_base")),
        outs="p7_calcium_slurry",
        parameters=calcium_parameters_from_mapping(phase7_values),
    )
    unit.simulate()
    return unit


def test_calcium_phosphate_calcium_balance(calcium_reactor):
    _assert_elements_close(calcium_reactor.ins, calcium_reactor.outs)
    assert calcium_reactor.formed_product_kmol_hr > 0.0


def test_calcium_phosphate_phosphorus_balance(calcium_reactor):
    inlet = calculate_elemental_flows(sum_stream_component_flows(calcium_reactor.ins))
    outlet = calculate_elemental_flows(sum_stream_component_flows(calcium_reactor.outs))
    assert inlet["phosphorus"] == pytest.approx(outlet["phosphorus"], abs=1e-9)


def _stripper(phase7_values, medium):
    parameters = replace(stripping_parameters_from_mapping(phase7_values), medium=medium)
    if medium == "vacuum":
        parameters = replace(parameters, pressure_pa=50000.0)
    feed = bst.Stream("strip_feed", Water=100.0, Ammonium=1.0, CarbonDioxide=0.2, units="kg/hr")
    unit = AmmoniaStripper(
        "A790",
        ins=(feed, bst.Stream("strip_carrier")),
        outs=("strip_liquid", "strip_gas"),
        parameters=parameters,
    )
    unit.simulate()
    return unit


def test_ammonia_stripper_nitrogen_balance(phase7_values):
    unit = _stripper(phase7_values, "air")
    _assert_elements_close(unit.ins, unit.outs)


def test_ammonia_stripper_gas_allocation(phase7_values):
    unit = _stripper(phase7_values, "air")
    assert unit.outs[1].imass["Ammonia"] > 0.0
    assert unit.outs[0].imass["Ammonium"] < unit.ins[0].imass["Ammonium"]


def test_air_stripping_physics(phase7_values):
    unit = _stripper(phase7_values, "air")
    assert unit.ins[1].imass["Oxygen"] > 0.0
    assert unit.ins[1].imass["Nitrogen"] > 0.0
    assert unit.power_utility.consumption > 0.0


def test_steam_stripping_water_balance(phase7_values):
    unit = _stripper(phase7_values, "steam")
    _assert_elements_close(unit.ins, unit.outs)
    assert unit.ins[1].imass["Water"] > 0.0
    assert unit.gross_heat_kw > 0.0


def test_vacuum_stripping_pressure_logic(phase7_values):
    unit = _stripper(phase7_values, "vacuum")
    assert unit.outs[0].P == pytest.approx(50000.0)
    assert unit.power_utility.consumption > 0.0


@pytest.mark.parametrize("acid_id,product_id", [("SulfuricAcid", "AmmoniumSulfate"), ("HydrochloricAcid", "AmmoniumChloride")])
def test_acid_absorber_element_balances(phase7_values, acid_id, product_id):
    parameters = replace(acid_parameters_from_mapping(phase7_values), acid_id=acid_id)
    gas = bst.Stream("absorber_gas", Ammonia=1.0, Nitrogen=2.0, units="kg/hr", phase="g")
    unit = AcidAbsorber(
        "A791",
        ins=(gas, bst.Stream("absorber_acid"), bst.Stream("absorber_water")),
        outs=("absorber_clean_gas", "absorber_product"),
        parameters=parameters,
    )
    unit.simulate()
    _assert_elements_close(unit.ins, unit.outs)
    assert unit.outs[1].imass[product_id] > 0.0


def test_acid_absorber_nitrogen_balance(phase7_values):
    parameters = acid_parameters_from_mapping(phase7_values)
    gas = bst.Stream("n_balance_gas", Ammonia=1.0, units="kg/hr", phase="g")
    unit = AcidAbsorber("A792", ins=(gas, bst.Stream("n_acid"), bst.Stream("n_water")), outs=("n_clean", "n_product"), parameters=parameters)
    unit.simulate()
    _assert_elements_close(unit.ins, unit.outs)


def test_ion_exchange_regeneration_balance(phase7_values):
    parameters = ion_exchange_parameters_from_mapping(phase7_values)
    feed = bst.Stream("ix_feed", Water=100.0, Ammonium=1.0, units="kg/hr")
    sites = bst.Stream("ix_sites", SodiumZeolite=0.1, units="kmol/hr")
    bed = IonExchangeBed("A793", ins=(feed, sites), outs=("ix_treated", "ix_loaded"), parameters=parameters)
    bed.simulate()
    brine = bst.Stream("ix_brine")
    rinse = bst.Stream("ix_rinse")
    regeneration = IonExchangeRegeneration(
        "R793",
        ins=(bed.outs[1], brine, rinse),
        outs=("ix_regenerated", "ix_regenerant"),
        parameters=parameters,
    )
    regeneration.simulate()
    _assert_elements_close((feed, sites, brine, rinse), (bed.outs[0], *regeneration.outs))


def test_ion_exchange_sodium_balance(phase7_values):
    parameters = ion_exchange_parameters_from_mapping(phase7_values)
    feed = bst.Stream("ix_na_feed", Water=10.0, Ammonium=0.5, units="kg/hr")
    sites = bst.Stream("ix_na_sites", SodiumZeolite=0.05, units="kmol/hr")
    bed = IonExchangeBed("A794", ins=(feed, sites), outs=("ix_na_treated", "ix_na_loaded"), parameters=parameters)
    bed.simulate()
    assert bed.outs[0].imass["SodiumIon"] > 0.0
    _assert_elements_close(bed.ins, bed.outs)


def test_evaporator_water_balance(phase7_values):
    feed = bst.Stream("evap_feed", Water=100.0, PotassiumIon=1.0, SodiumIon=1.0, units="kg/hr")
    unit = PotassiumEvaporator("E790", ins=feed, outs=("evap_conc", "evap_vapor"), parameters=potassium_parameters_from_mapping(phase7_values))
    unit.simulate()
    assert sum(stream.imass["Water"] for stream in unit.outs) == pytest.approx(feed.imass["Water"])
    assert unit.design_results["Concentration factor"] > 1.0


def test_potassium_concentration_balance(phase7_values):
    feed = bst.Stream("k_feed", Water=100.0, PotassiumIon=1.0, units="kg/hr")
    unit = PotassiumEvaporator("E791", ins=feed, outs=("k_conc", "k_vapor"), parameters=potassium_parameters_from_mapping(phase7_values))
    unit.simulate()
    assert sum(stream.imass["PotassiumIon"] for stream in unit.outs) == pytest.approx(1.0)


def test_membrane_concentrate_balance(phase7_values):
    parameters = replace(potassium_parameters_from_mapping(phase7_values), method="membrane")
    feed = bst.Stream("membrane_feed", Water=100.0, PotassiumIon=1.0, SodiumIon=0.5, units="kg/hr")
    unit = PotassiumMembraneConcentrator(
        "M790",
        ins=(feed, bst.Stream("membrane_cleaning")),
        outs=("membrane_concentrate", "membrane_permeate", "membrane_wastewater"),
        parameters=parameters,
    )
    unit.simulate()
    assert unit.outs[0].imass["PotassiumIon"] + unit.outs[1].imass["PotassiumIon"] == pytest.approx(1.0)
    assert sum(stream.F_mass for stream in unit.outs) == pytest.approx(sum(stream.F_mass for stream in unit.ins))
