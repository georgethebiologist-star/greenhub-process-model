# GreenHub Phase 5 Methodology

## Purpose And Boundary

Phase 5 extends the validated Phase 1-4 architecture with steady-state anaerobic digestion and raw-biogas production. It accepts either the conditioned protein-depleted liquid from an active protein-recovery route or the clarified protein-rich liquid through PR0. Fibre-panel processing, gas upgrading, digestate nutrient recovery, final TEA/LCA, uncertainty, and MCDA are excluded.

The baseline topology is:

```text
digester feed -> M501 -> H501 -> R501 -> V501
                                      -> raw biogas
                                      -> digestate
                                      -> uncaptured gas inventory
```

No T501 equalization tank, transfer pump, recycle, or solids-retention separator is active because hourly variability, hydraulics, and retention data are unavailable. Monthly operation uses independent steady states, not fake dynamics.

## Feed Modes

`AD1` and `AD3` use `conditioned_protein_depleted_liquid`. `AD2` selects PR0 and uses its material-conservative M403 outlet, preserving the clarified protein-rich composition while keeping a fully docked BioSTEAM graph. `AD0` is a no-conversion bypass with zero raw and uncaptured gas.

Feed characterization derives wet mass, TS, TSS, TDS, VS, COD, soluble and particulate COD, carbon, TN, TKN, organic N, ammoniacal N, TP, VFA, protein, C:N, COD:N, and COD:P from component inventories and metadata. Ratios remain blank when denominators are zero.

## Components And COD

Real chemicals retain ThermoSTEAM identities. Lumped proteins, organics, solids, nutrients, contaminants, and `MicrobialBiomass` are explicit pseudo-components. Their COD and C/N/P/S/VS factors are bookkeeping conventions, not exact formulas.

The model never applies a methane yield to undifferentiated total COD. Explicit substrate pools are assigned biodegradability, hydrolysis, and stage-conversion fractions once. Inert and persistent COD remains in the digestate. COD metadata are used to reconcile substrate removal, biomass, reduced sulphur, methane, and residual intermediate COD without adding a second residual-COD feed pool.

## Conditioning

M501 accepts the process liquid, commercial base solution, dilution water, and a reserved trace-nutrient stream. The active structural method is empirical pure-base dose:

```text
pure base = feed volume * base dose
solution mass = pure base / (solution mass fraction * purity)
```

Solution water is explicit. pH is metadata because buffering, alkalinity, and titration data are missing. Acid-equivalent conditioning is data-gated. Nutrient addition remains zero because no deficiency calculation and validated dosage rule exist.

## Reactor Selection And Sizing

AD1 uses a mesophilic continuous stirred-tank reactor because the current data do not justify staged or high-rate retention behavior. AD3 is a structural thermophilic alternative only.

Working-volume candidates are:

```text
V_HRT = liquid flow * 24 * HRT
V_COD = COD load * 24 / target COD OLR
V_VS  = VS load * 24 / target VS OLR
```

The baseline selects the maximum required volume. Total volume includes the working-volume and headspace fractions. Parallel tank count follows the optional maximum single-tank volume. Actual HRT and OLRs are recalculated from selected volume. Sizing disagreement is reported and warns above 25%; criteria are not silently discarded.

SRT equals HRT because no physical biomass-retention mechanism exists. Independent SRT control is not claimed. Cylindrical diameter, liquid height, freeboard, surface area, and insulation area are conceptual screening geometry, not structural design.

## Reaction Architecture

R501 is a staged fate model with distinct ledgers:

1. Hydrolysis applies substrate-specific accessible fractions.
2. Acidogenesis converts accessible sugars, proteins, lipids, and other organics.
3. Acetogenesis records VFA conversion separately.
4. Methanogenesis allocates available methanogenic COD to methane after biomass and sulphide COD demand.

Fixed conversions are used because rate constants, temperature coefficients, particle-size effects, VFA yields, population kinetics, and time-series calibration data are missing. These stages are steady-state ultimate fates, not dynamic VFA or microbial populations.

### Calculation Modes

`component_stoichiometric` and `hybrid` use component-derived conversion and a bounded methanogenesis fraction. `COD_yield` calculates a target from biodegradable-COD and COD-conversion fractions, scales component conversion to that target, and applies one methane yield. Requested methane above converted-COD potential raises an exception.

Buswell calculations remain available for explicit C/H/O/N/S formulas and are atom-balanced in tests. Formula-free pools do not receive invented formulas, so their digestion uses the COD/C/N/P/S ledger. Component Buswell methane and COD-yield methane are never applied simultaneously.

