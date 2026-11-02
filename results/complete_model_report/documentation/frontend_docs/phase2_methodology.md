# GreenHub Phase 2 Methodology

## Purpose and scope

Phase 2 establishes a data-ready material model for the measured raw liquid fraction. It does not implement downstream valorization pathways. The active BioSTEAM system remains feed storage followed by provisional primary separation.

The methodology follows the BioSTEAM guide sequence: define thermodynamics before streams, create units with explicit IDs/inputs/outputs, activate a dedicated flowsheet, create the system through that flowsheet, simulate, and then report and validate results.

## Material hierarchy

### Fundamental model components

Physical stream mass is represented by specific database chemicals, explicit ionic formulas, or documented pseudo-components. Real database identities are checked against the installed ThermoSTEAM version. Names that resolve to unintended salts are not accepted as free ions.

Pseudo-components represent one of three conventions:

- A material lump, such as soluble protein or suspended biogenic solids.
- An element-equivalent pool, such as other organic nitrogen or particulate phosphorus.
- A grouped inventory pool, such as persistent organics or heavy metals.

Every pseudo-component records its convention, phase, solubility, particle class, elemental fractions, analytical factors, property surrogate, and limitations. Water or glucose models provide only preliminary sensible heat and volume behavior. Heats of formation are provisional, so pseudo-component reaction enthalpies are not used.

### Aggregate analytical measurements

COD, TOC, BOD, TS, VS, TSS, TDS, TN, TKN, TP, pH, alkalinity, conductivity, turbidity, viscosity, and particle size remain records associated with the feed. They are compared with component-derived values but never allocated as extra mass.

## Input model and provenance

Each measurement row contains value, unit, basis, stream, sample, scenario, month, uncertainty range/distribution, data type, measurement status, quality class, source, comments, priority, allocation target, and active flag.

Missing values stay null. The following states are distinct: not measured, below detection limit, assumed absent, intentionally excluded, measured, assumed, estimated, and calculated. Only an explicit assumed-absent state should justify a scientific zero.

Quality classes are:

- A: project measurement
- B: supplier or industry data
- C: peer-reviewed literature
- D: engineering estimate
- E: placeholder or unknown

## Seasonal flow basis

The workbook stores total liquid mass and operating days separately for every month, sample, and scenario. The active model flow is:

```text
average kg/hr = monthly liquid mass / (operating days * 24)
```

This is a representative operating-hour flow for the selected month, not a claim of continuous annual production. The workbook also calculates annual availability for planning.

## Unit conversion and allocation

Canonical stream flow is `kg/hr`. Supported conversions include `t/d`, `t/y`, `kg/y`, volumetric flows with density, `mg/L`, `g/L`, `kg/m3`, wet-mass fractions, dry-solids fractions, `mol/L`, and `mmol/L`.

Nutrient reporting bases are converted explicitly. For example, NH4-N is converted to NH4 compound mass, PO4-P to phosphate-ion mass, P to P2O5, and K to K2O. Input basis is always retained in the allocation report.

Allocation precedence is direct component measurement before any aggregate constraint. If multiple active rows target one component, the smallest priority value is selected. Unknown residual pools are not generated unless a future reconciliation method is explicitly approved. Water is the only automatic residual and is calculated from the wet-mass balance.

Negative residual water is a hard failure. The model does not force inconsistent data to close.

## Reconciliation

The hierarchy is:

1. Direct individual components
2. Measured component groups
3. Aggregate indicators
4. Explicitly enabled residual lumps

Phase 2 implements levels 1-3 and leaves level 4 disabled. Calculated group totals and indicators are compared with measured aggregates. Relative gaps above 20% are warnings and gaps above 50% are labeled large gaps. Missing measurements are reported as not measured and do not fail the model.

## COD and TOC

For a molecular compound `CaHbOcNdSe`, theoretical COD uses nitrogen-to-ammonia and sulfur-to-hydrogen-sulfide convention:

```text
mol O2/mol substrate = a + b/4 - c/2 - 3d/4 - e/2
```

The result is converted to `kg O2/kg component`. Pseudo-component COD and TOC factors are explicit metadata. No COD is assigned to water, ash, metals, chloride, sulfate, carbonate, phosphate, or other already oxidized mineral species.

## Nitrogen and phosphorus

Total nitrogen is calculated from component elemental fractions. Organic nitrogen, inorganic nitrogen, and TKN are reported separately. Protein nitrogen is calculated from the provisional 16% protein-N convention.

Total, dissolved, and particulate phosphorus are calculated from orthophosphate and P-equivalent pools. P-equivalent pseudo-components intentionally use `kg component = kg P` to avoid inventing a molecular identity.

## Acid-base diagnostics

Ammonia equilibrium uses the temperature-dependent engineering relation:

```text
pKa = 0.09018 + 2729.92 / T[K]
fraction NH3 = 1 / (1 + 10^(pKa - pH))
```

Phosphate, carbonate, and sulfide functions use screening-level dilute-solution pKa values. These functions preserve the distinction between element-equivalent and compound mass. They do not calculate activities, ionic strength, or rigorous electrolyte equilibrium.

Measured ions are used for a charge-equivalent diagnostic. No counter-ion is added automatically and no composition is modified to force electroneutrality.

## Reaction preparation

The inactive library contains atom-balanced molecular reactions for acid/base reagents, lactic fermentation, methane formation, struvite, ammonia recovery, desulfurization, and optional mineral precipitation. Charged reactions use a `1e-5 kg/kmol` numerical mass tolerance because ThermoSTEAM ionic molecular weights include electron-mass differences; atom residual tolerance remains `1e-9`.

The Buswell utility accepts C/H/O/N/S empirical formulas and returns methane, carbon dioxide, ammonia, hydrogen sulfide, and water coefficients. It rejects non-carbon formulas and formulas that produce negative gas coefficients.

Protein precipitation and coagulation are empirical phase transfers. Protein is not destroyed. Acid demand, recovery, co-precipitation, and residual solubility must be parameterized separately in Phase 3.

## Separator and balances

All S101 splits are fractions to clarified liquid. Component-specific values override group values, which override soluble/particulate defaults. Unclassified components are reported.

The active system validates total mass, every component, and tracked C/H/O/N/P/S/K/Na/Mg/Ca/Cl flows at `1e-6 kg/hr`. It also checks that most suspended and inert solids enter wet solids and most soluble compounds remain clarified.

## Known limitations and Phase 3 handoff

- Feed assumptions marked `E` are dummy values.
- Pseudo-component thermodynamics are preliminary.
- Full acid-base/electrolyte equilibrium is not implemented.
- S101 has no equipment design, power, or CAPEX.
- T101 costing is outside its validated lower range at the dummy flow.
- No reaction is applied in Phase 2.
- Roadside-grass Mode A, PEF, and screw pressing remain inactive schemas.
- Product pricing, final CAPEX, TEA, LCA, uncertainty sampling, and MCDA are deferred.

Phase 3 should first replace placeholders with project measurements and calibrate one approved physical pathway before adding alternatives.
