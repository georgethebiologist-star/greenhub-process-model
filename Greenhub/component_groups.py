"""Reusable non-overlapping and analytical component groups."""

from __future__ import annotations

from Greenhub.chemicals import chemicals

COMPONENT_GROUPS: dict[str, frozenset[str]] = {
    "soluble_sugars": frozenset({"Glucose", "Fructose", "Sucrose", "Xylose", "Arabinose", "Galactose", "Mannose", "Maltose"}),
    "entrapped_sugars": frozenset({"EntrappedSugars"}),
    "structural_carbohydrates": frozenset({"Cellulose", "Hemicellulose", "Lignin", "Pectin", "Starch"}),
    "organic_acids": frozenset({"AceticAcid", "LacticAcid", "PropionicAcid", "ButyricAcid", "FormicAcid", "SuccinicAcid", "CitricAcid", "MalicAcid", "OxalicAcid"}),
    "vfas": frozenset({"AceticAcid", "PropionicAcid", "ButyricAcid", "FormicAcid"}),
    "soluble_proteins": frozenset({"SolubleProtein"}),
    "suspended_proteins": frozenset({"SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein"}),
    "peptides": frozenset({"Peptides"}),
    "amino_acids": frozenset({"AminoAcids"}),
    "recoverable_proteins": frozenset({"SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein"}),
    "protein_product_components": frozenset({"SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein"}),
    "protein_equivalents": frozenset({"SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein", "Peptides", "AminoAcids"}),
    "biodegradable_organics": frozenset({"Glucose", "Fructose", "Sucrose", "Xylose", "Arabinose", "Galactose", "Mannose", "Maltose", "AceticAcid", "LacticAcid", "PropionicAcid", "ButyricAcid", "FormicAcid", "SuccinicAcid", "CitricAcid", "MalicAcid", "OxalicAcid", "SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein", "Peptides", "AminoAcids", "Cellulose", "Hemicellulose", "Pectin", "Starch", "Lipids", "OtherBiodegradableOrganics", "MicrobialBiomass", "SuspendedSolids"}),
    "non_biodegradable_organics": frozenset({"Lignin", "NonBiodegradableOrganics", "PersistentOrganics", "Pesticides", "Microplastics"}),
    "organic_nitrogen_components": frozenset({"SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein", "Peptides", "AminoAcids", "OrganicNitrogen", "ParticulateNitrogen", "MicrobialBiomass"}),
    "inorganic_nitrogen_components": frozenset({"Ammonia", "Ammonium", "NitrateIon", "NitriteIon"}),
    "phosphorus_components": frozenset({"Orthophosphate", "DissolvedPhosphorus", "OrganicPhosphorus", "ParticulatePhosphorus"}),
    "dissolved_phosphorus": frozenset({"Orthophosphate", "DissolvedPhosphorus", "OrganicPhosphorus"}),
    "particulate_phosphorus": frozenset({"ParticulatePhosphorus"}),
    "major_cations": frozenset({"HydrogenIon", "Ammonium", "PotassiumIon", "SodiumIon", "MagnesiumIon", "CalciumIon"}),
    "major_anions": frozenset({"HydroxideIon", "NitrateIon", "NitriteIon", "Orthophosphate", "ChlorideIon", "SulfateIon", "BicarbonateIon", "CarbonateIon"}),
    "neutralization_salts": frozenset({"SodiumChloride", "CalciumChloride", "SodiumSulfate", "CalciumSulfate"}),
    "dissolved_minerals": frozenset({"HydrogenIon", "HydroxideIon", "PotassiumIon", "SodiumIon", "MagnesiumIon", "CalciumIon", "ChlorideIon", "SulfateIon", "BicarbonateIon", "CarbonateIon", "SolubleInertSolids", "SodiumChloride", "CalciumChloride", "SodiumSulfate"}),
    "suspended_solids": frozenset({"SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein", "EntrappedSugars", "Cellulose", "Hemicellulose", "Lignin", "Pectin", "Starch", "ParticulateBiodegradableOrganics", "ParticulateNitrogen", "ParticulatePotassium", "MicrobialBiomass", "SuspendedSolids", "SuspendedInertSolids", "InertSolids", "Ash", "Sand", "Litter", "ParticulatePhosphorus", "HeavyMetals", "Microplastics", "PathogenIndicators", "CalciumSulfate"}),
    "dissolved_solids": frozenset({"SolubleProtein", "Peptides", "AminoAcids", "SolubleInertSolids", "HydrogenIon", "HydroxideIon", "Ammonium", "NitrateIon", "NitriteIon", "Orthophosphate", "DissolvedPhosphorus", "OrganicPhosphorus", "PotassiumIon", "SodiumIon", "MagnesiumIon", "CalciumIon", "ChlorideIon", "SulfateIon", "BicarbonateIon", "CarbonateIon", "SodiumChloride", "CalciumChloride", "SodiumSulfate", "Flocculant"}),
    "volatile_solids": frozenset({"SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein", "Peptides", "AminoAcids", "EntrappedSugars", "Cellulose", "Hemicellulose", "Lignin", "Pectin", "Starch", "Lipids", "OtherBiodegradableOrganics", "ParticulateBiodegradableOrganics", "NonBiodegradableOrganics", "MicrobialBiomass", "SuspendedSolids"}),
    "fixed_solids": frozenset({"SolubleInertSolids", "SuspendedInertSolids", "InertSolids", "Ash", "Sand", "Litter", "HeavyMetals"}),
    "biogas_components": frozenset({"Methane", "CarbonDioxide", "Hydrogen", "HydrogenSulfide", "Ammonia", "Oxygen", "Nitrogen", "Siloxanes"}),
    "phase6_gas_components": frozenset({"Methane", "CarbonDioxide", "Hydrogen", "HydrogenSulfide", "Ammonia", "Oxygen", "Nitrogen", "Water", "Siloxanes"}),
    "phase6_particulates": frozenset({"SuspendedSolids", "SuspendedInertSolids", "Ash", "Microplastics"}),
    "phase6_media_components": frozenset({"ActivatedCarbon", "PSAAdsorbent", "CapturedHydrogenSulfide", "FerricOxide", "FerricSulfide", "ElementalSulfur"}),
    "phase6_amine_components": frozenset({"Monoethanolamine", "MEADegradationProducts", "Antifoam"}),
    "phase7_phosphorus_products": frozenset({"Struvite", "CalciumPhosphate", "DicalciumPhosphate", "Hydroxyapatite"}),
    "phase7_ammonium_products": frozenset({"AmmoniumSulfate", "AmmoniumChloride", "AmmoniumNitrate"}),
    "phase7_magnesium_reagents": frozenset({"MagnesiumChloride", "MagnesiumOxide", "MagnesiumHydroxide", "MagnesiumSulfate"}),
    "phase7_calcium_reagents": frozenset({"CalciumChloride", "CalciumHydroxide", "CalciumOxide"}),
    "phase7_bases": frozenset({"SodiumHydroxide", "PotassiumHydroxide", "CalciumHydroxide", "MagnesiumOxide", "MagnesiumHydroxide"}),
    "phase7_ion_exchange_media": frozenset({"SodiumZeolite", "AmmoniumZeolite"}),
    "phase7_soluble_nutrients": frozenset({"Ammonia", "Ammonium", "NitrateIon", "NitriteIon", "Orthophosphate", "DissolvedPhosphorus", "PotassiumIon"}),
    "digester_protein_substrates": frozenset({"SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein", "Peptides", "AminoAcids"}),
    "digester_carbohydrate_substrates": frozenset({"Glucose", "Fructose", "Sucrose", "Xylose", "Arabinose", "Galactose", "Mannose", "Maltose", "EntrappedSugars", "Cellulose", "Hemicellulose", "Pectin", "Starch", "SuspendedSolids", "ParticulateBiodegradableOrganics"}),
    "digester_vfa_substrates": frozenset({"AceticAcid", "LacticAcid", "PropionicAcid", "ButyricAcid", "FormicAcid"}),
    "digester_other_substrates": frozenset({"Lipids", "OtherBiodegradableOrganics"}),
    "digester_inorganic_carbon": frozenset({"CarbonDioxide", "BicarbonateIon", "CarbonateIon"}),
    "digester_sulfur_components": frozenset({"HydrogenSulfide", "SulfateIon", "SulfuricAcid", "SodiumSulfate", "CalciumSulfate", "AmmoniumSulfate", "ElementalSulfur", "CapturedHydrogenSulfide", "FerricSulfide"}),
    "contaminants": frozenset({"HeavyMetals", "PersistentOrganics", "Pesticides", "Microplastics", "PathogenIndicators", "Sand", "Litter"}),
    "heavy_metals": frozenset({"HeavyMetals"}),
    "persistent_contaminants": frozenset({"PersistentOrganics", "Pesticides", "Microplastics"}),
}

