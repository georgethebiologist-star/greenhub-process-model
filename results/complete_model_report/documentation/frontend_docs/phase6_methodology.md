# GreenHub Phase 6 Methodology

## 1. Purpose And Boundary

Phase 6 starts at the Phase 5 `raw_biogas` stream. It does not recalculate anaerobic methane production. The implemented boundary contains:

```text
raw biogas
-> common conditioning
-> selected gas-upgrading pathway
-> gas product + reject gas + wastewater + spent material
```

The selected pathway is controlled in the master workbook. BG0, BG2, BG3, BG4, and BG5 are active. BG1 and BG6 are explicit inactive architectures.

The next engineering section will add CHP, combustion, final biomethane compression, storage, grid-injection preparation, and the plant-wide utility network. Local Phase 6 duties are calculated now so those interfaces are ready, but no plant-wide heat or electricity credit is applied.

## 2. Input And Evidence Rules

The `Phase6Parameters` sheet uses the same provenance structure as earlier phases. Scenario-specific rows override `All` rows, and month-specific rows override `All` months. Every selected record carries:

- parameter name and Python name;
- value and unit;
- minimum and maximum;
- required or optional status;
- measurement status and source quality class;
- reference, method, comment, and limitation ID.

Required missing values raise an exception. Optional blanks are omitted from the resolved dictionary. Class-E required inputs require structural-test mode. The baseline is therefore executable for architecture and balance verification but is not calibrated project performance.

## 3. Chemicals And Bookkeeping

Existing methane, carbon dioxide, hydrogen, hydrogen sulfide, ammonia, oxygen, nitrogen, and water chemicals are reused. Phase 6 adds:

- real `Monoethanolamine` and `FerricOxide` where database identities are defensible;
- `Siloxanes` as a gaseous D5-equivalent marker;
- `ActivatedCarbon` and `PSAAdsorbent` as solid inventory markers;
- `CapturedHydrogenSulfide` as an H2S-equivalent retained pool;
- `FerricSulfide` for the simplified iron-sponge reaction;
- `AmmoniumChloride` for acid-scrubber bookkeeping;
- `Antifoam` as an optional liquid formulation marker;
- `MEADegradationProducts` as one formula-equivalent degradation pool.

These markers are sufficient for material, element, utility, TEA-inventory, and LCA-inventory interfaces. They are not compound-resolved product claims.

## 4. Normal Gas And Pressure Basis

Normal volume uses:

```text
T_N = 273.15 K
P_N = 101325 Pa
V_N = n R T_N / P_N
```

The resulting molar volume is imported from the Phase 5 gas-normalization implementation. Wet volume includes water. Dry volume excludes water. Reports always identify wet or dry basis.

Actual gas volume for screening design uses the ideal-gas expression:

```text
V_actual = n R T / P
```

## 5. Common Raw-Biogas Conditioning

### 5.1 G601 Raw-Biogas Cooler

G601 lowers temperature and pressure according to workbook values. Saturated water pressure is calculated with the Magnus equation over the restricted range of -45 to 80 degC:

```text
p_sat = 610.94 exp[17.625 T_C / (T_C + 243.04)]
```

For dry-gas molar flow `n_dry`, saturated gas water is:

```text
y_water = p_sat / P
n_water,sat = n_dry y_water / (1 - y_water)
```

G601 reports expected condensable water, sensible cooling, latent cooling, and fan electricity. It does not remove liquid itself; S601 performs the physical split.

### 5.2 S601 Condensate Separator

S601 transfers water above the saturation inventory to an explicit condensate stream, subject to a bounded carryover fraction. Small empirical NH3, H2S, and CO2 dissolution fractions may transfer trace gas into condensate. Working volume is residence-time based. No droplet distribution, demister correlation, or rigorous condensate speciation is claimed.

### 5.3 R601 Hydrogen-Sulfide Removal

The selected baseline uses activated carbon. Removed H2S is tracked in `CapturedHydrogenSulfide`, and fresh/spent carbon follows the selected media capacity.

Optional iron-sponge mode uses the screening reaction:

```text
Fe2O3 + 3 H2S -> Fe2S3 + 3 H2O
```

Optional biological mode uses:

```text
H2S + 0.5 O2 -> S + H2O
```

Air nitrogen, unused oxygen, reaction products, and spent material are retained. No iron hydration, microbial kinetics, or breakthrough curve is invented.

### 5.4 R602 Ammonia Removal

Water-wash mode applies bounded apparent gas-to-liquid transfer fractions for NH3, CO2, H2S, and CH4. Acid mode additionally applies molecular salt bookkeeping for HCl or H2SO4. It does not claim pH-dependent Henry equilibrium or rigorous ionic speciation.

### 5.5 F601 Particle And Siloxane Filter

