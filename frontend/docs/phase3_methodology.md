# GreenHub Phase 3 Methodology

## Purpose and Boundary

Phase 3 implements the physically meaningful GreenHub front end from roadside grass or a measured liquid fraction to a standardized raw liquid, clarified protein-rich liquid, and primary sludge. It follows the BioSTEAM sequence used by the project: define thermodynamics, create a fresh named flowsheet, create streams, create units with explicit `ID`, `ins`, and `outs`, create the system from the flowsheet, simulate, inspect results, validate, and export reports.

The active boundary is:

```text
F0: measured liquid -> T101 -> C301 -> clarified liquid + primary sludge
F1: grass -> U101 -> S201 -> C301 -> fibre cake + clarified liquid + sludge
F2: grass -> U101 -> U201 -> S201 -> C301 -> fibre cake + clarified liquid + sludge
F3: same topology as F2 with deterministic parameter overrides enabled
```

Downstream fibre use, protein precipitation and drying, digestion, gas upgrading, nutrient recovery, TEA, LCA, uncertainty analysis, and MCDA are deferred.

## Inputs and Provenance

`Greenhub/data/greenhub_feed_inputs.xlsx` is the canonical input source. Measured-liquid mass and composition remain on the Phase 2 sheets. Roadside-grass availability and composition are separate on `GrassAvailability` and `GrassMeasurements`; liquid composition is never reused as grass composition.

The `Phase3Parameters` sheet stores one parameter observation per row with:

- category and Python name;
- value and unit;
- applicable scenario and month;
- lower and upper bounds;
- required flag;
- measured/assumed status;
- source quality class and reference;
- calculation method, priority, active flag, and comment.

Resolution favors an exact scenario and month match over `All`; lower priority numbers break ties. Blank optional values remain `None`. Blank required values fail before unit construction. Required class-E values are accepted only when the user explicitly enables structural-test mode.

Each monthly wet mass is converted to an average operating flow:

```text
feed flow [kg/h] = monthly mass [kg] / (operating days x 24 h/day)
```

Monthly models remain separate. Annual quantities are sums of each monthly rate multiplied by that month's operating hours.

## Material Representation

Real ThermoSTEAM chemicals are used where database identities are unambiguous. Project-specific pools are explicit pseudo-components. Phase 3 adds conceptual pools needed for conservative transfer and separation, including entrapped sugars, particulate biodegradable organics, particulate nitrogen, dissolved phosphorus, particulate potassium, sand, litter, and optional flocculant.

Pseudo-components support mass balance, sensible heat, split classification, COD/TOC screening, elemental accounting, and inventory tracking. They do not imply exact molecular identities, rigorous phase equilibrium, electrolyte activity, or reaction thermodynamics.

Aggregate measurements such as COD, TOC, TSS, TN, TP, pH, conductivity, and alkalinity are analytical records. They are not added as extra stream mass.

## U101 Feed Preparation

U101 is a custom `bst.Unit` with one feed and two outlets:

```text
inlet:  roadside_grass
outlet 0: prepared_roadside_grass
outlet 1: preparation_rejects
```

Cleaning is an optional component-specific removal model. Resolution is component removal, group removal, documented biomass loss, then no removal. All removed mass appears in the reject stream. The current structural workbook provides separate removal assumptions for sand, litter, and inert solids; it does not assume complete cleaning.

Power is:

```text
P_U101 [kW] = wet feed [t/h] x specific electricity [kWh/t wet]
```

Design results report wet throughput, throughput per train, equipment count, reject flow, and specific electricity. No purchase cost is assigned.

## U201 PEF Pretreatment

U201 is a custom `bst.Unit`, not a chemical reactor. Its outlets are treated grass and an explicit documented-loss stream. Default documented mass loss is zero.

The empirical one-to-one transfer map is:

