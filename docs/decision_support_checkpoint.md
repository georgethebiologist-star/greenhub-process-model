# GreenHub decision-support checkpoint

Updated: 2026-10-28. Active implementation; this file is a resume aid, not a completion claim.

## Current correction checkpoint (2026-10-28)

- Recovered the interrupted full-suite result: one failure in the gas-only LCA boundary fixture. Adding `water_inputs` as a required exclusion broke existing project bases. Removed that registry extension and mapped pretreatment water into existing `materials`; valid flow IDs and burden directions are retained. LCA, process-assumption and failing decision-support tests pass together (16 tests).
- Corrected dynamic raw-press undilution: subtract added water only, never scale all components down. The calculation now retains its pretreatment state for inspection; a component-by-component regression checks reconstruction and solids preservation. Route separation remains unchanged.
- Full-suite completion for these latest corrections remains pending; the earlier green suite does not verify this state. No dataset maturity promotion or full-objective completion is claimed.

## Objective and boundaries

Use the existing empirical and seasonal simulation services. Preserve scenario IDs,
uncommitted TEA work, defaults and scientific evidence gates. Post-route TEA/LCA
must not mutate the process. Missing evidence remains incomplete; balance closure
is not scientific validation. Dynamic complete proxy remains a separately labelled
opt-in mode.

## Initial repository audit

- Dirty work at start: application `__init__`, `result_service`, `tea.py`, new
  TEA modules/register/reports/tests/docs, compact workbook and its lock file.
  These are preserved and extended in place.
- Existing actual time-aware capability: `SeasonalSimulationService` carries
  inventory and rebuilds the empirical route each daily/monthly timestep.
  Continuous calibrated dynamics are not available.
- Existing `dynamic_complete_reporting_service` is an independent proxy chain;
  it must not be relabelled as calibrated dynamics.
- Existing TEA is post-route with incomplete price/capacity inputs.
- No biomass degradation attachment/package located in repository/data.
  The user has been asked for its path; independent work continues.
- Material audit findings: storage residual omitted degradation; annual reporting
  labels balance closure as validation; planned intake and actual throughput need
  distinct reporting. Baseline chemistry changes require explicit evidence.

## Ownership / implementation

- Root: request/service integration, annual reporting corrections, coherent
  decision-support facade, sensitivity/design/uncertainty/Pareto, API/UI,
  reproducible examples and final verification.
- Process agent: storage/logistics/seasonal corrections, storage batch ledger,
  scientific/evidence audit and tests.
- TEA agent: existing TEA service/register/finance/reports, price evidence,
  accounting completeness and tests.
- LCA agent: post-route inventory/climate service, characterization metadata,
  boundaries/completeness and tests.

## Pending verification

Capture static/seasonal baseline outputs; test static–dynamic steady equivalence,
storage conservation/timestep behavior, scientific status semantics, complete vs
partial accounts, immutable analysis, seeded sampling and Pareto exclusions.
Run representative real cases and existing focused tests, then UI checks.

## Checkpoint 4 progress

- Imported the completed missing-data register as a traceable source at
  `Greenhub/data/Pre-treatment/Feedstock/complete_missing_data_with_traceability.csv`.
- Added the expanded 110-row process register as the default completed-input
  source, with a 57-row comparison extract against the original register.
- Added the Netherlands/EU industrial price benchmark register and normalized
  its malformed CSV quoting. Compatible product benchmarks are exposed as
  explicit TEA screening assumptions. The user-supplied biomethane all-in range
  is now included directly in EUR/m3 (0.59-1.17, midpoint 0.88); the separate
  EUR/MWh benchmark remains excluded because no gas-energy conversion is inferred.
- Added an opt-in `financial_assumptions.use_screening_price_benchmarks` switch
  for decision-support runs. Explicit user prices override benchmark values and
  the existing default remains unchanged.
- Added an opt-in `use_screening_process_assumptions` profile sourced from the
  expanded register. It supplies storage conditions through the existing request
  contract; feedstock, pretreatment, and digestion ranges remain traceable
  profile data until their equation gates are connected. The profile is
  non-default and preserves explicit user storage settings.
