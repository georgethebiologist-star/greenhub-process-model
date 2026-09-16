"""BioSTEAM units for the isolated dynamic shadow pathway.

The target-output classes preserve the original compatibility proof. The
calculation classes own mass routing from typed policy payloads and are checked
against the already validated dynamic pathway after every build.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from math import isfinite

import biosteam as bst

from Greenhub.dynamic_process import (
    DynamicProteinScenarioRun,
    DynamicUnitResult,
    ProteinExtractionMethod,
)

FRACTION_TOLERANCE = 1e-9


@dataclass(frozen=True)
class RawPressCalculationPayload:
    policy_id: str
    component_output_fractions: dict[str, tuple[float, float, float]]
    recovered_mass_closure_fraction: float | None
    source_metadata: dict[str, object]
    evidence_classes: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "calculation_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]: return asdict(self)


@dataclass(frozen=True)
class FirstCentrifugeCalculationPayload:
    policy_id: str
    component_fraction_to_debris: dict[str, float]
    sediment_wet_mass_fraction: float | None
    sediment_dry_matter_fraction: float | None
    soluble_protein_retention_fraction: float | None
    source_metadata: dict[str, object]
    evidence_classes: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "calculation_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]: return asdict(self)


@dataclass(frozen=True)
class ProteinExtractionCalculationPayload:
    policy_id: str
    method: str
    component_fraction_to_protein_phase: dict[str, float]
    soluble_protein_recovery_fraction: float | None
    allow_n_to_protein_proxy: bool
    source_metadata: dict[str, object]
    evidence_classes: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    calculation_ready: bool
    activation_status: str = "calculation_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]: return asdict(self)


@dataclass(frozen=True)
class SecondCentrifugeCalculationPayload:
    policy_id: str
    component_fraction_to_wet_cake: dict[str, float]
    protein_phase_capture_fraction: float | None
    target_wet_cake_moisture_fraction: float | None
    combined_recovery_lower_bound: float | None
    source_metadata: dict[str, object]
    evidence_classes: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "calculation_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]: return asdict(self)


@dataclass(frozen=True)
class ProteinDryingCalculationPayload:
    policy_id: str
    target_moisture_fraction: float | None
    drying_energy_kwh_per_kg_water: float | None
    source_metadata: dict[str, object]
    evidence_classes: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "calculation_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]: return asdict(self)


@dataclass(frozen=True)
class ResidualMixerCalculationPayload:
    policy_id: str
    include_press_cake: bool
    source_metadata: dict[str, object]
    evidence_classes: tuple[str, ...]
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_status: str = "calculation_shadow_system_report_only"

    def to_dict(self) -> dict[str, object]: return asdict(self)


@dataclass(frozen=True)
class DynamicProteinCalculationPayloads:
    raw_press: RawPressCalculationPayload
    first_centrifuge: FirstCentrifugeCalculationPayload
    protein_extraction: ProteinExtractionCalculationPayload
    second_centrifuge: SecondCentrifugeCalculationPayload
    protein_dryer: ProteinDryingCalculationPayload
    residual_mixer: ResidualMixerCalculationPayload

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_press": self.raw_press.to_dict(),
            "first_centrifuge": self.first_centrifuge.to_dict(),
            "protein_extraction": self.protein_extraction.to_dict(),
            "second_centrifuge": self.second_centrifuge.to_dict(),
            "protein_dryer": self.protein_dryer.to_dict(),
            "residual_mixer": self.residual_mixer.to_dict(),
        }


def build_dynamic_protein_calculation_payloads(
    run: DynamicProteinScenarioRun,
) -> DynamicProteinCalculationPayloads:
    """Extract calculation inputs from the already resolved pathway run."""

    preview = run.pathway_preview
    if preview is None:
        raise ValueError("Dynamic scenario run has no pathway preview.")
    return DynamicProteinCalculationPayloads(
        raw_press=build_raw_press_calculation_payload(preview.raw_press),
        first_centrifuge=build_first_centrifuge_calculation_payload(
            preview.first_centrifugation
        ),
        protein_extraction=build_protein_extraction_calculation_payload(
            preview.protein_extraction
        ),
        second_centrifuge=build_second_centrifuge_calculation_payload(
            preview.second_centrifugation
        ),
        protein_dryer=build_protein_drying_calculation_payload(preview.drying),
        residual_mixer=build_residual_mixer_calculation_payload(
            preview.biogas_mix_preparation
        ),
    )


def build_raw_press_calculation_payload(
    unit: DynamicUnitResult,
) -> RawPressCalculationPayload:
    fractions = _resolved_output_fractions(unit)
    if len(unit.outputs) != 3:
        raise ValueError("Raw press calculation payload requires three outputs.")
    trace = _payload_trace(unit)
    return RawPressCalculationPayload(
        policy_id=trace["policy_id"],
        component_output_fractions={
            name: (values[0], values[1], values[2])
            for name, values in fractions.items()
        },
        recovered_mass_closure_fraction=_optional_float(
            unit.applied_policy.get("recovered_mass_closure_fraction")
        ),
        source_metadata=_source_metadata(unit),
        evidence_classes=trace["evidence_classes"],
        warnings=unit.warnings,
        blockers=unit.blockers,
    )


def build_first_centrifuge_calculation_payload(
    unit: DynamicUnitResult,
) -> FirstCentrifugeCalculationPayload:
    fractions = _resolved_output_fractions(unit)
    if len(unit.outputs) != 2:
        raise ValueError("First centrifuge calculation payload requires two outputs.")
    trace = _payload_trace(unit)
    soluble_loss = _optional_float(
        unit.applied_policy.get("soluble_protein_loss_fraction")
    )
    return FirstCentrifugeCalculationPayload(
        policy_id=trace["policy_id"],
        component_fraction_to_debris={name: values[1] for name, values in fractions.items()},
        sediment_wet_mass_fraction=_optional_float(
            unit.applied_policy.get("debris_wet_mass_fraction_of_feed_juice")
        ),
        sediment_dry_matter_fraction=_optional_float(
            unit.applied_policy.get("debris_dry_matter_fraction")
        ),
        soluble_protein_retention_fraction=(
            1.0 - soluble_loss if soluble_loss is not None else None
        ),
        source_metadata=_source_metadata(unit),
        evidence_classes=trace["evidence_classes"],
        warnings=unit.warnings,
        blockers=unit.blockers,
    )


def build_protein_extraction_calculation_payload(
    unit: DynamicUnitResult,
) -> ProteinExtractionCalculationPayload:
    fractions = _resolved_output_fractions(unit)
    if len(unit.outputs) != 2:
        raise ValueError("Protein extraction calculation payload requires two outputs.")
    trace = _payload_trace(unit)
    method = str(unit.applied_policy.get("method") or ProteinExtractionMethod.GENERIC.value)
    recovery = _optional_float(
        unit.applied_policy.get("soluble_protein_recovery_fraction")
    )
    record_ids = set(trace["record_ids"])
    allow_n_proxy = "REC-001" in record_ids and recovery is not None
    calculation_anchor = {
        ProteinExtractionMethod.ISOELECTRIC.value: "REC-001",
        ProteinExtractionMethod.LACTIC_ACID.value: "PR-005",
        ProteinExtractionMethod.MEMBRANE.value: "REJ-001",
    }.get(method)
    ready = (
        recovery is not None
        and (
            (calculation_anchor is not None and calculation_anchor in record_ids)
            or (
                method == ProteinExtractionMethod.GENERIC.value
                and str(trace["policy_id"]).strip()
                and unit.applied_policy.get("status") == "proxy_enabled_report_only_closed"
                and unit.applied_policy.get("proxy_class")
                == "mixed_source_proxy_and_engineering_proxy_closure"
            )
        )
    )
    blockers = list(unit.blockers)
    if not ready:
        blockers.append(f"protein_method_not_calculation_ready:{method}")
    return ProteinExtractionCalculationPayload(
        policy_id=trace["policy_id"],
        method=method,
        component_fraction_to_protein_phase={
            name: values[0] for name, values in fractions.items()
        },
        soluble_protein_recovery_fraction=recovery,
        allow_n_to_protein_proxy=allow_n_proxy,
        source_metadata=_source_metadata(unit),
        evidence_classes=trace["evidence_classes"],
        warnings=unit.warnings,
        blockers=tuple(dict.fromkeys(blockers)),
        calculation_ready=ready,
    )


def build_second_centrifuge_calculation_payload(
    unit: DynamicUnitResult,
) -> SecondCentrifugeCalculationPayload:
    fractions = _resolved_output_fractions(unit)
    if len(unit.outputs) != 2:
        raise ValueError("Second centrifuge calculation payload requires two outputs.")
    trace = _payload_trace(unit)
    return SecondCentrifugeCalculationPayload(
        policy_id=trace["policy_id"],
        component_fraction_to_wet_cake={name: values[0] for name, values in fractions.items()},
        protein_phase_capture_fraction=_optional_float(
            unit.applied_policy.get("protein_phase_capture_fraction")
        ),
        target_wet_cake_moisture_fraction=_optional_float(
            unit.applied_policy.get("target_wet_cake_moisture_fraction")
        ),
        combined_recovery_lower_bound=_optional_float(
            unit.applied_policy.get("combined_recovery_lower_bound")
        ),
        source_metadata=_source_metadata(unit),
        evidence_classes=trace["evidence_classes"],
        warnings=unit.warnings,
        blockers=unit.blockers,
    )


def build_protein_drying_calculation_payload(
    unit: DynamicUnitResult,
) -> ProteinDryingCalculationPayload:
    trace = _payload_trace(unit)
    return ProteinDryingCalculationPayload(
        policy_id=trace["policy_id"],
        target_moisture_fraction=_optional_float(
            unit.applied_policy.get("target_moisture_fraction")
        ),
        drying_energy_kwh_per_kg_water=_optional_float(
            unit.applied_policy.get("drying_energy_kwh_per_kg_water")
        ),
        source_metadata=_source_metadata(unit),
        evidence_classes=trace["evidence_classes"],
        warnings=unit.warnings,
        blockers=unit.blockers,
    )


def build_residual_mixer_calculation_payload(
    unit: DynamicUnitResult,
) -> ResidualMixerCalculationPayload:
    trace = _payload_trace(unit)
    return ResidualMixerCalculationPayload(
        policy_id=trace["policy_id"],
        include_press_cake=bool(unit.applied_policy.get("include_press_cake", False)),
        source_metadata=_source_metadata(unit),
        evidence_classes=trace["evidence_classes"],
        warnings=unit.warnings,
        blockers=unit.blockers,
    )


class _DynamicTargetOutputUnit(bst.Unit):
    """Write reviewed exact-component targets without design or costing."""

    line = "Dynamic target-output shadow unit"

    def _init(
        self,
        target_output_component_masses: Sequence[Mapping[str, float]],
        *,
        target_output_stream_ids: Sequence[str] = (),
        policy_id: str = "",
        policy_status: str = "shadow_target_output_report_only",
        evidence_classes: Sequence[str] = (),
        warnings: Sequence[str] = (),
        blockers: Sequence[str] = (),
        provenance: Mapping[str, object] | None = None,
    ) -> None:
        targets = tuple(dict(values) for values in target_output_component_masses)
        if len(targets) != self._N_outs:
            raise ValueError(
                f"{type(self).__name__} requires {self._N_outs} target output mappings."
            )
        if target_output_stream_ids and len(target_output_stream_ids) != self._N_outs:
            raise ValueError("target_output_stream_ids must match the unit outlet count.")
        if any(value < 0.0 for target in targets for value in target.values()):
            raise ValueError("Shadow target component masses must be nonnegative.")
        self.target_output_component_masses = targets
        self.target_output_stream_ids = tuple(target_output_stream_ids)
        self.shadow_policy_id = policy_id
        self.shadow_policy_status = policy_status
        self.shadow_evidence_classes = tuple(evidence_classes)
        self.shadow_warnings = tuple(warnings)
        self.shadow_blockers = tuple(blockers)
        self.shadow_provenance = dict(provenance or {})
        self.shadow_mode = "target_output_report_only"

    def _run(self) -> None:
        chemical_ids = set(self.chemicals.IDs)
        for outlet, target in zip(self.outs, self.target_output_component_masses):
            unknown = sorted(set(target) - chemical_ids)
            if unknown:
                raise KeyError(
                    f"{self.ID} target contains unknown chemicals: {', '.join(unknown)}."
                )
            outlet.empty()
            for component, mass_kg_hr in target.items():
                if mass_kg_hr:
                    outlet.imass[component] = mass_kg_hr


class DynamicRawPressUnit(_DynamicTargetOutputUnit):
    """Shadow raw press with explicit cake, juice, and unrecovered outputs."""

    _N_ins = 1
    _N_outs = 3
    line = "Dynamic raw press shadow"


class DynamicFirstCentrifugeUnit(_DynamicTargetOutputUnit):
    """Shadow first centrifuge producing clarified juice and cell debris."""

    _N_ins = 1
    _N_outs = 2
    line = "Dynamic first centrifuge shadow"


class DynamicProteinExtractionUnit(_DynamicTargetOutputUnit):
    """Shadow selected protein extraction producing two target phases."""

    _N_ins = 1
    _N_outs = 2
    line = "Dynamic protein extraction shadow"


class DynamicSecondCentrifugeUnit(_DynamicTargetOutputUnit):
    """Shadow recovery centrifuge producing wet cake and final supernatant."""

    _N_ins = 2
    _N_outs = 2
    line = "Dynamic second centrifuge shadow"


class DynamicProteinDryerUnit(_DynamicTargetOutputUnit):
    """Shadow dryer producing dry product and explicit evaporated water."""

    _N_ins = 1
    _N_outs = 2
    line = "Dynamic protein dryer shadow"


class DynamicResidualMixerUnit(_DynamicTargetOutputUnit):
    """Shadow mixer combining only cell debris and final supernatant."""

    _N_ins = 2
    _N_outs = 1
    line = "Dynamic residual mixer shadow"


class _DynamicPartitionCalculationUnit(bst.Unit):
    """Calculate output masses from resolved per-component fractions."""

    line = "Dynamic partition calculation shadow"
    _link_streams = False

    def _init(self, payload: object) -> None:
        self.calculation_payload = payload
        self.shadow_policy_id = payload.policy_id
        self.shadow_policy_status = payload.activation_status
        self.shadow_evidence_classes = payload.evidence_classes
        self.shadow_warnings = payload.warnings
        self.shadow_blockers = payload.blockers
        self.shadow_provenance = dict(payload.source_metadata)
        self.shadow_mode = "calculation_shadow_system_report_only"

    def _combined_input_masses(self) -> dict[str, float]:
        return {
            component: sum(float(stream.imass[component]) for stream in self.ins)
            for component in self.chemicals.IDs
            if any(float(stream.imass[component]) for stream in self.ins)
        }

    def _apply_primary_fractions(self, fractions: Mapping[str, float]) -> None:
        combined = self._combined_input_masses()
        primary, secondary = self.outs
        primary.empty()
        secondary.empty()
        for component, feed_mass in combined.items():
            fraction = float(fractions.get(component, 0.0))
            _validate_fraction(fraction, f"{self.ID}:{component}")
            primary.imass[component] = feed_mass * fraction
            secondary.imass[component] = feed_mass * (1.0 - fraction)


class DynamicRawPressCalculationUnit(_DynamicPartitionCalculationUnit):
    _N_ins = 1
    _N_outs = 3
    _link_streams = False
    line = "Dynamic raw press calculation shadow"

    def _run(self) -> None:
        combined = self._combined_input_masses()
        for outlet in self.outs:
            outlet.empty()
        payload = self.calculation_payload
        for component, feed_mass in combined.items():
            fractions = payload.component_output_fractions.get(component)
            if fractions is None:
                raise KeyError(f"{self.ID} has no resolved raw-press fractions for {component}.")
            _validate_fraction_tuple(fractions, self.ID, component)
            for outlet, fraction in zip(self.outs, fractions):
                outlet.imass[component] = feed_mass * fraction


class DynamicFirstCentrifugeCalculationUnit(_DynamicPartitionCalculationUnit):
    _N_ins = 1
    _N_outs = 2
    _link_streams = False
    line = "Dynamic first centrifuge calculation shadow"

    def _run(self) -> None:
        self._apply_primary_fractions(
            {
                component: 1.0 - fraction
                for component, fraction in self.calculation_payload.component_fraction_to_debris.items()
            }
        )


class DynamicProteinExtractionCalculationUnit(_DynamicPartitionCalculationUnit):
    _N_ins = 1
    _N_outs = 2
    _link_streams = False
    line = "Dynamic protein extraction calculation shadow"

    def _run(self) -> None:
        payload = self.calculation_payload
        if not payload.calculation_ready:
            raise RuntimeError(
                f"Protein method '{payload.method}' is not calculation-shadow ready."
            )
        fractions = dict(payload.component_fraction_to_protein_phase)
        if payload.method == ProteinExtractionMethod.ISOELECTRIC.value and not payload.allow_n_to_protein_proxy:
            raise RuntimeError("Isoelectric N-to-protein proxy permission is required.")
        if payload.soluble_protein_recovery_fraction is None:
            raise RuntimeError("Selected protein method has no resolved recovery fraction.")
        fractions["SolubleProtein"] = float(payload.soluble_protein_recovery_fraction)
        self._apply_primary_fractions(fractions)


class DynamicSecondCentrifugeCalculationUnit(_DynamicPartitionCalculationUnit):
    _N_ins = 2
    _N_outs = 2
    _link_streams = False
    line = "Dynamic second centrifuge calculation shadow"

    def _run(self) -> None:
        payload = self.calculation_payload
        moisture = payload.target_wet_cake_moisture_fraction
        if moisture is None or not 0.0 <= moisture < 1.0:
            raise ValueError("Second centrifuge requires target wet-cake moisture in [0, 1).")
        fractions = dict(payload.component_fraction_to_wet_cake)
        fractions.pop("Water", None)
        combined = self._combined_input_masses()
        wet_cake, supernatant = self.outs
        wet_cake.empty()
        supernatant.empty()
        dry_cake_mass = 0.0
        for component, feed_mass in combined.items():
            if component == "Water":
                continue
            fraction = float(fractions.get(component, 0.0))
            _validate_fraction(fraction, f"{self.ID}:{component}")
            cake_mass = feed_mass * fraction
            wet_cake.imass[component] = cake_mass
            supernatant.imass[component] = feed_mass - cake_mass
            dry_cake_mass += cake_mass
        available_water = combined.get("Water", 0.0)
        target_water = (
            dry_cake_mass * moisture / (1.0 - moisture) if moisture else 0.0
        )
        if target_water > available_water + FRACTION_TOLERANCE:
            raise ValueError("Wet-cake moisture target requires more water than available.")
        wet_cake.imass["Water"] = target_water
        supernatant.imass["Water"] = max(available_water - target_water, 0.0)


class DynamicProteinDryerCalculationUnit(_DynamicPartitionCalculationUnit):
    _N_ins = 1
    _N_outs = 2
    _link_streams = False
    line = "Dynamic protein dryer calculation shadow"

    def _run(self) -> None:
        target = self.calculation_payload.target_moisture_fraction
        if target is None or not 0.0 <= target < 1.0:
            raise ValueError("Protein dryer requires target moisture in [0, 1).")
        combined = self._combined_input_masses()
        product, evaporated = self.outs
        product.empty()
        evaporated.empty()
        dry_mass = 0.0
        for component, mass in combined.items():
            if component == "Water":
                continue
            if mass:
                product.imass[component] = mass
                dry_mass += mass
        target_water = dry_mass * target / (1.0 - target) if target else 0.0
        available_water = combined.get("Water", 0.0)
        if target_water > available_water + FRACTION_TOLERANCE:
            raise ValueError("Dryer target moisture requires more water than available.")
        product.imass["Water"] = target_water
        evaporated.imass["Water"] = max(available_water - target_water, 0.0)


class DynamicResidualMixerCalculationUnit(_DynamicPartitionCalculationUnit):
    _N_ins = 2
    _N_outs = 1
    _link_streams = False
    line = "Dynamic residual mixer calculation shadow"

    def _run(self) -> None:
        if self.calculation_payload.include_press_cake:
            raise ValueError("Press cake cannot enter the in-project residual mixer.")
        combined = self._combined_input_masses()
        outlet = self.outs[0]
        outlet.empty()
        for component, mass in combined.items():
            outlet.imass[component] = mass


def _resolved_output_fractions(
    unit: DynamicUnitResult,
) -> dict[str, tuple[float, ...]]:
    inputs: dict[str, float] = {}
    for stream in unit.inputs:
        for component, mass in stream.component_masses_kg_per_kg_feed.items():
            inputs[component] = inputs.get(component, 0.0) + float(mass)
    fractions: dict[str, tuple[float, ...]] = {}
    for component, input_mass in inputs.items():
        if input_mass <= FRACTION_TOLERANCE:
            continue
        values = tuple(
            float(stream.component_masses_kg_per_kg_feed.get(component, 0.0))
            / input_mass
            for stream in unit.outputs
        )
        _validate_fraction_tuple(values, unit.unit_id, component)
        fractions[component] = values
    return fractions


def _validate_fraction_tuple(
    fractions: Sequence[float], unit_id: str, component: str
) -> None:
    for fraction in fractions:
        _validate_fraction(float(fraction), f"{unit_id}:{component}")
    if abs(sum(fractions) - 1.0) > FRACTION_TOLERANCE:
        raise ValueError(
            f"{unit_id} resolved fractions for {component} do not conserve mass."
        )


def _validate_fraction(value: float, name: str) -> None:
    if not isfinite(value) or value < -FRACTION_TOLERANCE or value > 1.0 + FRACTION_TOLERANCE:
        raise ValueError(f"{name} fraction must be within [0, 1].")


def _payload_trace(unit: DynamicUnitResult) -> dict[str, object]:
    policy = unit.applied_policy
    evidence = _collect_key_values(
        policy,
        {"evidence_class", "proxy_class", "field_evidence_class", "metadata_field_evidence_class"},
        include_mapping_values=True,
    )
    return {
        "policy_id": str(policy.get("policy_id") or ""),
        "evidence_classes": tuple(sorted(evidence)),
        "source_ids": tuple(sorted(_collect_key_values(policy, {"source_id"}))),
        "record_ids": tuple(
            sorted(_collect_key_values(policy, {"record_id", "parameter_id"}))
        ),
    }


def _source_metadata(unit: DynamicUnitResult) -> dict[str, object]:
    trace = _payload_trace(unit)
    return {
        "applied_policy": dict(unit.applied_policy),
        "source_ids": list(trace["source_ids"]),
        "record_ids": list(trace["record_ids"]),
        "unit_metrics": dict(unit.metrics),
        "fraction_origin": "resolved_conservative_dynamic_process_unit_outputs",
        "target_output_masses_stored": False,
    }


def _collect_key_values(
    value: object,
    keys: set[str],
    *,
    include_mapping_values: bool = False,
) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in keys:
                if isinstance(nested, Mapping) and include_mapping_values:
                    found.update(str(item) for item in nested.values() if item not in (None, ""))
                elif isinstance(nested, (list, tuple, set)):
                    found.update(str(item) for item in nested if item not in (None, ""))
                elif nested not in (None, "") and not isinstance(nested, Mapping):
                    found.add(str(nested))
            found.update(
                _collect_key_values(
                    nested, keys, include_mapping_values=include_mapping_values
                )
            )
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(
                _collect_key_values(
                    nested, keys, include_mapping_values=include_mapping_values
                )
            )
    return found


def _optional_float(value: object) -> float | None:
    return None if value is None or value == "" else float(value)
