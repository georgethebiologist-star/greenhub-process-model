"""Structured parameters for the provisional Phase 2 primary separator."""

from __future__ import annotations

from dataclasses import dataclass, field

from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA


@dataclass(frozen=True)
class SeparatorParameters:
    """Fractions routed to clarified liquid, resolved by explicit precedence."""

    component_splits_to_clarified: dict[str, float] = field(
        default_factory=lambda: {
            "Water": 0.97,
            "SolubleProtein": 0.95,
            "SuspendedProtein": 0.10,
            "SuspendedSolids": 0.10,
            "SuspendedInertSolids": 0.05,
            "InertSolids": 0.05,
            "Ash": 0.05,
            "ParticulatePhosphorus": 0.10,
            "HeavyMetals": 0.15,
            "Microplastics": 0.10,
            "PathogenIndicators": 0.10,
        }
    )
    group_splits_to_clarified: dict[str, float] = field(
        default_factory=lambda: {
            "soluble_sugars": 0.99,
            "organic_acids": 0.99,
            "soluble_proteins": 0.95,
            "peptides": 0.98,
            "amino_acids": 0.99,
            "inorganic_nitrogen_components": 0.99,
            "dissolved_phosphorus": 0.99,
            "dissolved_minerals": 0.99,
            "structural_carbohydrates": 0.10,
            "suspended_proteins": 0.10,
            "particulate_phosphorus": 0.10,
            "persistent_contaminants": 0.50,
        }
    )
    default_soluble_split_to_clarified: float = 0.98
    default_particulate_split_to_clarified: float = 0.10

    def validate(self) -> None:
        """Ensure all supplied recoveries follow the fraction-to-clarified convention."""

        values = {
            **{f"component:{key}": value for key, value in self.component_splits_to_clarified.items()},
            **{f"group:{key}": value for key, value in self.group_splits_to_clarified.items()},
            "default:soluble": self.default_soluble_split_to_clarified,
            "default:particulate": self.default_particulate_split_to_clarified,
        }
        invalid = {key: value for key, value in values.items() if not 0.0 <= value <= 1.0}
        if invalid:
            raise ValueError(f"Separator fractions to clarified liquid must be within [0, 1]: {invalid}")
        unknown_components = set(self.component_splits_to_clarified) - set(chemicals.IDs)
        unknown_groups = set(self.group_splits_to_clarified) - set(COMPONENT_GROUPS)
        if unknown_components or unknown_groups:
            raise KeyError(
                f"Unknown separator component overrides={sorted(unknown_components)}, "
                f"group overrides={sorted(unknown_groups)}."
            )


@dataclass(frozen=True)
class ResolvedSeparatorSplits:
    splits_to_clarified: dict[str, float]
    source_by_component: dict[str, str]
    warnings: tuple[str, ...]


def resolve_separator_splits(parameters: SeparatorParameters | None = None) -> ResolvedSeparatorSplits:
    """Resolve component > group > solubility-default split hierarchy."""

    parameters = parameters or SeparatorParameters()
    parameters.validate()
    splits: dict[str, float] = {}
    sources: dict[str, str] = {}
    warnings: list[str] = []
    for component_id in chemicals.IDs:
        if component_id in parameters.component_splits_to_clarified:
            splits[component_id] = parameters.component_splits_to_clarified[component_id]
            sources[component_id] = "component_override"
            continue
        matched_group = next(
            (
                group_name
                for group_name in parameters.group_splits_to_clarified
                if component_id in COMPONENT_GROUPS[group_name]
            ),
            None,
        )
        if matched_group:
            splits[component_id] = parameters.group_splits_to_clarified[matched_group]
            sources[component_id] = f"group:{matched_group}"
            continue
        metadata = COMPONENT_METADATA[component_id]
        if metadata.solubility_class == "soluble":
            splits[component_id] = parameters.default_soluble_split_to_clarified
            sources[component_id] = "default_soluble"
        elif metadata.particle_class == "suspended" or metadata.default_phase == "s":
            splits[component_id] = parameters.default_particulate_split_to_clarified
            sources[component_id] = "default_particulate"
        else:
            splits[component_id] = parameters.default_soluble_split_to_clarified
            sources[component_id] = "fallback_unclassified"
            warnings.append(
                f"Component '{component_id}' is unclassified; default soluble split was used."
            )
    return ResolvedSeparatorSplits(splits, sources, tuple(warnings))