F601 removes specified fractions of the particulate group and aggregate siloxane marker. Media inventory follows gas contact time and bulk density. Replacement follows captured contaminant divided by media capacity. Blank contaminant measurements remain zero and do not create artificial loading.

## 6. BG0 Raw-Biogas Reference

BG0 bypasses all common conditioning and upgrading. A full-pass splitter creates the reference gas product and a zero reject stream. This case provides an engineering reference only; `biomethane_produced_nm3_hr` remains zero because raw gas is not labelled biomethane.

## 7. BG2 High-Pressure Water Scrubbing

### 7.1 Configuration

```text
conditioned gas + flash-gas recycle
-> C611 compressor
-> E611 aftercooler
-> A611 absorber
-> V611/D611 moisture guards
-> biomethane

rich water -> V612 flash -> A612 regenerator -> P611 -> water recycle
```

### 7.2 Apparent Absorption

For each selected gas component, an empirical reference absorption fraction `f_ref` is scaled by pressure, liquid circulation, and temperature:

```text
exposure = (P/P_ref)(L/G)/(L/G)_ref exp[k_T(T_ref - T)]
f = 1 - (1 - f_ref)^exposure
```

`f` is bounded between zero and one. This gives physically monotonic response without claiming a Henry-law stage calculation. CO2, H2S, NH3, CH4, and water remain explicit in gas and liquid ledgers.

V612 releases selected dissolved fractions at flash pressure. A selected portion of flash gas returns to the compressor feed. A612 releases additional gas at regeneration pressure, applies water purge, and returns regenerated water through P611. Fresh water equals the calculated circulation deficit and cannot be negative.

### 7.3 Design And Utilities

A611 geometry uses actual gas volume divided by a selected superficial velocity. Packing height is explicit. Flash volume uses liquid residence time and density. C611, E611, and P611 are installed BioSTEAM units; A611/V612/A612 are transparent custom Level-1 units without invented CAPEX.

## 8. BG3 Membrane Separation

### 8.1 Transport Equation

For component `i` and one area segment:

```text
J_i = permeance_i (y_i,feed P_feed - y_i,perm P_perm)
dn_i = J_i dA
```

The GPU conversion is explicit. Negative driving force gives zero transfer. Transfer is capped by component availability. The membrane area is divided into sequential segments; feed and permeate compositions update after every segment. This is preferable to applying inlet composition over the full module.

Stage cut is calculated:

```text
stage cut = total permeate molar flow / stage feed molar flow
```

It is not an independently imposed purity or recovery target. One to three stages are supported. Downstream permeate may be split between recycle and reject. Compression, aftercooling, drying, stage pressure loss, module count, and membrane replacement interfaces are reported.

The active structural baseline uses class-E pure-component-equivalent permeances. Mixed-gas selectivity, plasticization, competitive sorption, aging, fouling, and validated module hydraulics require vendor or pilot data.

## 9. BG4 Pressure Swing Adsorption

BG4 is a Level-1 steady cycle-average representation. Component adsorption fractions are adjusted by pressure relative to a calibration pressure and remain bounded. Captured gas enters blowdown. A selected fraction of remaining product enters purge. Optional purge recycle is supported.

Adsorbent inventory is based on CO2 captured during adsorption time:

```text
m_CO2,cycle = m_CO2,captured x t_ads / 60
m_adsorbent = m_CO2,cycle / working_capacity x number_of_beds
```

Bed volume uses bulk density. Annual attrition produces equal fresh and spent adsorbent flows. Blowdown, purge, product, and spent material close component balances. No dynamic breakthrough, competitive isotherm, equalization sequence, or pressure history is claimed.

## 10. BG5 MEA Chemical Absorption

### 10.1 Equivalent Loading

The active Level-1 model represents reversible amine capacity without explicit ions. Required MEA circulation is calculated once from captured CO2 and the selected loading window:

```text
n_MEA = n_CO2,captured / (alpha_rich - alpha_lean)
```

Fresh MEA replaces degradation and physical loss. Fresh water restores selected solution concentration. Optional antifoam may remain blank and then contributes zero.

The absorber transfers the selected CO2, H2S, and CH4 fractions into rich solvent. Methane is released to stripper overhead so it appears as explicit reject-gas loss rather than accumulating in the recycle. H2S regeneration, water overhead, reflux, physical solvent loss, and degradation are explicit.

### 10.2 Heat

Absorption cooling is:

```text
Q_abs = n_CO2,captured x heat_of_absorption
```

Regeneration heat uses the selected Level-1 specific-energy basis:

```text
Q_reboiler = m_CO2,released x specific_regeneration_energy
```

The physical rich/lean exchanger is represented by linked calculation blocks. E641 computes rich-side heating and recovered duty from solvent heat capacity, temperature difference, and recovery fraction. E643 applies the same bounded duty to the lean stream. This creates one physical solvent tear stream instead of two algebraically dependent BioSTEAM tears. No mass or chemistry crosses the exchanger, and the two reported duties must match.

