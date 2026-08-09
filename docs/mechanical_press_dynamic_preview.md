# Dynamic Mechanical Press Preview

## Scope and status

`Greenhub.mechanical_separation` is an opt-in, report-only bridge between the
whole-feed `DynamicFeedstockPools` object and a future dynamic separation unit.
It is not imported by the empirical simulation path, does not create model
overrides, and is not connected to `seasonal_service` or the API.

The current three-output boundary is not a raw press alone. It covers small-scale
fractionation followed by fermentation/protein precipitation, with final streams
named press cake, brown juice, and protein concentrate. Brown juice must therefore
not be interpreted as untreated green juice.

## Evidence files used

- `greenhub_mechanical_pretreatment_pressing_data.csv` supplies the clover-grass
  final-stream mass yields: press cake `0.395`, brown juice `0.568`, and protein
  concentrate `0.037` kg/kg fresh feed.
- `greenhub_mechanical_separation_component_partitioning.csv` supplies typed
  component-partition candidates and their traceability fields.

The loader preserves source and record IDs, material, process boundary, basis,
transferability, confidence, source notes, and the original partition text. Rows
with a range instead of a scalar, an incompatible boundary, an incompatible
product stream, or an incompatible basis are retained as `blocked_report_only`.
No range midpoint is calculated.

## Current mapping decision

The clover-grass records matching the `0.395/0.568/0.037` yields provide complete
three-stream records for total solids, volatile solids, carbon, total nitrogen,
total phosphorus, total potassium, total sulfur, and water.

Only Water has an exact GreenHub component mapping. Its source fractions are:

| Record | Stream | Source fraction |
|---|---|---:|
| `MSP_0125` | press cake | 0.313008 |
| `MSP_0126` | brown juice | 0.667882 |
| `MSP_0127` | protein concentrate | 0.036122 |
| | total | 1.017012 |

The source explicitly says not to renormalize this analytical closure. The
preview therefore preserves these values, flags all three records, and leaves
Water unmapped. This satisfies the rule that applied component allocations must
conserve mass without silently changing evidence.

TS, VS, and elemental C/N/P/K/S remain evidence metadata. They cannot be applied
to individual Ash, protein, sugar, cellulose, hemicellulose, lignin, or residual
dry-matter pools without an additional allocation assumption.

## Components and pools still blocked

- SolubleProtein and SuspendedProtein lack separate source-backed partitions at
  the selected boundary.
- Total-protein records are ranges, incomplete stream recoveries, or belong to
  raw/repeated alfalfa pressing boundaries. They are not applied.
- Sucrose, Glucose, Fructose, and metadata-only fructan lack WSC or individual
  sugar partitions.
- Ash lacks a matching total-ash partition; elemental nutrient partitions are
  not equivalent to total Ash.
- Cellulose, Hemicellulose, and Lignin lack complete matching fiber partitions.
- Residual unallocated dry matter remains an explicit unmapped whole-feed pool.
- `hexose_subtotal` remains metadata because its mass is already represented by
  the Glucose and Fructose component pools.

## Total-protein fallback

`TotalProteinPartitionFallbackPolicy` exists only as an explicit opt-in marker.
If a future complete total-protein partition is reviewed, this policy can permit
the same stream split to be applied to soluble and suspended protein. That action
must carry a rationale and warning because the source did not observe protein
solubility classes. No fallback is constructed or enabled by default.

## Preview outputs

`preview_mechanical_separation(...)` returns:

- product-stream masses in kg/kg fresh feed;
- applied component masses by stream in kg/kg fresh feed;
- unmapped component masses and metadata-only pools;
- per-component mass-balance residuals;
- blocked source record IDs, warnings, and partition provenance;
- `can_drive_simulation`, which remains false while any required partition or
  required metadata-only pool is unmapped, or any selected evidence is blocked.

Explicit caller-supplied component partitions remain available for scenario
testing. They must contain finite, nonnegative shares summing to one and are
labelled `explicit_caller_input`; they are not model defaults.

## Implemented preparation layer

The backend now also provides:

- `summarize_press_partition_evidence()` and deterministic CSV/Markdown audit
  writers;
- `PressComponentPartitionPolicy`, `PressComponentPartitionRule`, and
  `PressPartitionPolicyBuildResult`;
- `build_conservative_press_partition_policy()` with all fallback policies off
  by default;
- explicit Water-closure, total-protein, total-WSC, and fiber fallback policy
  objects;
- stream component and metadata-pool masses, per-component residuals, and
  per-stream assigned/unassigned mass summaries;
- `DynamicPressPreviewBundle` and a JSON-safe extraction-readiness adapter in
  `Greenhub.dynamic_press`.

The generated `dynamic_press_preview` artifacts use an explicitly enabled,
report-only Water closure policy to demonstrate the pathway. This does not
change the conservative default or activate normal simulations.

Generated artifacts:

- `Greenhub/results/mechanical_partition_evidence_summary.csv`
- `Greenhub/results/dynamic_press_preview.csv`
- `Greenhub/results/dynamic_press_stream_components.csv`
- `docs/mechanical_partition_evidence_summary.md`
- `docs/dynamic_press_preview.md`

## Activation blockers

Activation requires one boundary-consistent grass or grass-clover experiment
with conservative partitions for water, soluble/insoluble protein, WSC sugars,
ash/minerals, structural fibers, and residual dry matter. A raw press scenario
also requires yields that exclude downstream precipitation/recovery. Until then,
the dynamic press object is useful for evidence review and architecture testing,
but cannot drive seasonal or BioSTEAM calculations.
