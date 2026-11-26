"""Human-readable labels for reported BioSTEAM unit operations."""

from __future__ import annotations

import re


_UNIT_LABELS = {
    "M401": "Protein acidification mixer",
    "H401": "Protein-liquor heater",
    "R401": "Protein precipitation reactor",
    "C401": "Protein separator",
    "W401": "Protein-cake washer",
    "D401": "Protein-cake dewatering unit",
    "DR401": "Protein dryer",
    "M402": "Protein side-stream mixer",
    "M403": "Protein-liquor neutralization mixer",
}


def unit_display_name(unit_id: str, unit: object) -> str:
    """Prefer explicit equipment labels over BioSTEAM's generic ``line`` text."""
    label = _UNIT_LABELS.get(str(unit_id))
    if label:
        return label
    operation = type(unit).__name__
    return re.sub(r"(?<!^)(?=[A-Z])", " ", operation).strip()
