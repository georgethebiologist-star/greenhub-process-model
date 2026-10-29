"""
Greenhub.storage

Lightweight storage and degradation framework.
- Provides a StorageModel that tracks inventory (kg), capacity, and optional degradation.
- If degradation parameters are missing, the model records a clear provenance/limitation
  and does not silently convert missing data into zeros: inventory remains unchanged
  except for explicit inflow/outflow.

This module is intentionally small and additive so it can be integrated safely as a
compatibility-friendly process-area helper. It does not change any existing factories
or integration surfaces; integration into seasonal controllers is additive and must be
opted-in by higher-level code.

Provenance: each simulation step returns a `provenance` dict listing applied methods
and any limitations or sources. No external data is assumed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import exp, isfinite
from typing import Optional, Dict, Any, Mapping


@dataclass
class StorageModel:
    """Simple storage inventory with optional first-order degradation.

    Parameters
    - capacity_kg: optional storage capacity. If None, storage is unbounded.
    - initial_inventory_kg: starting mass in kg.
    - degradation_rate_per_day: optional first-order degradation constant (1/day).
      If None, degradation is explicitly considered not implemented for provenance.
    """

    capacity_kg: Optional[float] = None
    initial_inventory_kg: float = 0.0
    degradation_rate_per_day: Optional[float] = None

    # runtime state
    inventory_kg: float = field(init=False)

    def __post_init__(self) -> None:
        for name, value in (("capacity_kg", self.capacity_kg), ("initial_inventory_kg", self.initial_inventory_kg), ("degradation_rate_per_day", self.degradation_rate_per_day)):
            if value is not None:
                _nonnegative_finite(name, value)
        self.inventory_kg = float(self.initial_inventory_kg)

    def simulate_step(self, inflow_kg: float = 0.0, outflow_kg: float = 0.0, days: float = 1.0) -> Dict[str, Any]:
        """Advance storage by one step.

        Returns a dict with keys:
        - inventory_kg: new inventory after accounting inflow/outflow and degradation (if applied)
        - applied_degradation_kg: mass lost to degradation (0.0 if not implemented or zero)
        - overflow_kg: mass that could not be stored because capacity was exceeded
        - provenance: dict documenting applied methods, limitations, and sources
        """
        # Validate before mutation, so a rejected call leaves the state intact.
        for name, value in (("inflow_kg", inflow_kg), ("outflow_kg", outflow_kg), ("days", days)):
            _nonnegative_finite(name, value)
        provenance: Dict[str, Any] = {
            "methods": [],
            "limitations": [],
            "sources": [],
        }

        initial = self.inventory_kg
        # apply inflow
        self.inventory_kg += float(inflow_kg)
        provenance["methods"].append({"inflow_kg": float(inflow_kg)})

        # apply outflow (withdrawal before degradation to match perfectly-mixed withdraw assumption)
        withdrawal = float(outflow_kg)
        if withdrawal < 0:
            raise ValueError("outflow_kg must be non-negative")
        withdrawn = min(withdrawal, self.inventory_kg)
        self.inventory_kg -= withdrawn
        provenance["methods"].append({"outflow_kg": withdrawn})

        # apply degradation if parameter is provided
        applied_degradation_kg = 0.0
        if self.degradation_rate_per_day is None:
            # Explicitly mark degradation as not implemented / missing-data
            provenance["limitations"].append("degradation_not_implemented")
            provenance["methods"].append({"degradation": "not_implemented"})
            applied_degradation_kg = 0.0
        else:
            # first-order loss: mass_after = mass_before * exp(-k * days)
            k = float(self.degradation_rate_per_day)
            if k < 0:
                raise ValueError("degradation_rate_per_day must be non-negative")
            mass_before = self.inventory_kg
            mass_after = mass_before * exp(-k * float(days))
            applied_degradation_kg = mass_before - mass_after
            self.inventory_kg = mass_after
            provenance["methods"].append({"degradation": {"k_1_per_day": k, "days": float(days)}})
            provenance["sources"].append("user_provided_degradation_rate")

        # apply capacity limit and compute overflow
        overflow_kg = 0.0
        if self.capacity_kg is not None:
            if self.inventory_kg > float(self.capacity_kg):
                overflow_kg = self.inventory_kg - float(self.capacity_kg)
                self.inventory_kg = float(self.capacity_kg)
                provenance["limitations"].append("capacity_overflow")

        provenance_summary = {
            "applied_degradation_kg": applied_degradation_kg,
            "overflow_kg": overflow_kg,
            "inventory_kg": self.inventory_kg,
        }

        return {"inventory_kg": self.inventory_kg, "applied_degradation_kg": applied_degradation_kg, "overflow_kg": overflow_kg, "withdrawn_kg": withdrawn, "mass_balance_residual_kg": initial + float(inflow_kg) - withdrawn - applied_degradation_kg - overflow_kg - self.inventory_kg, "provenance": provenance, "summary": provenance_summary}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capacity_kg": self.capacity_kg,
            "inventory_kg": self.inventory_kg,
            "degradation_rate_per_day": self.degradation_rate_per_day,
        }


def _nonnegative_finite(name: str, value: object) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite non-negative number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite non-negative number.") from exc
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be a finite non-negative number.")
    return number


@dataclass(frozen=True)
class StorageConditions:
    """Explicit batch residence and component retention kinetics, with no default rates.

    ``aerobic_fraction`` is the fraction of residence *time* exposed to air.
    Each rate is a first-order disappearance coefficient for one named component;
    it is not a methane, carbon dioxide, or leaching emission factor. The missing
    fate of disappeared material remains outside the retained process feed.
    """

    storage_days: float = 0.0
    aerobic_fraction: float = 0.0
    component_rates: dict[str, dict[str, dict[str, object]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _nonnegative_finite("storage_days", self.storage_days)
        fraction = _nonnegative_finite("aerobic_fraction", self.aerobic_fraction)
        if fraction > 1.0:
            raise ValueError("aerobic_fraction must be within [0, 1].")
        if not isinstance(self.component_rates, dict):
            raise ValueError("component_rates must map component names to aerobic/anaerobic rate records.")
        for component, regimes in self.component_rates.items():
            if not isinstance(component, str) or not component or not isinstance(regimes, dict):
                raise ValueError("Each component_rates entry needs a component name and rate mapping.")
            if set(regimes) - {"aerobic", "anaerobic"}:
                raise ValueError(f"Unknown storage regime for {component}; use aerobic or anaerobic.")
            for regime, record in regimes.items():
                if not isinstance(record, dict):
                    raise ValueError(f"Storage rate {component}/{regime} requires a parameter record.")
                if record.get("value") is not None:
                    _nonnegative_finite(f"{component}/{regime}/value", record["value"])
                if record.get("unit", "1/day") != "1/day":
                    raise ValueError("Storage kinetic rates must use unit '1/day'; convert explicitly before activation.")
                if record.get("basis", "component_mass") != "component_mass":
                    raise ValueError("Storage rates require basis 'component_mass'; whole-feed/VS rates cannot silently become component rates.")

    @classmethod
    def from_dict(cls, value: Mapping[str, object] | None) -> "StorageConditions":
        payload = dict(value or {})
        unknown = set(payload) - {"storage_days", "aerobic_fraction", "component_rates"}
        if unknown:
            raise ValueError(f"Unknown storage condition fields: {', '.join(sorted(unknown))}.")
        return cls(**payload)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def simulate_storage_batch(
    component_masses_kg: Mapping[str, float],
    conditions: StorageConditions | Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Integrate component retention exactly and retain uncharacterized losses.

    For each component, M(t)=M(0) exp[-t(f*k_air+(1-f)*k_anoxic)].
    The weighted exposure is an explicit phenomenological assumption; neither
    oxygen limitation nor microbial/intermediate kinetics is claimed. Missing
    active rates block the affected component's prediction, not other components.
    """
    if not isinstance(conditions, StorageConditions):
        conditions = StorageConditions.from_dict(conditions)
    masses = {name: _nonnegative_finite(f"component_masses_kg/{name}", mass) for name, mass in component_masses_kg.items()}
    retained = dict(masses)
    exported = {name: 0.0 for name in masses}
    blockers: list[str] = []
    assumptions: list[dict[str, object]] = []
    unmodeled = []
    time = float(conditions.storage_days)
    fraction = float(conditions.aerobic_fraction)
    for component, mass in masses.items():
        if time == 0.0 or mass == 0.0:
            continue
        rate = 0.0
        missing = False
        for regime, exposure in (("aerobic", fraction), ("anaerobic", 1.0 - fraction)):
            if exposure == 0.0:
                continue
            record = conditions.component_rates.get(component, {}).get(regime, {})
            value = record.get("value")
            if value is None or record.get("source_status") in {"missing", "blocked"}:
                blockers.append(f"Missing eligible {regime} component-mass retention rate for {component}.")
                missing = True
                continue
            source_status = str(record.get("source_status", "engineering_assumption"))
            if source_status in {"measured", "direct_literature", "indirect_proxy"} and not (record.get("source_url") or record.get("source_doi") or record.get("source_id")):
                blockers.append(f"Storage rate {component}/{regime} claims {source_status} without an identifiable source.")
                missing = True
                continue
            rate += exposure * float(value)
            assumptions.append({
                "policy_id": f"storage.{component}.{regime}.retention_rate",
                "value": float(value), "unit": "1/day", "basis": "component_mass",
                "source_status": source_status, "evidence_class": record.get("evidence_class", source_status),
                "source_id": record.get("source_id"), "source_url": record.get("source_url"),
                "source_doi": record.get("source_doi"), "source_table_page": record.get("source_table_page"),
                "retrieval_date": record.get("retrieval_date"), "geography": record.get("geography"),
                "reference_year": record.get("reference_year"), "applicability": record.get("applicability", "User-selected component retention scenario; calibration not demonstrated."),
                "conversion_scaling_method": record.get("conversion_scaling_method", "Exact first-order integration with residence-time weighted exposure."),
                "uncertainty": record.get("uncertainty"),
                "warning": record.get("warning", "No validated GreenHub storage kinetics or loss-species fate is implied."),
            })
        if missing:
            unmodeled.append(component)
            continue
        retained[component] = mass * exp(-rate * time)
        exported[component] = mass - retained[component]
    total_initial, total_retained, total_exported = sum(masses.values()), sum(retained.values()), sum(exported.values())
    fate_missing = total_exported > 0.0
    return {
        "storage_conditions": conditions.to_dict(),
        "model": "component_first_order_retention", "aerobic_fraction_interpretation": "fraction_of_residence_time_exposed_to_air",
        "input_component_masses_kg": masses, "retained_component_masses_kg": retained,
        "exported_component_masses_kg": exported, "unmodeled_components": unmodeled,
        "total_input_kg": total_initial, "total_retained_kg": total_retained, "total_exported_kg": total_exported,
        "mass_balance_residual_kg": total_initial - total_retained - total_exported,
        "emissions_kg": None if fate_missing or blockers else {},
        "intermediate_products_kg": None if fate_missing or blockers else {},
        "leaching_kg": None if fate_missing or blockers else {},
        "fate_status": "uncharacterized_exported_material" if fate_missing else ("unknown_missing_kinetics" if blockers else "no_exported_material"),
        "calculation_complete": not blockers, "emissions_inventory_complete": not blockers and not fate_missing,
        "validated_simulation_ready": False, "assumptions": assumptions, "blockers": blockers,
        "warnings": (["Disappeared component mass is an uncharacterized export. It is not CO2, methane, leachate or a retained intermediate; species/element fate needs evidence."] if fate_missing else []) + (["Components with missing rates remain unchanged conditionally; unchanged mass is not a prediction of zero degradation."] if blockers else []),
    }


