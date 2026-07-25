"""Reusable schemas for active and future GreenHub process streams."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from Greenhub.component_groups import COMPONENT_GROUPS


@dataclass(frozen=True)
class StreamTemplate:
    stream_id: str
    display_name: str
    expected_phase: str
    expected_component_groups: tuple[str, ...]
    physical_metadata: tuple[str, ...]
    canonical_reporting_units: tuple[str, ...]
    required_measurements: tuple[str, ...]
    optional_measurements: tuple[str, ...]
    active_in_phase_2: bool = False
    active_in_phase_3: bool = False

    def validate(self) -> None:
        unknown = set(self.expected_component_groups) - set(COMPONENT_GROUPS)
        if unknown:
            raise KeyError(f"Stream template '{self.stream_id}' uses unknown groups: {sorted(unknown)}")


LIQUID_METADATA = ("temperature", "pressure", "pH", "density", "conductivity", "viscosity")
SOLIDS_METADATA = ("temperature", "pressure", "moisture", "total_solids", "volatile_solids")


def _liquid(
    stream_id: str,
    display_name: str,
    groups: tuple[str, ...],
    active_phase_2: bool = False,
    active_phase_3: bool = False,
) -> StreamTemplate:
    return StreamTemplate(
        stream_id,
        display_name,
        "l",
        groups,
        LIQUID_METADATA,
        ("kg/hr", "m3/hr", "mg/L"),
        ("total_wet_flow",),
        ("COD", "TOC", "TN", "TP", "TS", "TSS", "TDS"),
        active_phase_2,
        active_phase_3,
    )


def _solid(
    stream_id: str,
    display_name: str,
    groups: tuple[str, ...],
    active_phase_3: bool = False,
) -> StreamTemplate:
    return StreamTemplate(
        stream_id,
        display_name,
        "s",
        groups,
        SOLIDS_METADATA,
        ("kg/hr", "kg TS/hr", "wt.%"),
        ("wet_mass", "moisture"),
        ("protein", "N", "P", "K", "ash"),
        False,
        active_phase_3,
    )


STREAM_TEMPLATES = {
    "incoming_grass": _solid("incoming_grass", "Incoming roadside grass", ("structural_carbohydrates", "protein_equivalents", "dissolved_minerals", "contaminants"), True),
    "pef_treated_grass": _solid("pef_treated_grass", "PEF-treated grass", ("structural_carbohydrates", "protein_equivalents", "soluble_sugars", "dissolved_minerals"), True),
    "pressed_fibre_cake": _solid("pressed_fibre_cake", "Pressed fibre cake", ("structural_carbohydrates", "suspended_solids", "particulate_phosphorus", "contaminants"), True),
    "raw_liquid_fraction": _liquid("raw_liquid_fraction", "Raw liquid fraction", ("soluble_cod_components", "particulate_cod_components", "inorganic_nitrogen_components", "phosphorus_components", "dissolved_minerals", "contaminants"), True, True),
    "primary_sludge": _solid("primary_sludge", "Primary sludge", ("suspended_solids", "particulate_cod_components", "particulate_phosphorus", "contaminants"), True),
    "clarified_protein_liquid": _liquid("clarified_protein_liquid", "Clarified protein-rich liquid", ("soluble_cod_components", "protein_equivalents", "inorganic_nitrogen_components", "dissolved_phosphorus", "dissolved_minerals"), True, True),
    "protein_precipitation_slurry": _liquid("protein_precipitation_slurry", "Protein precipitation slurry", ("protein_equivalents", "soluble_cod_components", "dissolved_minerals")),
    "wet_protein_cake": _solid("wet_protein_cake", "Wet protein cake", ("protein_equivalents", "suspended_solids")),
    "dry_protein_product": _solid("dry_protein_product", "Dry protein product", ("protein_equivalents", "fixed_solids")),
    "protein_depleted_liquid": _liquid("protein_depleted_liquid", "Protein-depleted liquid", ("soluble_cod_components", "inorganic_nitrogen_components", "dissolved_phosphorus", "dissolved_minerals")),
    "conditioned_digester_feed": _liquid("conditioned_digester_feed", "Conditioned digester feed", ("biodegradable_organics", "inorganic_nitrogen_components", "phosphorus_components", "dissolved_minerals")),
    "raw_biogas": StreamTemplate("raw_biogas", "Raw biogas", "g", ("biogas_components",), ("temperature", "pressure", "water_content"), ("kg/hr", "Nm3/hr", "vol.%"), ("methane", "carbon_dioxide"), ("hydrogen_sulfide", "ammonia", "water")),
    "digestate": _liquid("digestate", "Whole digestate", ("particulate_cod_components", "inorganic_nitrogen_components", "phosphorus_components", "dissolved_minerals")),
    "biomethane": StreamTemplate("biomethane", "Biomethane", "g", ("biogas_components",), ("temperature", "pressure", "water_content"), ("kg/hr", "Nm3/hr", "vol.%"), ("methane",), ("carbon_dioxide", "hydrogen_sulfide")),
    "upgrading_offgas": StreamTemplate("upgrading_offgas", "Upgrading offgas", "g", ("biogas_components",), ("temperature", "pressure"), ("kg/hr", "Nm3/hr", "vol.%"), ("carbon_dioxide",), ("methane", "hydrogen_sulfide")),
    "digestate_solids": _solid("digestate_solids", "Digestate solids", ("suspended_solids", "particulate_phosphorus", "contaminants")),
    "nutrient_rich_liquid": _liquid("nutrient_rich_liquid", "Nutrient-rich liquid", ("inorganic_nitrogen_components", "dissolved_phosphorus", "dissolved_minerals")),
    "struvite_product": _solid("struvite_product", "Struvite product", ("phosphorus_components", "fixed_solids")),
    "phosphorus_depleted_liquid": _liquid("phosphorus_depleted_liquid", "Phosphorus-depleted liquid", ("inorganic_nitrogen_components", "dissolved_minerals")),
    "ammonium_sulfate_product": _liquid("ammonium_sulfate_product", "Ammonium sulfate product", ("inorganic_nitrogen_components", "major_anions")),
    "nitrogen_depleted_liquid": _liquid("nitrogen_depleted_liquid", "Nitrogen-depleted liquid", ("dissolved_phosphorus", "dissolved_minerals")),
    "potassium_concentrate": _liquid("potassium_concentrate", "Potassium concentrate", ("dissolved_minerals", "inorganic_nitrogen_components", "dissolved_phosphorus")),
    "evaporator_condensate": _liquid("evaporator_condensate", "Evaporator condensate", ("inorganic_nitrogen_components", "organic_acids")),
    "treated_residual_water": _liquid("treated_residual_water", "Treated residual water", ("dissolved_minerals", "contaminants")),
}

for _template in STREAM_TEMPLATES.values():
    _template.validate()


def stream_template_table() -> list[dict[str, object]]:
    return [asdict(template) for template in STREAM_TEMPLATES.values()]
