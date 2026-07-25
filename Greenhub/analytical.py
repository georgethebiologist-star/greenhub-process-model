"""Derived analytical indicators from component mass flows."""

from __future__ import annotations

from collections.abc import Mapping

from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA


def _sum_flows(component_flows: Mapping[str, float], component_ids) -> float:
    return sum(float(component_flows.get(ID, 0.0)) for ID in component_ids)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


def calculate_elemental_flows(component_flows: Mapping[str, float]) -> dict[str, float]:
    """Calculate tracked elemental mass flows in kg element/h."""

    fields = {
        "carbon": "carbon_mass_fraction",
        "hydrogen": "hydrogen_mass_fraction",
        "oxygen": "oxygen_mass_fraction",
        "nitrogen": "nitrogen_mass_fraction",
        "phosphorus": "phosphorus_mass_fraction",
        "sulfur": "sulfur_mass_fraction",
        "potassium": "potassium_mass_fraction",
        "sodium": "sodium_mass_fraction",
        "magnesium": "magnesium_mass_fraction",
        "calcium": "calcium_mass_fraction",
        "chloride": "chloride_mass_fraction",
    }
    return {
        element: sum(
            float(flow) * getattr(COMPONENT_METADATA[component_id], field)
            for component_id, flow in component_flows.items()
        )
        for element, field in fields.items()
    }


def calculate_analytical_indicators(
    component_flows: Mapping[str, float],
    *,
    volumetric_flow_m3_hr: float | None,
    alkalinity_mg_caco3_L: float | None = None,
) -> dict[str, float | None]:
    """Calculate Phase 2 indicators without creating aggregate stream mass."""

    wet_mass = sum(float(i) for i in component_flows.values())
    water = float(component_flows.get("Water", 0.0))
    dry_solids = wet_mass - water
    suspended = _sum_flows(component_flows, COMPONENT_GROUPS["suspended_solids"])
    dissolved = max(0.0, dry_solids - suspended)
    volatile = sum(
        float(flow) * COMPONENT_METADATA[ID].volatile_solids_fraction
        for ID, flow in component_flows.items()
    )
    fixed = max(0.0, dry_solids - volatile)
    total_cod = sum(
        float(flow) * (COMPONENT_METADATA[ID].cod_factor or 0.0)
        for ID, flow in component_flows.items()
    )
    soluble_cod = sum(
        float(component_flows.get(ID, 0.0)) * (COMPONENT_METADATA[ID].cod_factor or 0.0)
        for ID in COMPONENT_GROUPS["soluble_cod_components"]
    )
    particulate_cod = sum(
        float(component_flows.get(ID, 0.0)) * (COMPONENT_METADATA[ID].cod_factor or 0.0)
        for ID in COMPONENT_GROUPS["particulate_cod_components"]
    )
    elemental = calculate_elemental_flows(component_flows)
    organic_n = sum(
        float(component_flows.get(ID, 0.0)) * COMPONENT_METADATA[ID].nitrogen_mass_fraction
        for ID in COMPONENT_GROUPS["organic_nitrogen_components"]
    )
    inorganic_n = sum(
        float(component_flows.get(ID, 0.0)) * COMPONENT_METADATA[ID].nitrogen_mass_fraction
        for ID in COMPONENT_GROUPS["inorganic_nitrogen_components"]
    )
    tkn = organic_n + sum(
        float(component_flows.get(ID, 0.0)) * COMPONENT_METADATA[ID].nitrogen_mass_fraction
        for ID in {"Ammonia", "Ammonium"}
    )
    dissolved_p = sum(
        float(component_flows.get(ID, 0.0)) * COMPONENT_METADATA[ID].phosphorus_mass_fraction
        for ID in COMPONENT_GROUPS["dissolved_phosphorus"]
    )
    particulate_p = sum(
        float(component_flows.get(ID, 0.0)) * COMPONENT_METADATA[ID].phosphorus_mass_fraction
        for ID in COMPONENT_GROUPS["particulate_phosphorus"]
    )
    vfa = _sum_flows(component_flows, COMPONENT_GROUPS["vfas"])
    soluble_sugars = _sum_flows(component_flows, COMPONENT_GROUPS["soluble_sugars"])
    protein = _sum_flows(component_flows, COMPONENT_GROUPS["protein_equivalents"])

    indicators: dict[str, float | None] = {
        "total_wet_mass_kg_hr": wet_mass,
        "water_mass_kg_hr": water,
        "dry_solids_kg_hr": dry_solids,
        "tss_kg_hr": suspended,
        "tds_kg_hr": dissolved,
        "volatile_solids_kg_hr": volatile,
        "fixed_solids_kg_hr": fixed,
        "cod_kg_hr": total_cod,
        "soluble_cod_kg_hr": soluble_cod,
        "particulate_cod_kg_hr": particulate_cod,
        "toc_kg_hr": elemental["carbon"],
        "total_nitrogen_kg_hr": elemental["nitrogen"],
        "organic_nitrogen_kg_hr": organic_n,
        "inorganic_nitrogen_kg_hr": inorganic_n,
        "tkn_kg_hr": tkn,
        "total_phosphorus_kg_hr": elemental["phosphorus"],
        "dissolved_phosphorus_kg_hr": dissolved_p,
        "particulate_phosphorus_kg_hr": particulate_p,
        "potassium_kg_hr": elemental["potassium"],
        "soluble_sugars_kg_hr": soluble_sugars,
        "total_protein_kg_hr": protein,
        "vfa_kg_hr": vfa,
        "c_to_n_ratio": _safe_ratio(elemental["carbon"], elemental["nitrogen"]),
        "cod_to_n_ratio": _safe_ratio(total_cod, elemental["nitrogen"]),
        "cod_to_p_ratio": _safe_ratio(total_cod, elemental["phosphorus"]),
        "alkalinity_mg_caco3_L": alkalinity_mg_caco3_L,
    }
    indicators.update({f"{name}_kg_hr": value for name, value in elemental.items()})

    if volumetric_flow_m3_hr and volumetric_flow_m3_hr > 0.0:
        volume = volumetric_flow_m3_hr
        indicators.update(
            {
                "ts_g_L": dry_solids / volume,
                "tss_mg_L": suspended / volume * 1000.0,
                "tds_mg_L": dissolved / volume * 1000.0,
                "vs_g_L": volatile / volume,
                "fixed_solids_g_L": fixed / volume,
                "cod_mg_L": total_cod / volume * 1000.0,
                "soluble_cod_mg_L": soluble_cod / volume * 1000.0,
                "particulate_cod_mg_L": particulate_cod / volume * 1000.0,
                "toc_mg_L": elemental["carbon"] / volume * 1000.0,
                "total_nitrogen_mg_L": elemental["nitrogen"] / volume * 1000.0,
                "tkn_mg_L": tkn / volume * 1000.0,
                "total_phosphorus_mg_L": elemental["phosphorus"] / volume * 1000.0,
                "soluble_sugars_g_L": soluble_sugars / volume,
                "total_protein_g_L": protein / volume,
                "vfa_g_L": vfa / volume,
                "vfa_to_alkalinity_ratio": (
                    vfa / volume * 1000.0 / alkalinity_mg_caco3_L
                    if alkalinity_mg_caco3_L and alkalinity_mg_caco3_L > 0.0
                    else None
                ),
            }
        )
    return indicators
