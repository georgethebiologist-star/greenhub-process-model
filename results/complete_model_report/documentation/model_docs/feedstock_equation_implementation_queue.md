# Feedstock Equation Implementation Queue

This report is read-only. It does not implement equations, activate parameters, enable dynamic mode, or modify model calculations.

## Status Counts

- `blocked_dynamic_model_scope`: 10
- `blocked_missing_inputs`: 1
- `implemented_typed`: 1
- `needs_source_review`: 5
- `needs_unit_conversion_policy`: 2

## First Safest Candidate

- None.

## Blocked Or Out Of Scope

- `EQ-WR-001` (`blocked_dynamic_model_scope`): weather/time-dependent dynamic feedstock equation
- `EQ-WR-002` (`blocked_dynamic_model_scope`): weather/time-dependent dynamic feedstock equation
- `EQ-WR-003` (`blocked_dynamic_model_scope`): weather/time-dependent dynamic feedstock equation
- `EQ-WR-004` (`blocked_dynamic_model_scope`): weather/time-dependent dynamic feedstock equation
- `EQ-WR-005` (`blocked_dynamic_model_scope`): weather/time-dependent dynamic feedstock equation
- `EQ-WR-006` (`blocked_dynamic_model_scope`): weather/time-dependent dynamic feedstock equation
- `EQ-WR-007` (`blocked_dynamic_model_scope`): weather/time-dependent dynamic feedstock equation
- `EQ001` (`blocked_dynamic_model_scope`): Duplicate identity, unresolved symbols, required inputs, or source-location metadata block implementation.
- `EQ002` (`blocked_dynamic_model_scope`): Duplicate identity, unresolved symbols, required inputs, or source-location metadata block implementation.
- `EQ006` (`blocked_dynamic_model_scope`): Duplicate identity, unresolved symbols, required inputs, or source-location metadata block implementation.
- `EQ_CP_MASS_WEIGHTED` (`blocked_missing_inputs`): Not activatable until dry roadside-grass Cp and temperature dependence are validated.

## Queue

### EQ-WR-001

- canonical_field: `k`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `P; sum_T`
- output_field: `k`
- source_or_doi: `10.24425/jwld.2022.140786`
- blocked_reason: weather/time-dependent dynamic feedstock equation
- recommended_next_action: Define dynamic weather/time inputs and scope before typed implementation.

### EQ-WR-002

- canonical_field: `cellulose_dry_basis`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `precipitation_mm`
- output_field: `cellulose_g_per_kg_DM`
- source_or_doi: `10.24425/jwld.2022.140786`
- blocked_reason: weather/time-dependent dynamic feedstock equation
- recommended_next_action: Define dynamic weather/time inputs and scope before typed implementation.

### EQ-WR-003

- canonical_field: `cellulose_dry_basis`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `precipitation_mm`
- output_field: `hemicellulose_g_per_kg_DM`
- source_or_doi: `10.24425/jwld.2022.140786`
- blocked_reason: weather/time-dependent dynamic feedstock equation
- recommended_next_action: Define dynamic weather/time inputs and scope before typed implementation.

### EQ-WR-004

- canonical_field: `lignin_dry_basis`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `precipitation_mm`
- output_field: `lignin_g_per_kg_DM`
- source_or_doi: `10.24425/jwld.2022.140786`
- blocked_reason: weather/time-dependent dynamic feedstock equation
- recommended_next_action: Define dynamic weather/time inputs and scope before typed implementation.

### EQ-WR-005

- canonical_field: `cellulose_dry_basis`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `temperature_C`
- output_field: `cellulose_g_per_kg_DM`
- source_or_doi: `10.24425/jwld.2022.140786`
- blocked_reason: weather/time-dependent dynamic feedstock equation
- recommended_next_action: Define dynamic weather/time inputs and scope before typed implementation.

### EQ-WR-006

- canonical_field: `cellulose_dry_basis`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `temperature_C`
- output_field: `hemicellulose_g_per_kg_DM`
- source_or_doi: `10.24425/jwld.2022.140786`
- blocked_reason: weather/time-dependent dynamic feedstock equation
- recommended_next_action: Define dynamic weather/time inputs and scope before typed implementation.

### EQ-WR-007

- canonical_field: `lignin_dry_basis`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `temperature_C`
- output_field: `lignin_g_per_kg_DM`
- source_or_doi: `10.24425/jwld.2022.140786`
- blocked_reason: weather/time-dependent dynamic feedstock equation
- recommended_next_action: Define dynamic weather/time inputs and scope before typed implementation.

### EQ001

- canonical_field: `Modified Gompertz cumulative methane model`
- source_file: `Bigas production + upgrade/Feed BMP/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `lag_time`
- output_field: `Modified Gompertz cumulative methane model`
- source_or_doi: `Grass from Road Verges as a Substrate for Biogas Production`
- blocked_reason: Duplicate identity, unresolved symbols, required inputs, or source-location metadata block implementation.
- recommended_next_action: Keep out of feedstock resolution until dynamic digestion scope is designed.

### EQ002

- canonical_field: `fixed_carbon_dry_basis`
- source_file: `Bigas production + upgrade/Feed BMP/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `ash_pct; moisture_pct; volatile_matter_pct`
- output_field: `Fixed carbon by difference`
- source_or_doi: `Is Lincolnshire road verge biomass a suitable feedstock for anaerobic digestion?`
- blocked_reason: Duplicate identity, unresolved symbols, required inputs, or source-location metadata block implementation.
- recommended_next_action: Keep out of feedstock resolution until dynamic digestion scope is designed.

### EQ006

