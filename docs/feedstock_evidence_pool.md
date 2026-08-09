# Feedstock Evidence Pool

`build_feedstock_evidence_pool()` creates one report-only table for feedstock evidence. It does not activate calculations, create `model_overrides`, change empirical defaults, or select values for the model.

## Included Evidence

- measured project data supplied by the caller
- user overrides supplied by the caller
- direct literature rows
- derived literature rows
- indirect proxy rows
- engineering assumptions from the feedstock assumption register
- missing rows

## Required Flags

Each row includes:

- `canonical_field`
- `parameter_id`
- `value`, `value_min`, `value_max`, `raw_value`
- `unit`
- `source`
- `certainty_class`
- `use_status`
- `confidence_score`
- `requires_user_confirmation`
- `limitation_note`

## Certainty Classes

- `measured_project`: 1.0
- `direct_literature`: 0.75
- `derived_from_literature`: 0.65
- `indirect_proxy`: 0.4
- `engineering_assumption`: 0.25
- `user_override`: 0.5 by default, 0.6 when source metadata is supplied
- `missing`: 0.0

Confidence scores are reporting metadata only. They must not change calculations until a separate activation path is designed and tested.

## Use Status

- `report_only_candidate`: visible for review, not active
- `requires_confirmation`: needs explicit user or reviewer acceptance
- `reference_only`: useful context but not a candidate default
- `blocked_report_only`: visible as a gap, not usable for activation

This pool simplifies future activation by letting measured data, literature, proxies, assumptions, overrides, and missing rows share one JSON-safe shape while keeping activation decisions explicit.
