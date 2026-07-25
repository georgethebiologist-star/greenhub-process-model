"""Shared pytest fixtures for GreenHub model tests."""

from __future__ import annotations

import gc
import sys
from pathlib import Path
from types import SimpleNamespace

import biosteam as bst
import pytest

# Console-script launchers do not always add the working directory to sys.path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Greenhub.chemicals import set_thermo
from Greenhub.phase3_inputs import load_phase3_inputs
from Greenhub.phase4_inputs import load_phase4_inputs
from Greenhub.phase5_inputs import load_phase5_inputs
from Greenhub.phase5_units import (
    AnaerobicDigester,
    BiogasDisengagement,
    digestion_parameters_from_mapping,
    gas_partition_parameters_from_mapping,
)
from Greenhub.phase7_inputs import load_phase7_inputs
from Greenhub.systems import create_phase4_scenario, create_phase5_scenario

PHASE5_TEST_FILES = {
    "test_digester_feed_characterization.py",
    "test_digester_conditioning.py",
    "test_digester_pH_adjustment.py",
    "test_digester_sizing_HRT.py",
    "test_digester_sizing_OLR.py",
    "test_hydrolysis_reactions.py",
    "test_acidogenesis_reactions.py",
    "test_acetogenesis_reactions.py",
    "test_methanogenesis_reactions.py",
    "test_buswell_extended.py",
    "test_COD_digestion_mode.py",
    "test_hybrid_digestion_mode.py",
    "test_protein_digestion.py",
    "test_organic_N_mineralization.py",
    "test_ammonia_equilibrium_digester.py",
    "test_ammonia_inhibition.py",
    "test_sulphate_reduction.py",
    "test_phosphorus_mineralization.py",
    "test_biomass_growth.py",
    "test_gas_liquid_partitioning.py",
    "test_dissolved_methane.py",
    "test_raw_biogas_composition.py",
    "test_biogas_normalization.py",
    "test_digestate_composition.py",
    "test_digester_heat_balance.py",
    "test_digester_mixing_power.py",
    "test_phase5_system.py",
    "test_phase5_scenarios.py",
    "test_phase5_scenario_isolation.py",
    "test_phase5_seasonal.py",
    "test_phase5_mass_balance.py",
    "test_phase5_COD_balance.py",
    "test_phase5_carbon_balance.py",
    "test_phase5_nitrogen_balance.py",
    "test_phase5_phosphorus_balance.py",
    "test_phase5_sulphur_balance.py",
    "test_phase5_energy_balance.py",
    "test_phase5_reporting.py",
    "test_phase5_limitations_register.py",
    "test_phase5_missing_data.py",
}
PHASE6_TEST_FILES = {
    "test_phase6_conditioning.py",
    "test_phase6_water_scrubbing.py",
    "test_phase6_membranes.py",
    "test_phase6_psa.py",
    "test_phase6_mea.py",
    "test_phase6_scenarios.py",
    "test_phase6_reporting.py",
}
PHASE7_TEST_FILES = {
    "test_phase7_balance_and_utilities.py",
    "test_phase7_integrated_scenarios.py",
    "test_phase7_orders.py",
    "test_phase7_rebuild.py",
    "test_phase7_specifications.py",
    "test_phase7_units.py",
    "test_phase7_system.py",
    "test_phase7_seasonal.py",
    "test_phase7_reporting.py",
}


def pytest_collection_modifyitems(items) -> None:
    """Run older phases before the larger Phase 5 and Phase 6 graphs."""

    def phase_order(item) -> int:
        if item.path.name in PHASE6_TEST_FILES:
            return 2
        if item.path.name in PHASE7_TEST_FILES:
            return 3
        if item.path.name in PHASE5_TEST_FILES:
            return 1
        return 0

    items.sort(key=phase_order)


@pytest.fixture(autouse=True)
def clean_biosteam_registry():
    """Keep tests independent of BioSTEAM's process registries."""

    bst.main_flowsheet.clear()
    set_thermo()
    yield
    bst.main_flowsheet.clear()
    gc.collect()


