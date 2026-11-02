# Feedstock Proxy Resolution Preparation

`Greenhub/feedstock_proxy.py` now has a read-only evidence classification layer for future dynamic gates. It does not activate parameters, modify `SimulationResult.dataset_readiness`, change PR1 behavior, or integrate with `seasonal_service`.

## Resolution hierarchy

Future resolution should follow this order:

1. Actual measured GreenHub project data.
2. Direct roadside-grass literature proxies.
3. Older fallback roadside/verge literature proxies.
4. Indirect proxy or sensitivity rows selected explicitly by a user.
5. Reference-only rows.
6. Blocked rows.

Measured GreenHub data must override all proxy evidence, even if a direct literature row is available.

## Evidence categories

- `project_data_ready`: reserved for measured GreenHub data when available.
- `direct_literature_proxy`: direct roadside or road-verge literature evidence with usable numeric data.
- `fallback_literature_proxy`: older direct Czubaszek/Wrobel-style rows used only when no primary direct row exists.
- `sensitivity_only_indirect_proxy`: indirect grass, proxy species, or sensitivity-bound rows. These require user selection.
- `reference_only`: useful context that must not become a default, such as BMP reference rows.
- `below_detection_limit`: reported as non-detect and not loaded as a numeric default.
- `blocked_missing`: explicit missing rows retained for reporting and data-gap tracking.
- `blocked_no_equation_mapping`: rows that provide an equation concept but no resolved numeric value or mapping.
- `blocked_wrong_basis`: rows whose basis is unclear or incompatible until confirmed.

## Ready now

The existing active proxy loader remains unchanged. It can still return direct active proxy fields already allowed by the prior layer, including moisture/as-received, volatile matter, ash, C, H, O, N, S, C:N ratio, bulk density, total protein, and extractive sugars.

The new classification helpers expose candidate metadata for review:

- `classify_feedstock_proxy_evidence()`
- `feedstock_proxy_resolution_candidates()`
- `summarize_feedstock_proxy_evidence()`

## Still blocked

Missing and unresolved rows remain blocked, including soluble protein, true protein, soluble sugars as process-release sugar, COD/BOD fractions, liquid density/viscosity/EC, alkalinity, nitrogen species, VFA species, cellulose/hemicellulose/lignin as direct roadside measurements, particle size, amino-acid profile, and thermal properties.

Indirect extended candidates are available only for sensitivity scenarios. Ranges keep their endpoints and raw text; no midpoint is derived.

## Future dynamic gates

This layer prepares the data model for future dynamic gates by attaching source priority, readiness category, user-selection requirements, equation/basis flags, values, units, source details, and limitation notes to each candidate. A later integration step can use these candidates in reports or review screens before any model calculation is allowed to consume them.
