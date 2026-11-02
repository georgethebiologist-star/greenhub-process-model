# Feedstock Dynamic Resolution Preview

`Greenhub/feedstock_resolution.py` adds a report-only preview for future time-aware feedstock gates. It combines the generated GreenHub time grid with feedstock proxy evidence candidates and canonical field names.

It does not enable `ResolutionMode.DYNAMIC`, activate parameters, interpolate seasonal data, change PR1 behavior, or modify `seasonal_service`.

## Gate Categories

- `resolvable_now`: direct active proxy candidates already allowed by the read-only proxy layer.
- `requires_user_selection`: fallback, indirect, sensitivity, reference, or otherwise non-default candidates.
- `blocked_missing`: explicit missing rows retained for reporting.
- `blocked_wrong_basis`: rows whose basis must be confirmed before use.
- `blocked_no_equation_mapping`: equation-only rows that need mapping and resolved inputs.
- `blocked_time_mapping`: seasonal rows that do not overlap the generated time grid.

## Time Metadata

Each preview row includes:

- `time_basis`: `static`, `monthly`, or `daily`.
- `applicable_months`: generated grid labels where the candidate could apply.
- `seasonal_class`: `spring`, `summer`, `autumn`, or null.
- `no_interpolation`: always true.

Static candidates are listed against the generated grid but are not interpolated. Seasonal Czubaszek rows are mapped by coarse season only: spring to March-May, summer to June-August, and autumn to September-November. If the generated grid has no overlap with that class, the row is `blocked_time_mapping`.

## Ready Now

The preview can support future reporting or UI review of feedstock data readiness. Direct roadside literature rows that are already safe active proxies appear as `resolvable_now`, but this status is still report-only.

## Still Blocked

Missing, wrong-basis, and equation-only records remain blocked. Indirect extended candidates remain sensitivity-only and require explicit user selection. No midpoint is derived from ranges, and no seasonal interpolation is performed.

## Future Use

A later integration step can expose `summarize_feedstock_resolution_gates()` in a dataset readiness report. Model calculations should only consume these candidates after a separate measured-data override and user-selection workflow is implemented.
