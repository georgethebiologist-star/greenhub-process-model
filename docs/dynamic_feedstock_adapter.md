# Dynamic Feedstock Adapter

## Scope

The dynamic feedstock adapter is an opt-in, preview-only translation from validated `DynamicFeedstockInputBundle` objects to feed-profile-compatible rows. Calling the adapter does not register a `FeedProfile`, create model overrides, enable dynamic resolution mode, or change empirical and seasonal simulations.

## Mappings Available Today

- `moisture_wet_basis` becomes the feed-profile `moisture_fraction`. The existing seasonal feed-profile completion logic would interpret this as the `Water` wet-mass fraction, but the adapter does not call that logic.
- `ash_dry_basis` maps to the existing `Ash` pseudo-component. Its wet-feed mass fraction is `ash_dry_basis * total_solids_wet_basis`.
- `total_protein_dry_basis` remains metadata by default because the current feed contains separate `SolubleProtein` and `SuspendedProtein` pools and no reviewed allocation between them exists.
- `extractive_sugars_dry_basis` remains metadata by default because the `soluble_sugars` component group contains several species and no reviewed species allocation exists.

Caller-owned protein and sugar allocation maps may be passed explicitly for preview evaluation. The adapter validates that allocations sum to one and target only the existing initial-feed protein pools or soluble-sugar component group. These allocations are not persisted as project defaults.

An optional `DynamicFeedstockPoolPolicy` may instead build whole-grass protein, WSC, structural-fiber, ash, water, and residual pools before any press split. This leaves the default adapter unchanged when no policy is supplied. See `docs/dynamic_feedstock_pooling.md`.

## Metadata-Only Fields

`total_solids_wet_basis` is retained as conversion metadata after supporting dry-to-wet basis calculations. `volatile_solids_dry_basis`, `carbon_dry_basis`, `nitrogen_dry_basis`, and `sulfur_dry_basis` remain aggregate validation metadata because no one-to-one component mappings exist. `bulk_density` remains a physical-property field.

Every unmapped field remains in `metadata_fields` and `unmapped_fields` with its value, unit, evidence class, confidence, and provenance. A warning explains why it was not converted.

## Readiness Flag

`can_drive_simulation` is false by default because protein and sugar mappings are unresolved. It can become true only when all required mappings are explicit, all required values resolve, moisture and TS reconciliation is valid, mapped wet-feed fractions do not exceed one, and no invalid measured-data rows are present. A literature-pooled row remains false because fructan, combined hexose, and residual dry matter have no exact components. This flag describes adapter-row completeness only; no simulation service consumes it.

## Before Seasonal Integration

Seasonal integration requires reviewed project rules for soluble/suspended protein allocation and soluble-sugar speciation, a policy for completing the remaining dry-matter fraction, measured-data acceptance review, a dedicated opt-in request contract, and regression tests proving the empirical feed profile and normal seasonal service remain unchanged.