| Source pool | Destination pool | Driver |
|---|---|---|
| `SuspendedProtein` | `SolubleProtein` | suspended-protein solubilization x cell-disintegration index |
| `EntrappedSugars` | `Glucose` | sugar-release fraction |
| `ParticulateBiodegradableOrganics` | `OtherBiodegradableOrganics` | soluble-COD release fraction |
| `ParticulateNitrogen` | `OrganicNitrogen` | nitrogen-release fraction |
| `ParticulatePhosphorus` | `DissolvedPhosphorus` | phosphorus-release fraction |
| `ParticulatePotassium` | `PotassiumIon` | potassium-release fraction |

Every transfer subtracts and adds the same `kg/h`. Source and destination metadata use compatible elemental conventions so C, N, P, K, and other tracked elements remain conserved. No aggregate COD component is created.

The PEF soluble-protein-release parameter also raises the press recovery of already soluble protein using:

```text
R_new = R_base + release_fraction x (1 - R_base)
```

The juice-yield enhancement is added to the base press yield and bounded at one.

Electrical demand is:

```text
P_U201 [kW] = wet feed [t/h] x specific energy [kWh/t wet]
```

Temperature has one controlling mode:

- `specified`: use treatment temperature or inlet temperature plus specified rise;
- `calculated`: convert retained electrical energy to a rise using effective heat capacity and thermal-retention efficiency.

For calculated mode:

```text
retained heat [kJ/h] = wet feed [t/h] x specific energy [kWh/t] x 3600 x efficiency
delta T [K] = retained heat / (feed [kg/h] x Cp_effective [kJ/kg/K])
```

Electrical energy is entered once in `power_utility`; the temperature calculation is a retained-energy interpretation, not a second utility.

## S201 Screw Press

S201 is a custom partitioning unit. Outlet order is deliberately fixed:

```text
outlet 0: pressed_fibre_cake
outlet 1: raw_liquid_fraction
```

All non-water parameters use a documented fraction-to-juice convention, except inputs explicitly named `recovery_to_cake`, which are converted to `1 - recovery_to_cake`. Split precedence is:

```text
component override
-> group recovery
-> metadata-based soluble or particulate default
-> warned unclassified fallback
```

This permits different behavior for soluble protein, suspended protein, sugars, acids, amino acids, ammonium, phosphorus, potassium, soluble salts, cellulose, hemicellulose, lignin, inert solids, and contaminants.

Water is not assigned by an arbitrary component split. After all non-water masses are fixed, the shared analytical solver determines water allocation.

For a cake-moisture target `x` and cake non-water mass `M_s`:

```text
cake water = M_s x x / (1 - x)
juice water = available water - cake water
```

For a juice-yield target `Y`, wet feed `M_f`, and juice non-water mass `M_j,s`:

```text
juice water = Y x M_f - M_j,s
cake water = available water - juice water
```

Negative water or a requirement above available water is an infeasible specification and raises an informative error. When both targets are feasible but inconsistent by more than two percentage points, the model warns and follows one explicit mode:

- `cake_moisture_priority`;
- `juice_yield_priority`;
- `reconciliation_mode`, which uses the midpoint of the two water allocations.

The structural workbook currently selects `juice_yield_priority` because its dummy yield and moisture targets are mutually inconsistent. The achieved moisture is reported; it is not disguised as the target.

Press power is wet `t/h x kWh/t wet`. Design results include throughput, train count, cake and liquid flow, achieved cake moisture, achieved juice yield, and specific electricity. No heat utility or purchase cost is created.

## Standardized Raw-Liquid Interface

Both entry modes expose the same stream key, `raw_liquid_fraction`, immediately before C301. The interface contains all component mass flows, assumed or measured density, volume, calculated analytical indicators, retained physical measurements, data-quality rows, reconciliation records, and warnings.

For F0, pH, conductivity, alkalinity, particle size, and measured-versus-calculated reconciliation are retained from measured-liquid characterization. For F1-F3, component-derived COD, TOC, solids, and nutrient indicators are recalculated; unsupported pH, conductivity, alkalinity, and particle size remain missing.

## C301 Primary Centrifuge

C301 is a custom physical separation unit with explicit optional auxiliaries:

```text
inlets: raw liquid, wash water, flocculant
outlet 0: clarified protein-rich liquid
outlet 1: primary sludge
```

