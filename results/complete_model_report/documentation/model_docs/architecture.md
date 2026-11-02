# GreenHub Architecture

## Runtime Sequence

```text
Master Excel workbook
-> validated input bundles
-> feed characterization
-> historical scenario factories
-> one connected BioSTEAM flowsheet and System
-> process-area facade
-> simulation and nested validators
-> metrics
-> integrated and compatibility reports
```

`Greenhub.integration.create_integrated_greenhub_system()` is the canonical alpha builder. It delegates construction to the tested nutrient-recovery factory and does not duplicate unit calculations. The recursive Python dataclasses are compatibility containers; their units belong to one BioSTEAM graph, one flowsheet, and one final `System`.

## Responsibilities

| Responsibility | Current module |
|---|---|
| Thermodynamics and pseudo-components | `Greenhub/chemicals.py`, `Greenhub/component_metadata.py` |
| Workbook and feed data | `Greenhub/input_data.py`, `Greenhub/phaseX_inputs.py` |
| Unit calculations | `Greenhub/phase3_units.py` through `Greenhub/phase7_units.py`, plus upgrading modules |
| Connected system factories | `Greenhub/systems.py`, `Greenhub/phase7_systems.py` |
| Canonical process-area interface | `Greenhub/integration.py` |
| Conservation and plausibility checks | `Greenhub/phaseX_validation.py` |
| Process and system metrics | `Greenhub/phaseX_metrics.py` |
| Integrated reporting | `Greenhub/integrated_reporting.py`, `Greenhub/model_completeness.py` |
| Historical report compatibility | `Greenhub/phaseX_reporting.py` |

## Compatibility Rule

Historical scenario IDs, workbook sheet names, unit IDs, and public factories remain stable. Module moves and broad renames are deferred until equivalence tests and an explicit migration approval exist.

## Extension Rule

Add a new unit by documenting its basis, inputs, outputs, equations, units, ranges, fallbacks, and missing data; implement `_run`; add `_design`, utilities, or `_cost` only when supported; connect it in one scenario factory; add unit and boundary tests; then update the completeness-register classification.
