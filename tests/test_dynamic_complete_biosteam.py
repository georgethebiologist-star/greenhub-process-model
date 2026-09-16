from __future__ import annotations

import json
from pathlib import Path

import biosteam as bst
import pytest

from Greenhub.dynamic_complete_proxy import DynamicCompleteProxyConfig
from Greenhub.dynamic_downstream_biosteam import (
    DynamicADProxyUnit,
    DynamicAmmoniaRecoveryUnit,
    DynamicBiogasUpgradingUnit,
    DynamicCHPProxyUnit,
    DynamicDigestateSeparationUnit,
    DynamicIonExchangeUnit,
    DynamicPhosphorusRecoveryUnit,
    DynamicPotassiumWaterConcentrationUnit,
    run_dynamic_complete_biosteam_grid,
    run_dynamic_complete_biosteam_step,
    write_dynamic_complete_biosteam_reports,
)
from Greenhub.feedstock_proxy import load_feedstock_proxies


@pytest.fixture(scope="module")
def may_system():
    return run_dynamic_complete_biosteam_step(
        DynamicCompleteProxyConfig(), "2026-05"
    )


@pytest.fixture(scope="module")
def complete_grid():
    return run_dynamic_complete_biosteam_grid()


def test_default_may_builds_isolated_downstream_biosteam_units(may_system):
    assert isinstance(may_system.units["ad"], DynamicADProxyUnit)
    assert isinstance(may_system.units["biogas_upgrading"], DynamicBiogasUpgradingUnit)
    assert isinstance(may_system.units["digestate_separation"], DynamicDigestateSeparationUnit)
    assert isinstance(may_system.units["ammonia_recovery"], DynamicAmmoniaRecoveryUnit)
    assert isinstance(may_system.units["phosphorus_recovery"], DynamicPhosphorusRecoveryUnit)
    assert isinstance(
        may_system.units["potassium_water_concentration"],
        DynamicPotassiumWaterConcentrationUnit,
    )
    assert isinstance(may_system.units["ion_exchange"], DynamicIonExchangeUnit)
    assert len(may_system.units) == 13
    assert may_system.validation.closes is True
    assert may_system.can_drive_complete_biosteam_proxy is True
    assert may_system.can_drive_simulation is False
    assert may_system.validated_simulation_ready is False


def test_default_grid_builds_and_validates_all_seven_months(complete_grid):
    assert complete_grid.time_labels == (
        "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"
    )
    assert complete_grid.all_steps_parity_passed is True
    assert complete_grid.all_steps_complete_biosteam_ready is True
    assert complete_grid.all_empirical_flowsheets_unchanged is True
    assert complete_grid.max_stream_residual_kg_hr <= 1e-7
    assert complete_grid.max_component_residual_kg_hr <= 1e-7
    json.dumps(complete_grid.to_dict())


def test_press_cake_is_external_and_never_enters_ad(may_system):
    press_cake = may_system.streams["press_cake"]
    assert press_cake not in tuple(may_system.units["ad"].ins)
    assert all("press_cake" not in stream.ID for stream in may_system.units["ad"].ins)
    assert may_system.validation.press_cake_boundary_valid is True
    assert may_system.proxy_step.ad.metrics["press_cake_included"] is False


def test_water_scrubbing_produces_biomethane_and_reject_gas(may_system):
    assert "biomethane_product" in may_system.streams
    assert "reject_gas" in may_system.streams
    assert may_system.streams["biomethane_product"].F_mass > 0.0
    assert may_system.streams["reject_gas"].F_mass > 0.0
    metrics = may_system.units["biogas_upgrading"].proxy_scaled_metrics
    assert metrics["methane_slip_kg_hr"] > 0.0
    assert metrics["biomethane_m3_hr"] > 0.0


def test_chp_is_an_energy_route_not_biomethane_upgrading():
    result = run_dynamic_complete_biosteam_step(
        DynamicCompleteProxyConfig(
            upgrading_method="chp_utilities",
            resource_recovery_methods=(),
        ),
        "2026-05",
    )
    assert isinstance(result.units["chp"], DynamicCHPProxyUnit)
    assert "biomethane_product" not in result.stream_records
    assert "chp_flue_gas_proxy" in result.stream_records
    metrics = result.units["chp"].proxy_scaled_metrics
    assert metrics["chp_electricity_output_kwh_hr"] > 0.0
    assert metrics["chp_heat_output_kwh_hr"] > 0.0
    assert result.validation.closes is True


