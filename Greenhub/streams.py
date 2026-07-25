"""Material stream factories for the GreenHub model."""

from __future__ import annotations

from collections.abc import Mapping

import biosteam as bst

from Greenhub.characterization import CharacterizationResult, characterize_feed
from Greenhub.chemicals import chemicals
from Greenhub.input_data import FeedSpecification, load_feed_specification
from Greenhub.settings import DEFAULT_PRESSURE_PA, DEFAULT_TEMPERATURE_K

BASELINE_FEED_ID = "raw_liquid_fraction"
BASELINE_FEED_FLOWS_KG_HR: dict[str, float] = {
    "Water": 900.0,
    "Glucose": 10.0,
    "Sucrose": 5.0,
    "AceticAcid": 2.0,
    "LacticAcid": 1.0,
    "Ammonium": 0.5,
    "SolubleProtein": 20.0,
    "SuspendedSolids": 45.0,
    "InertSolids": 5.0,
}


def validate_component_flows(component_flows: Mapping[str, float]) -> dict[str, float]:
    """Validate component flows before creating a BioSTEAM stream."""

    if not isinstance(component_flows, Mapping):
        raise TypeError("component_flows must be a mapping of component IDs to mass flows.")
    if not component_flows:
        raise ValueError("component_flows cannot be empty.")
    unknown = sorted(set(component_flows) - set(chemicals.IDs))
    if unknown:
        raise KeyError(f"Unknown component IDs in feed specification: {', '.join(unknown)}.")
    normalized: dict[str, float] = {}
    for component_id, value in component_flows.items():
        if value is None:
            raise ValueError(f"Component '{component_id}' has a missing flow value.")
        flow = float(value)
        if flow < 0.0:
            raise ValueError(f"Component '{component_id}' has a negative flow ({flow} kg/hr).")
        normalized[component_id] = flow
    if sum(normalized.values()) <= 0.0:
        raise ValueError("Total feed flow must be greater than zero.")
    return normalized


def create_liquid_fraction(
    component_flows: Mapping[str, float] | None = None,
    *,
    ID: str = BASELINE_FEED_ID,
    T: float = DEFAULT_TEMPERATURE_K,
    P: float = DEFAULT_PRESSURE_PA,
) -> bst.Stream:
    """Create a liquid-fraction stream directly from canonical kg/hr flows."""

    flows = validate_component_flows(
        BASELINE_FEED_FLOWS_KG_HR if component_flows is None else component_flows
    )
    return bst.Stream(ID=ID, T=T, P=P, units="kg/hr", **flows)


def create_liquid_fraction_from_inputs(
    feed_specification: FeedSpecification | None = None,
    *,
    ID: str = BASELINE_FEED_ID,
) -> tuple[bst.Stream, FeedSpecification, CharacterizationResult]:
    """Create the active feed through the Phase 2 characterization engine."""

    specification = feed_specification or load_feed_specification()
    characterization = characterize_feed(specification, ID=ID)
    return characterization.stream, specification, characterization