## Protein, Nitrogen, Phosphorus, And Sulphur

Protein digestion is partial. Converted protein contributes carbon, COD, organic N, and sulphur once. Additional `OrganicNitrogen` and `ParticulateNitrogen` mineralization occurs after substrate conversion, preventing duplicate ammonification.

One combined biomass pool receives a fixed COD yield and is capped by available C, N, P, and S. Required inorganic nutrients are withdrawn explicitly. Residual mineralized nitrogen is converted to TAN, then distributed between NH4 and NH3 with:

```text
pKa = 0.09018 + 2729.92 / T
f_NH3 = 1 / (1 + 10^(pKa - pH))
```

Organic and particulate phosphorus transfer to orthophosphate while total P is conserved. No struvite precipitation or nutrient recovery is performed.

Sulphate reduction is disabled in the baseline. When explicitly enabled, converted sulphate contributes sulphur to H2S and consumes COD-equivalent reducing potential. H2S cannot be generated without sulphur inventory. The model does not resolve complete sulphide electrolyte chemistry.

## Inhibition

A bounded piecewise-linear pH factor is available and cannot become negative. Free-ammonia inhibition is implemented only as an optional non-competitive screening factor and requires an explicit inhibition constant. It is disabled in the baseline because no GreenHub threshold exists. VFA, chloride, and salinity inhibition remain disabled for the same reason. Indicators are reported without inventing thresholds.

## Gas-Liquid Partitioning

V501 uses Level-1 empirical fractions because matrix-specific Henry constants, kLa, gas holdup, pressure-response, and dissolved-gas measurements are missing. Methane, CO2, H2, H2S, and NH3 are explicitly allocated among captured raw gas, dissolved digestate inventory, and uncaptured gas. Gas capture is less than 100%, and dissolved methane is nonzero by default.

H2S transfer is informed by a screening pH speciation, while CO2 and NH3 remain empirical. Water vapour uses a specified wet-gas mole fraction rather than a saturation model. Gas volumes are normalized at 273.15 K and 101325 Pa and are never mixed with actual-volume conditions. The output is raw biogas, not upgraded biomethane.

## Heat And Electricity

H501 applies the digester temperature setpoint. Heating and cooling duties are reported separately; for the current PR3/AD1 placeholder, H501 cools the warm Phase 4 outlet. R501 reports steady vessel heat loss from conceptual insulation area, U-value, ambient temperature, and digester temperature. Reaction heat and future heat-recovery credits are omitted.

Average mixing electricity is:

```text
shaft power = working volume * specific mixing power
electric power = shaft power * operating schedule / motor efficiency
```

M501 conditioning mixing is separately reported. No pump or gas-compression electricity is added without hydraulic data.

## Conservation And Validation

M501, H501, and V501 are component-conservative. R501 exports a component reaction-delta ledger. The whole-plant check applies all upstream phase transfers and molecular reaction deltas before comparing external products.

Strict checks cover total mass, every component, COD, C, N, P, S, non-negativity, gas allocation, AD0 zero methane, and methane below the converted-COD ceiling. Hydrogen and oxygen are informational only because pseudo-components lack defensible unique formulas. A full atom-balance claim is therefore intentionally not made.

## Scenarios And Seasonality

AD0-AD3 are active and rebuild safely in one Python session. AD4 two-stage and AD5 high-rate routes raise clear missing-data exceptions. Monthly rates are multiplied by each month's operating hours; annual quantities are summed, and peak monthly volume is retained for design. No annual-average-only sizing claim is made.

## Design, Costing, And Data Gaps

Custom Phase 5 units expose design results, heat utilities, power utilities, warnings, and limitation IDs. No digester, gas-holder, or custom separator CAPEX is assigned because no approved vendor quote or traceable correlation exists. H501 retains its supported built-in BioSTEAM result. Cost warnings are not globally suppressed.

The permanent limitation register records the module, unit, category, simplification, reason, result impact, affected outputs, priority, required data, preferred source, validation method, temporary value, uncertainty need, and planned upgrade. Major missing evidence includes BMP/time-course digestion tests, seasonal COD/VFA/TAN/alkalinity/sulphate data, titration curves, inhibition tests, dissolved-gas measurements, reactor/mixer vendor data, hourly availability, and regulatory characterization.

## Phase 6 Interface

Future work may consume `raw_biogas` and `digestate` as standardized interfaces. Gas upgrading, sulphur removal, nutrient recovery, digestate separation, TEA/LCA, uncertainty, and MCDA must preserve the Phase 5 inventories and limitation links. No future pathway should reinterpret the current class-E structural outputs as validated performance.
