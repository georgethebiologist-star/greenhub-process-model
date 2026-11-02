# Feedstock Resolution Modes

GreenHub feedstock resolution modes are independent. The current empirical model path remains the default and is not overwritten by proxy or dynamic report layers.

## Modes

- `empirical_existing`: current GreenHub empirical behavior. This is the default calculation path.
- `measured_project_data`: future project or lab measurements. These outrank proxies only inside the report-only resolver for now.
- `literature_proxy_static`: static literature proxy review path. It does not replace empirical defaults.
- `dynamic_time_aware_report_only`: current time-grid-aware preview for reports and readiness displays. It does not interpolate or activate calculations.
- `dynamic_time_aware_active_future`: documented future mode. It is blocked and not selectable for calculations.
- `expert_override`: future user-owned, high-risk override path requiring explicit provenance, review, and guard tests.

## Current Default

`default_feedstock_resolution_mode()` returns `empirical_existing`.

## Safety Rules

- Dynamic modes must not overwrite empirical defaults.
- `dynamic_time_aware_active_future` is not calculation-ready.
- Measured project data outranks proxies only in report-only resolution scaffolding.
- Expert overrides are user-owned and high-risk.
- No mode in `Greenhub/feedstock_resolution.py` is connected to `seasonal_service`, the parameter resolver, API selection, frontend, or model calculations.
