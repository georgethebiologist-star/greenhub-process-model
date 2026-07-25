"""Thermodynamic components for the GreenHub Phase 2-7 model.

Real ThermoSTEAM chemicals are used only when the installed database resolves
the intended compound unambiguously. Ionic pools and project-specific lumps
are explicit pseudo-components. Their thermodynamic models are adequate for
Phase 2-6 material balances and preliminary sensible-heat calculations, but
not for rigorous electrolyte or phase-equilibrium calculations. Phase 5 reuses
the combined ``MicrobialBiomass`` pool rather than inventing unsupported
acidogen, acetogen, and methanogen species. Phase 6 adds only the minimum gas-
cleaning, adsorbent, and solvent bookkeeping components needed to conserve
mass and elements across the conditioning and upgrading alternatives.
"""

from __future__ import annotations

from collections.abc import Iterable

import thermosteam as tmo
from biosteam import settings as bst_settings

REAL_CHEMICAL_IDS = (
    "Water",
    "Glucose",
    "Fructose",
    "Sucrose",
    "Xylose",
    "Arabinose",
    "Galactose",
    "Mannose",
    "Maltose",
    "AceticAcid",
    "LacticAcid",
    "PropionicAcid",
    "ButyricAcid",
    "FormicAcid",
    "SuccinicAcid",
    "CitricAcid",
    "MalicAcid",
    "OxalicAcid",
    "Ammonia",
    "Methane",
    "CarbonDioxide",
    "Hydrogen",
    "HydrogenSulfide",
    "Oxygen",
    "Nitrogen",
    "HydrochloricAcid",
    "SulfuricAcid",
    "SodiumHydroxide",
    "CalciumHydroxide",
    "MagnesiumChloride",
    "SodiumChloride",
    "CalciumCarbonate",
    "Monoethanolamine",
    "FerricOxide",
    "PotassiumHydroxide",
    "MagnesiumOxide",
    "MagnesiumHydroxide",
    "MagnesiumSulfate",
    "CalciumOxide",
)

ION_COMPONENTS = {
    "HydrogenIon": "H+",
    "HydroxideIon": "OH-",
    "Ammonium": "NH4+",
    "NitrateIon": "NO3-",
    "NitriteIon": "NO2-",
    "Orthophosphate": "PO4-3",
    "PotassiumIon": "K+",
    "SodiumIon": "Na+",
    "MagnesiumIon": "Mg+2",
    "CalciumIon": "Ca+2",
    "ChlorideIon": "Cl-",
    "SulfateIon": "SO4-2",
    "BicarbonateIon": "HCO3-",
    "CarbonateIon": "CO3-2",
}

LUMPED_COMPONENTS: tuple[tuple[str, str, float, str], ...] = (
    ("SolubleProtein", "l", 110.0, "Water"),
    ("SuspendedProtein", "s", 110.0, "Glucose"),
    ("PrecipitatedProtein", "s", 110.0, "Glucose"),
    ("HeatCoagulatedProtein", "s", 110.0, "Glucose"),
    ("DegradedProtein", "s", 110.0, "Glucose"),
    ("Peptides", "l", 110.0, "Water"),
    ("AminoAcids", "l", 110.0, "Water"),
    ("Cellulose", "s", 162.14, "Glucose"),
    ("Hemicellulose", "s", 132.11, "Glucose"),
    ("Lignin", "s", 180.0, "Glucose"),
    ("Pectin", "s", 176.12, "Glucose"),
    ("Starch", "s", 162.14, "Glucose"),
    ("Lipids", "l", 885.0, "Water"),
    ("OtherBiodegradableOrganics", "l", 100.0, "Water"),
    ("NonBiodegradableOrganics", "l", 100.0, "Water"),
    ("MicrobialBiomass", "s", 113.0, "Glucose"),
    ("SolubleInertSolids", "l", 60.0, "Water"),
    ("SuspendedSolids", "s", 24.0, "Glucose"),
    ("SuspendedInertSolids", "s", 60.0, "Glucose"),
    ("InertSolids", "s", 60.0, "Glucose"),
    ("Ash", "s", 60.0, "Glucose"),
    ("OrganicNitrogen", "l", 14.0067, "Water"),
    ("OrganicPhosphorus", "l", 30.9738, "Water"),
    ("ParticulatePhosphorus", "s", 30.9738, "Glucose"),
    ("HeavyMetals", "s", 65.0, "Glucose"),
    ("PersistentOrganics", "l", 500.0, "Water"),
    ("Pesticides", "l", 300.0, "Water"),
    ("Microplastics", "s", 1000.0, "Glucose"),
    ("PathogenIndicators", "s", 1000.0, "Glucose"),
    ("EntrappedSugars", "s", 180.156, "Glucose"),
    ("ParticulateBiodegradableOrganics", "s", 100.0, "Glucose"),
    ("ParticulateNitrogen", "s", 14.0067, "Glucose"),
    ("DissolvedPhosphorus", "l", 30.9738, "Water"),
    ("ParticulatePotassium", "s", 39.0983, "CalciumCarbonate"),
    ("Sand", "s", 60.08, "CalciumCarbonate"),
    ("Litter", "s", 1000.0, "Glucose"),
    ("Flocculant", "l", 100.0, "Water"),
    ("Antifoam", "l", 500.0, "Water"),
)

