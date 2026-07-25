"""Active Phase 2 unit operations for the GreenHub model."""

from __future__ import annotations

import biosteam as bst

from Greenhub.input_data import FeedSpecification
from Greenhub.separator import SeparatorParameters, resolve_separator_splits
from Greenhub.streams import create_liquid_fraction_from_inputs


def create_units(
    feed_specification: FeedSpecification | None = None,
    separator_parameters: SeparatorParameters | None = None,
) -> dict[str, object]:
    """Create T101 storage and the provisional S101 mass-allocation separator.

    Every split is the fraction routed to outlet 0, ``clarified_liquid``.
    S101 has no mechanical design, power, or CAPEX model in Phase 2.
    """

    feed, specification, characterization = create_liquid_fraction_from_inputs(feed_specification)
    resolved_splits = resolve_separator_splits(separator_parameters)

    T101 = bst.StorageTank(
        ID="T101",
        ins=feed,
        outs="stored_liquid_fraction",
        tau=24.0,
        vessel_type="Floating roof",
    )
    S101 = bst.Splitter(
        ID="S101",
        ins=T101 - 0,
        outs=("clarified_liquid", "wet_solids_slurry"),
        split=resolved_splits.splits_to_clarified,
    )
    return {
        "T101": T101,
        "S101": S101,
        "feed": feed,
        "feed_specification": specification,
        "characterization": characterization,
        "separator_splits": resolved_splits,
        "stored_liquid_fraction": T101 - 0,
        "clarified_liquid": S101 - 0,
        "wet_solids": S101 - 1,
    }


# Compatibility alias for Phase 1 notebooks; values now come from the hierarchy.
PRELIMINARY_SPLIT_TO_CLARIFIED = resolve_separator_splits().splits_to_clarified
