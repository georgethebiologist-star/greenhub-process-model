# Dynamic Press Preview

This is a report-only dynamic feedstock/separation preparation artifact. It does not modify empirical, seasonal, API, or BioSTEAM calculations.

## Data Used

- `greenhub_mechanical_pretreatment_pressing_data.csv`: final stream yields `0.395/0.568/0.037`.
- `greenhub_mechanical_separation_component_partitioning.csv`: component and metadata partition evidence.
- Mechanical `source_register.csv`, `assumption_and_missing_data_register.csv`, and `equation_registry.csv` were audited for boundary and missing-data context.

## Fallback Status

- `water_closure_correction`: `enabled`
- `total_protein`: `disabled`
- `total_sugar_wsc`: `disabled`
- `fiber`: `disabled`

## Stream Mass Split

| Stream | kg/kg feed | Assigned components/pools | Unassigned capacity |
|---|---:|---:|---:|
| brown_juice | 0.568000 | 0.407160 | 0.160840 |
| press_cake | 0.395000 | 0.190819 | 0.204181 |
| protein_concentrate | 0.037000 | 0.022021 | 0.014979 |

## Downstream Readiness

| Pathway | Ready |
|---|---|
| Protein extraction preview | False |
| Anaerobic digestion preview | False |
| Nutrient recovery preview | False |

## Blockers

- unmapped_components:Ash,Cellulose,Fructose,Glucose,Hemicellulose,Lignin,SolubleProtein,Sucrose,SuspendedProtein
- unmapped_required_pools:fructan,residual_unallocated_dry_matter
- elemental_nutrient_speciation_not_partitioned
- normal_simulation_integration_disabled

## Activation Status

`can_drive_simulation = False`. Unmapped pools are not forced to fill stream yields, and empirical calculations remain independent.
