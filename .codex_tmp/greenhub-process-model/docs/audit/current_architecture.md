# Current Architecture

> Alpha checkpoint update: `Greenhub/integration.py` now provides a compatibility-first
> process-area facade over this unchanged connected graph. Historical factories remain
> the calculation implementation; no module move or scenario rename was performed.

Audit date: 2026-07-29

## Execution Path

```text
greenhub_feed_inputs.xlsx
  -> phase-specific input loaders
  -> feed characterization and reconciliation
  -> create_phase7_scenario
       -> create_phase6_scenario
            -> create_phase5_scenario
                 -> create_phase4_scenario
                      -> create_phase3_scenario
  -> one BioSTEAM flowsheet and one System graph
  -> simulate upstream-to-downstream units
  -> phase-specific validation/metrics refresh
  -> Phase 7 validation, metrics, comparison and seasonal reporting
```

The recursion is software composition, not separate physical systems. The selected
Phase 7 model's `system.units` contains all 51 active units in one connected BioSTEAM
System. This satisfies integrated simulation but obscures process-area access behind
four `upstream_model` links.

## Model Containers

| Container | Responsibility | Integration relationship |
|---|---|---|
| `GreenHubModel` | Historical T101/S101 foundation | Independent compatibility builder |
| `Phase3Model` | Feedstock preparation and separation | Base model for later scenarios |
| `Phase4Model` | Protein recovery | Wraps `Phase3Model` |
| `Phase5Model` | Anaerobic digestion | Wraps `Phase4Model` |
| `Phase6Model` | Biogas conditioning/upgrading | Wraps `Phase5Model` |
| `Phase7Model` | Nutrient recovery and final system | Wraps `Phase6Model` |

## Process-Area Mapping

| Preferred area | Current unit IDs/classes | Current API |
|---|---|---|
| Feedstock and Characterization | feed specification, characterization result, no physical unit | nested Phase3 attributes |
| Feed Preparation and Primary Separation | U101, U201, S201, C301 | `create_phase3_scenario` |
| Protein Recovery | M401, H401, R401, C401, W401, D401, DR401, M402, M403 | `create_phase4_scenario` |
| Anaerobic Digestion | M501, H501, R501, V501 | `create_phase5_scenario` |
| Biogas Upgrading | G601-S601-R601-R602-F601 and selected BG equipment | `create_phase6_scenario` |
| Nutrient Recovery | T701 through V741 plus route mixers | `create_phase7_scenario` |
| Shared Utilities | BioSTEAM heat/power utilities; no active CHP network | no process-area object |
| Integrated GreenHub System | all selected units | `create_phase7_scenario`; `main.py` |

## Architectural Risks

1. `create_greenhub_system` sounds canonical but creates only T101/S101.
2. Normal user-facing text, system IDs, workbook sheets, reports, and dataclasses expose
   development phase numbers.
3. Process areas are not directly addressable from `Phase7Model`.
4. Reporting is richest for the terminal phase and does not provide a single concise
   process-area index.
5. The active flowsheet ID originates in the Phase 3 builder even when the complete
   graph includes all later areas.
6. Imports are broad and `systems.py` is nearly 2,000 lines; moving code now would risk
   circular imports and compatibility regressions.

## Safe Target

Add an integrated facade and named process-area views without moving existing modules.
Preserve all phase factories and scenario IDs. Mark the old two-unit
`create_greenhub_system` behavior in migration documentation before any future rename.
Only after facade and equivalence tests pass should implementation modules move into
process-area packages.
