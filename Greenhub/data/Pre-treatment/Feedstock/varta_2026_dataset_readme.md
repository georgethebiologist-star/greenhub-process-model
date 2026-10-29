# VARTA 2026 grass nutrient datasets

The two CSV files in this folder are English, machine-readable extracts of
`261027 Nutriënten Grasmonsters VARTA.xlsx`.

- `varta_2026_grass_fiber_measurements.csv` contains the fiber/whole-grass table.
- `varta_2026_grass_juice_measurements.csv` contains the grass-juice table.
- `varta_2026_dataset_traceability.csv` records the source workbook, source sheets,
  translation policy, activation state, readiness state, and limitations.

Each row retains the original sample label, source worksheet, and source row.
Values below detection limits remain censored strings such as `< 17`; they are
not converted to zero. The explicit `grass_varta_default` profile uses the
Greenhub whole-grass fiber sample and adds measured wet-basis nitrogen,
phosphorus, potassium, and total-solids inputs while retaining the existing
structural component closure for fields not supplied by the laboratory report.

The existing `grass_baseline` workbook selector remains unchanged for backward
compatibility. Selecting `grass_varta_default` activates the traceable measured
profile through `load_roadside_grass_specification`.
