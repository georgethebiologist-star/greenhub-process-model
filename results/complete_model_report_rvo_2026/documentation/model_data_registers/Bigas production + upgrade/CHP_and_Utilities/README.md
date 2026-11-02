# GreenHub CHP and Utilities literature dataset

This suite contains source-traceable inputs for reciprocating biogas engines, microturbines, gas turbines, boilers, CHP heat recovery and plant utility integration.

## Required model behavior
Do not use a single fixed CHP efficiency. Select a technology/model and use its full-load performance plus its source-specific part-load curve. Where only a graph was available, the curve remains missing rather than digitized or interpolated. The available textual 50% load observations are preserved.

## Data basis
EPA tables primarily report natural-gas performance on an HHV basis, while manufacturers often report LHV-based engine performance. These bases must not be mixed. Biogas applicability requires actual methane/CO2 composition, LHV, contaminants, gas pressure and manufacturer derating.

## Files
The eleven requested files are present, together with a source register, manifest, limitation register and this README.

## Important limitations
- A universal biogas LHV is not inserted.
- Complete engine and gas-turbine part-load curves were graph-only and were not digitized.
- Availability, equipment life and minimum stable load remain missing where not explicitly tabulated.
- The measured methane-slip case is from one site over four days and is suitable only as a sensitivity observation.
- Cost values retain their source currency and cost year; no inflation or currency conversion was applied.

## Integration readiness
Numerical values use one observation per row. Missing values are blank and marked `data_status=missing`. Equations are supplied symbolically and in Python-style form. Source URLs and exact table/page locations are included.
