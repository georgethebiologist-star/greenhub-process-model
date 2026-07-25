"""Tests for the common Phase 6 raw-biogas conditioning train."""

import biosteam as bst
import pytest

from Greenhub.phase6_inputs import load_phase6_inputs
from Greenhub.phase6_units import (
    ParticleSiloxaneFilter,
    pretreatment_parameters_from_mapping,
)
from Greenhub.systems import create_phase6_scenario


def test_phase6_cooling_and_condensate_balance():
    model = create_phase6_scenario("BG2").simulate()
    balances = {row.unit_id: row for row in model.validation.unit_balances}

    assert model.streams["cooled_raw_biogas"].T < model.streams["raw_biogas"].T
    assert model.streams["raw_biogas_condensate"].imass["Water"] > 0.0
    assert abs(balances["G601"].mass_error_kg_hr) < 1e-6
    assert abs(balances["S601"].mass_error_kg_hr) < 1e-6


def test_phase6_h2s_removal_balance():
    model = create_phase6_scenario("BG2").simulate()
    inlet = model.units["R601"].ins[0]
    outlet = model.units["R601"].outs[0]

    assert outlet.imass["HydrogenSulfide"] < inlet.imass["HydrogenSulfide"]
    assert model.streams["spent_h2s_removal_media"].F_mass > 0.0
    balance = next(
        row for row in model.validation.unit_balances if row.unit_id == "R601"
    )
    assert balance.maximum_component_error_kg_hr < 1e-6


def test_phase6_ammonia_removal_balance():
    model = create_phase6_scenario("BG2").simulate()
    inlet = model.units["R602"].ins[0]
    outlet = model.units["R602"].outs[0]

    assert outlet.imass["Ammonia"] < inlet.imass["Ammonia"]
    assert model.streams["ammonia_scrubber_liquor"].F_mass > 0.0
    assert abs(model.validation.component_errors_kg_hr["Ammonia"]) < 1e-6


def test_phase6_filter_balance():
    values = load_phase6_inputs(scenario_id="BG2").parameter_values
    parameters = pretreatment_parameters_from_mapping(
        values,
        enabled=True,
    ).filtration
    feed = bst.Stream(
        "filter_test_feed",
        Methane=1.0,
        Siloxanes=0.01,
        SuspendedSolids=0.02,
        units="kg/hr",
        phase="g",
    )
    fresh_media = bst.Stream("filter_test_fresh_media")
    unit = ParticleSiloxaneFilter(
        "F697",
        ins=(feed, fresh_media),
        outs=("filter_test_gas", "filter_test_spent"),
        parameters=parameters,
    )
    unit.simulate()

    conditioned, spent = unit.outs
    assert conditioned.imass["Siloxanes"] < feed.imass["Siloxanes"]
    assert conditioned.imass["SuspendedSolids"] < feed.imass["SuspendedSolids"]
    assert spent.imass["Siloxanes"] > 0.0
    assert sum(stream.F_mass for stream in unit.outs) == pytest.approx(
        sum(stream.F_mass for stream in unit.ins),
        abs=1e-9,
    )
