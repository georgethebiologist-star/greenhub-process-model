# GreenHub Phase 4 Methodology

## 1. Scope and Boundary

Phase 4 begins at `clarified_protein_rich_liquid`, the common C301 outlet from either the F0 measured-liquid mode or the F1-F3 roadside-grass modes. It ends at:

- `dry_protein_product`;
- `dryer_exhaust`;
- `conditioned_protein_depleted_liquid`;
- retained upstream side streams such as fibre cake and primary sludge.

No digestion, biomethane upgrading, nutrient recovery, product-market pricing, full TEA, LCA, uncertainty, or MCDA is included.

## 2. BioSTEAM Structure

Thermodynamics are initialized before streams. Units use explicit `ID`, `ins`, and `outs`, and the complete no-recycle system is created through the active fresh flowsheet. The baseline train is:

```text
M401 -> H401 -> R401 -> C401 -> W401 -> D401 -> DR401
                       liquids -> M402 -> M403
```

H401 is BioSTEAM `HXutility`; M402 is BioSTEAM `Mixer`. The remaining Phase 4 operations are custom `bst.Unit` subclasses because no installed built-in unit matches the required empirical recovery, cake-moisture, washing, product-loss, and neutralization bookkeeping without unsupported assumptions.

## 3. Protein Pools

The recoverable true-protein inlet contains:

```text
SolubleProtein + SuspendedProtein
```

Recovery-state pools are:

```text
PrecipitatedProtein
HeatCoagulatedProtein
DegradedProtein
```

All five pools use the same representative molecular-weight and C/H/O/N/S, COD, and TOC conventions. Their transformation is therefore a one-to-one mass reclassification, not synthesis or destruction.

`Peptides` and `AminoAcids` are reported separately. They are nitrogen- and COD-bearing material but are not counted as recoverable true protein. Ammonia and ammonium are inorganic nitrogen and never counted as protein nitrogen.

Aggregate roadside-grass protein is not one molecular species. The pool model cannot resolve individual proteins, exact isoelectric points, protonation sites, digestibility, or biological quality.

## 4. Acid Demand

M401 supports three methods.

### Empirical dose

```text
pure acid [kg/h] = dose [kg/m3] x liquid flow [m3/h]
```

### Simplified acid-equivalent balance

Demand includes measured alkalinity, free-H+ difference, and an optional buffer-capacity term. Acid equivalents are converted using one equivalent per mole HCl and two per mole H2SO4.

### Titration interpolation

The model linearly interpolates within a strictly increasing dose and non-increasing pH table. It rejects extrapolation and requires at least two active measured points.

Commercial solution flow is:

```text
solution = pure acid / (solution mass fraction x purity)
reagent water = solution - pure acid
```

Acid demand is never inferred from protein mass.

## 5. pH Limitations

pH is metadata, not a stream component. The model does not solve electrolyte activities, ionic strength, charge balance, dissociation equilibrium, buffering reactions, or local pH gradients. Acid-equivalent mode is a transparent screening calculation, not rigorous thermodynamics.

## 6. Precipitation and Kinetics

R401 supports direct yield, bounded pH response, and first-order recovery.

The optional aggregate-pI response is:

```text
X_pH = X_max exp[-0.5 ((pH - pI) / width)^2]
```

The kinetic mode is:

```text
X = X_pH (1 - exp(-k t))
```

An optional Arrhenius correction is available only when a reference rate and supported activation energy are supplied:

```text
k(T) = k_ref exp[-Ea/R (1/T - 1/T_ref)]
```

All recoveries are bounded from zero to one. The structural baseline uses direct-yield mode because fitted kinetics are unavailable.

## 7. Heat Coagulation

Heat recovery transfers remaining soluble protein to `HeatCoagulatedProtein`. Combined PR3 applies acid recovery first and heat recovery to the remaining soluble pool. This avoids double counting. H401 computes sensible heating through BioSTEAM enthalpy and utility handling.

## 8. Co-precipitation

C401 uses separate categories for suspended solids, colloidal carbohydrates, lipids, particulate phosphorus, mineral ash, heavy metals, microplastics, and other particulates. When a component matches several categories, the largest selected fixed-capture fraction is used and reported.

One universal non-protein split is not used. Soluble salts remain in liquid except for uniform liquid entrainment or explicit wash behavior.

## 9. Protein Separator

C401 first applies fixed dry-component capture. It then solves one uniform dissolved-liquid entrainment fraction, `f`, to meet cake moisture `m`:

```text
f = m fixed_dry_solids / [(1 - m) water - m dissolved_solids]
```

The solver rejects negative denominators and targets requiring more liquid than is available. Dry capture is never changed to force cake moisture.

## 10. Cake Washing

W401 is an optional single-stage displacement wash. Wash water is specified per kg dry cake. Independent removal fractions apply to soluble salts, sugars, residual acid, soluble COD, and protein wash loss. Insoluble protein is not arbitrarily dissolved. All removed material enters `protein_cake_wash_filtrate`.

## 11. Dewatering

