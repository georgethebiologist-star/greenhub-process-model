"""Tests for the GreenHub Phase 2 thermodynamic package."""

from Greenhub.chemicals import ION_COMPONENTS, PSEUDOCOMPONENT_IDS, chemicals


def test_required_chemicals_exist():
    required = {
        "Water", "Glucose", "Fructose", "Sucrose", "AceticAcid", "LacticAcid",
        "Ammonia", "Ammonium", "Orthophosphate", "PotassiumIon", "Methane",
        "CarbonDioxide", "SolubleProtein", "SuspendedProtein", "SuspendedSolids",
        "InertSolids", "Struvite", "Monoethanolamine", "Siloxanes",
        "ActivatedCarbon", "PSAAdsorbent", "CapturedHydrogenSulfide",
        "FerricOxide", "FerricSulfide", "AmmoniumChloride",
        "MEADegradationProducts", "Antifoam",
    }
    assert required.issubset(set(chemicals.IDs))


def test_pseudocomponents_are_initialized():
    for component_id in PSEUDOCOMPONENT_IDS:
        chemical = chemicals[component_id]
        assert chemical.MW > 0.0
        assert chemical.locked_state in {"g", "l", "s"}
        assert chemical.Cn is not None


def test_ionic_formulas_are_explicit():
    for component_id, formula in ION_COMPONENTS.items():
        assert chemicals[component_id].formula == formula
