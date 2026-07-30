# GreenHub Repository Inventory

Audit date: 2026-07-29

## Scope And Instructions

The active scientific scope is `Greenhub/`, `tests/`, `docs/`, repository-root
scientific configuration, and the prompt files explicitly available in the current
Codex task. No `AGENTS.md` file was found and `.agents/` contains no files.

The protected `frontend/`, `api/`, and `backend/` directories were not entered,
searched, modified, imported, or connected. Environment, IDE, cache, Git-internal,
and temporary directories were not modified.

## Inventory Summary

| Item | Count | Evidence |
|---|---:|---|
| GreenHub Python modules | 60 | `Get-ChildItem Greenhub -Filter *.py` |
| Python source lines | 20,874 | line count of the 60 modules |
| Test modules | 130 | `Get-ChildItem tests -Filter test_*.py` |
| Collected tests | 262 | `pytest --collect-only -q --disable-warnings` |
| Existing methodology documents | 9 | `docs/*.md` before this audit |
| Protein-recovery scientific CSVs | 17 | `Greenhub/data/Protein recovery/*.csv` |
| Master-workbook sheets | 14 | `greenhub_feed_inputs.xlsx` inspection |

## Active Scientific Architecture

| Responsibility | Current files | Status |
|---|---|---|
| Thermodynamics and material metadata | `chemicals.py`, `component_metadata.py`, `component_groups.py` | Active |
| Feedstock and characterization | `input_data.py`, `input_schema.py`, `characterization.py`, `analytical.py`, `reconciliation.py` | Active |
| Foundation storage/separation | `streams.py`, `units.py`, `separator.py`, early portion of `systems.py` | Compatibility path |
| Feed preparation and primary separation | `phase3_inputs.py`, `phase3_units.py`, `phase3_metrics.py`, `phase3_validation.py`, `phase3_reporting.py` | Active |
| Protein recovery | `phase4_*` modules and `systems.py` factories | Active for PR0-PR3; PR4-PR6 data-gated |
| Anaerobic digestion | `phase5_*` modules and `systems.py` factories | Active for AD0-AD3; AD4-AD5 data-gated |
| Biogas conditioning/upgrading | `phase6_*`, `phase6_upgrading.py`, `systems.py` | BG0 and BG2-BG5 active; BG1/BG6 data-gated |
| Nutrient recovery | `phase7_*`, `phase7_systems.py` | NR0-NR7 active structural models |
| Integrated executable | `main.py` | Builds the complete selected Phase 1-7 graph |
| Tests | `tests/`, `pytest_shard_plugin.py` | 262 passing baseline tests |

## Data And Output Locations

- `Greenhub/data/greenhub_feed_inputs.xlsx` is the active 14-sheet master workbook.
- `Greenhub/data/greenhub_feed_inputs_phase*_backup.xlsx` are historical workbook
  snapshots; they are not runtime inputs.
- `Greenhub/data/Protein recovery/` contains 17 flat CSV datasets and three Markdown
  descriptions. No current Python module loads these CSVs.
- `Greenhub/results/` contains generated reports from the historical phase entrypoints
  and the current integrated Phase 7 run.

## Entry Points And Compatibility

- `python -m Greenhub.main` is the active complete-model workflow.
- `create_phase3_scenario`, `create_phase4_scenario`, `create_phase5_scenario`,
  `create_phase6_scenario`, and `create_phase7_scenario` remain public.
- `create_greenhub_system` currently builds only the historical T101/S101 foundation.
  Its name is therefore misleading for alpha users, but changing it directly would be
  a breaking change.

## External Material Required

- The pre-snapshot Git repository containing incremental Phase 1-7 commits.
- Any phase transition patch that reportedly contained approximately 7,000 insertions
  and 14,000 deletions.
- Laboratory files, vendor quotations, calibration notebooks, or source PDFs not
  present in the allowed repository tree or current task attachments.