def apply_storage_conditions(masses, config, available_components=None):
    """Shared opt-in entry point for static residence and seasonal inventory."""
    config = dict(config or {})
    model = config.pop("model", "component_retention")
    if model == "grass_reactions":
        from .storage_reactions import simulate_reactions
        allowed = {"storage_days", "aerobic_fraction", "allow_assumptions", "reaction_ids", "moisture_activity", "temperature_c", "max_step_days", "elapsed_days"}
        if set(config)-allowed:
            raise ValueError("Unknown grass reaction storage fields: " + ", ".join(sorted(set(config)-allowed)))
        report=simulate_reactions(masses, config, available_components)
        if available_components is not None and float(config.get('storage_days',0))>0:
            from Greenhub.analytical import calculate_elemental_flows
            inputs=dict(masses)
            inputs['Oxygen']=inputs.get('Oxygen',0)+report['external_oxygen_kg']
            outputs=dict(report['retained_component_masses_kg'])
            for key,value in report['exported_component_masses_kg'].items(): outputs[key]=outputs.get(key,0)+value
            entering=calculate_elemental_flows(inputs); leaving=calculate_elemental_flows(outputs)
            report['core_element_residual_kg']={key:entering[key]-leaving[key] for key in entering}
            if any(abs(value)>max(1e-6,sum(masses.values())*1e-8) for value in report['core_element_residual_kg'].values()):
                report['blockers'].append('Package molecular-formula basis differs from legacy lumped component elemental fractions. Storage-to-core element reconciliation is incomplete; no overall elemental validation is claimed.')
                report['calculation_complete']=False
        return report
    if model != "component_retention":
        raise ValueError("Storage model must be component_retention or grass_reactions.")
    return simulate_storage_batch(masses, config)