- Extended the existing biomass schedule with optional `source_id` and
  `location` metadata. These values flow into the shared seasonal availability
  schedule and timestep feed records without changing default quantities or
  season dates.
- Added opt-in pretreatment controls to the dynamic BioSTEAM adapter and a
  mass-balance-safe raw-press state calculation. Raw-press reports now expose
  added water and press energy, with a timestep aggregation helper for later
  TEA/LCA integration; annualization remains schedule-gated.
- Extended pretreatment utility aggregation with explicit operating-hour input.
  Annual water and press-energy totals are now calculated only when hours are
  supplied for every timestep; otherwise the result is marked incomplete.
- Added an LCA bridge on the pretreatment state object that emits explicit
  electricity and added-water inventory rows only when an annualization factor
  is supplied. No water-treatment burden is invented without a characterization
  factor.
- Improved process-state snapshots to report optional stream density, viscosity,
  expanded biodegradable COD/carbohydrate pools, and storage age when supplied;
  unavailable analytical properties remain null rather than being filled with
  zeros.
- State snapshots now also preserve explicit numeric stream metadata for pH,
  particle size, and analytical properties when present; absent values remain
  unresolved.
- Full regression suite reached 100% after the utility/result-contract changes;
  targeted tests also pass for the new feedstock, pretreatment, TEA, LCA, and
  adapter paths.
- A later full-suite run exposed and fixed an optional-state-property regression:
  unsupported BioSTEAM density/viscosity calculations are now reported as
  unavailable instead of failing simulation execution. The repaired full suite
  again reached 100%.
- Added `Greenhub/complete_missing_data.py` to preserve numeric screening values,
  ranges, provenance, and unresolved/blocked status without converting missing
  evidence into zero.
- Hardened CSV export to union optional per-row fields, including seasonal
  terminal-gas diagnostics, and avoid machine-specific artifact paths.
- Full suite reached 100% execution with two failures fixed in the export and
  seasonal API paths; targeted regressions now pass.
- Remaining scientific limits are intentional: validated product prices,
  complete installed CAPEX, full LCA characterization, route-level TRL, and
  calibrated dynamic kinetics remain evidence-gated.
- Added a coherent opt-in dynamic pretreatment dilution basis through
  `DynamicProteinScenarioConfig.pretreatment_water_addition_kg_per_kg_wet_feed`.
  Process water is applied before pressing, normalized to the resulting diluted
  wet-feed basis, and reused by the press and all downstream report-only units.
  Provenance records the basis transformation; the empirical/BioSTEAM route and
  default zero-water behavior remain unchanged. Negative values are rejected and
  the pathway mass balance closes in targeted tests.
- Extended the LCA result declaration with explicit boundary, wet/dry-feed
  functional units, reference flows, included/excluded inventory groups, and
  allocation/substitution status. This is reporting metadata only; missing
  inventories and characterization factors remain blocked rather than being
  converted into zero impacts.
- Extended state snapshots with the first available outlet state and an explicit
  changed-property list per unit. Existing inlet fields remain unchanged; the
  additional records expose changes in flow, moisture, temperature, pressure,
  composition, COD, and other tracked properties.
- Connected adapter-level pretreatment water controls to the shared dynamic
  scenario basis when no explicit scenario object is supplied. Conflicting
  adapter/scenario values are rejected; zero remains the compatibility default.
  Calculation-shadow tests confirm the isolated empirical flowsheet remains
  unchanged while the feed record reflects the configured dilution.
- Corrected storage reaction substep integration to apply first-order conversion
  only over each incremental exposure interval. The prior cumulative-fraction
  application to an already depleted pool could overstate degradation as the
  timestep was refined; lag handling and explicit assumption gates are retained.
- Added the frontend-ready `STATE-MOISTURE` plot using existing plot contracts,
  showing inlet and outlet moisture fractions for each unit when outlet state
  data are available; unresolved outlet properties remain null.
