"""Rotterdam monthly ambient-air comparator for seasonal digester heat loss.

KNMI station 344, monthly mean temperature, 2021–2025. Original integers
are tenths of a degree Celsius. This is a five-year climatological proxy,
not a measurement of GreenHub site air, stored grass, or process-liquid inlet.
Source: https://cdn.knmi.nl/knmi/map/page/klimatologie/gegevens/maandgegevens/mndgeg_344_tg.txt
Retrieved 2026-11-09; attribution: Royal Netherlands Meteorological Institute.
"""

from __future__ import annotations

import json
from pathlib import Path

_DATASET = json.loads(
    (Path(__file__).parent / "data" / "weather" / "knmi_rotterdam_344_2021_2025.json").read_text(encoding="utf-8")
)
SOURCE_URL = _DATASET["source_url"]
ROTTERDAM_MONTHLY_TENTHS_C = {
    int(year): tuple(int(value) for value in values)
    for year, values in _DATASET["jan_to_dec_tenths_degC"].items()
}
if set(ROTTERDAM_MONTHLY_TENTHS_C) != set(range(2021, 2026)) or any(
    len(values) != 12 for values in ROTTERDAM_MONTHLY_TENTHS_C.values()
):
    raise ValueError("KNMI Rotterdam five-year monthly weather table is incomplete")


def monthly_ambient_c(month: int) -> float:
    """Five-year mean of KNMI monthly means at Rotterdam, in degrees C."""
    if not 1 <= month <= 12:
        raise ValueError("month must be 1..12")
    return sum(row[month - 1] for row in ROTTERDAM_MONTHLY_TENTHS_C.values()) / (10 * len(ROTTERDAM_MONTHLY_TENTHS_C))
