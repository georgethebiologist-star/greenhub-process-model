# Baseline Dynamic Operational Scenario

## Status

`Greenhub.dynamic_process` is an opt-in, report-only process preparation layer.
It creates typed Python stream and unit results, not BioSTEAM streams. It does
not alter empirical feed profiles, seasonal simulations, API behavior, TEA,
LCA, or anaerobic-digestion calculations.

## Process Order

1. Resolve the time-aware dynamic feedstock bundle.
2. Build whole-feed Water, protein, sugar, ash, fiber, and residual pools.
3. Preview mechanical partitioning and adapt it to a raw two-stream boundary.
4. Send brown juice to the first centrifugation.
5. Route clarified juice to protein extraction and cell debris to residual use.
6. Split extraction output into protein-rich phase and extraction supernatant.
7. Use the second centrifugation to form wet protein cake and final supernatant.
8. Dry the wet protein cake by removing Water only.
9. Combine cell debris and final supernatant as a future biogas-feed candidate.
10. Record press cake as an external-scope system output; never route it to the in-project biogas candidate.

## Raw Press Boundary

The source yields `0.395` press cake, `0.568` brown juice, and `0.037` protein
concentrate describe a boundary that includes downstream protein recovery. The
baseline raw-press adapter therefore does not expose protein concentrate as an
active raw output. For the blocked source benchmark preview, brown juice and
concentrate are recombined to a `0.605` kg/kg-feed liquid precursor while press
cake remains `0.395` kg/kg feed.

This recombination closes total mass but cannot recover unknown component
identities. The result reports `overall_closes=True`, `identity_closes=False`,
and preserves unresolved mass and component blockers. An explicit raw-press
policy can instead route every feed component conservatively between cake and
brown juice.

SolubleProtein belongs in brown juice when an explicit press partition sends it
there. SuspendedProtein, particulate solids, and structural fibers may be sent
to press cake or captured as cell debris by explicit policies. Mechanical
pressing never sends SolubleProtein directly to a protein product in this
baseline pathway.

## Separation Logic

The first centrifugation preferentially captures SuspendedProtein,
SuspendedSolids, and cell-debris pools when fractions are supplied. SolubleProtein
and sugars remain in clarified juice except for explicit losses.

Protein extraction consumes clarified juice. Recovered SolubleProtein enters a
protein-rich phase; unrecovered protein, sugars, and unspecified Water remain in
the extraction supernatant. The second centrifugation captures the protein-rich
phase as wet protein cake and routes losses to final supernatant. Drying changes
only Water mass and reports missing energy data separately.

Final supernatant and cell debris are combined without running AD. Press cake is
always excluded from this in-project residual route; any future press-cake use
requires a separate external-scope scenario and report.

## Conservative And Demo Policies

The default orchestrator supplies no centrifugation, extraction, recovery, or
drying coefficients. It returns pass-through/empty partial streams with blockers
instead of inventing values. `can_drive_simulation` remains `False`.

`demo_baseline_operational_policy()` provides illustrative engineering fractions
for end-to-end mass movement. Every assumption is labelled
`demo_engineering_assumption`, is not a project default, and does not activate
simulation. The demo closes total and component identity but still lacks COD,
BMP, biodegradability, nutrient speciation, validated equipment performance,
drying energy, and measured recovery coefficients.

## Activation Blockers

- Paired raw-feed, press-cake, and raw-juice component partitions.
- First-centrifuge solids and protein capture measured on GreenHub material.
- Clarified-juice protein recovery, co-precipitation, Water split, and acid data.
- Second-centrifuge protein loss and wet-cake moisture measurements.
- Drying target and measured energy demand.
- COD, BMP, biodegradability, and nutrient speciation for residual streams.