@pytest.fixture
def simple_input_mapping():
    """Small dictionary dataset used by characterization unit tests."""

    def row(name, python_name, value, unit, target=None, data_type="component", basis="compound mass", status="measured"):
        return {
            "name": name,
            "python_name": python_name,
            "value": value,
            "unit": unit,
            "basis": basis,
            "stream": "raw_liquid_fraction",
            "sample_id": "test",
            "scenario": "baseline",
            "month": "All",
            "data_type": data_type,
            "measurement_status": status,
            "source_class": "A" if status == "measured" else "E",
            "distribution": "none",
            "priority": 10,
            "allocation_target": target,
            "active": True,
        }

    return {
        "sample_id": "test",
        "scenario": "baseline",
        "selected_month": "July",
        "total_mass_flow_kg_hr": 100.0,
        "monthly_total_mass_kg": 2400.0,
        "operating_days": 1.0,
        "control": {"estimate_unknown_residuals": False},
        "records": [
            row("Density", "density", 1000.0, "kg/m3", data_type="physical"),
            row("Temperature", "temperature", 25.0, "degC", data_type="physical"),
            row("pH", "ph", 7.0, "pH", data_type="physical"),
            row("Glucose", "glucose", 10.0, "g/L", "Glucose"),
            row("Soluble protein", "soluble_protein", 5.0, "g/L", "SolubleProtein"),
            row("Suspended solids", "suspended_solids", 2.0, "g/L", "SuspendedSolids"),
            row("COD", "cod", None, "mg/L", data_type="aggregate", basis="O2 equivalent", status="not_measured"),
        ],
    }


@pytest.fixture
def phase3_values():
    """Resolved structural F2 values for focused custom-unit tests."""

    return dict(load_phase3_inputs(scenario_id="F2").parameter_values)


@pytest.fixture
def phase4_values():
    """Resolved structural PR3 values for focused Phase 4 tests."""

    return dict(load_phase4_inputs(scenario_id="PR3").parameter_values)


@pytest.fixture
def phase5_values():
    """Resolved structural AD1 values for focused digestion tests."""

    return dict(load_phase5_inputs(scenario_id="AD1").parameter_values)


@pytest.fixture
def phase7_values():
    """Resolved structural NR4 values for focused Phase 7 unit tests."""

    return dict(load_phase7_inputs(scenario_id="NR4").parameter_values)


@pytest.fixture
def representative_phase5_reactor(phase5_values):
    """Compact R501 case for reaction tests without rebuilding Phases 1-4."""

    feed = bst.Stream(
        "representative_digester_feed",
        Water=90.0,
        Glucose=4.0,
        AceticAcid=1.0,
        SolubleProtein=2.0,
        OrganicNitrogen=0.2,
        OrganicPhosphorus=0.1,
        SulfateIon=0.1,
        HeavyMetals=0.001,
        PersistentOrganics=0.001,
        Pesticides=0.001,
        Microplastics=0.001,
        PathogenIndicators=0.001,
        units="kg/hr",
    )
    reactor = AnaerobicDigester(
        "R598",
        ins=feed,
        outs="representative_digester_broth",
        parameters=digestion_parameters_from_mapping(phase5_values, enabled=True),
    )
    reactor.simulate()
    return reactor


@pytest.fixture
def representative_phase5_separator(representative_phase5_reactor, phase5_values):
    """Compact V501 case for raw-gas and digestate tests."""

    separator = BiogasDisengagement(
        "V598",
        ins=representative_phase5_reactor.outs[0],
        outs=("representative_raw_biogas", "representative_digestate", "representative_uncaptured_gas"),
        parameters=gas_partition_parameters_from_mapping(phase5_values),
        digester_pH=7.2,
    )
    separator.simulate()
    return separator


@pytest.fixture(scope="session")
def simulated_phase4_pr3():
    """One immutable PR3 result shared by read-only conservation tests."""

    return create_phase4_scenario("PR3").simulate()


@pytest.fixture
def simulated_phase5_ad1():
    """Fresh AD1 result for one test, avoiding retained cleared registries."""

    return create_phase5_scenario("AD1").simulate()


@pytest.fixture(scope="session")
def phase5_snapshot():
    """Plain-data AD1 snapshot shared by balance tests without retaining a flowsheet."""

    model = create_phase5_scenario("AD1").simulate()
    snapshot = SimpleNamespace(
        validation=model.validation,
        metrics=dict(model.metrics),
        limitations=tuple(model.limitations),
        selected_month=model.input_bundle.selected_month,
    )
    bst.main_flowsheet.clear()
    return snapshot
