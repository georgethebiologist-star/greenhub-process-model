# Phase 7 Equations And Bases

## Reporting Conversions

Elemental and compound bases are never compared without conversion.

```text
kg NH4 = kg NH4-N * MW(NH4) / AW(N)
kg NH3 = kg NH3-N * MW(NH3) / AW(N)
kg NO3 = kg NO3-N * MW(NO3) / AW(N)
kg PO4 = kg PO4-P * MW(PO4) / AW(P)
kg struvite = kg struvite-P * MW(struvite) / AW(P)
kg K2O = kg K * 1.205
```

Physical stream components carry compound mass. Analytical metrics report elemental kg N/h, kg P/h, and kg K/h separately.

## Cake Moisture And Entrainment

For captured dry particulate `D`, feed water `W`, dissolved non-water material `L`, target cake moisture `xw`, and common liquid entrainment `e`:

```text
xw = e W / [D + e (W + L)]
e = xw D / [W (1 - xw) - xw L]
```

The implemented solution is bounded to `[0, 1]`. If target moisture is physically unreachable, the achievable endpoint is used and reported.

## Struvite

```text
Mg2+ + NH4+ + PO4--- + 6 H2O -> MgNH4PO4.6H2O(s)
```

```text
n_struvite = min(
    n_Mg,
    n_NH4_available,
    n_PO4,
    target_P_recovery * n_PO4,
    n_H2O / 6
)
```

Competition is allocated only after struvite, preventing the same phosphorus from entering multiple products.

```text
3 Ca2+ + 2 PO4--- -> Ca3(PO4)2(s)
Mg2+ + 2 OH- -> Mg(OH)2(s)
Ca2+ + CO3-- -> CaCO3(s)
```

## Calcium-Phosphate Alternatives

```text
3 Ca2+ + 2 PO4--- -> Ca3(PO4)2(s)
Ca2+ + PO4--- + H2O -> CaHPO4(s) + OH-
5 Ca2+ + 3 PO4--- + OH- -> Ca5(PO4)3OH(s)
```

The extent is the minimum of the target phosphate recovery and every stoichiometric reactant limit.

## Ammonia Equilibrium And Stripping

The free-ammonia fraction is:

```text
f_NH3 = 1 / [1 + 10^(pKa(T) - pH)]
```

The apparent transfer model is:

```text
NTU = k_app
      * sqrt((G/L) / (G/L)_ref)
      * Hpacking / Href
      * sqrt(Pref / P)
      * (T / 298.15)^1.5

removal = 1 - exp(-NTU * f_NH3)
```

Removal is bounded to `[0, 1]` and cannot exceed explicit NH3 plus NH4. NH4 stripping uses:

```text
NH4+ -> NH3(g) + H+
```

Gas-mover power is:

```text
Pshaft = Qactual * deltaP / efficiency
```

## Acid Capture

```text
2 NH3 + H2SO4 -> (NH4)2SO4
NH3 + HCl -> NH4Cl
```

Captured ammonia is limited by feed ammonia, absorber efficiency, and acid moles. Excess acid remains in the liquid product.

## Ion Exchange

`Z` denotes the conserved aluminosilicate exchange-site framework.

```text
Na-Z + NH4+ -> NH4-Z + Na+
NH4-Z + NaCl -> Na-Z + NH4+ + Cl-
```

Average media inventory is:

```text
captured_NH4 = feed_NH4 * recovery
media = captured_NH4 * service_time / (capacity * breakthrough_fraction)
bed_volume = media / bulk_density
```

NaCl demand follows selected mol NaCl per mol exchanged NH4.

## Potassium Concentration

Evaporation:

```text
water_evaporated = feed_water * removal_fraction
Qgross = water_evaporated * latent_heat / thermal_efficiency
```

Membrane:

```text
net_pressure = max(0, applied_pressure - osmotic_pressure)
water_recovery = reference_recovery * sqrt(net_pressure / reference_net_pressure)
area = permeate_volume / water_flux
```

Each solute uses:

```text
concentrate_i = feed_i * rejection_i
permeate_i = feed_i - concentrate_i
```

## Heat Allocation

```text
eligible_demand = sum(demand where source_temperature >= demand_temperature)
recoverable_budget = available_heat * recovery_efficiency
recovered_heat = min(eligible_demand, recoverable_budget)
external_heat = gross_heat - recovered_heat
```

The current default available heat is zero because the CHP and plant heat network are not implemented.