Wash water and flocculant are disabled by zero workbook values unless deliberately enabled. If enabled, they are external system inputs and remain in the mass balance.

Non-water splits use fraction to clarified liquid. Component overrides cover soluble protein, suspended protein, particulate phosphorus, particulate heavy metals, microplastics, and sand. Group rules cover dissolved phosphorus, particulate COD, volatile solids, and suspended solids. Remaining classified soluble components use 0.99 to clarified liquid; classified particulates use the TSS removal efficiency. Any unclassified fallback produces a warning.

Sludge water is solved analytically from the target wet-basis moisture using the same feasibility-safe water solver. `sludge_solids_fraction` and `sludge_moisture_fraction` must be complementary when both are entered; a conflict raises an error. Liquid entrainment is used only as the fallback if no moisture target is supplied.

Hydraulic flow and power are:

```text
Q [m3/h] = total centrifuge inlet mass [kg/h] / feed density [kg/m3]
P_C301 [kW] = Q [m3/h] x specific electricity [kWh/m3]
```

Design results include hydraulic throughput, throughput per train, dry-solids load, equipment count, sludge flow and moisture, polymer, wash water, and specific electricity. Density is an explicit workbook record, not silently inferred from water.

## Flowsheet and System Construction

Every call to `create_phase3_scenario` creates and activates a fresh flowsheet named from the scenario and a monotonic build counter. Units and streams therefore cannot leak between scenarios or cause duplicate-ID registry errors.

Systems are created through `bst.main_flowsheet.create_system` from terminal streams. There is no recycle, so no unnecessary convergence settings or numerical solver options are introduced. Direct analytical specifications are used for press and centrifuge water allocation.

## Metrics

The common metric set includes wet throughput, liquid and dry-cake yields, cake moisture, stream flow rates, protein/sugar/COD/TSS/N/P/K flows, cake nutrient and contaminant retention, extraction fractions, clarification efficiency, soluble-protein retention, unit electricity, total electricity, process water, and balance residuals.

Ratios return missing rather than failing when a denominator is zero. F0 therefore reports grass-normalized metrics as missing instead of inventing a grass basis.

## Validation

Default warning and failure tolerances are `1e-8` and `1e-6 kg/h`, respectively. Validation includes:

- unit total-mass closure;
- component closure around ordinary separators;
- declared PEF transfer-adjusted component closure;
- PEF protein and COD conservation;
- C, H, O, N, P, S, K, Na, Mg, Ca, and Cl closure;
- plant boundary including preparation rejects, fibre cake, documented losses, clarified liquid, primary sludge, wash water, and polymer;
- non-negative flows and bounded recoveries;
- reduction of suspended solids through C301;
- retention of most soluble protein in clarified liquid;
- monthly-to-annual arithmetic closure.

An essential failure raises an informative exception. Non-fatal assumption conflicts and data-quality issues are deduplicated in the validation report and assumption register.

## Reports

The selected model exports BioSTEAM system, unit, utility, design, stream, interface, energy, balance, and assumption tables to `phase3_front_end_report.xlsx`. All F0-F3 metrics and selected-scenario monthly/annual totals are exported to `phase3_scenario_comparison.xlsx`. Detailed CSVs make every transfer and partition auditable by component.

Graphviz setup is performed immediately before `system.diagram`. Diagram failure is caught so scientific simulation and spreadsheet reporting can still complete.

## Costing and Interpretation

U101, U201, S201, and C301 deliberately report no CAPEX. A custom cost will be added only after a documented base cost, capacity basis, scaling exponent, currency, base year, and valid range are approved. T101 in F0 is a built-in BioSTEAM storage tank; its below-range cost warning is retained.

All current active Phase 3 process values are structural quality-E assumptions. They verify architecture and conservation but must not be presented as measured performance, final equipment design, product economics, environmental impact, or an optimum GreenHub configuration.

## Phase 4 Interface

The next phase can attach protein recovery to `clarified_protein_rich_liquid` while preserving F0-F3 comparability. It should consume the existing component metadata and raw-liquid characterization, add only calibrated transformations, retain source-quality metadata, and extend rather than replace the current validation boundaries.