D401 compares incoming solids with `target_dryer_feed_solids_fraction`. It bypasses without power if the target is already met. Otherwise, fixed solids are retained, configured protein loss is routed to filtrate, and dissolved liquid entrainment is solved for the target solids fraction.

## 12. Dryer Selection

A low-temperature belt dryer is selected structurally because the feed is a dewatered, heat-sensitive cake rather than a pumpable atomization feed. Spray drying is not assumed. Vendor testing is required for actual temperature, residence time, capacity, air flow, product handling, fouling, and cost.

## 13. Dryer Mass Balance

After explicit dry dust and protein entrainment losses:

```text
target product water = retained dry matter x moisture / (1 - moisture)
evaporated water = inlet water - target product water
```

All evaporated water and dry losses enter `dryer_exhaust`. Thermal degradation transfers retained precipitated/coagulated protein into `DegradedProtein`; it does not destroy mass, nitrogen, COD, or TOC.

## 14. Dryer Energy

Exactly one method is active.

### Thermodynamic screening method

```text
Q_useful = sensible water + sensible dry solids + latent evaporation
Q_external = Q_useful / [thermal efficiency x (1 - heat-loss fraction)]
```

### Empirical specific-demand method

```text
Q_useful = water evaporated x specific heat demand
```

The methods are mutually exclusive. Electricity is specified per kg water evaporated. No hypothetical heat-recovery credit is subtracted. Air mass, humidity, recycle, and psychrometrics are not represented; drying air is a utility-only interface. Drying assumptions strongly affect energy demand.

## 15. Neutralization and Salt Formation

M403 supports sodium hydroxide and calcium hydroxide commercial solutions. The structural baseline neutralizes residual molecular acid stoichiometrically:

```text
HCl + NaOH -> NaCl + H2O
2 HCl + Ca(OH)2 -> CaCl2 + 2 H2O
H2SO4 + 2 NaOH -> Na2SO4 + 2 H2O
H2SO4 + Ca(OH)2 -> CaSO4 + 2 H2O
```

All reactions are validated for component availability, atoms, and mass. Product pH remains metadata. Simplified molecular salts avoid losing sodium, calcium, chloride, or sulfate inventory but do not constitute an electrolyte or solubility model.

Calcium-phosphate precipitation is prepared and validated but disabled by default. It requires explicit calcium availability, phosphate availability, pH conditions, and conversion.

## 16. Scenarios

- PR0: bypass; all protein remains in the conditioned-liquid stream.
- PR1: acid precipitation, separation, dewatering, drying, and neutralization.
- PR2: heat coagulation, separation, dewatering, and drying without acid/base addition.
- PR3: combined acid and heat, single wash, dewatering, drying, and neutralization.
- PR4: lactic fermentation inactive pending conversion, yield, kinetic, and biomass data.
- PR5: CO2 precipitation inactive pending gas-liquid transfer, pressure, dissolution, and titration data.
- PR6: ultrafiltration inactive pending flux, retention, TMP, fouling, and cleaning data.

## 17. Validation

The default failure tolerance is `1e-6 kg/h`. Unit and plant checks include:

- total and component mass;
- declared pool-transfer-adjusted components;
- reaction-adjusted components;
- C, H, O, N, P, S, K, Na, Mg, Ca, and chloride;
- true-protein reconciliation;
- total nitrogen;
- COD and TOC;
- cake and product moisture;
- no negative flows;
- monthly and annual aggregation;
- repeated isolated scenario construction.

Precipitation, washing, drying, and separation redistribute COD/TOC and nitrogen. They do not destroy these inventories.

## 18. Costing

No custom Phase 4 unit has CAPEX because no approved GreenHub correlation, currency basis, reference year, size exponent, or vendor quote is available. H401 utility use is costable through BioSTEAM settings, but Phase 4 is not a final TEA. No selling price is assigned.

## 19. Product Quality

The model reports wet/dry purity, moisture, ash, carbohydrate, lipid, N, P, sodium, chloride, sulfur, salt, and modelled contaminant pools. The product remains `unclassified`. Regulatory, food, feed, fertilizer, microbiological, pathogen, toxicological, and legal suitability are not determined.

## 20. Data Gaps

Priority data needs are:

1. monthly clarified-liquid protein and solids measurements;
2. acid titration curves by month or representative feed class;
3. recovery versus pH, temperature, and residence time;
4. component-specific co-precipitation and separator capture;
5. cake wash displacement data;
6. mechanical dewatering performance;
7. dryer moisture, heat, air, dust, degradation, and capacity data;
8. neutralization titration and salt/inhibition measurements;
9. product-quality and regulatory criteria;
10. vendor design and cost data.

## 21. Phase 5 Interface

`conditioned_protein_depleted_liquid` is the future digestion inlet. It retains residual protein, peptides, amino acids, sugars, organic acids, COD, N, P, K, minerals, neutralization salts, and contaminants. Phase 5 should consume this stream directly and preserve the existing monthly, metadata, and validation interfaces rather than rebuilding its inventory.

Phase 4 is not a final TEA or LCA.
