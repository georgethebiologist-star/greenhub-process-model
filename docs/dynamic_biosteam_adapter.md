# Dynamic BioSTEAM shadow adapter

`Greenhub.dynamic_biosteam_adapter` is the isolated handoff between the
report-only dynamic protein pathway and BioSTEAM-compatible material streams.
It does not connect to the empirical flowsheet, seasonal service, API, or any
active process system.

## Behavior

- One-step mode adapts one monthly `DynamicPathwayPreview` on an explicit feed
  basis, with `1000 kg/h` as the default.
- Grid mode builds seven independent May-November 2026 shadow stream sets. It
  is a batch preview, not a scheduled dynamic BioSTEAM simulation.
- Exact GreenHub components are assigned to BioSTEAM streams. `fructan`,
  `residual_unallocated_dry_matter`, and any other unresolved pools remain in
  parallel adapter records and are never hidden as chemicals.
- Every named stream is registered only inside a temporary dynamic flowsheet.
  The prior main flowsheet is restored and checked after each build.
- Press cake remains an external-scope output. The in-project biogas candidate
  remains cell debris plus final supernatant only.

## Outputs

The report writer creates:

- `Greenhub/results/dynamic_biosteam_adapter_streams.csv`
- `Greenhub/results/dynamic_biosteam_adapter_balance.csv`
- `Greenhub/results/dynamic_biosteam_adapter_provenance.csv`

## Activation boundary

The adapter proves mass scaling, component identity, metadata preservation,
and registry isolation. `can_drive_simulation` and
`validated_simulation_ready` remain false. Real BioSTEAM unit operations still
need validated separation policies, energy/utility models, operating-state
logic, and an explicit opt-in system factory. `DynamicBioSTEAMUnitSpec` records
that future handoff without implementing those units.
