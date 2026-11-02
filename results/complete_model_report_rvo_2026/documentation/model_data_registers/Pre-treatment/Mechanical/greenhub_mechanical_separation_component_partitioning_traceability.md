# GreenHub mechanical-separation component-partitioning traceability

## Dataset scope

The CSV contains **162 records**, including **74 rows with an explicit partition fraction or range**. Calculated fractions are included only where one source provides both a compatible stream mass yield and component concentration.

Transferability distribution:
- A direct grass or green forage: 24
- B legume or green-biomass proxy: 138
- C broader wet-plant proxy: 0
- D low-transferability reference only: 0

## Direct grass and grass-clover evidence

Direct grass/grass-clover records include:

- perennial ryegrass feed and screw-pressed pulp composition for DM, crude protein, ash, NDF, ADF, hemicellulose, cellulose and ADL;
- grass-clover PEF effects on juice and protein yield;
- generic green-biomass partition ranges from the DCA report;
- clover-grass Organofinery mass yields and source-consistent TS, VS, C, N, P, K, S and water partitions.

The clover-grass Organofinery dataset has the strongest calculable component partitioning because the same paper reports final-stream mass yields and concentrations.

## Lucerne, alfalfa and clover proxy records

Alfalfa and red-clover records are class B because their wet leafy-biomass processing is relevant, but protein solubility, buffering, mineral content and cell-wall structure differ from roadside grass.

Useful alfalfa evidence includes:
- 65% fresh-mass expression to juice and 40% protein recovery in a historical twin-screw process, reported through a peer-reviewed review;
- protein recovery increasing from 40% to 53% after water addition and secondary re-pressing;
- pilot-scale 6 bar pressing with 16% one-pass and 48% cumulative recovered protein after up to ten rehydration/repressing cycles.

## Broader plant proxies

No broader wet-plant proxy was used to generate an active coefficient in this version. The dataset intentionally avoids dry mineral comminution and unrelated woody pressing equations.

## Source capability: partition coefficients versus composition benchmarks

### Supports calculated partition coefficients
Santamaría-Fernández et al. provides:
- fresh-mass yields for press cake, brown juice and protein concentrate;
- paired TS, VS, C, N, P, K and S concentrations;
- a clear downstream Organofinery boundary.

For each stream and component:

`partition_fraction = mass_yield_fraction × stream_concentration / feed_concentration`

Water partition is calculated as:

`water_partition = mass_yield_fraction × (1 − stream_TS) / (1 − feed_TS)`

All formulas and numeric substitutions are preserved in the CSV notes.

### Supports reported partition coefficients but not full closure
The alfalfa twin-screw and multi-pass studies report juice mass or protein recovery coefficients but do not provide the complete feed–juice–cake composition needed to calculate all component closures.

### Composition benchmark only
The DCA perennial-ryegrass tables provide paired feed and press-cake concentrations but no stream mass yield. These rows cannot produce partition fractions without an additional, same-experiment mass yield.

### Qualitative only
“Around half” of crude protein retained in pulp is retained as text and is not converted to 0.50.

## Process boundaries

- **Raw pressing:** historical alfalfa twin-screw expression; DCA plant-versus-pulp composition.
- **Maceration/PEF plus pressing:** grass-clover PEF study.
- **Downstream protein recovery:** Organofinery press cake, brown juice and protein concentrate; DCA generic protein-concentrate ranges.
- **Repeated extraction:** alfalfa cake rehydration and re-pressing.

Brown juice must not be treated as raw green juice. The protein-concentrate stream is downstream of precipitation/fermentation and separation.

## Safe for report-only use

- DCA generic ranges of 50–70% DM and 40–60% protein retained in fibre;
- perennial-ryegrass feed and cake composition without stream yields;
- PEF relative improvements without absolute paired mass flows;
- qualitative protein retention statements;
- secondary-review historical alfalfa coefficients until original papers are retrieved.

## Potential future opt-in partition policies

### `organofinery_clover_grass_downstream`
Can use the calculated clover-grass fresh-mass, water, TS, VS, C, N, P, K and S stream fractions. The model must reproduce the same boundary: cake plus brown juice plus protein concentrate.

### `organofinery_red_clover_downstream`
Same structure as above, but lower transferability to roadside grass.

### `alfalfa_single_pass_6bar`
Can use the reported 16% recovered-protein value as a legume scenario, provided GreenHub labels it “recovered protein” rather than soluble protein release.

### `alfalfa_rehydration_multipass`
Can use the reported cumulative 48% recovery after up to ten passes as a discrete scenario, not as a continuous kinetic law.

### `generic_green_biomass_range`
The DCA ranges may be used only as a broad opt-in sensitivity envelope.

## Components still missing

No high-confidence direct grass dataset was found with complete paired feed, raw juice and cake mass balances for:

- water and total solids at a pressing-only boundary;
- soluble versus insoluble protein;
- true protein versus non-protein nitrogen;
- WSC, fructans, sucrose, glucose and fructose;
- ash and individual minerals at a raw pressing-only boundary;
- Ca and Mg partitions;
- complete NDF, ADF, ADL, cellulose, hemicellulose and lignin partitions;
- direct roadside-grass values;
- paired operating settings such as screw speed, screen aperture, cone gap, throughput and pressure with component partitioning.

These fields should remain inactive until the same experiment reports both mass yields and matched feed/stream concentrations.
