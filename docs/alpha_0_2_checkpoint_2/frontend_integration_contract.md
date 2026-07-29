# Frontend Integration Contract

No frontend file was changed. A future client should generate controls from `GET /api/v1/parameters` or `editable_parameter_registry.csv`, not duplicate limits or scientific defaults.

Each control exposes its stable parameter ID, label, value, default, unit, input type, validated limits when available, allowed options, edit mode, provenance, warnings, rebuild requirement, and affected outputs/units/plots. A null limit means unknown, not zero or unbounded approval.

Submit scenario choices and overrides through `SimulationRequest` schema `1.0.0`. Treat validation issues with `blocking=true` as non-runnable. Display `status`, `origin`, `basis`, `warning`, and uncertainty beside numerical results so structural assumptions are not presented as measurements.

Use `ProcessGraph.nodes` and `ProcessGraph.edges` directly; do not parse Graphviz images. Use plot IDs and source-result fields rather than labels as data keys. An unavailable plot returns valid metadata and an empty series rather than fabricated zero data.

Artifact links in `export_references` are relative to the run resource. The frontend must not assume a local filesystem path or execute formula text.