- canonical_field: `TOC fraction of COD`
- source_file: `Bigas production + upgrade/Feed BMP/equation_registry.csv`
- implementation_status: `blocked_dynamic_model_scope`
- activation_status: `reference_only`
- required_inputs: `cod; toc`
- output_field: `TOC fraction of COD`
- source_or_doi: `Is Lincolnshire road verge biomass a suitable feedstock for anaerobic digestion?`
- blocked_reason: Duplicate identity, unresolved symbols, required inputs, or source-location metadata block implementation.
- recommended_next_action: Keep out of feedstock resolution until dynamic digestion scope is designed.

### EQ_CP_MASS_WEIGHTED

- canonical_field: `specific_heat_capacity`
- source_file: `roadside_grass_missing_proxy_candidates_extended.csv`
- implementation_status: `blocked_missing_inputs`
- activation_status: `reference_only`
- required_inputs: `Measured wet-basis moisture x_w; water Cp; independently sourced dry-grass Cp`
- output_field: `solid_cp`
- source_or_doi: `Mass-weighted sensible heat-capacity relation`
- blocked_reason: Not activatable until dry roadside-grass Cp and temperature dependence are validated.
- recommended_next_action: Source missing component inputs before typed implementation.

### EQ-CALC-001

- canonical_field: `moisture_wet_basis`
- source_file: `Pre-treatment/Feedstock/equation_registry.csv`
- implementation_status: `implemented_typed`
- activation_status: `report_only`
- required_inputs: `total_solids_wb_pct`
- output_field: `moisture_wb_pct`
- source_or_doi: `10.3390/en16114488`
- blocked_reason: none
- recommended_next_action: Keep typed implementation under existing activation tests.

### EQ003

- canonical_field: `bmp_buswell`
- source_file: `Bigas production + upgrade/Feed BMP/equation_registry.csv`
- implementation_status: `needs_source_review`
- activation_status: `reference_only`
- required_inputs: `none`
- output_field: `Buswell theoretical methane potential`
- source_or_doi: `Is Lincolnshire road verge biomass a suitable feedstock for anaerobic digestion?`
- blocked_reason: catalogued equation has no approved typed implementation
- recommended_next_action: Implement an approved function with dimensional, source-reference, trend, boundary, and invalid-input tests.

### EQ004

- canonical_field: `bmp_boyle`
- source_file: `Bigas production + upgrade/Feed BMP/equation_registry.csv`
- implementation_status: `needs_source_review`
- activation_status: `reference_only`
- required_inputs: `none`
- output_field: `Boyle theoretical methane potential`
- source_or_doi: `Is Lincolnshire road verge biomass a suitable feedstock for anaerobic digestion?`
- blocked_reason: catalogued equation has no approved typed implementation
- recommended_next_action: Implement an approved function with dimensional, source-reference, trend, boundary, and invalid-input tests.

### EQ005

- canonical_field: `Theoretical methane fraction in biogas`
- source_file: `Bigas production + upgrade/Feed BMP/equation_registry.csv`
- implementation_status: `needs_source_review`
- activation_status: `reference_only`
- required_inputs: `none`
- output_field: `Theoretical methane fraction in biogas`
- source_or_doi: `Is Lincolnshire road verge biomass a suitable feedstock for anaerobic digestion?`
- blocked_reason: catalogued equation has no approved typed implementation
- recommended_next_action: Implement an approved function with dimensional, source-reference, trend, boundary, and invalid-input tests.

### EQ_GLF_TS_FROM_PAIRED_BASIS

- canonical_field: `liquid_total_solids`
- source_file: `roadside_grass_missing_proxy_candidates_extended.csv`
- implementation_status: `needs_source_review`
- activation_status: `reference_only`
- required_inputs: `C_N; FM = 1280 ±100 mg/kg FM; C_N; DM = 38788 ±3030 mg/kg DM`
- output_field: `glf_ts`
- source_or_doi: `10.1002/jpln.202200308`
- blocked_reason: source equation referenced by data row but not reviewed for typed implementation
- recommended_next_action: Review equation source, inputs, units, and canonical output.

### EQ_VS_CORR

- canonical_field: `S2/H1.1_fresh_vs`
- source_file: `roadside_grass_composition_scientific.csv`
- implementation_status: `needs_source_review`
- activation_status: `reference_only`
- required_inputs: `%VS_uncorrected`
- output_field: `S2/H1.1_fresh_vs`
- source_or_doi: `10.1016/j.biombioe.2020.105570`
- blocked_reason: source equation referenced by data row but not reviewed for typed implementation
- recommended_next_action: Review equation source, inputs, units, and canonical output.

### EQ_K_FROM_K2O

- canonical_field: `liquid_total_potassium`
- source_file: `roadside_grass_missing_proxy_candidates_extended.csv`
- implementation_status: `needs_unit_conversion_policy`
- activation_status: `reference_only`
- required_inputs: `2260 ±126 mg K2O/kg FM; atomic masses K=39.0983; O=15.999 g/mol`
- output_field: `glf_total_k`
- source_or_doi: `10.1002/jpln.202200308`
- blocked_reason: calculation depends on explicit unit conversion
- recommended_next_action: Add reviewed conversion test preserving original and SI values.

### EQ_P_FROM_P2O5

- canonical_field: `liquid_total_phosphorus`
- source_file: `roadside_grass_missing_proxy_candidates_extended.csv`
- implementation_status: `needs_unit_conversion_policy`
- activation_status: `reference_only`
- required_inputs: `406 ±5 mg P2O5/kg FM; atomic masses P=30.973761998; O=15.999 g/mol`
- output_field: `glf_total_p`
- source_or_doi: `10.1002/jpln.202200308`
- blocked_reason: calculation depends on explicit unit conversion
- recommended_next_action: Add reviewed conversion test preserving original and SI values.
