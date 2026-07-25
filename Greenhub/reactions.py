"""Inactive, validated stoichiometric foundation for later GreenHub phases."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Mapping

import thermosteam as tmo

from Greenhub.chemicals import chemicals
from Greenhub.component_metadata import COMPONENT_METADATA


@dataclass(frozen=True)
class BuswellResult:
    substrate_formula: dict[str, float]
    water: float
    methane: float
    carbon_dioxide: float
    ammonia: float
    hydrogen_sulfide: float

    @property
    def atom_residuals(self) -> dict[str, float]:
        a = self.substrate_formula.get("C", 0.0)
        b = self.substrate_formula.get("H", 0.0)
        c = self.substrate_formula.get("O", 0.0)
        d = self.substrate_formula.get("N", 0.0)
        e = self.substrate_formula.get("S", 0.0)
        return {
            "C": a - self.methane - self.carbon_dioxide,
            "H": b + 2.0 * self.water - 4.0 * self.methane - 3.0 * self.ammonia - 2.0 * self.hydrogen_sulfide,
            "O": c + self.water - 2.0 * self.carbon_dioxide,
            "N": d - self.ammonia,
            "S": e - self.hydrogen_sulfide,
        }


def parse_empirical_formula(formula: str | Mapping[str, float]) -> dict[str, float]:
    """Parse a simple C/H/O/N/S empirical formula for Buswell calculations."""

    if isinstance(formula, Mapping):
        atoms = {str(key): float(value) for key, value in formula.items() if float(value)}
    else:
        matches = re.findall(r"([A-Z][a-z]?)([0-9]*\.?[0-9]*)", formula)
        if not matches or "".join(element + number for element, number in matches) != formula:
            raise ValueError(f"Unsupported empirical formula '{formula}'.")
        atoms = {element: float(number or 1.0) for element, number in matches}
    unsupported = set(atoms) - {"C", "H", "O", "N", "S"}
    if unsupported:
        raise ValueError(f"Buswell supports only C/H/O/N/S; received {sorted(unsupported)}.")
    if atoms.get("C", 0.0) <= 0.0:
        raise ValueError("Buswell substrate must contain carbon.")
    return atoms


def buswell(formula: str | Mapping[str, float]) -> BuswellResult:
    """Return theoretical Buswell products per mole of biodegradable substrate."""

    atoms = parse_empirical_formula(formula)
    a, b, c, d, e = (atoms.get(i, 0.0) for i in "CHONS")
    methane = a / 2.0 + b / 8.0 - c / 4.0 - 3.0 * d / 8.0 - e / 4.0
    carbon_dioxide = a / 2.0 - b / 8.0 + c / 4.0 + 3.0 * d / 8.0 + e / 4.0
    water = a - b / 4.0 - c / 2.0 + 3.0 * d / 4.0 + e / 2.0
    if methane < -1e-12 or carbon_dioxide < -1e-12:
        raise ValueError("Formula yields negative methane or carbon dioxide and is not suitable for Buswell use.")
    result = BuswellResult(atoms, water, methane, carbon_dioxide, d, e)
    if max(abs(value) for value in result.atom_residuals.values()) > 1e-9:
        raise RuntimeError(f"Internal Buswell atom-balance failure: {result.atom_residuals}")
    return result


@dataclass(frozen=True)
class ReactionDefinition:
    name: str
    stoichiometry: str
    reactant: str
    category: str
    rigorous: bool
    enabled_in_phase_2: bool
    comment: str

    def create(self, conversion: float = 1.0) -> tmo.Reaction:
        """Create an independently testable ThermoSTEAM Reaction object."""

        if not 0.0 <= conversion <= 1.0:
            raise ValueError("Reaction conversion must be within [0, 1].")
        return tmo.Reaction(
            self.stoichiometry,
            reactant=self.reactant,
            X=conversion,
            chemicals=chemicals,
            check_atomic_balance=self.rigorous,
            check_mass_balance=self.rigorous,
        )


@dataclass(frozen=True)
class EmpiricalTransformation:
    name: str
    source_component: str
    target_component: str
    category: str
    comment: str

    def validate(self) -> None:
        if self.source_component not in chemicals.IDs or self.target_component not in chemicals.IDs:
            raise KeyError(f"Empirical transformation '{self.name}' references an unknown component.")
        source_mw = chemicals[self.source_component].MW
        target_mw = chemicals[self.target_component].MW
        if abs(source_mw - target_mw) > 1e-9:
            raise ValueError(f"Empirical mass-transfer components for '{self.name}' must share an MW convention.")
        source = COMPONENT_METADATA[self.source_component]
        target = COMPONENT_METADATA[self.target_component]
        comparable_fields = (
            "carbon_mass_fraction",
            "hydrogen_mass_fraction",
            "oxygen_mass_fraction",
            "nitrogen_mass_fraction",
            "phosphorus_mass_fraction",
            "sulfur_mass_fraction",
            "cod_factor",
            "toc_factor",
        )
        inconsistent = {
            field: (getattr(source, field), getattr(target, field))
            for field in comparable_fields
            if getattr(source, field) != getattr(target, field)
        }
        if inconsistent:
            raise ValueError(
                f"Empirical transformation '{self.name}' changes conserved metadata: {inconsistent}."
            )


REACTION_DEFINITIONS = (
    ReactionDefinition("hcl_dissociation", "HydrochloricAcid -> HydrogenIon + ChlorideIon", "HydrochloricAcid", "acid_base", True, False, "Prepared for acid-equivalent accounting; no activity-coefficient model is implied."),
    ReactionDefinition("naoh_dissociation", "SodiumHydroxide -> SodiumIon + HydroxideIon", "SodiumHydroxide", "acid_base", True, False, "Prepared for neutralization accounting."),
    ReactionDefinition("calcium_hydroxide_dissociation", "CalciumHydroxide -> CalciumIon + 2 HydroxideIon", "CalciumHydroxide", "acid_base", True, False, "Prepared for alternative neutralization."),
    ReactionDefinition("magnesium_chloride_dissociation", "MagnesiumChloride -> MagnesiumIon + 2 ChlorideIon", "MagnesiumChloride", "struvite", True, False, "Prepared for struvite reagent accounting."),
    ReactionDefinition("neutralization", "HydrogenIon + HydroxideIon -> Water", "HydrogenIon", "acid_base", True, False, "Strong-acid/base equivalent reaction."),
    ReactionDefinition("hcl_naoh_neutralization", "HydrochloricAcid + SodiumHydroxide -> SodiumChloride + Water", "HydrochloricAcid", "protein_recovery", True, False, "Simplified non-electrolyte salt formation for Phase 4."),
    ReactionDefinition("hcl_calcium_hydroxide_neutralization", "2 HydrochloricAcid + CalciumHydroxide -> CalciumChloride + 2 Water", "HydrochloricAcid", "protein_recovery", True, False, "Alternative Phase 4 calcium-base neutralization."),
    ReactionDefinition("sulfuric_naoh_neutralization", "SulfuricAcid + 2 SodiumHydroxide -> SodiumSulfate + 2 Water", "SulfuricAcid", "protein_recovery", True, False, "Alternative sulfate salt formation."),
    ReactionDefinition("sulfuric_calcium_hydroxide_neutralization", "SulfuricAcid + CalciumHydroxide -> CalciumSulfate + 2 Water", "SulfuricAcid", "protein_recovery", True, False, "Alternative calcium-sulfate formation; hydration is not resolved."),
    ReactionDefinition("lactic_fermentation", "Glucose -> 2 LacticAcid", "Glucose", "protein_recovery", True, False, "Alternative biological acidification."),
    ReactionDefinition("overall_glucose_digestion", "Glucose -> 3 Methane + 3 CarbonDioxide", "Glucose", "digestion", True, False, "Theoretical overall conversion only; not a kinetic digester model."),
    ReactionDefinition("acetoclastic_methanogenesis", "AceticAcid -> Methane + CarbonDioxide", "AceticAcid", "digestion", True, False, "Future anaerobic digestion reaction."),
    ReactionDefinition("hydrogenotrophic_methanogenesis", "CarbonDioxide + 4 Hydrogen -> Methane + 2 Water", "CarbonDioxide", "digestion", True, False, "Future anaerobic digestion reaction."),
    ReactionDefinition("propionate_conversion", "PropionicAcid + 2 Water -> AceticAcid + CarbonDioxide + 3 Hydrogen", "PropionicAcid", "digestion", True, False, "Neutral-acid form used for atom-balanced preparation."),
    ReactionDefinition("butyrate_conversion", "ButyricAcid + 2 Water -> 2 AceticAcid + 2 Hydrogen", "ButyricAcid", "digestion", True, False, "Neutral-acid form used for atom-balanced preparation."),
    ReactionDefinition("sulfate_reduction", "SulfateIon + 4 Hydrogen + 2 HydrogenIon -> HydrogenSulfide + 4 Water", "SulfateIon", "digestion", True, False, "Optional pathway; conversion remains user-defined."),
    ReactionDefinition("struvite_precipitation", "MagnesiumIon + Ammonium + Orthophosphate + 6 Water -> Struvite", "Orthophosphate", "struvite", True, False, "Later limited by Mg, NH4, PO4 and an explicit recovery."),
    ReactionDefinition("ammonia_liberation", "Ammonium + HydroxideIon -> Ammonia + Water", "Ammonium", "ammonia_recovery", True, False, "Stoichiometric base demand; equilibrium fraction is calculated separately."),
    ReactionDefinition("ammonium_sulfate_absorption", "2 Ammonia + SulfuricAcid -> AmmoniumSulfate", "Ammonia", "ammonia_recovery", True, False, "Prepared acid-absorption reaction."),
    ReactionDefinition("h2s_to_sulfur", "2 HydrogenSulfide + Oxygen -> 2 ElementalSulfur + 2 Water", "HydrogenSulfide", "desulfurization", True, False, "Optional activated-carbon oxidation pathway."),
    ReactionDefinition("calcium_carbonate_precipitation", "CalciumIon + CarbonateIon -> CalciumCarbonate", "CalciumIon", "scaling", True, False, "Disabled optional scaling pathway."),
    ReactionDefinition("calcium_phosphate_precipitation", "3 CalciumIon + 2 Orthophosphate -> CalciumPhosphate", "Orthophosphate", "scaling", True, False, "Disabled competing phosphorus pathway."),
)

EMPIRICAL_TRANSFORMATIONS = (
    EmpiricalTransformation("protein_precipitation", "SolubleProtein", "PrecipitatedProtein", "protein_recovery", "Phase transfer/recovery model; acid demand is calculated separately."),
    EmpiricalTransformation("protein_coagulation", "SolubleProtein", "HeatCoagulatedProtein", "protein_recovery", "Heat-induced state change, not molecular destruction."),
    EmpiricalTransformation("precipitated_protein_degradation", "PrecipitatedProtein", "DegradedProtein", "protein_recovery", "Optional thermal quality loss with mass, N, COD, and TOC retained."),
    EmpiricalTransformation("coagulated_protein_degradation", "HeatCoagulatedProtein", "DegradedProtein", "protein_recovery", "Optional thermal quality loss with mass, N, COD, and TOC retained."),
)


def build_reaction_library(conversion: float = 1.0) -> dict[str, tmo.Reaction]:
    """Build and validate all rigorous molecular reactions without applying them."""

    library = {definition.name: definition.create(conversion) for definition in REACTION_DEFINITIONS}
    for transformation in EMPIRICAL_TRANSFORMATIONS:
        transformation.validate()
    return library


def reaction_library_table() -> list[dict[str, object]]:
    """Return auditable definitions and balance errors for reporting."""

    rows = []
    for definition in REACTION_DEFINITIONS:
        reaction = definition.create()
        row = asdict(definition)
        row["mass_balance_error"] = float(reaction.mass_balance_error())
        atom_error = reaction.atomic_balance_error()
        row["maximum_atom_balance_error"] = max(abs(float(value)) for value in atom_error.values()) if len(atom_error) else 0.0
        rows.append(row)
    for transformation in EMPIRICAL_TRANSFORMATIONS:
        transformation.validate()
        row = asdict(transformation)
        row.update({"stoichiometry": f"{transformation.source_component} -> {transformation.target_component}", "rigorous": False, "enabled_in_phase_2": False, "mass_balance_error": 0.0, "maximum_atom_balance_error": None})
        rows.append(row)
    return rows


# Import-time construction catches invalid IDs or stoichiometry before a unit uses it.
REACTION_LIBRARY = build_reaction_library()