- Expanded scenario-batch reporting with evaluated/technically-feasible counts,
  rejection reasons, and deterministic sensitivity objective deltas relative to
  the baseline. Sampling distributions, seeds, correlations, and Pareto
  eligibility rules remain unchanged and explicit.
- Corrected state-engine equation usage to reference canonical registry IDs for
  seasonal storage degradation, precipitation residence time, and protein
  precipitation recovery. The previous labels could report false fallbacks or
  misclassify precipitation efficiency as a COD equation.
- Connected calculated seasonal storage totals to the existing
  `inventory_evolution` result output, including initial, final, average, peak,
  and degradation mass. Steady-state runs retain the existing structural
  fallback when no seasonal inventory controller is present.
- Connected seasonal inlet/outlet state rows to the standard
  `process_state_history` result field. Quasi-dynamic runs now expose one
  time-stamped state record per seasonal step, while steady-state behavior is
  unchanged.
- Extended calculated seasonal inventory evolution with per-timestep inventory,
  degradation, and overflow records. The existing inventory plot now renders
  that timeline when present and retains the final-value fallback otherwise.
- Connected the opt-in press-energy assumption through the dynamic scenario and
  calculation-shadow payloads. The raw-press calculation now exposes the
  configured kWh/t wet-feed value; zero/None remains the compatibility default,
  and conflicting adapter/scenario values are rejected.
- Corrected calculation-shadow pretreatment utility reporting so configured
  process water is applied on the shared diluted feed basis exactly once. Water
  addition and press energy are reconstructed from the original wet-feed basis
  for reporting, preventing dilution from being counted again inside the raw
  press. Added regression coverage for water and energy utility totals.
- Exposed the existing frontend-ready scientific result-contract collections
  through decision-support reports under `state_outputs`: process-state
  snapshots/history, unit-state summaries, parameter sensitivity, equation use,
  component fate, utility consumption, and inventory evolution. This is a
  reporting connection only; it does not alter simulation chemistry or route
  formation.
- Updated the decision-support UI to render unit-state summaries and the
  equation, sensitivity, utility, and inventory evidence carried in
  `state_outputs`; nulls and structural fallbacks remain visibly distinct from
  measured or calculated values.
- Corrected state-engine utility reporting so an absent unit power demand is
  reported as `null` with an unavailable status instead of an inferred zero;
  explicit zero demand remains a calculated value. Added regression tests for
  both cases to prevent silent under-reporting in downstream analyses.
- Expanded the report-only dynamic AD residual ledger with explicit BMP basis
  metadata: methane potential is identified as applying to final-supernatant VS
  only, while unmodeled residual VS is reported separately. This improves
  scientific traceability without activating AD kinetics or treating the proxy
  as a validated digestion result.
- Added an opt-in quasi-dynamic AD residence-time screening calculation using
  the supplied T80/T90 BMP markers. It uses the lower implied first-order rate
  as a conservative envelope, reports conversion and methane at residence, and
  remains explicitly labelled as unvalidated screening; the default remains
  unchanged and `kinetics_run` remains false.
- Normalized benchmark price traceability into typed TEA records by extracting
  a calendar reference year while preserving the original source period label.
  This avoids passing free-form date text into typed financial metadata and does
  not change price values or benchmark activation behavior.
- Connected explicit logistics results to the LCA inventory through
  `logistics_to_lca_inventory()`. Transport activity is now visible as a
  transport flow, while the absent transport characterization factor keeps
  climate readiness incomplete rather than silently assigning zero impact.
- Added an additive TEA `logistics_result` input. When an explicit logistics
  calculation is supplied, matching logistics cost-register lines use its
  annual transport cost directly and retain a calculated-from-logistics
  provenance status; omitted logistics data remain incomplete as before.
- Propagated opt-in AD residence-time screening outputs into integrated dynamic
  step products, grid ranges, and CSV summaries: methane at residence time and
  the inferred conversion fraction are now scenario-comparable while retaining
  their explicit screening status.
