# VARTA 2026 grass nutrient datasets

The two CSV files in this folder are English, machine-readable extracts of
`261027 Nutriënten Grasmonsters VARTA.xlsx`.

- `varta_2026_grass_fiber_measurements.csv` contains the fiber/whole-grass table.
- `varta_2026_grass_juice_measurements.csv` contains the grass-juice table.
- `varta_2026_dataset_traceability.csv` records the source workbook, source sheets,
  translation policy, activation state, readiness state, and limitations.
- `261027 Nutriënten Grasmonsters VARTA.xlsx` is the archived original workbook;
  its SHA-256 is recorded in the source register.
- `fen_grass_harvest_yield_cp_nielsen_2021_table1_reference.csv` and
  `fen_grass_biorefinery_fractionation_annual_nielsen_2021_tables_3_4_reference.csv`
  are literature-only Danish forage references, not roadside-grass defaults.
- `fen_grass_protein_fraction_extractability_nielsen_2021_table2_reference.csv`
  contains literature-only CNCPS fractions, not measured protein extraction
  efficiencies.

Each row retains the original sample label, source worksheet, and source row.
Values below detection limits remain censored strings such as `< 17`; they are
not converted to zero. The explicit `grass_varta_default` profile uses the
Greenhub whole-grass fiber sample and adds measured wet-basis nitrogen,
phosphorus, potassium, and total-solids inputs while retaining the existing
structural component closure for fields not supplied by the laboratory report.

The existing `grass_baseline` workbook selector remains unchanged for backward
compatibility. Selecting `grass_varta_default` activates the traceable measured
profile through `load_roadside_grass_specification`.

The source field `dry_matter_fraction` is retained as a legacy alias, but its
values are percentage points (for example, `14.3` means 14.3%); the explicit
`dry_matter_percent` column contains the same reported values and is used by
the loader before division by 100.

The whole-grass and juice sheets are separate laboratory sample lists. The
GreenHub whole-grass row is dated 2026-07-16; the GreenHub juice row has no
date or shared batch identifier in the extract. Their nutrient concentrations
must not be combined into a press or protein-recovery balance until original
sample lineage and matched inlet/outlet masses are supplied. Both extracts now
have exact source-register links in the FAIR catalog; the juice extract remains
reference-only for Phase 3 component partition.
