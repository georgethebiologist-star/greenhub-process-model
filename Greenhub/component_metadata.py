"""Metadata used for material characterization and analytical indicators."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from Greenhub.chemicals import ION_COMPONENTS, PSEUDOCOMPONENT_IDS, chemicals

ATOMIC_WEIGHTS = {
    "C": 12.0107,
    "H": 1.00794,
    "O": 15.9994,
    "N": 14.0067,
    "P": 30.973762,
    "S": 32.065,
    "K": 39.0983,
    "Na": 22.98977,
    "Mg": 24.305,
    "Ca": 40.078,
    "Cl": 35.453,
}


@dataclass(frozen=True)
class ComponentMetadata:
    """Scientific and reporting metadata for one BioSTEAM component."""

    component_id: str
    display_name: str
    category: str
    subcategory: str
    real_or_pseudo: str
    formula: str | None
    molecular_weight: float
    molecular_weight_convention: str
    default_phase: str
    solubility_class: str
    particle_class: str
    biodegradable: bool
    cod_factor: float | None
    toc_factor: float | None
    carbon_mass_fraction: float
    hydrogen_mass_fraction: float
    oxygen_mass_fraction: float
    nitrogen_mass_fraction: float
    phosphorus_mass_fraction: float
    sulfur_mass_fraction: float
    potassium_mass_fraction: float
    sodium_mass_fraction: float
    magnesium_mass_fraction: float
    calcium_mass_fraction: float
    chloride_mass_fraction: float
    ash_fraction: float
    volatile_solids_fraction: float
    heating_value_mj_kg: float | None
    property_source: str
    property_surrogate: str | None
    reference: str
    comment: str
    active_in_phase_2: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _element_fraction(chemical, element: str) -> float:
    atoms = chemical.atoms or {}
    count = float(atoms.get(element, 0.0))
    return count * ATOMIC_WEIGHTS[element] / chemical.MW if count else 0.0


def theoretical_cod_factor(chemical) -> float | None:
    """Return kg O2/kg using the COD convention N->NH3 and S->H2S."""

    atoms = chemical.atoms or {}
    if not atoms or any(i not in {"C", "H", "O", "N", "S"} for i in atoms):
        return None
    a = float(atoms.get("C", 0.0))
    b = float(atoms.get("H", 0.0))
    c = float(atoms.get("O", 0.0))
    d = float(atoms.get("N", 0.0))
    e = float(atoms.get("S", 0.0))
    oxygen_moles = a + b / 4.0 - c / 2.0 - 3.0 * d / 4.0 - e / 2.0
    return max(0.0, oxygen_moles * 31.9988 / chemical.MW)


def _base_metadata(component_id: str) -> ComponentMetadata:
    chemical = chemicals[component_id]
    formula = chemical.formula
    real_or_pseudo = "pseudo" if component_id in PSEUDOCOMPONENT_IDS else "real"
    source = "GreenHub explicit pseudo-component" if real_or_pseudo == "pseudo" else "ThermoSTEAM database"
    return ComponentMetadata(
        component_id=component_id,
        display_name=component_id,
        category="other",
        subcategory="unclassified",
        real_or_pseudo=real_or_pseudo,
        formula=formula,
        molecular_weight=float(chemical.MW),
        molecular_weight_convention=(
            "Formula molecular weight" if formula else "Representative lump molecular weight"
        ),
        default_phase=chemical.locked_state or "l",
        solubility_class="soluble" if (chemical.locked_state or "l") != "s" else "insoluble",
        particle_class="dissolved" if (chemical.locked_state or "l") != "s" else "suspended",
        biodegradable=False,
        cod_factor=None,
        toc_factor=_element_fraction(chemical, "C"),
        carbon_mass_fraction=_element_fraction(chemical, "C"),
        hydrogen_mass_fraction=_element_fraction(chemical, "H"),
        oxygen_mass_fraction=_element_fraction(chemical, "O"),
        nitrogen_mass_fraction=_element_fraction(chemical, "N"),
        phosphorus_mass_fraction=_element_fraction(chemical, "P"),
        sulfur_mass_fraction=_element_fraction(chemical, "S"),
        potassium_mass_fraction=_element_fraction(chemical, "K"),
        sodium_mass_fraction=_element_fraction(chemical, "Na"),
        magnesium_mass_fraction=_element_fraction(chemical, "Mg"),
        calcium_mass_fraction=_element_fraction(chemical, "Ca"),
        chloride_mass_fraction=_element_fraction(chemical, "Cl"),
        ash_fraction=0.0,
        volatile_solids_fraction=0.0,
        heating_value_mj_kg=None,
        property_source=source,
        property_surrogate=("Water or glucose sensible-property surrogate" if real_or_pseudo == "pseudo" else None),
        reference="BioSTEAM guide and GreenHub material-flow specification",
        comment=(
            "Pseudo-component enthalpy of formation and phase-equilibrium properties are provisional."
            if real_or_pseudo == "pseudo"
            else "Database component; suitability still depends on the future unit model."
        ),
    )


def _replace(component_id: str, **changes) -> ComponentMetadata:
    return replace(_base_metadata(component_id), **changes)


def _build_registry() -> dict[str, ComponentMetadata]:
    registry = {ID: _base_metadata(ID) for ID in chemicals.IDs}

    sugars = {"Glucose", "Fructose", "Sucrose", "Xylose", "Arabinose", "Galactose", "Mannose", "Maltose"}
    acids = {"AceticAcid", "LacticAcid", "PropionicAcid", "ButyricAcid", "FormicAcid", "SuccinicAcid", "CitricAcid", "MalicAcid", "OxalicAcid"}
    gases = {"Methane", "CarbonDioxide", "Hydrogen", "HydrogenSulfide", "Oxygen", "Nitrogen", "Siloxanes"}
    reagents = {
        "HydrochloricAcid", "SulfuricAcid", "SodiumHydroxide",
        "PotassiumHydroxide", "CalciumHydroxide", "CalciumOxide",
        "MagnesiumChloride", "MagnesiumOxide", "MagnesiumHydroxide",
        "MagnesiumSulfate", "CalciumCarbonate", "Monoethanolamine",
        "FerricOxide",
    }

    for ID in sugars:
        registry[ID] = _replace(ID, category="organic", subcategory="soluble_sugar", biodegradable=True, cod_factor=theoretical_cod_factor(chemicals[ID]), volatile_solids_fraction=1.0)
    for ID in acids:
        registry[ID] = _replace(ID, category="organic", subcategory="organic_acid", biodegradable=True, cod_factor=theoretical_cod_factor(chemicals[ID]), volatile_solids_fraction=1.0)
    for ID in gases:
        registry[ID] = _replace(ID, category="gas", subcategory="biogas_or_utility", cod_factor=theoretical_cod_factor(chemicals[ID]) if ID in {"Methane", "Hydrogen", "HydrogenSulfide"} else 0.0, active_in_phase_2=False)
    for ID in reagents:
        registry[ID] = _replace(ID, category="reagent", subcategory="future_process_chemical", active_in_phase_2=False)

    registry["Water"] = _replace("Water", category="water", subcategory="water", cod_factor=0.0, toc_factor=0.0)
    registry["Ammonia"] = _replace("Ammonia", category="nitrogen", subcategory="ammonia", cod_factor=0.0)

    ion_categories = {
        "HydrogenIon": ("acid_base", "proton_equivalent"),
        "HydroxideIon": ("acid_base", "hydroxide_equivalent"),
        "Ammonium": ("nitrogen", "ammonium"),
        "NitrateIon": ("nitrogen", "nitrate"),
        "NitriteIon": ("nitrogen", "nitrite"),
        "Orthophosphate": ("phosphorus", "orthophosphate"),
        "PotassiumIon": ("mineral", "cation"),
        "SodiumIon": ("mineral", "cation"),
        "MagnesiumIon": ("mineral", "cation"),
        "CalciumIon": ("mineral", "cation"),
        "ChlorideIon": ("mineral", "anion"),
        "SulfateIon": ("mineral", "anion"),
        "BicarbonateIon": ("inorganic_carbon", "alkalinity"),
        "CarbonateIon": ("inorganic_carbon", "alkalinity"),
    }
    for ID, (category, subcategory) in ion_categories.items():
        registry[ID] = _replace(ID, category=category, subcategory=subcategory, cod_factor=0.0, property_surrogate="Water sensible heat and liquid molar-volume surrogate", comment="Explicit ionic formula for mass tracking; no rigorous electrolyte activity model is claimed.")

    lump_overrides = {
        "SolubleProtein": dict(category="protein", subcategory="soluble_true_protein", biodegradable=True, cod_factor=1.50, toc_factor=0.53, carbon_mass_fraction=0.53, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.23, nitrogen_mass_fraction=0.16, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95),
        "SuspendedProtein": dict(category="protein", subcategory="suspended_protein", biodegradable=True, cod_factor=1.50, toc_factor=0.53, carbon_mass_fraction=0.53, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.23, nitrogen_mass_fraction=0.16, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95),
        "PrecipitatedProtein": dict(category="protein", subcategory="precipitated_protein", biodegradable=True, cod_factor=1.50, toc_factor=0.53, carbon_mass_fraction=0.53, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.23, nitrogen_mass_fraction=0.16, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95, active_in_phase_2=False),
        "HeatCoagulatedProtein": dict(category="protein", subcategory="heat_coagulated_protein", biodegradable=True, cod_factor=1.50, toc_factor=0.53, carbon_mass_fraction=0.53, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.23, nitrogen_mass_fraction=0.16, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95, active_in_phase_2=False, comment="Empirical heat-coagulated protein pool; it shares the SolubleProtein mass and elemental convention."),
        "DegradedProtein": dict(category="protein", subcategory="thermally_degraded_protein", biodegradable=True, cod_factor=1.50, toc_factor=0.53, carbon_mass_fraction=0.53, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.23, nitrogen_mass_fraction=0.16, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95, active_in_phase_2=False, comment="Bookkeeping pool for explicitly enabled thermal quality loss; no mass, N, COD, or TOC destruction is implied."),
        "Peptides": dict(category="protein", subcategory="peptides", biodegradable=True, cod_factor=1.50, toc_factor=0.53, carbon_mass_fraction=0.53, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.23, nitrogen_mass_fraction=0.16, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95),
        "AminoAcids": dict(category="protein", subcategory="free_amino_acids", biodegradable=True, cod_factor=1.20, toc_factor=0.45, carbon_mass_fraction=0.45, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.32, nitrogen_mass_fraction=0.15, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95),
        "Cellulose": dict(category="organic", subcategory="structural_carbohydrate", biodegradable=True, cod_factor=1.185, toc_factor=0.444, carbon_mass_fraction=0.444, hydrogen_mass_fraction=0.062, oxygen_mass_fraction=0.494, volatile_solids_fraction=1.0),
        "Hemicellulose": dict(category="organic", subcategory="structural_carbohydrate", biodegradable=True, cod_factor=1.21, toc_factor=0.455, carbon_mass_fraction=0.455, hydrogen_mass_fraction=0.061, oxygen_mass_fraction=0.484, volatile_solids_fraction=1.0),
        "Lignin": dict(category="organic", subcategory="structural_carbohydrate", biodegradable=False, cod_factor=1.80, toc_factor=0.65, carbon_mass_fraction=0.65, hydrogen_mass_fraction=0.06, oxygen_mass_fraction=0.29, volatile_solids_fraction=1.0),
        "Pectin": dict(category="organic", subcategory="structural_carbohydrate", biodegradable=True, cod_factor=1.07, toc_factor=0.41, carbon_mass_fraction=0.41, hydrogen_mass_fraction=0.05, oxygen_mass_fraction=0.54, volatile_solids_fraction=1.0),
        "Starch": dict(category="organic", subcategory="structural_carbohydrate", biodegradable=True, cod_factor=1.185, toc_factor=0.444, carbon_mass_fraction=0.444, hydrogen_mass_fraction=0.062, oxygen_mass_fraction=0.494, volatile_solids_fraction=1.0),
        "Lipids": dict(category="organic", subcategory="lipid", biodegradable=True, cod_factor=2.90, toc_factor=0.77, carbon_mass_fraction=0.77, hydrogen_mass_fraction=0.12, oxygen_mass_fraction=0.11, volatile_solids_fraction=1.0),
        "OtherBiodegradableOrganics": dict(category="organic", subcategory="other_biodegradable", biodegradable=True, cod_factor=1.30, toc_factor=0.45, carbon_mass_fraction=0.45, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.48, volatile_solids_fraction=1.0),
        "NonBiodegradableOrganics": dict(category="organic", subcategory="non_biodegradable", biodegradable=False, cod_factor=1.20, toc_factor=0.50, carbon_mass_fraction=0.50, hydrogen_mass_fraction=0.06, oxygen_mass_fraction=0.44, volatile_solids_fraction=1.0),
        "MicrobialBiomass": dict(category="organic", subcategory="combined_anaerobic_biomass", biodegradable=True, cod_factor=1.42, toc_factor=0.53, carbon_mass_fraction=0.53, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.24, nitrogen_mass_fraction=0.12, phosphorus_mass_fraction=0.02, sulfur_mass_fraction=0.01, volatile_solids_fraction=0.95, molecular_weight_convention="Representative C/N/P/S-balanced biomass bookkeeping unit", comment="Combined anaerobic biomass pool for Phase 5. Separate acidogenic, acetogenic, and methanogenic populations require kinetic and composition data that are not yet available."),
        "SolubleInertSolids": dict(category="solids", subcategory="soluble_inert", ash_fraction=1.0),
        "SuspendedSolids": dict(category="solids", subcategory="suspended_biogenic", biodegradable=True, cod_factor=1.20, toc_factor=0.45, carbon_mass_fraction=0.45, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.45, nitrogen_mass_fraction=0.03, volatile_solids_fraction=0.90),
        "SuspendedInertSolids": dict(category="solids", subcategory="suspended_inert", ash_fraction=1.0),
        "InertSolids": dict(category="solids", subcategory="suspended_inert", ash_fraction=1.0),
        "Ash": dict(category="solids", subcategory="ash", ash_fraction=1.0),
        "OrganicNitrogen": dict(category="nitrogen", subcategory="other_organic_n", nitrogen_mass_fraction=1.0, molecular_weight_convention="kg component equals kg N equivalent"),
        "OrganicPhosphorus": dict(category="phosphorus", subcategory="organic_p", phosphorus_mass_fraction=1.0, molecular_weight_convention="kg component equals kg P equivalent"),
        "ParticulatePhosphorus": dict(category="phosphorus", subcategory="particulate_p", phosphorus_mass_fraction=1.0, molecular_weight_convention="kg component equals kg P equivalent"),
        "HeavyMetals": dict(category="contaminant", subcategory="heavy_metals", ash_fraction=1.0),
        "PersistentOrganics": dict(category="contaminant", subcategory="pfas_pool"),
        "Pesticides": dict(category="contaminant", subcategory="pesticide_pool"),
        "Microplastics": dict(category="contaminant", subcategory="microplastic_pool"),
        "PathogenIndicators": dict(category="contaminant", subcategory="pathogen_indicator_pool"),
        "EntrappedSugars": dict(category="organic", subcategory="entrapped_sugar", biodegradable=True, cod_factor=theoretical_cod_factor(chemicals["Glucose"]), toc_factor=_element_fraction(chemicals["Glucose"], "C"), carbon_mass_fraction=_element_fraction(chemicals["Glucose"], "C"), hydrogen_mass_fraction=_element_fraction(chemicals["Glucose"], "H"), oxygen_mass_fraction=_element_fraction(chemicals["Glucose"], "O"), volatile_solids_fraction=1.0, molecular_weight_convention="Glucose-equivalent entrapped sugar pool", comment="Empirical solid sugar pool used only for mass-conserving PEF release to Glucose."),
        "ParticulateBiodegradableOrganics": dict(category="organic", subcategory="particulate_biodegradable", biodegradable=True, cod_factor=1.30, toc_factor=0.45, carbon_mass_fraction=0.45, hydrogen_mass_fraction=0.07, oxygen_mass_fraction=0.48, volatile_solids_fraction=1.0, comment="Empirical particulate pool with metadata matched to OtherBiodegradableOrganics for conservative PEF transfer."),
        "ParticulateNitrogen": dict(category="nitrogen", subcategory="particulate_n", nitrogen_mass_fraction=1.0, molecular_weight_convention="kg component equals kg N equivalent", comment="Particulate nitrogen-equivalent pool; may transfer one-to-one to OrganicNitrogen during PEF screening calculations."),
        "DissolvedPhosphorus": dict(category="phosphorus", subcategory="dissolved_p", phosphorus_mass_fraction=1.0, molecular_weight_convention="kg component equals kg P equivalent", comment="Dissolved phosphorus-equivalent pool; not a claim of a unique molecular species."),
        "ParticulatePotassium": dict(category="mineral", subcategory="particulate_k", potassium_mass_fraction=_element_fraction(chemicals["PotassiumIon"], "K"), molecular_weight_convention="Mass convention matched to PotassiumIon", comment="Particulate potassium-equivalent pool for conservative release to PotassiumIon."),
        "Sand": dict(category="contaminant", subcategory="mineral_grit", ash_fraction=1.0, comment="Grouped sand and mineral grit; molecular weight is a bookkeeping convention."),
        "Litter": dict(category="contaminant", subcategory="coarse_litter", ash_fraction=1.0, comment="Grouped coarse roadside litter tracked for preparation rejects; no exact molecular identity is claimed."),
        "Flocculant": dict(category="reagent", subcategory="optional_polymer", active_in_phase_2=False, comment="Generic optional polymer inventory; disabled by default and not assigned electrolyte or degradation rigor."),
        "Antifoam": dict(category="reagent", subcategory="optional_amine_antifoam", active_in_phase_2=False, comment="Generic optional antifoam inventory. It remains zero unless project-specific dosing is entered."),
        "Siloxanes": dict(category="contaminant", subcategory="d5_equivalent_siloxane_marker", cod_factor=None, active_in_phase_2=False, molecular_weight_convention="D5-equivalent formula used only for aggregate siloxane inventory", property_surrogate="Water sensible-property surrogate", comment="Aggregate volatile-siloxane marker using a D5-equivalent formula. It does not claim that all measured siloxanes are D5 or that gas-phase equilibrium is rigorous."),
        "ActivatedCarbon": dict(category="reagent", subcategory="gas_cleaning_media", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Activated-carbon media inventory; surface chemistry and pore-size distribution require vendor data."),
        "PSAAdsorbent": dict(category="reagent", subcategory="psa_adsorbent_inventory", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Generic PSA adsorbent inventory. The carbon formula is an elemental bookkeeping convention, not a declared zeolite or carbon grade."),
        "CapturedHydrogenSulfide": dict(category="waste", subcategory="adsorbed_h2s_equivalent", cod_factor=theoretical_cod_factor(chemicals["CapturedHydrogenSulfide"]), active_in_phase_2=False, molecular_weight_convention="H2S-equivalent retained sulfur inventory", comment="Solid bookkeeping pool for intact H2S-equivalent adsorption. It avoids inventing activated-carbon oxidation products."),
        "FerricSulfide": dict(category="waste", subcategory="spent_iron_sponge", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Fe2S3 bookkeeping product for the documented iron-sponge stoichiometry; hydration and mixed iron phases are neglected."),
        "AmmoniumChloride": dict(category="waste", subcategory="ammonia_scrubber_salt", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Molecular NH4Cl inventory for the simplified HCl ammonia scrubber; rigorous electrolyte speciation is not claimed."),
        "MEADegradationProducts": dict(category="waste", subcategory="mea_degradation_equivalent", cod_factor=None, active_in_phase_2=False, molecular_weight_convention="MEA-equivalent C/H/O/N formula", comment="Unresolved MEA degradation and heat-stable-salt inventory represented on an MEA-equivalent elemental basis; no exact product identity is claimed."),
        "SodiumChloride": dict(category="mineral", subcategory="neutralization_salt", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Molecular salt pool used by the simplified non-electrolyte neutralization model."),
        "CalciumChloride": dict(category="mineral", subcategory="neutralization_salt", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Dissolved CaCl2 inventory from HCl neutralization with calcium hydroxide."),
        "SodiumSulfate": dict(category="mineral", subcategory="neutralization_salt", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Dissolved Na2SO4 inventory from sulfuric-acid neutralization."),
        "CalciumSulfate": dict(category="mineral", subcategory="neutralization_salt", cod_factor=0.0, ash_fraction=1.0, active_in_phase_2=False, comment="Simplified anhydrous CaSO4 pool; gypsum hydration and scaling are not modelled."),
    }
    for ID, changes in lump_overrides.items():
        registry[ID] = _replace(ID, **changes)

    for ID in {
        "Struvite", "AmmoniumSulfate", "AmmoniumNitrate",
        "AmmoniumChloride", "CalciumPhosphate", "DicalciumPhosphate",
        "Hydroxyapatite", "ElementalSulfur",
    }:
        registry[ID] = _replace(ID, category="future_product", subcategory="reaction_product", active_in_phase_2=False)
    for ID in {"SodiumZeolite", "AmmoniumZeolite"}:
        registry[ID] = _replace(
            ID,
            category="reagent",
            subcategory="ion_exchange_site_equivalent",
            ash_fraction=1.0,
            active_in_phase_2=False,
            molecular_weight_convention="Aluminosilicate exchange-site equivalent",
            comment=(
                "Formula-balanced ion-exchange site marker; commercial mineral "
                "identity and thermophysical properties remain provisional."
            ),
        )
    return registry


COMPONENT_METADATA = _build_registry()


def metadata_table() -> list[dict[str, Any]]:
    """Return metadata rows in BioSTEAM component order."""

    return [COMPONENT_METADATA[ID].as_dict() for ID in chemicals.IDs]
