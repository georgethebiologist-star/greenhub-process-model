"""Isolated BioSTEAM units for the complete dynamic proxy pathway.

The complete proxy ledger remains authoritative. Unit operations scale its
resolved per-step mass transformations from their actual BioSTEAM inlet mass,
while analytical nutrient pools and unsupported identities remain in parallel
records. Nothing in this module connects to the empirical GreenHub flowsheet.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import biosteam as bst

from Greenhub.chemicals import thermo
from Greenhub.dynamic_biosteam_adapter import (
    DynamicBioSTEAMAdapterConfig,
    _FLOWSHEET_LOCK,
    _build_calculation_shadow_system_from_run,
    _flowsheet_registry_snapshot,
    _unregister_isolated_flowsheet,
)
from Greenhub.dynamic_complete_proxy import (
    MASS_TOLERANCE_KG_HR,
    CompleteProxyStream,
    CompleteProxyUnitResult,
    DynamicCompleteProxyConfig,
    DynamicCompleteProxyStepResult,
    TraceableProxyValue,
    run_dynamic_complete_proxy_scenario_grid,
    run_dynamic_complete_proxy_scenario_step,
)


RESULTS_DIR = Path(__file__).resolve().parent / "results"
PARITY_TOLERANCE_KG_HR = max(MASS_TOLERANCE_KG_HR, 1e-7)
BOOKKEEPING_CARRIERS = {
    "DryMatter": "OtherBiodegradableOrganics",
    "RecoveredNitrogen": "OrganicNitrogen",
    "CarrierAndWater": "SolubleInertSolids",
    "StruviteEquivalent": "Struvite",
    "Potassium": "PotassiumIon",
    "CapturedNitrogenEquivalent": "OrganicNitrogen",
    "CarbonDioxideEquivalent": "CarbonDioxide",
}


@dataclass(frozen=True)
class DynamicDownstreamStreamRecord:
    source_stream_id: str
    adapter_stream_id: str
    stream_mass_kg_hr: float
    biosteam_component_masses_kg_hr: dict[str, float]
    metadata_masses_kg_hr: dict[str, float]
    carrier_mappings: dict[str, str]
    source_unit: str
    destination: str
    source_status: str
    warnings: tuple[str, ...]

    @property
    def represented_mass_kg_hr(self) -> float:
        return sum(self.biosteam_component_masses_kg_hr.values())

    @property
    def unrepresented_mass_kg_hr(self) -> float:
        return self.stream_mass_kg_hr - self.represented_mass_kg_hr

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "represented_mass_kg_hr": self.represented_mass_kg_hr,
            "unrepresented_mass_kg_hr": self.unrepresented_mass_kg_hr,
        }


@dataclass(frozen=True)
class DynamicDownstreamUnitPayload:
    unit_id: str
    method: str
    input_mass_kg_hr: float
    external_input_mass_kg_hr: float
    output_records: tuple[DynamicDownstreamStreamRecord, ...]
    metrics: dict[str, float | str | bool | None]
    evidence: tuple[TraceableProxyValue, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "ledger_scaled_biosteam_report_only"

    @property
    def expected_total_input_mass_kg_hr(self) -> float:
        return self.input_mass_kg_hr + self.external_input_mass_kg_hr

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "output_records": [item.to_dict() for item in self.output_records],
            "evidence": [item.to_dict() for item in self.evidence],
            "expected_total_input_mass_kg_hr": self.expected_total_input_mass_kg_hr,
        }


@dataclass(frozen=True)
class DynamicCompleteBioSTEAMStreamParity:
    source_stream_id: str
    biosteam_stream_id: str
    target_mass_kg_hr: float
    actual_mass_kg_hr: float
    residual_kg_hr: float
    max_component_residual_kg_hr: float
    metadata_preserved: bool
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicCompleteBioSTEAMValidation:
    stream_parities: tuple[DynamicCompleteBioSTEAMStreamParity, ...]
    protein_parity_passed: bool
    downstream_parity_passed: bool
    metadata_inclusive_balances_close: bool
    press_cake_boundary_valid: bool
    empirical_flowsheet_unchanged: bool
    max_stream_residual_kg_hr: float
    max_component_residual_kg_hr: float
    closes: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "stream_parities": [item.to_dict() for item in self.stream_parities],
        }


@dataclass(frozen=True)
class DynamicCompleteBioSTEAMStepResult:
    proxy_step: DynamicCompleteProxyStepResult
    protein_system_result: Any
    system: Any
    units: dict[str, Any]
    streams: dict[str, Any]
    stream_records: dict[str, DynamicDownstreamStreamRecord]
    unit_payloads: dict[str, DynamicDownstreamUnitPayload]
    isolated_flowsheet: Any
    validation: DynamicCompleteBioSTEAMValidation
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: dict[str, object]
    can_drive_complete_biosteam_proxy: bool
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "complete_biosteam_proxy_report_only"

    @property
    def time_label(self) -> str:
        return self.proxy_step.time_label

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.proxy_step.scenario_id,
            "time_label": self.time_label,
            "system_id": self.system.ID,
            "unit_ids": {key: unit.ID for key, unit in self.units.items()},
            "stream_ids": {key: stream.ID for key, stream in self.streams.items()},
            "stream_records": {key: value.to_dict() for key, value in self.stream_records.items()},
            "unit_payloads": {key: value.to_dict() for key, value in self.unit_payloads.items()},
            "validation": self.validation.to_dict(),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "provenance": dict(self.provenance),
            "can_drive_complete_biosteam_proxy": self.can_drive_complete_biosteam_proxy,
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


@dataclass(frozen=True)
class DynamicCompleteBioSTEAMGridResult:
    config: DynamicCompleteProxyConfig
    steps: tuple[DynamicCompleteBioSTEAMStepResult, ...]
    time_labels: tuple[str, ...]
    all_steps_parity_passed: bool
    all_steps_complete_biosteam_ready: bool
    all_empirical_flowsheets_unchanged: bool
    max_stream_residual_kg_hr: float
    max_component_residual_kg_hr: float
    warning_counts: dict[str, int]
    blocker_counts: dict[str, int]
    can_drive_simulation: bool = False
    validated_simulation_ready: bool = False
    activation_status: str = "complete_biosteam_proxy_grid_report_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "config": self.config.to_dict(),
            "steps": [item.to_dict() for item in self.steps],
            "time_labels": list(self.time_labels),
            "all_steps_parity_passed": self.all_steps_parity_passed,
            "all_steps_complete_biosteam_ready": self.all_steps_complete_biosteam_ready,
            "all_empirical_flowsheets_unchanged": self.all_empirical_flowsheets_unchanged,
            "max_stream_residual_kg_hr": self.max_stream_residual_kg_hr,
            "max_component_residual_kg_hr": self.max_component_residual_kg_hr,
            "warning_counts": dict(self.warning_counts),
            "blocker_counts": dict(self.blocker_counts),
            "can_drive_simulation": self.can_drive_simulation,
            "validated_simulation_ready": self.validated_simulation_ready,
            "activation_status": self.activation_status,
        }


class _DynamicLedgerScaledUnit(bst.Unit):
    """Scale an audited proxy-ledger transformation from actual inlet mass."""

    _link_streams = False
    line = "Dynamic complete proxy ledger unit"

    def _init(self, payload: DynamicDownstreamUnitPayload) -> None:
        if len(payload.output_records) != self._N_outs:
            raise ValueError(
                f"{type(self).__name__} requires {self._N_outs} output records."
            )
        self.proxy_payload = payload
        self.proxy_policy_id = payload.unit_id
        self.proxy_evidence = tuple(item.to_dict() for item in payload.evidence)
        self.proxy_warnings = payload.warnings
        self.proxy_blockers = payload.blockers
        self.proxy_activation_status = payload.activation_status
        self.proxy_scale_factor = 1.0
        self.proxy_scaled_metrics = dict(payload.metrics)

    def _run(self) -> None:
        expected = self.proxy_payload.expected_total_input_mass_kg_hr
        actual = sum(float(stream.F_mass) for stream in self.ins)
        if expected <= PARITY_TOLERANCE_KG_HR:
            scale = 1.0 if actual <= PARITY_TOLERANCE_KG_HR else 0.0
        else:
            scale = actual / expected
        if not math.isfinite(scale) or scale < 0.0:
            raise ValueError(f"{self.ID} calculated an invalid ledger scale factor.")
        self.proxy_scale_factor = scale
        for outlet, record in zip(self.outs, self.proxy_payload.output_records):
            outlet.empty()
            for component, mass in record.biosteam_component_masses_kg_hr.items():
                outlet.imass[component] = mass * scale
        self.proxy_scaled_metrics = {
            key: (_scale_metric(key, value, scale))
            for key, value in self.proxy_payload.metrics.items()
        }


class DynamicADProxyUnit(_DynamicLedgerScaledUnit):
    _N_ins = 2
    _N_outs = 2
    line = "Dynamic AD proxy conversion"


class DynamicGasConditioningUnit(_DynamicLedgerScaledUnit):
    _N_ins = 1
    _N_outs = 2
    line = "Dynamic gas conditioning proxy"


class DynamicBiogasUpgradingUnit(_DynamicLedgerScaledUnit):
    _N_ins = 1
    _N_outs = 2
    line = "Dynamic biogas upgrading proxy"


class DynamicCHPProxyUnit(_DynamicLedgerScaledUnit):
    _N_ins = 1
    _N_outs = 1
    line = "Dynamic CHP energy-route proxy"


class DynamicDigestateSeparationUnit(_DynamicLedgerScaledUnit):
    _N_ins = 1
    _N_outs = 2
    line = "Dynamic digestate separation proxy"


class DynamicAmmoniaRecoveryUnit(_DynamicLedgerScaledUnit):
    _N_ins = 2
    _N_outs = 2
    line = "Dynamic ammonia recovery proxy"


class DynamicPhosphorusRecoveryUnit(_DynamicLedgerScaledUnit):
    _N_ins = 2
    _N_outs = 2
    line = "Dynamic phosphorus recovery proxy"


class DynamicPotassiumWaterConcentrationUnit(_DynamicLedgerScaledUnit):
    _N_ins = 1
    _N_outs = 3
    line = "Dynamic potassium and water concentration proxy"


class DynamicIonExchangeUnit(_DynamicLedgerScaledUnit):
    _N_ins = 1
    _N_outs = 2
    line = "Dynamic ion exchange proxy"


def build_dynamic_complete_biosteam_system(
    step_result: DynamicCompleteProxyStepResult,
) -> DynamicCompleteBioSTEAMStepResult:
    """Extend the isolated protein calculation system with downstream units."""

    integrated = step_result.protein_result
    scenario_config = integrated.config.protein_config()
    adapter_config = DynamicBioSTEAMAdapterConfig(
        scenario_id=step_result.scenario_id,
        time_label=step_result.time_label,
        basis_feed_kg_per_hr=step_result.config.basis_feed_kg_per_hr,
        scenario_config=scenario_config,
    )
    protein = _build_calculation_shadow_system_from_run(
        adapter_config,
        integrated.protein_run,
    )
    if protein.system is None:
        raise RuntimeError("Protein calculation shadow system is unavailable.")

    records, payloads = _build_records_and_payloads(step_result)
    prefix = f"dyn_complete_{_safe_id(step_result.time_label)}"
    flowsheet = protein.isolated_flowsheet
    with _FLOWSHEET_LOCK:
        before_flowsheet = bst.main_flowsheet.get_flowsheet()
        before_snapshot = _flowsheet_registry_snapshot(before_flowsheet)
        flowsheet_registry = bst.Flowsheet.flowsheet.__dict__
        flowsheet_registry[flowsheet.ID] = flowsheet
        try:
            with flowsheet:
                streams = dict(protein.streams)
                for stream_id, record in records.items():
                    streams[stream_id] = bst.Stream(
                        ID=record.adapter_stream_id,
                        thermo=thermo,
                    )
                metadata_mass = _residual_metadata_carrier_mass(step_result)
                streams["ad_metadata_carrier"] = bst.Stream(
                    ID=f"{prefix}_ad_metadata_carrier",
                    thermo=thermo,
                    OtherBiodegradableOrganics=metadata_mass,
                    units="kg/hr",
                )
                units = dict(protein.units)
                units["ad"] = DynamicADProxyUnit(
                    f"{prefix}_ad",
                    ins=(streams["biogas_feed_candidate"], streams["ad_metadata_carrier"]),
                    outs=(streams["raw_biogas"], streams["digestate"]),
                    thermo=thermo,
                    payload=payloads["ad"],
                )
                gas_unit_key = _build_gas_unit(
                    units, streams, payloads["gas_route"], prefix
                )
                current = "digestate"
                for index, source_unit in enumerate(step_result.resource_recovery, start=1):
                    key = _resource_unit_key(source_unit.method)
                    payload = payloads[key]
                    external_stream = None
                    requires_external_port = source_unit.method in {
                        "ammonia_recovery", "phosphorus_recovery"
                    }
                    if payload.external_input_mass_kg_hr or requires_external_port:
                        external_stream = bst.Stream(
                            ID=f"{prefix}_{key}_external_input",
                            thermo=thermo,
                            SolubleInertSolids=payload.external_input_mass_kg_hr,
                            units="kg/hr",
                        )
                        streams[f"{key}_external_input"] = external_stream
                    unit_class = _resource_unit_class(source_unit.method)
                    ins = (
                        (streams[current], external_stream)
                        if external_stream is not None
                        else streams[current]
                    )
                    unit = unit_class(
                        f"{prefix}_{index:02d}_{key}",
                        ins=ins,
                        outs=tuple(streams[item.source_stream_id] for item in payload.output_records),
                        thermo=thermo,
                        payload=payload,
                    )
                    units[key] = unit
                    current = _residual_output_id(source_unit)
                system = bst.System.from_units(
                    ID=f"{prefix}_system",
                    units=tuple(units.values()),
                )
                system.simulate()
        finally:
            _unregister_isolated_flowsheet(flowsheet)
        after_flowsheet = bst.main_flowsheet.get_flowsheet()
        empirical_unchanged = (
            after_flowsheet is before_flowsheet
            and _flowsheet_registry_snapshot(after_flowsheet) == before_snapshot
            and protein.validation.empirical_flowsheet_unchanged
        )

    placeholder = DynamicCompleteBioSTEAMValidation(
        stream_parities=(),
        protein_parity_passed=protein.validation.closes,
        downstream_parity_passed=False,
        metadata_inclusive_balances_close=False,
        press_cake_boundary_valid=False,
        empirical_flowsheet_unchanged=empirical_unchanged,
        max_stream_residual_kg_hr=math.inf,
        max_component_residual_kg_hr=math.inf,
        closes=False,
    )
    provisional = DynamicCompleteBioSTEAMStepResult(
        proxy_step=step_result,
        protein_system_result=protein,
        system=system,
        units=units,
        streams=streams,
        stream_records=records,
        unit_payloads=payloads,
        isolated_flowsheet=flowsheet,
        validation=placeholder,
        warnings=tuple(dict.fromkeys((
            *step_result.warnings,
            "unsupported ledger identities use declared BioSTEAM bookkeeping carriers",
        ))),
        blockers=step_result.blockers,
        provenance={
            "mode": "complete_biosteam_proxy_report_only",
            "authoritative_reference": "dynamic_complete_proxy.py",
            "gas_unit_key": gas_unit_key,
            "metadata_bridge_component": "OtherBiodegradableOrganics",
            "bookkeeping_carriers": dict(BOOKKEEPING_CARRIERS),
            "press_cake_boundary": "external_system_output",
            "empirical_model_modified": False,
            "model_overrides": [],
        },
        can_drive_complete_biosteam_proxy=False,
    )
    validation = validate_dynamic_complete_biosteam_against_proxy(provisional)
    ready = (
        validation.closes
        and step_result.can_drive_complete_proxy_model
        and not step_result.blockers
    )
    return DynamicCompleteBioSTEAMStepResult(
        **{
            **provisional.__dict__,
            "validation": validation,
            "can_drive_complete_biosteam_proxy": ready,
        }
    )


def run_dynamic_complete_biosteam_step(
    config: DynamicCompleteProxyConfig,
    time_label: str,
) -> DynamicCompleteBioSTEAMStepResult:
    return build_dynamic_complete_biosteam_system(
        run_dynamic_complete_proxy_scenario_step(config, time_label)
    )


def run_dynamic_complete_biosteam_grid(
    config: DynamicCompleteProxyConfig | None = None,
) -> DynamicCompleteBioSTEAMGridResult:
    config = config or DynamicCompleteProxyConfig()
    proxy_grid = run_dynamic_complete_proxy_scenario_grid(config)
    steps = tuple(build_dynamic_complete_biosteam_system(step) for step in proxy_grid.steps)
    return DynamicCompleteBioSTEAMGridResult(
        config=config,
        steps=steps,
        time_labels=tuple(item.time_label for item in steps),
        all_steps_parity_passed=all(item.validation.closes for item in steps),
        all_steps_complete_biosteam_ready=all(item.can_drive_complete_biosteam_proxy for item in steps),
        all_empirical_flowsheets_unchanged=all(item.validation.empirical_flowsheet_unchanged for item in steps),
        max_stream_residual_kg_hr=max((item.validation.max_stream_residual_kg_hr for item in steps), default=0.0),
        max_component_residual_kg_hr=max((item.validation.max_component_residual_kg_hr for item in steps), default=0.0),
        warning_counts=dict(sorted(Counter(warning for item in steps for warning in item.warnings).items())),
        blocker_counts=dict(sorted(Counter(blocker for item in steps for blocker in item.blockers).items())),
    )


def validate_dynamic_complete_biosteam_against_proxy(
    result: DynamicCompleteBioSTEAMStepResult,
) -> DynamicCompleteBioSTEAMValidation:
    parities: list[DynamicCompleteBioSTEAMStreamParity] = []
    source_metadata = _source_metadata_by_stream_id(result.proxy_step)
    for stream_id, record in result.stream_records.items():
        stream = result.streams[stream_id]
        actual = float(stream.F_mass)
        component_residuals = [
            abs(float(stream.imass[name]) - target)
            for name, target in record.biosteam_component_masses_kg_hr.items()
        ]
        max_component = max(component_residuals, default=0.0)
        residual = actual - record.stream_mass_kg_hr
        metadata_preserved = record.metadata_masses_kg_hr == source_metadata.get(
            stream_id,
            record.metadata_masses_kg_hr,
        )
        passed = (
            abs(residual) <= PARITY_TOLERANCE_KG_HR
            and max_component <= PARITY_TOLERANCE_KG_HR
            and abs(record.unrepresented_mass_kg_hr) <= PARITY_TOLERANCE_KG_HR
            and metadata_preserved
        )
        parities.append(DynamicCompleteBioSTEAMStreamParity(
            source_stream_id=stream_id,
            biosteam_stream_id=stream.ID,
            target_mass_kg_hr=record.stream_mass_kg_hr,
            actual_mass_kg_hr=actual,
            residual_kg_hr=residual,
            max_component_residual_kg_hr=max_component,
            metadata_preserved=metadata_preserved,
            passed=passed,
        ))
    press_cake = result.streams["press_cake"]
    ad_inputs = tuple(result.units["ad"].ins)
    press_valid = press_cake not in ad_inputs and all(
        "press_cake" not in stream.ID for stream in ad_inputs
    )
    downstream_passed = all(item.passed for item in parities)
    metadata_balances = all(
        abs(payload.expected_total_input_mass_kg_hr - sum(record.stream_mass_kg_hr for record in payload.output_records))
        <= PARITY_TOLERANCE_KG_HR
        for payload in result.unit_payloads.values()
    )
    max_stream = max((abs(item.residual_kg_hr) for item in parities), default=0.0)
    max_component = max((item.max_component_residual_kg_hr for item in parities), default=0.0)
    protein_passed = bool(result.protein_system_result.validation.closes)
    empirical = result.validation.empirical_flowsheet_unchanged
    closes = protein_passed and downstream_passed and metadata_balances and press_valid and empirical
    return DynamicCompleteBioSTEAMValidation(
        stream_parities=tuple(parities),
        protein_parity_passed=protein_passed,
        downstream_parity_passed=downstream_passed,
        metadata_inclusive_balances_close=metadata_balances,
        press_cake_boundary_valid=press_valid,
        empirical_flowsheet_unchanged=empirical,
        max_stream_residual_kg_hr=max_stream,
        max_component_residual_kg_hr=max_component,
        closes=closes,
        warnings=(
            "BioSTEAM bookkeeping carriers are mass devices, not validated molecular speciation",
        ),
    )


def write_dynamic_complete_biosteam_reports(
    result_or_grid: DynamicCompleteBioSTEAMStepResult | DynamicCompleteBioSTEAMGridResult,
    output_dir: str | Path | None = None,
) -> dict[str, str]:
    target = Path(output_dir) if output_dir is not None else RESULTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "streams": target / "dynamic_complete_biosteam_streams.csv",
        "units": target / "dynamic_complete_biosteam_units.csv",
        "balances": target / "dynamic_complete_biosteam_balances.csv",
        "parity": target / "dynamic_complete_biosteam_parity.csv",
        "assumptions": target / "dynamic_complete_biosteam_assumptions.csv",
    }
    steps = result_or_grid.steps if isinstance(result_or_grid, DynamicCompleteBioSTEAMGridResult) else (result_or_grid,)
    stream_rows: list[dict[str, object]] = []
    unit_rows: list[dict[str, object]] = []
    balance_rows: list[dict[str, object]] = []
    parity_rows: list[dict[str, object]] = []
    assumption_rows: list[dict[str, object]] = []
    for step in steps:
        for stream_id, record in step.stream_records.items():
            entries = [(name, mass, "", "") for name, mass in record.biosteam_component_masses_kg_hr.items()]
            entries += [("", "", name, mass) for name, mass in record.metadata_masses_kg_hr.items()]
            if not entries:
                entries = [("", "", "", "")]
            for component, component_mass, metadata, metadata_mass in entries:
                stream_rows.append({
                    "scenario_id": step.proxy_step.scenario_id,
                    "time_label": step.time_label,
                    "source_stream_id": stream_id,
                    "biosteam_stream_id": record.adapter_stream_id,
                    "stream_mass_kg_hr": record.stream_mass_kg_hr,
                    "component": component,
                    "component_mass_kg_hr": component_mass,
                    "metadata_pool": metadata,
                    "metadata_mass_kg_hr": metadata_mass,
                    "carrier_mappings": json.dumps(record.carrier_mappings, sort_keys=True),
                    "source_status": record.source_status,
                })
        for key, unit in step.units.items():
            inputs = tuple(unit.ins)
            outputs = tuple(unit.outs)
            row = {
                "scenario_id": step.proxy_step.scenario_id,
                "time_label": step.time_label,
                "unit_key": key,
                "unit_id": unit.ID,
                "unit_type": type(unit).__name__,
                "input_streams": "|".join(item.ID for item in inputs),
                "output_streams": "|".join(item.ID for item in outputs),
                "input_mass_kg_hr": sum(float(item.F_mass) for item in inputs),
                "output_mass_kg_hr": sum(float(item.F_mass) for item in outputs),
                "residual_kg_hr": sum(float(item.F_mass) for item in inputs) - sum(float(item.F_mass) for item in outputs),
                "metrics": json.dumps(getattr(unit, "proxy_scaled_metrics", {}), sort_keys=True),
            }
            unit_rows.append(row)
            balance_rows.append(dict(row))
        for parity in step.validation.stream_parities:
            parity_rows.append({"scenario_id": step.proxy_step.scenario_id, "time_label": step.time_label, **parity.to_dict()})
        parity_rows.append({
            "scenario_id": step.proxy_step.scenario_id,
            "time_label": step.time_label,
            "source_stream_id": "__protein_calculation_system__",
            "biosteam_stream_id": step.protein_system_result.system.ID,
            "target_mass_kg_hr": step.proxy_step.config.basis_feed_kg_per_hr,
            "actual_mass_kg_hr": step.proxy_step.config.basis_feed_kg_per_hr,
            "residual_kg_hr": 0.0,
            "max_component_residual_kg_hr": max(
                (item.parity_residual_kg_hr for item in step.protein_system_result.validation.unit_parities),
                default=0.0,
            ),
            "metadata_preserved": step.protein_system_result.validation.metadata_records_preserved,
            "passed": step.protein_system_result.validation.closes,
        })
        for item in step.proxy_step.closure_policy.values:
            assumption_rows.append({"scenario_id": step.proxy_step.scenario_id, "time_label": step.time_label, **item.to_dict()})
    _write_rows(paths["streams"], stream_rows)
    _write_rows(paths["units"], unit_rows)
    _write_rows(paths["balances"], balance_rows)
    _write_rows(paths["parity"], parity_rows)
    _write_rows(paths["assumptions"], assumption_rows)
    return {key: str(path) for key, path in paths.items()}


def _build_records_and_payloads(
    step: DynamicCompleteProxyStepResult,
) -> tuple[dict[str, DynamicDownstreamStreamRecord], dict[str, DynamicDownstreamUnitPayload]]:
    prefix = f"dyn_complete_{_safe_id(step.time_label)}"
    records: dict[str, DynamicDownstreamStreamRecord] = {}
    payloads: dict[str, DynamicDownstreamUnitPayload] = {}
    units = (step.ad, step.gas_route, *step.resource_recovery)
    for source_unit in units:
        output_records = tuple(
            _stream_record(stream, prefix)
            for stream in source_unit.outputs
        )
        if source_unit in step.resource_recovery:
            output_records = _with_blocked_product_ports(
                source_unit.method,
                output_records,
                prefix,
            )
        for record in output_records:
            records[record.source_stream_id] = record
        key = (
            "ad" if source_unit is step.ad
            else "gas_route" if source_unit is step.gas_route
            else _resource_unit_key(source_unit.method)
        )
        payloads[key] = DynamicDownstreamUnitPayload(
            unit_id=source_unit.unit_id,
            method=source_unit.method,
            input_mass_kg_hr=source_unit.input_mass_kg_hr,
            external_input_mass_kg_hr=source_unit.external_input_mass_kg_hr,
            output_records=output_records,
            metrics=dict(source_unit.metrics),
            evidence=source_unit.evidence,
            warnings=source_unit.warnings,
            blockers=source_unit.blockers,
        )
    gas_payload = payloads["gas_route"]
    if gas_payload.method == "none" and len(gas_payload.output_records) == 1:
        zero = DynamicDownstreamStreamRecord(
            source_stream_id="reject_gas",
            adapter_stream_id=f"{prefix}_reject_gas",
            stream_mass_kg_hr=0.0,
            biosteam_component_masses_kg_hr={},
            metadata_masses_kg_hr={},
            carrier_mappings={},
            source_unit="gas_route_none",
            destination="not_generated",
            source_status="not_selected",
            warnings=(),
        )
        records[zero.source_stream_id] = zero
        payloads["gas_route"] = DynamicDownstreamUnitPayload(
            **{**gas_payload.__dict__, "output_records": (*gas_payload.output_records, zero)}
        )
    return records, payloads


def _with_blocked_product_ports(
    method: str,
    records: tuple[DynamicDownstreamStreamRecord, ...],
    prefix: str,
) -> tuple[DynamicDownstreamStreamRecord, ...]:
    expected = {
        "digestate_separation": 2,
        "ammonia_recovery": 2,
        "phosphorus_recovery": 2,
        "potassium_water_concentration": 3,
        "ion_exchange": 2,
    }[method]
    missing_ids = {
        "digestate_separation": ("nutrient_rich_solids",),
        "ammonia_recovery": ("ammonium_product",),
        "phosphorus_recovery": ("struvite_product",),
        "potassium_water_concentration": ("potassium_concentrate", "recovered_water"),
        "ion_exchange": ("ammonium_ion_exchange_product",),
    }[method]
    existing = {item.source_stream_id for item in records}
    additions = []
    for stream_id in missing_ids:
        if len(records) + len(additions) >= expected:
            break
        if stream_id in existing:
            continue
        additions.append(DynamicDownstreamStreamRecord(
            source_stream_id=stream_id,
            adapter_stream_id=f"{prefix}_{stream_id}",
            stream_mass_kg_hr=0.0,
            biosteam_component_masses_kg_hr={},
            metadata_masses_kg_hr={},
            carrier_mappings={},
            source_unit=f"{method}_blocked",
            destination="not_generated",
            source_status="blocked_missing_without_assumptions",
            warnings=("zero-flow BioSTEAM port retained for blocked policy",),
        ))
    return (*records, *additions)


def _stream_record(stream: CompleteProxyStream, prefix: str) -> DynamicDownstreamStreamRecord:
    exact_ids = set(thermo.chemicals.IDs)
    represented: dict[str, float] = {}
    mappings: dict[str, str] = {}
    for name, mass in stream.components_kg_hr.items():
        component = name if name in exact_ids else BOOKKEEPING_CARRIERS.get(name)
        if component is None:
            raise KeyError(
                f"No explicit BioSTEAM bookkeeping carrier exists for {name!r}."
            )
        represented[component] = represented.get(component, 0.0) + float(mass)
        if component != name:
            mappings[name] = component
    record = DynamicDownstreamStreamRecord(
        source_stream_id=stream.stream_id,
        adapter_stream_id=f"{prefix}_{_safe_id(stream.stream_id)}",
        stream_mass_kg_hr=float(stream.mass_kg_hr),
        biosteam_component_masses_kg_hr=represented,
        metadata_masses_kg_hr=dict(stream.metadata_kg_hr),
        carrier_mappings=mappings,
        source_unit=stream.source_unit,
        destination=stream.destination,
        source_status=stream.source_status,
        warnings=stream.warnings,
    )
    if abs(record.unrepresented_mass_kg_hr) > PARITY_TOLERANCE_KG_HR:
        raise ValueError(
            f"Stream {stream.stream_id!r} has {record.unrepresented_mass_kg_hr:.6g} "
            "kg/h not represented by exact chemicals or declared carriers."
        )
    return record


def _build_gas_unit(
    units: dict[str, Any],
    streams: dict[str, Any],
    payload: DynamicDownstreamUnitPayload,
    prefix: str,
) -> str:
    method = payload.method
    if method == "common_conditioning":
        key = "gas_conditioning"
        cls = DynamicGasConditioningUnit
    elif method == "chp_utilities":
        key = "chp"
        cls = DynamicCHPProxyUnit
    else:
        key = "biogas_upgrading"
        cls = DynamicBiogasUpgradingUnit
    unit = cls(
        f"{prefix}_{key}",
        ins=streams["raw_biogas"],
        outs=tuple(streams[item.source_stream_id] for item in payload.output_records),
        thermo=thermo,
        payload=payload,
    )
    units[key] = unit
    return key


def _resource_unit_key(method: str) -> str:
    return {
        "digestate_separation": "digestate_separation",
        "ammonia_recovery": "ammonia_recovery",
        "phosphorus_recovery": "phosphorus_recovery",
        "potassium_water_concentration": "potassium_water_concentration",
        "ion_exchange": "ion_exchange",
    }[method]


def _resource_unit_class(method: str) -> type[_DynamicLedgerScaledUnit]:
    return {
        "digestate_separation": DynamicDigestateSeparationUnit,
        "ammonia_recovery": DynamicAmmoniaRecoveryUnit,
        "phosphorus_recovery": DynamicPhosphorusRecoveryUnit,
        "potassium_water_concentration": DynamicPotassiumWaterConcentrationUnit,
        "ion_exchange": DynamicIonExchangeUnit,
    }[method]


def _residual_output_id(unit: CompleteProxyUnitResult) -> str:
    product_prefixes = (
        "nutrient_rich_solids",
        "ammonium_product",
        "struvite_product",
        "potassium_concentrate",
        "recovered_water",
        "ammonium_ion_exchange_product",
    )
    candidates = [
        stream.stream_id
        for stream in unit.outputs
        if not stream.stream_id.startswith(product_prefixes)
    ]
    if len(candidates) != 1:
        raise ValueError(f"Could not identify one residual output for {unit.unit_id}.")
    return candidates[0]


def _residual_metadata_carrier_mass(step: DynamicCompleteProxyStepResult) -> float:
    stream = step.protein_result.protein_run.pathway_preview.biogas_mix_preparation.outputs[0]
    return sum(float(value) for value in stream.metadata_pools_kg_per_kg_feed.values()) * step.config.basis_feed_kg_per_hr


def _source_metadata_by_stream_id(
    step: DynamicCompleteProxyStepResult,
) -> dict[str, dict[str, float]]:
    return {
        stream.stream_id: dict(stream.metadata_kg_hr)
        for unit in (step.ad, step.gas_route, *step.resource_recovery)
        for stream in unit.outputs
    }


def _scale_metric(key: str, value: float | str | bool | None, scale: float) -> float | str | bool | None:
    if isinstance(value, bool) or value is None or not isinstance(value, (int, float)):
        return value
    extensive_tokens = ("_kg_hr", "_m3_hr", "_kwh_hr", "_mj_hr")
    return float(value) * scale if key.endswith(extensive_tokens) else value


def _safe_id(value: str) -> str:
    return "_".join(part for part in "".join(
        character if character.isalnum() else " " for character in value
    ).split() if part)


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(rows[0]) if rows else ("scenario_id", "time_label")
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
