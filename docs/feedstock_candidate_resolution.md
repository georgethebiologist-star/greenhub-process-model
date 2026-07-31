# Feedstock Candidate Resolution

`Greenhub/feedstock_resolution.py` includes a controlled, report-only resolver for feedstock proxy candidates.

This is a bridge toward future dynamic gates. It does not enable `ResolutionMode.DYNAMIC`, modify `seasonal_service`, create model overrides, activate parameters, interpolate seasonal data, or derive midpoint values from ranges.

## Resolver Functions

- `resolve_feedstock_candidate(canonical_field, time_label, mode="report_only", allow_indirect=False)`
- `resolve_feedstock_candidates_for_grid(canonical_fields, time_labels, mode="report_only", allow_indirect=False)`
- `validate_measured_feedstock_overrides(overrides)`
- `resolve_with_measured_overrides(canonical_field, time_label, measured_overrides, mode="report_only")`
- `feedstock_resolution_to_report_rows(records)`

Only `report_only` mode is accepted.

## Independent Resolution Modes

These modes are named for planning and reporting. They are independent tracks; dynamic modes must not overwrite empirical defaults.

- `empirical_existing`: the current GreenHub empirical behavior. This remains the default calculation path and is not changed by feedstock proxy reports.
- `measured_project_data`: future GreenHub lab/project measurements. These can outrank proxies in report-only resolution once validated, but do not enter calculations from this module.
- `literature_proxy_static`: static direct or fallback literature proxy values for review and reporting.
- `dynamic_time_aware_report_only`: time-grid-aware preview and candidate selection. This is the only dynamic mode currently scaffolded.
- `dynamic_time_aware_active_future`: reserved future calculation mode. It is not implemented or enabled.
- `expert_override`: reserved future manually approved override path with explicit provenance and guard tests.

The current resolver helpers are deliberately report-only and empirical-safe. They do not write `model_overrides`, do not call the parameter resolver, and do not change existing empirical model outputs.

## Resolution Hierarchy

1. `measured_project_data`
2. `direct_literature_proxy`
3. `fallback_literature_proxy`
4. `sensitivity_only_indirect_proxy`, only when `allow_indirect=True`
5. blocked candidates

Indirect and sensitivity candidates require explicit opt-in. Missing, wrong-basis, no-equation, and time-mapping failures return blocked reasons instead of values.

## Measured Overrides

`MeasuredFeedstockOverride` is a report-only structure for future GreenHub laboratory or project measurements. It includes `canonical_field`, `value`, `unit`, optional `time_label`, `source_id`, `lab_reference`, and `notes`.

Measured overrides outrank all literature and proxy candidates when valid. Validation currently checks:

- source or lab metadata is present; missing metadata is flagged in warnings
- the override unit matches the expected canonical unit from the candidate inventory
- wrong units return `requires_basis_conversion` and do not expose a selected value

Static overrides apply to any requested `time_label`. Time-specific overrides apply only to their matching label. They still do not enter model calculations.

## Returned Record

Each resolution record includes:

- `canonical_field`
- `time_label`
- `selected_parameter_id`
- `value`, `value_min`, `value_max`, and `unit`
- `source_priority`
- `resolution_status`
- `blocked_reason`
- `requires_user_selection`
- `provenance`

Blocked records and user-selection-only records do not expose a selected value for calculation.

`feedstock_resolution_to_report_rows()` deliberately returns report rows only. It does not include a `model_overrides` key.

## Remaining Activation Work

Before any calculation can consume these records, GreenHub still needs measured-data override handling, explicit user-selection workflow, unit/basis validation at the model boundary, and dedicated tests proving no blocked or indirect rows can enter `model_overrides` accidentally.