def test_mea_runs_only_with_flagged_assumption_closure():
    enabled = run_dynamic_complete_biosteam_step(
        DynamicCompleteProxyConfig(
            upgrading_method="mea",
            resource_recovery_methods=(),
        ),
        "2026-05",
    )
    policy_ids = {item.policy_id for item in enabled.unit_payloads["gas_route"].evidence}
    statuses = {item.source_status for item in enabled.unit_payloads["gas_route"].evidence}
    assert {"ASSUMP-MEA-001", "ASSUMP-MEA-002"} <= policy_ids
    assert "engineering_assumption" in statuses
    assert enabled.can_drive_complete_biosteam_proxy is True

    strict = run_dynamic_complete_biosteam_step(
        DynamicCompleteProxyConfig(
            upgrading_method="mea",
            resource_recovery_methods=(),
            allow_assumptions=False,
        ),
        "2026-05",
    )
    assert strict.can_drive_complete_biosteam_proxy is False
    assert strict.blockers


def test_resource_recovery_sequence_produces_all_candidate_streams(may_system):
    expected = {
        "ammonium_product",
        "struvite_product",
        "potassium_concentrate",
        "recovered_water",
        "ammonium_ion_exchange_product",
        "final_residual_liquor",
    }
    assert expected <= set(may_system.stream_records)
    assert all(may_system.streams[name].F_mass >= 0.0 for name in expected)
    assert may_system.validation.metadata_inclusive_balances_close is True


def test_metadata_pools_remain_parallel_and_carriers_are_explicit(may_system):
    digestate = may_system.stream_records["digestate"]
    assert digestate.carrier_mappings["DryMatter"] == "OtherBiodegradableOrganics"
    assert "total_N" in digestate.metadata_masses_kg_hr
    assert "total_P" in digestate.metadata_masses_kg_hr
    assert digestate.unrepresented_mass_kg_hr == pytest.approx(0.0, abs=1e-8)
    assert may_system.provenance["metadata_bridge_component"] == "OtherBiodegradableOrganics"


def test_strict_mode_builds_but_does_not_claim_complete_readiness():
    result = run_dynamic_complete_biosteam_step(
        DynamicCompleteProxyConfig(allow_assumptions=False), "2026-05"
    )
    assert result.validation.closes is True
    assert result.can_drive_complete_biosteam_proxy is False
    assert "digestate_N_P_K_S_speciation_missing" in result.blockers
    assert result.can_drive_simulation is False
    assert result.validated_simulation_ready is False


def test_complete_biosteam_reports_are_written(complete_grid, tmp_path):
    paths = write_dynamic_complete_biosteam_reports(complete_grid, tmp_path)
    assert set(paths) == {"streams", "units", "balances", "parity", "assumptions"}
    assert all(Path(path).is_file() for path in paths.values())
    assert "carrier_mappings" in Path(paths["streams"]).read_text(encoding="utf-8")
    assert "max_component_residual_kg_hr" in Path(paths["parity"]).read_text(encoding="utf-8")


def test_empirical_registry_and_proxy_data_remain_unchanged():
    flowsheet = bst.main_flowsheet.get_flowsheet()
    snapshot = tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in flowsheet.registries
    )
    proxies = dict(load_feedstock_proxies())
    result = run_dynamic_complete_biosteam_step(
        DynamicCompleteProxyConfig(
            upgrading_method="common_conditioning",
            resource_recovery_methods=("digestate_separation",),
        ),
        "2026-05",
    )
    assert result.validation.empirical_flowsheet_unchanged is True
    assert bst.main_flowsheet.get_flowsheet() is flowsheet
    assert tuple(
        tuple(sorted((item.ID, id(item)) for item in registry))
        for registry in flowsheet.registries
    ) == snapshot
    assert dict(load_feedstock_proxies()) == proxies

