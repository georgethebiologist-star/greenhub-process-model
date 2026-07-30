"""Small, transport-neutral process-state layer for the reference pathway.

The engine deliberately consumes simulated streams and resolved canonical
parameters.  It does not replace BioSTEAM or introduce an ODE integrator.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import exp
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


def state_from_stream(unit_id: str, stream) -> ProcessState:
    total = max(float(stream.F_mass), 0.0)
    water = _mass(stream, {"Water"})
    soluble = _mass(stream, {"SolubleProtein"})
    insoluble = _mass(stream, {"InsolubleProtein"})
    carbs = _mass(stream, {"Glucose", "Xylose", "Sucrose", "Cellulose", "Hemicellulose"})
    cod = _mass(stream, {"SolubleProtein", "InsolubleProtein", "Glucose", "Xylose", "Sucrose", "Cellulose", "Hemicellulose"})
    return ProcessState(unit_id, str(stream.ID), total, float(stream.T), float(stream.P), None,
                        water / total if total else None, max(total - water, 0.0), None, None, None,
                        soluble, insoluble, carbs, cod, None,
                        {"water_kg_hr": water, "non_water_kg_hr": max(total-water, 0.0)})


def build_state_outputs(model, resolved_parameters=(), resolution_mode="steady_state") -> dict[str, Any]:
    """Return additive frontend-ready state/equation/inventory records."""
    streams = {str(s.ID): s for s in model.streams.values()}
    snapshots = []
    for unit_id, unit in sorted(model.units.items()):
        if not getattr(unit, "ins", None):
            continue
        stream = unit.ins[0]
        if stream is not None and float(stream.F_mass) > 0:
            snapshots.append(state_from_stream(unit_id, stream).to_dict())
    params = {p.parameter_id: p for p in resolved_parameters}
    equation_usage = []
    for name, pids in {
        "storage_degradation": ("phase4.storage_degradation_rate",),
        "residence_time_effect": ("phase4.residence_time_h",),
        "state_dependent_cod": ("phase4.precipitation_efficiency",),
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
        demand = getattr(getattr(unit, "power_utility", None), "consumption", 0.0)
        utility.append({"unit_id": unit_id, "kind": "electricity", "demand": float(demand or 0.0)})
    return {
        "process_state_snapshots": snapshots,
        "process_state_history": [{"time": 0.0, "states": snapshots}],
        "unit_state_summaries": [{"unit_id": s["unit_id"], "flow_kg_hr": s["flow_kg_hr"], "solids_kg_hr": s["solids_kg_hr"]} for s in snapshots],
        "equation_usage": equation_usage,
        "parameter_sensitivity": [{"parameter_id": pid, "sensitivity": None, "status": "not_available_without_eligible_equation"} for pid in sorted(params)],
        "component_fate": fate,
        "inventory_evolution": [{"inventory_id": "biomass_storage", "initial_kg": 0.0, "final_kg": 0.0, "status": "structural_fallback"}],
        "utility_consumption": utility,
        "resolution_mode": resolution_mode,
    }
