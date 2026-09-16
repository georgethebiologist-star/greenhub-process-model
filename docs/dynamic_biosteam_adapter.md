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
- `Greenhub/results/dynamic_biosteam_shadow_units.csv`
- `Greenhub/results/dynamic_biosteam_shadow_system_balance.csv`

## Shadow unit system

The adapter now builds a real, isolated `bst.System` containing six report-only
units: raw press, first centrifuge, selected protein extraction, second
centrifuge, protein dryer, and residual mixer. Each unit executes `_run()` and
writes exact-component targets from the already validated dynamic pathway.
The units do not yet own partition equations, kinetics, design, utilities, or
costing.

All stream and unit IDs use a `dyn_<time_label>_` prefix. The raw press retains
press cake and unrecovered process mass as terminal outputs. The residual mixer
accepts only cell debris and final supernatant. Metadata-only pools remain in
parallel adapter records and are not assigned to BioSTEAM chemicals.

One system is built per month for May-November 2026. These are independent
shadow systems, not a continuous dynamic schedule. Temporary flowsheet
switching is locked, and the previous empirical stream, unit, and system
registries are compared by object identity after every build.

## Calculation-owning shadow system

The opt-in `calculation_shadow_system_report_only` mode now runs six separate
`bst.Unit` calculations. Typed payloads are extracted from the resolved dynamic
scenario: raw-press component partitions, first-centrifuge capture fractions,
isoelectric soluble-protein recovery, second-centrifuge wet-cake moisture,
dryer target moisture, and the residual-mixer boundary. The units calculate
their outputs from their inlet streams; they do not store target output masses.

The baseline isoelectric route uses the explicitly permitted `REC-001` N-to-
protein proxy, `PCEN_0003` wet-cake moisture, and the scenario target of 15%
product moisture. Lactic-acid (`PR-005`) and membrane (`REJ-001`) routes are now
calculation-owning proxy alternatives and retain parity with their respective
`dynamic_process` records. Heat remains blocked; generic recovery requires an
explicit caller policy. Methods are mutually exclusive and never blended.

Grid reports are written to:

- `Greenhub/results/dynamic_biosteam_calculation_units.csv`
- `Greenhub/results/dynamic_biosteam_calculation_balance.csv`
- `Greenhub/results/dynamic_biosteam_calculation_parity.csv`

## Activation boundary

The adapter proves mass scaling, component identity, metadata preservation,
unit topology, target-output parity, and registry isolation.
`can_drive_simulation` and `validated_simulation_ready` remain false. The
calculation-owning units reproduce `dynamic_process.py`, but their policies
still contain literature proxies and engineering closure. Project-measured
separation policies, dryer energy/utilities, operating-state logic, and an
explicit guarded activation runner are still required.
