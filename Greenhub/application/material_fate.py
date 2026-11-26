"""Annual grass-juice, product, and terminal residual-water inventories."""

from __future__ import annotations

from Greenhub.analytical import calculate_elemental_flows


PRODUCT_LABELS = {
    "dry_protein_product": "Protein",
    "biostimulant_product": "Biostimulant concentrate",
    "biomethane": "Biomethane",
    "phosphorus_product": "Phosphorus product",
    "ammonium_product": "Ammonium product",
    "potassium_concentrate": "Potassium concentrate",
    "nutrient_rich_solids": "Nutrient-rich solids",
}
WATER_ALIASES = {
    "residual_liquor", "treated_water", "phase7_wastewater",
    "phase6_wastewater", "technology_wastewater", "conditioning_wastewater",
}


def accumulate_material_fate(totals: dict, streams, hours: float) -> None:
    """Sum actual timestep stream components, keeping terminal outlets distinct."""
    for stream in streams:
        aliases = set(stream.aliases) | {stream.stream_id}
        if "raw_liquid_fraction" in aliases:
            key, label, kind = "grass_juice", "Grass juice", "input"
        elif stream.sink_unit is None and aliases & PRODUCT_LABELS.keys():
            key = next(name for name in PRODUCT_LABELS if name in aliases)
            label, kind = PRODUCT_LABELS[key], "product"
        elif stream.sink_unit is None and aliases & WATER_ALIASES:
            key, label, kind = stream.stream_id, stream.stream_id.replace("_", " ").title(), "residual_water"
        else:
            continue
        target = totals.setdefault(key, {"label": label, "kind": kind, "components_kg": {}})
        for component, value in stream.components.items():
            amount = float(value.value or 0.0) * hours
            if amount > 0.0:
                components = target["components_kg"]
                components[component] = components.get(component, 0.0) + amount


def finalize_material_fate(totals: dict, basis: str) -> dict:
    def record(key: str, item: dict) -> dict:
        components = {name: value for name, value in sorted(item["components_kg"].items()) if value > 0.0}
        return {
            "stream_id": key,
            "label": item["label"],
            "mass_kg": sum(components.values()),
            "components_kg": components,
            "elements_kg": calculate_elemental_flows(components),
        }

    juice = record("grass_juice", totals.get("grass_juice", {"label": "Grass juice", "components_kg": {}}))
    products = [record(key, totals[key]) for key in PRODUCT_LABELS if key in totals and totals[key]["components_kg"]]
    water_streams = [record(key, item) for key, item in totals.items() if item["kind"] == "residual_water" and item["components_kg"]]
    water_components: dict[str, float] = {}
    for item in water_streams:
        for component, amount in item["components_kg"].items():
            water_components[component] = water_components.get(component, 0.0) + amount
    residual_water = record("residual_water", {"label": "Residual water", "components_kg": water_components})
    residual_water["streams"] = water_streams
    return {"basis": basis, "grass_juice": juice, "products": products, "residual_water": residual_water}
