# Proxy-enabled dynamic protein pathway

## Scope

This backend path is opt-in and report-only. It does not modify the empirical
BioSTEAM model, seasonal service, API, or frontend. The active sequence is:

`whole feed -> raw press -> brown juice -> first centrifuge -> selected protein recovery -> second centrifuge -> drying`

Press cake is always a GreenHub system output with external downstream scope.
Only cell debris and final supernatant form the in-project biogas-feed candidate.

## Method selection

Isoelectric precipitation is the baseline. Lactic-acid recovery, membrane
recovery, heat, and caller-defined generic recovery are mutually exclusive
alternatives. `select_dynamic_protein_extraction_method()` returns one policy;
it never blends methods.

## Evidence used in proxy mode

- `MSP_0150`: 40% alfalfa total-protein recovery to juice. It is applied to
  `SolubleProtein` and `SuspendedProtein` only as an explicit total-protein
  proxy. The unresolved press composition remains unresolved bulk.
- `CAP-ALF-001`: greater-than-80% soluble white-protein retention in heat-treated
  alfalfa juice. The preview uses 80% as a conservative scenario bound, not as a
  point estimate. Particulate capture remains missing.
- `REC-001`: 0.34 of incoming grass-clover juice nitrogen precipitated at pH
  4-4.5. It routes `SolubleProtein` only when both proxy mode and the explicit
  N-to-protein permission are enabled.
- `LOSS-001`: 0.31 free-amino-acid nitrogen is retained as loss metadata; it is
  not subtracted a second time from the `REC-001` recovery.
- `PR-005`: 0.151 alfalfa whole-plant protein recovery can support a lactic-acid
  scenario bound, but is not clarified-juice evidence.
- `REJ-001`: 0.52 apparent crude-protein rejection in fresh clover-grass juice
  can support a membrane retention proxy. Rejection is not validated retentate
  mass recovery.
- `BMP_DFOS_VS`: 0.52028 m3 CH4/kg VS is attached only as de-FOS-whey proxy
  metadata for the supernatant-like residual. Methane is not calculated because
  residual VS and biodegradability are unresolved.

Every applied proxy retains source title/ID, DOI or URL, original material,
process boundary, basis, transferability, proxy class, and a non-validation
warning in policy provenance.

## Current blockers

The conservative pathway still blocks unsupported routing. Closed proxy mode can
produce an inspectable dried product, but it is not validation: soluble versus
suspended protein pressing, first-centrifuge component selectivity,
centrifuge-only precipitated-protein capture, sugar/ash/fiber fine splits, and
dryer energy still lack direct GreenHub evidence.

`can_drive_simulation` remains false. `can_drive_proxy_preview` also remains
false until all required protein-pathway mass-routing blocks resolve. No TEA,
LCA, AD kinetics, model override, or normal dynamic-mode activation occurs.

## Closed proxy preview mode

`preview_closed_proxy_dynamic_protein_pathway()` explicitly selects
`DynamicProxyClosurePolicy`. Source-backed proxy values remain separate:
`RAW_0001-RAW_0016` for the direct PRG raw-press boundary,
`CEN_0011/CEN_0013` for the alfalfa sediment proxy, `CAP-ALF-001` for
soluble-protein retention, `PCEN_0003` for direct PRG wet-cake moisture,
`REC-001` for isoelectric recovery, and `BMP_DFOS_VS` for supernatant-like
residual BMP.

Unsupported component-level splits, extraction slurry Water, centrifuge-only
protein/ash capture, and residual VS classification use explicit
`engineering_proxy_closure` values. Their provenance states that they exist only
to close the report-only preview and are neither measured nor literature
validated. Dryer energy remains missing.

Closed mode produces press cake, brown juice, clarified juice, protein-rich
phase, wet protein cake, dried protein product, evaporated Water, and a residual
biogas-feed candidate with component identity and total mass closure.
`can_drive_proxy_preview=True`, while `validated_simulation_ready=False` and
`can_drive_simulation=False`. COD, biodegradability, nutrient speciation, dryer
energy, and AD kinetics remain unresolved.

## New source-backed blocker reductions

- `raw_press_lolium_perenne_2025` uses `RAW_0001-RAW_0003` for direct PRG fresh
  stream yields, `RAW_0010-RAW_0011` for bulk DM routing, `RAW_0012-RAW_0013`
  for total crude-protein routing, and `RAW_0014-RAW_0016` for Water. Neither
  fresh-mass nor Water closure is normalized. The component-resolved
  `raw_press_unrecovered_process_mass` stream preserves losses/hold-up. Total CP
  is applied to both protein classes only as a labelled proxy; sugars, Ash, and
  fiber-species routing remain engineering closure.
- `centrifuge_alfalfa_raw_debris_3500g_proxy` uses `CEN_0011` for wet sediment
  yield and `CEN_0013` for sediment DM. These B-class alfalfa values constrain
  debris mass and DM, while component allocation within that sediment remains
  proxy closure. `CAP-ALF-001` still provides only an alfalfa soluble-protein
  retention bound.
- `second_centrifuge_prg_pH3_5_21000g` uses direct PRG `PCEN_0003` wet-cake
  moisture of 0.781. `PCEN_0010` is available only as an opt-in 0.90 lower-bound
  envelope for combined precipitation plus centrifugation and is never treated
  as pure centrifuge capture.
- Drying target moisture is an explicit scenario input. Closed proxy mode uses
  the frontend-ready baseline `target_moisture_fraction=0.15`, labelled
  `scenario_input_baseline`; callers may pass an explicit override, labelled
  `scenario_input_override`. Neither is measured drying performance. Drying
  removes only Water and dryer energy remains missing.

The optional `raw_press_red_clover_cp_ash_sugar_proxy` policy is available but
inactive by default. It retains its legume warning and does not invent a cake
sugar closure where the source reports no determination.

## Grid-level scenario runner

`DynamicProteinScenarioConfig` and `run_dynamic_protein_scenario_grid()` run the
closed proxy pathway independently for each generated month. The default grid
is May-November 2026 and uses `raw_press_lolium_perenne_2025`,
`centrifuge_alfalfa_raw_debris_3500g_proxy`, and
`second_centrifuge_prg_pH3_5_21000g`, with isoelectric recovery and the explicit
drying target-moisture input `0.15`.

`write_dynamic_protein_scenario_grid_reports()` writes
`dynamic_protein_grid_summary.csv`, `dynamic_protein_grid_streams.csv`,
`dynamic_protein_grid_units.csv`, and `dynamic_protein_grid_blockers.csv` under
`Greenhub/results/` by default. Reports retain monthly policy IDs, evidence
classes, source/record IDs, warnings, blockers, streams, and component masses.
The runner remains opt-in and report-only: it creates no BioSTEAM streams,
model overrides, service integration, or global dynamic-mode activation.
