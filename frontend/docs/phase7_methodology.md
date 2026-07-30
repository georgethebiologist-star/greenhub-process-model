# Phase 7 Methodology

## Boundary And Build Sequence

The factory calls the selected Phase 6 factory, then takes `upstream.streams["digestate"]`. That stream is the actual result of the selected F/PR/AD chain. Phase 7 never creates a fixed digestate template.

The BioSTEAM build order follows the project convention:

1. Configure the shared thermo and settings.
2. Create a fresh named flowsheet through the upstream factory.
3. Create streams separately from explicitly identified units.
4. Connect units with BioSTEAM stream piping.
5. Create the integrated system from external end streams.
6. Add convergence settings only when Phase 6 or NR6 contains a real recycle.
7. Simulate, validate, calculate metrics, then report.

The default is NR4 Order A:

```text
Phase 5 digestate
-> T701 equalization
-> S701 solid-liquid separation
-> R711/S711 struvite recovery
-> M721/H721/A721 ammonia stripping
-> A722/V722 acid capture and liquid product storage
-> residual liquor
```

NR7 adds E741 or M741 and V741. Orders B and C reconnect the same mechanism-based units rather than applying alternative fixed splits.

## Unit Methods

### T701 Equalization

T701 is a steady-state homogenization vessel. Working volume equals liquid volumetric flow times residence time. Total volume divides working volume by the working fraction. Mixer electricity is volume times specified power density divided by motor efficiency. Optional measured residual-gas release transfers explicit CH4, CO2, NH3, and H2S without chemical conversion.

Heat loss, settling, storage dynamics, and continuing digestion are not active because supporting data are absent.

### T701 Equalization

The working volume is hydraulic flow times residence time. A configurable cylindrical
height-to-diameter ratio gives the reported dimensions. The reported class-E heat loss
uses the workbook U-value, exposed tank area, and positive feed-to-ambient temperature
difference; it is a design estimate, not a dynamic tank-temperature prediction.

### S701 Solid-Liquid Separation

Particulate classes receive independent capture fractions. Microbial biomass, particulate phosphorus, fixed solids, and contaminant pools have dedicated controls. A single entrained-liquor fraction is solved from captured dry particulate and target cake moisture. That fraction transfers water and every dissolved component together, preventing impossible independent water/solute splits.

S701 is a Level-1 mechanical allocation. The workbook can select `screw_press`,
`decanter_centrifuge`, or `belt_filter`, but these alternatives do not receive distinct
performance curves until pilot or vendor data are supplied.

### R711/S711 Struvite

R711 dynamically prepares the selected magnesium and base solutions. Molecular reagents are converted to explicit ions and counterions. Struvite formation is bounded by Mg, NH4, PO4, target recovery, and six waters per mole. Residual reactants remain in mother liquor. Simplified competing Ca phosphate, Mg hydroxide, and Ca carbonate reactions run only after struvite allocation.

S711 captures target crystals and non-target solids with separate efficiencies. Mother-liquor entrainment follows product moisture. Existing upstream struvite can also be physically recovered and is distinguished from newly formed material in reactor design results.

### R712/S712 Calcium Phosphate

R712 selects one explicit formula: calcium phosphate, dicalcium phosphate, or hydroxyapatite. The selected stoichiometry is reactant-limited. This is bookkeeping for a configured product alternative, not proof of mineral purity. S712 uses the same physical crystal-separation method as S711.

### M721/H721/A721/A722

M721 adds a mass-explicit base solution. The target pH is metadata; pure base dose comes from the workbook until digestate titration data are available. H721 calculates sensible heat from mass, heat capacity, and temperature lift.

A721 calculates free ammonia from temperature-dependent NH4/NH3 equilibrium and combines it with an apparent NTU response to pH, pressure, gas ratio, packing height, and transfer coefficient. NH4 converted to NH3 produces an explicit hydrogen ion. Air, steam, and vacuum modes create distinct carrier, water, pressure, heat, and blower/vacuum duties.

A722 consumes H2SO4 or HCl stoichiometrically and creates explicit ammonium sulfate or ammonium chloride. It reports a liquid solution with residual water and acid. No dry-crystal claim is made.

### A731/R731 Ion Exchange

The Na-form and NH4-form zeolites are formula-balanced exchange-site equivalents. A731 consumes regenerated Na sites while transferring NH4 from liquor and Na to liquor. R731 consumes NaCl, restores Na sites, and transfers NH4 plus chloride to an ammonium-rich regenerant. The media loop is a real BioSTEAM recycle and receives convergence tolerances.

Capacity, breakthrough fraction, and service time size average media inventory. Dynamic breakthrough, competing-ion selectivity, and attrition are not represented.

### E741/M741 Potassium Concentration

E741 removes a selected fraction of water and transfers specified volatile CO2/NH3 to vapor. All nonvolatile salts and contaminants co-concentrate. The scaling index is only a concentration ratio.

M741 calculates water recovery from net pressure and applies different rejection factors to K, other monovalent ions, divalent ions, organics, solids, and contaminants. Cleaning water leaves as wastewater. The concentrate is not a pure potassium fertilizer.

### Product Finishing

W711/W712 and D711/D712 are supported but disabled by default. Washing uses empirical mother-liquor displacement and target-product loss. Drying removes water to a target wet-basis moisture and blocks temperatures above the configured stability limit. Experimental solubility, attrition, stability, and dryer data are required before activation.

## Utilities

Every Phase 7 unit reports local power and heat/cooling utility duty. Recovered heat is credited only when:

- an upstream metric or explicit interface provides available heat;
- the source temperature is at least the demand temperature;
- the recovery efficiency and available heat bound are respected.

The allocation is performed once across eligible Phase 7 demand. Current Phase 6 has no CHP/utility network, so the default credit is zero. The same rule applies to CHP electricity.

## Seasonality And Sizing

Each selected month is an independent steady state. Annual quantities multiply rates by that month's operating hours. Key equipment reports peak load, safety-factor design load, and minimum positive turndown. No intermonth inventory carryover or hourly dynamic response is claimed.

## Validation

Unit checks compare inlet components plus explicit reaction deltas with outlets, then independently require raw mass and elemental conservation. Boundary checks include digestate and every Phase 7 reagent/carrier input against every product, residual, wastewater, and off-gas output. Strict elements are C, H, O, N, P, K, Mg, Ca, S, Cl, and Na. Aggregate contaminants are also checked individually.
