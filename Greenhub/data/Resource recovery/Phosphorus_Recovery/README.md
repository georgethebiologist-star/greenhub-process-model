# GreenHub phosphorus-recovery datasets

This package covers struvite and defensible calcium-phosphate precipitation routes for digestate,
centrate and agricultural wastewater.

## Equilibrium-basis rule
Activity-based constants must be compared with ionic activities. Concentration-based empirical
constants may only be used in their original matrix, temperature and ionic-strength range.
The two bases must never be mixed.

Total P is not treated as orthophosphate. Dissolved orthophosphate, TAN, Mg, Ca, pH, temperature,
alkalinity and ionic strength are required scenario inputs.

No unsupported numerical assumptions were inserted. Missing kinetics, product properties,
separation performance and equipment cost inputs remain blank and are registered explicitly.

Use `parameter_id` as the provenance key and `python_variable` as the BioSTEAM-facing key.
Filter by route, matrix, operating conditions, equilibrium basis and transferability.
