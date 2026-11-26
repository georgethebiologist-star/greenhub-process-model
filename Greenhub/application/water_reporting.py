"""Shared fresh-process-water activity accounting for reports and post-route tools."""

from __future__ import annotations


WATER_DENSITY_KG_PER_M3 = 1000.0


def fresh_water_kg_per_hour_from_model(model) -> float:
    """Sum water component mass in upstream and downstream external inputs."""
    phase7 = getattr(model, "legacy_model", model)
    phase6 = getattr(phase7, "upstream_model", None)
    external = [*(getattr(phase6, "external_inputs", ()) or ()), *(getattr(phase7, "external_inputs", ()) or ())]
    unique = {str(stream.ID): stream for stream in external}
    return sum(float(stream.imass["Water"]) for stream in unique.values() if "Water" in stream.chemicals.IDs)


def fresh_water_kg_per_hour_from_result(streams) -> float:
    """Recover fresh-water input mass from serialized external feed streams."""
    total = 0.0
    for stream in streams:
        if (getattr(stream, "source_unit", None) is not None
                or getattr(stream, "stream_id", None) == "feed"
                or "feed" in getattr(stream, "aliases", ())):
            continue
        water = getattr(stream, "components", {}).get("Water")
        if water is not None and water.value is not None:
            total += float(water.value)
    return total


def kg_to_m3(water_kg: float) -> float:
    """Convert water mass to volume using the explicit 1000 kg/m3 reference density."""
    return float(water_kg) / WATER_DENSITY_KG_PER_M3