- Added objective metadata to sampled Pareto fronts, including direction, unit,
  and definition for both axes. This prevents frontend reports from presenting
  a minimize objective as maximize or hiding its unit basis.
- Updated the Pareto UI to consume that metadata for axis labels, units, and
  maximize/minimize direction, keeping the sampled-feasible interpretation
  visible in the chart itself.
- Wired the existing optional logistics result through `DecisionSupportService`
  into both post-route TEA and LCA. This connects transport cost and emissions
  evidence when supplied, while preserving the prior default of no logistics
  result and leaving missing transport characterization visibly incomplete.
- Corrected the logistics-to-LCA adapter basis: `Greenhub/logistics.py` already
  applies an explicit fuel emission factor and returns kg CO2, so the adapter
  now uses the registered fossil-CO2 identity factor. Limited or unavailable
  vehicle inputs still remain incomplete; no transport factor is fabricated.
- Added an opt-in, traceable Netherlands electricity screening factor from the
  existing CBS-derived process-data register. It is not part of the default
  LCA registry, is labelled `proxy_factor`, and can be overridden by a complete
  project-specific factor record; heat and other missing factors remain blocked.
- Improved the existing sensitivity UI to display deterministic operating-profit
  and climate objective deltas, including incomplete/rejected statuses, instead
  of plotting only feed throughput. The backend sampling and API contract are
  unchanged, so TEA/LCA assumption paths remain user-selectable and traceable.
- Added an explicit UI checkbox for the Netherlands electricity screening proxy;
  it writes the existing additive `use_screening_lca_factors` configuration flag
  and remains off by default. The label states its 2024 CBS-derived proxy basis
  and the need to replace it for a project LCA.
- Added an additive `maturity_summary` to decision-support reports. It reports
  process evidence classes, TEA completeness statuses, LCA factor evidence, and
  missing-input counts without converting them into a validation score or TRL.
  The existing results UI now exposes this summary alongside raw provenance.
- Extended options-contract regression coverage so the new LCA screening factor
  and its opt-in activation guidance are exposed without changing default
  behavior.
- Exported the opt-in `screening_lca_factors` helper from the application package
  surface and added an import-level regression test, keeping the factor's proxy
  provenance unchanged.
- Corrected maturity-summary parameter counts to normalize enum evidence classes
  to their stable values, avoiding misleading `ValueStatus.*` or unspecified
  labels in exported reports.
- Extended the existing frontend request-payload check to verify both states of
  the LCA screening checkbox: the proxy flag is false by default and true only
  when explicitly selected.
- Documented the additive logistics, screening-LCA, financial-assumption, and
  climate-factor inputs in the generated decision-support OpenAPI metadata and
  added a contract regression test.
- Corrected TEA route selection so an explicitly supplied logistics result
  activates the matching `feedstock_logistics` cost record even when that
  record is not a formed process route tag. The default TEA remains unchanged
  when no logistics result is supplied, and the result is still counted once.
### Steady-state storage inventory output

Steady-state simulations with explicit `storage_conditions` now populate the existing `inventory_evolution` result contract from the storage report. The output identifies the `steady_state_storage_condition` basis, retains the reported exported mass and fate status, and leaves the time line empty because no temporal history was simulated. Average and peak are reported on the explicit steady-state basis rather than being presented as a time-resolved estimate.

### Pretreatment equation ownership

The active dynamic raw-press calculation unit now calls `apply_screening_pretreatment_state()` for process-water and press-energy calculations. Existing raw-press component-fraction routing remains unchanged. This removes duplicate equation ownership while preserving the default zero-water/unspecified-energy behavior and keeps the screening assumptions visible through the existing route payload and utility outputs.

### Pretreatment equation traceability

`equation_usage` now includes `pretreatment_water_addition` and `pretreatment_press_energy`, linked to the canonical `phase3.pretreatment.*` parameter IDs. Each record reports whether the parameter was available and used or whether the route remained a structural fallback. This makes the active pretreatment equations visible through the existing simulation, export, and decision-support result contracts.