COMPONENT_GROUPS["soluble_cod_components"] = frozenset(
    COMPONENT_GROUPS["soluble_sugars"] | COMPONENT_GROUPS["organic_acids"] | COMPONENT_GROUPS["soluble_proteins"] | COMPONENT_GROUPS["peptides"] | COMPONENT_GROUPS["amino_acids"] | {"Lipids", "OtherBiodegradableOrganics", "NonBiodegradableOrganics"}
)
COMPONENT_GROUPS["particulate_cod_components"] = frozenset(
    COMPONENT_GROUPS["structural_carbohydrates"] | COMPONENT_GROUPS["entrapped_sugars"] | COMPONENT_GROUPS["suspended_proteins"] | {"ParticulateBiodegradableOrganics", "MicrobialBiomass", "SuspendedSolids", "Microplastics"}
)
COMPONENT_GROUPS["anaerobic_substrates"] = frozenset(
    COMPONENT_GROUPS["digester_protein_substrates"]
    | COMPONENT_GROUPS["digester_carbohydrate_substrates"]
    | COMPONENT_GROUPS["digester_vfa_substrates"]
    | COMPONENT_GROUPS["digester_other_substrates"]
)
COMPONENT_GROUPS["phase7_nutrient_products"] = frozenset(
    COMPONENT_GROUPS["phase7_phosphorus_products"]
    | COMPONENT_GROUPS["phase7_ammonium_products"]
)


def get_group(name: str) -> frozenset[str]:
    """Return a named component group or raise a descriptive error."""

    try:
        return COMPONENT_GROUPS[name]
    except KeyError as error:
        raise KeyError(f"Unknown component group '{name}'.") from error


def validate_component_groups() -> None:
    """Ensure every group references components present in the active thermo."""

    known = set(chemicals.IDs)
    invalid = {name: sorted(ids - known) for name, ids in COMPONENT_GROUPS.items() if ids - known}
    if invalid:
        raise ValueError(f"Component groups contain unknown component IDs: {invalid}")


validate_component_groups()
