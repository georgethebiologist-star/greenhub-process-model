# Dynamic Complete Proxy Model

`Greenhub.dynamic_complete_proxy` is the complete, opt-in dynamic proxy layer.
It composes the isolated protein calculation-shadow path with drying utilities,
material-conserving AD, one selected gas route, and sequential digestate/resource
recovery. It does not modify the empirical flowsheet, seasonal service, API, or
legacy Phase 3-7 calculations.

The separate opt-in dashboard API now consumes this layer; see
[dynamic dashboard reporting](dynamic_dashboard_reporting.md). The dashboard
baseline is 30,000 t/year with a capped seasonal supply schedule and spray-dryer
utility proxy. The direct core's historical May–November/1,000 kg/h configuration
remains available. `mass_only` now excludes dryer energy explicitly, and heat
extraction honors a supplied generic recovery fraction. Historical CSV artifacts
are not automatically regenerated.

## Status and boundary

- Default months are May-November 2026 at a configurable fresh-feed basis.
- Press cake is an external system output and never enters in-project AD.
- One protein method and one gas/upgrading/energy route are active per scenario.
- Multiple resource-recovery methods may run in the configured sequence.
- With `allow_assumptions=True`, all current proxy data gaps are closed and
  `can_drive_complete_proxy_model=True` when mass ledgers close.
- `can_drive_simulation=False` and `validated_simulation_ready=False` always.

## Evidence policy

Direct project datasets are preferred. Phase 4-7 CSV values are reused only as
`greenhub_legacy_proxy_result`. Remaining closures are labelled
`engineering_assumption`. Every scalar stores its unit, policy/source ID,
certainty class, source file, and warning. The 15% protein-product moisture is a
`user_input` baseline, not measured dryer performance.

Key source-backed anchors include de-FOS whey BMP, membrane/PSA/water-scrubbing
performance, digestate separator partitions, ammonia and phosphate recovery,
clean-water recovery, and CHP efficiencies. Legacy dryer utility ratios, Phase
6 conditioning ratios, Phase 7 TAN/product ratios, and explicit assumptions fill
the still-unmeasured GreenHub closures.

## Outputs

`write_dynamic_complete_proxy_reports()` writes:

- `Greenhub/results/dynamic_complete_proxy_summary.csv`
- `Greenhub/results/dynamic_complete_proxy_streams.csv`
- `Greenhub/results/dynamic_complete_proxy_units.csv`
- `Greenhub/results/dynamic_complete_proxy_alternatives.csv`
- `Greenhub/results/dynamic_complete_proxy_assumptions.csv`
- `Greenhub/results/dynamic_complete_proxy_balances.csv`
- `Greenhub/results/dynamic_complete_proxy_blockers.csv`

Validated activation still requires project measurements for residual COD/VS
conversion, elemental routing and ionic speciation, dryer utilities, gas-system
performance at GreenHub scale, and recovered-product composition and quality.