V641 condenses overhead water and returns selected reflux. P641 and E642 provide circulation pressure and final lean-solvent cooling. A rigorous future model needs electrolyte activities, rate-based packing, VLE, water vaporization, approach temperatures, corrosion, and degradation data.

## 11. Recycle Convergence

No convergence settings are added to BG0 or any zero-recycle configuration. For actual water, membrane, PSA, or MEA recycle loops, BioSTEAM uses Aitken iteration with:

```text
absolute molar tolerance = 1e-8 kmol/hr
relative molar tolerance = 1e-7
temperature tolerance = 1e-4 K
maximum iterations = 200
```

BioSTEAM may place detected loops in generated subsystems. The factory propagates these tolerances recursively to those subsystems; otherwise they would retain looser package defaults.

## 12. Mass, Component, And Element Balances

For each Phase 6 unit:

```text
outlet inventory = inlet inventory + explicit reaction delta
```

At the Phase 6 boundary, external inputs include raw biogas, water, media, air, acid, adsorbent, and MEA makeup. Outputs include gas product, reject gas, wastewater, and spent material. Every defined component is checked.

CHONPS elemental flows are calculated from explicit formulas and metadata. The Phase 6 components have formula conventions sufficient for strict carbon, hydrogen, oxygen, nitrogen, phosphorus, and sulfur closure. Methane receives a separate destination balance across product, reject, wastewater, and spent material.

The default failure tolerance is `1e-6 kg/hr`. Residuals above `1e-8 kg/hr` are also reported as warnings even when below failure tolerance.

## 13. Gas-Quality Validation

Conditioned gas is checked against workbook limits for:

- maximum temperature;
- minimum pressure;
- maximum wet water fraction;
- maximum dry H2S and NH3 ppmv;
- maximum dry oxygen fraction;
- maximum particulate and siloxane mass;
- minimum dry methane fraction.

In structural-test mode, a failed suitability check becomes a prominent warning. Outside structural mode it raises an error. These are pathway feed checks, not proof of compliance with any current grid or vehicle-fuel standard.

For BG2-BG5, reject gas must be more CO2-rich than product gas. Stage cuts, adsorption, removals, loadings, and inventories must remain non-negative and bounded.

## 14. Utilities, Design, And Costing

Every Phase 6 unit reports electricity, heating, cooling, design quantities, warnings, and limitation IDs. The common comparison reports local Phase 6 utilities per unit and per normal cubic metre of product.

Built-in compressors, pumps, and utility exchangers retain BioSTEAM design and cost results. Structural throughput is far below the built-in compressor cost range, so `CostWarning` is expected and not suppressed. Custom cleaning and upgrading units have zero CAPEX until an approved capacity correlation or vendor quotation is available.

The current `net_usable_energy_kw_direct_basis` subtracts local electricity and heat from product methane LHV. It is not a plant-wide utility-network result and does not include future heat quality, CHP, final compression, or site demand matching.

## 15. Common Comparison Metrics

All active scenarios report:

- raw biogas processed and biomethane produced;
- wet and dry gas composition;
- dry methane purity, recovery, slip, and explicit destinations;
- CO2 removal and reject composition;
- product pressure;
- electricity, heat, and cooling;
- fresh water, wastewater, and chemical makeup;
- direct-basis net usable energy;
- technology-specific equipment capacity;
- recycle status and calculation level.

The comparison workbook does not score or rank alternatives.

## 16. Test Coverage

Dedicated tests verify:

- common cooler, condensate, H2S, NH3, particle, and siloxane balances;
- water-scrubber mass, methane, water, flash recycle, and circulation response;
- membrane stage balance, stage cut, area response, and recycle convergence;
- PSA cycle-average balance, capacity response, and purge methane accounting;
- MEA solvent, loading, regeneration, heat, and working-capacity response;
- scenario isolation, deterministic rebuild, inactive data gates, and gas-quality reporting;
- selected, comparison, limitation, CSV, and Excel report generation.

## 17. Data Needed Before Technology Selection

The highest-priority missing evidence is:

- seasonal complete raw-gas composition, humidity, pressure, and flow;
- H2S, NH3, siloxane, and particulate loading and media breakthrough data;
- water-scrubber pilot gas/liquid balances and mass-transfer data;
- mixed-gas membrane and module vendor performance;
- PSA competitive isotherms and validated cycle data;
- rate-based MEA, electrolyte, heat-balance, loss, and degradation data;
- selected product use and applicable gas-quality standard;
- traceable vendor quotations and cost bases;
- CHP, final gas handling, and plant utility-network specifications.

Until these data replace class-E inputs, Phase 6 outputs are structural engineering results only.