FORMULA_PSEUDOCOMPONENTS: tuple[tuple[str, str, str, str], ...] = (
    ("Struvite", "H16MgNO10P", "s", "Glucose"),
    ("AmmoniumSulfate", "H8N2O4S", "l", "Water"),
    ("AmmoniumNitrate", "H4N2O3", "l", "Water"),
    ("CalciumPhosphate", "Ca3O8P2", "s", "Glucose"),
    ("CalciumChloride", "CaCl2", "l", "Water"),
    ("SodiumSulfate", "Na2SO4", "l", "Water"),
    ("CalciumSulfate", "CaSO4", "s", "Glucose"),
    ("ElementalSulfur", "S", "s", "Glucose"),
    # D5-equivalent formula is a transparent marker convention for the
    # unresolved mixed siloxane inventory; it is not an identity claim.
    ("Siloxanes", "C10H30O5Si5", "g", "Water"),
    ("ActivatedCarbon", "C", "s", "Glucose"),
    ("PSAAdsorbent", "C", "s", "Glucose"),
    ("CapturedHydrogenSulfide", "H2S", "s", "Glucose"),
    ("FerricSulfide", "Fe2S3", "s", "Glucose"),
    ("AmmoniumChloride", "H4NCl", "l", "Water"),
    # Equivalent formula preserves C/H/O/N when MEA is assigned to the
    # unresolved degradation-products inventory.
    ("MEADegradationProducts", "C2H7NO", "l", "Water"),
    ("DicalciumPhosphate", "CaHPO4", "s", "Glucose"),
    ("Hydroxyapatite", "Ca5HO13P3", "s", "Glucose"),
    # These formulas retain the common aluminosilicate framework so the
    # sodium/ammonium exchange and NaCl regeneration reactions are elemental-
    # and mass-balanced. They are site-equivalent bookkeeping species, not a
    # claim that the selected commercial zeolite has this exact composition.
    ("SodiumZeolite", "AlNaO4Si", "s", "Glucose"),
    ("AmmoniumZeolite", "AlH4NO4Si", "s", "Glucose"),
)

PSEUDOCOMPONENT_IDS = tuple(ION_COMPONENTS) + tuple(i[0] for i in LUMPED_COMPONENTS) + tuple(
    i[0] for i in FORMULA_PSEUDOCOMPONENTS
)


def _create_pseudochemical(
    ID: str,
    *,
    phase: str,
    surrogate: tmo.Chemical,
    MW: float | None = None,
    formula: str | None = None,
) -> tmo.Chemical:
    """Create a stable pseudo-component with documented surrogate properties."""

    kwargs = {"ID": ID, "phase": phase}
    if formula is not None:
        kwargs["formula"] = formula
    else:
        kwargs["MW"] = MW
    pseudo = tmo.Chemical.blank(**kwargs)
    pseudo.default()
    pseudo.copy_models_from(surrogate, names=("Cn", "V"))
    pseudo.Hf = 0.0
    return pseudo


def create_chemicals() -> tmo.Chemicals:
    """Create and compile the GreenHub thermodynamic package."""

    real = {ID: tmo.Chemical(ID) for ID in REAL_CHEMICAL_IDS}
    components = list(real.values())

    for ID, formula in ION_COMPONENTS.items():
        components.append(
            _create_pseudochemical(
                ID,
                phase="l",
                formula=formula,
                surrogate=real["Water"],
            )
        )

    for ID, phase, MW, surrogate_ID in LUMPED_COMPONENTS:
        components.append(
            _create_pseudochemical(
                ID,
                phase=phase,
                MW=MW,
                surrogate=real[surrogate_ID],
            )
        )

    for ID, formula, phase, surrogate_ID in FORMULA_PSEUDOCOMPONENTS:
        components.append(
            _create_pseudochemical(
                ID,
                phase=phase,
                formula=formula,
                surrogate=real[surrogate_ID],
            )
        )

    chemicals = tmo.Chemicals(components)
    chemicals.compile()
    return chemicals


def set_thermo(
    components: tmo.Chemicals | Iterable[str | tmo.Chemical] | None = None,
) -> tmo.Thermo:
    """Compile and activate the GreenHub thermodynamic package."""

    if components is None:
        components = create_chemicals()
    thermo = tmo.Thermo(components)
    bst_settings.set_thermo(thermo)
    return thermo


thermo = set_thermo()
chemicals = thermo.chemicals
