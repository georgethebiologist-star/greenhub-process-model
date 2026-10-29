"""Small, transport-neutral process-state layer for the reference pathway.

The engine deliberately consumes simulated streams and resolved canonical
parameters.  It does not replace BioSTEAM or introduce an ODE integrator.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import exp, isfinite
from typing import Any


@dataclass(frozen=True)
class ProcessState:
    unit_id: str
    stream_id: str
    flow_kg_hr: float
    temperature_k: float | None
    pressure_pa: float | None
    pH: float | None
    moisture_fraction: float | None
    solids_kg_hr: float | None
    density_kg_m3: float | None
    viscosity_pa_s: float | None
    particle_size_um: float | None
    soluble_protein_kg_hr: float
    insoluble_protein_kg_hr: float
    carbohydrates_kg_hr: float
    cod_kg_hr: float
    storage_age_h: float | None
    analytical_properties: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mass(stream, ids: set[str]) -> float:
    return sum(float(stream.imass[name]) for name in ids if name in stream.chemicals.IDs)


def state_from_stream(unit_id: str, stream, *, storage_age_h: float | None = None) -> ProcessState:
    total = max(float(stream.F_mass), 0.0)
    water = _mass(stream, {"Water"})
    soluble = _mass(stream, {"SolubleProtein"})
    insoluble = _mass(stream, {"InsolubleProtein"})
    carbs = _mass(stream, {
        "Glucose", "Xylose", "Sucrose", "Cellulose", "Hemicellulose",
        "OtherBiodegradableOrganics",
    })
    cod = _mass(stream, {
        "SolubleProtein", "InsolubleProtein", "Glucose", "Xylose", "Sucrose",
        "Cellulose", "Hemicellulose", "OtherBiodegradableOrganics", "Lipids",
    })
    density = _stream_property(stream, "rho")
    viscosity = _stream_property(stream, "mu")
    pH = _metadata_number(stream, ("pH", "ph", "pH_value"))
    particle_size = _metadata_number(stream, ("particle_size_um", "d50_um", "median_particle_size_um"))
    analytical = {"water_kg_hr": water, "non_water_kg_hr": max(total-water, 0.0)}
    metadata = getattr(stream, "metadata", None)
    if isinstance(metadata, dict):
        analytical.update({str(key): float(value) for key, value in metadata.items()
                           if isinstance(value, (int, float)) and isfinite(float(value))})
    return ProcessState(unit_id, str(stream.ID), total, float(stream.T), float(stream.P), pH,
                        water / total if total else None, max(total - water, 0.0), density, viscosity, particle_size,
                        soluble, insoluble, carbs, cod, storage_age_h,
                        analytical)


def _metadata_number(stream, names: tuple[str, ...]) -> float | None:
    metadata = getattr(stream, "metadata", None)
    if not isinstance(metadata, dict):
        return None
    for name in names:
        value = metadata.get(name)
        if isinstance(value, (int, float)) and isfinite(float(value)):
            return float(value)
    return None


def _stream_property(stream, name: str) -> float | None:
    """Read an optional stream property without turning unavailable data into zero."""

    try:
        value = getattr(stream, name)
    except Exception:
        return None
    try:
        value = float(value)
    except Exception:
        return None
    return value if isfinite(value) and value > 0.0 else None


def _nonnegative_stream_property(stream, name: str) -> float | None:
    try:
        value = float(getattr(stream, name))
    except Exception:
        return None
    return value if isfinite(value) and value >= 0.0 else None


def build_state_outputs(model, resolved_parameters=(), resolution_mode="steady_state") -> dict[str, Any]:
    """Return additive frontend-ready state/equation/inventory records."""
    streams = {str(s.ID): s for s in model.streams.values()}
    snapshots = []
    for unit_id, unit in sorted(model.units.items()):
        if not getattr(unit, "ins", None):
            continue
        stream = unit.ins[0]
        if stream is not None and float(stream.F_mass) > 0:
            inlet = state_from_stream(
                unit_id,
                stream,
                storage_age_h=_nonnegative_stream_property(unit, "storage_age_h"),
            ).to_dict()
            outputs = tuple(getattr(unit, "outs", ()) or ())
            outlet = next((item for item in outputs if item is not None and float(item.F_mass) > 0), None)
            if outlet is not None:
                outlet_state = state_from_stream(
                    unit_id,
                    outlet,
                    storage_age_h=_nonnegative_stream_property(unit, "storage_age_h"),
                ).to_dict()
                inlet["outlet_state"] = outlet_state
                inlet["changed_properties"] = _changed_state_properties(inlet, outlet_state)
            else:
                inlet["outlet_state"] = None
                inlet["changed_properties"] = []
            snapshots.append(inlet)
    params = {p.parameter_id: p for p in resolved_parameters}
    equation_usage = []
    for name, pids in {
        "pretreatment_water_addition": ("phase3.pretreatment.water_addition_kg_per_kg_wet_feed",),
        "pretreatment_press_energy": ("phase3.pretreatment.press_energy_kwh_per_t_wet_feed",),
        "storage_degradation": ("seasonal.storage_degradation_rate_per_day",),
        "residence_time_effect": ("phase4.precipitation_residence_time_min",),
        "protein_precipitation_recovery": ("phase4.precipitation_efficiency",),
    }.items():
        available = [pid for pid in pids if pid in params and params[pid].active_value is not None and not params[pid].blocked]
        equation_usage.append({"equation_id": name, "parameter_ids": list(pids), "used": bool(available),
                               "fallback": not bool(available), "status": "calculated" if available else "structural_fallback"})
    fate = []
    for snapshot in snapshots:
        fate.append({"unit_id": snapshot["unit_id"], "stream_id": snapshot["stream_id"],
                     "cod_kg_hr": snapshot["cod_kg_hr"], "soluble_protein_kg_hr": snapshot["soluble_protein_kg_hr"]})
    utility = []
    for unit_id, unit in sorted(model.units.items()):
        power = getattr(unit, "power_utility", None)
        demand = getattr(power, "consumption", None) if power is not None else None
        if demand is None:
            utility.append({"unit_id": unit_id, "kind": "electricity", "demand": None,
                            "status": "unavailable", "warning": "Unit power demand was not provided; no zero was inferred."})
        else:
            value = float(demand)
            utility.append({"unit_id": unit_id, "kind": "electricity", "demand": value,
                            "status": "calculated", "warning": None})
    return {
        "process_state_snapshots": snapshots,
        "process_state_history": [{"time": 0.0, "states": snapshots}],
        "unit_state_summaries": [{"unit_id": s["unit_id"], "flow_kg_hr": s["flow_kg_hr"], "solids_kg_hr": s["solids_kg_hr"],
                                  "outlet_flow_kg_hr": (s["outlet_state"] or {}).get("flow_kg_hr"),
                                  "changed_properties": s.get("changed_properties", [])} for s in snapshots],
        "equation_usage": equation_usage,
        "parameter_sensitivity": [{"parameter_id": pid, "sensitivity": None, "status": "not_available_without_eligible_equation"} for pid in sorted(params)],
        "component_fate": fate,
        "inventory_evolution": [{"inventory_id": "biomass_storage", "initial_kg": 0.0, "final_kg": 0.0, "status": "structural_fallback"}],
        "utility_consumption": utility,
        "resolution_mode": resolution_mode,
    }


def _changed_state_properties(inlet: dict[str, Any], outlet: dict[str, Any], tolerance: float = 1e-9) -> list[str]:
    """Identify state fields changed by a unit without treating unavailable data as zero."""

    fields = (
        "flow_kg_hr", "temperature_k", "pressure_pa", "pH", "moisture_fraction",
        "solids_kg_hr", "density_kg_m3", "viscosity_pa_s", "particle_size_um",
        "soluble_protein_kg_hr", "insoluble_protein_kg_hr", "carbohydrates_kg_hr", "cod_kg_hr",
    )
    changed: list[str] = []
    for field in fields:
        left, right = inlet.get(field), outlet.get(field)
        if left is None or right is None:
            if left != right:
                changed.append(field)
        elif abs(float(left) - float(right)) > tolerance * max(1.0, abs(float(left)), abs(float(right))):
            changed.append(field)
    return changed
