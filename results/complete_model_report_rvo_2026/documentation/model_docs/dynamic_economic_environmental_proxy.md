# Economic and environmental proxy analysis

`Greenhub/dynamic_economic_environmental.py` consumes the scheduled annual
report. It never changes process calculations. It exposes
`proxy_analysis_ready`, `validated_tea_ready=false`, and
`validated_lca_ready=false`. Blocked/strict process scenarios receive factor
metadata and limitations, but no analysis totals.

## Factors and provenance

Every factor is in `FACTOR_DEFAULTS`, returned by `/dynamic-complete/options`
and editable in the dashboard. **None of these defaults is a sourced price,
market forecast, jurisdiction-specific emission factor, or validated LCA
inventory.** They are deliberately illustrative placeholders. Metadata records
the policy ID, value, unit, source status, certainty, source ID and warning.
Default factors use `engineering_assumption` with an empty source file and an
explicit no-source warning. User overrides use `user_input`, with the same
warning. Inputs must be finite and non-negative; fractions are bounded by one.

| Factor | Illustrative value | Unit |
| --- | ---: | --- |
| Protein product price | 2.00 | EUR/kg dried product |
| Biomethane price | 0.80 | EUR/m³ product gas |
| Fertilizer candidate price | 0.10 | EUR/kg candidate wet product |
| External press cake credit | 0.03 | EUR/kg cake |
| Electricity price | 0.18 | EUR/kWh |
| Heat price | 16 | EUR/GJ |
| Reagent / other utility costs | 0 / 0 | EUR/t feed |
| Natural gas displacement | 2 | kg CO₂e/m³ recovered CH₄ |
| Electricity emissions | 0.4 | kg CO₂e/kWh |
| Heat emissions | 56 | kg CO₂e/GJ |
| Fertilizer displacement | 0.5 | kg CO₂e/kg candidate wet product |
| Methane GWP multiplier | 28 | kg CO₂e/kg CH₄ |
| Unrecovered methane emitted | 1 | fraction of tracked slip |

The methane multiplier is an unsourced scenario coefficient, not a declaration
of compliance with a named assessment standard or time horizon. Attach and
validate sources before interpreting these outputs as TEA or LCA.

## Economic arithmetic

Revenues multiply scheduled annual dried product, product gas, fertilizer
candidates and external press cake by their corresponding prices. Fertilizer
revenue includes ammonium, struvite and potassium concentrate once each; it
does not double-count intermediate digestate, nutrient-rich solids or loaded
ion-exchange media. Product marketability is unvalidated.

Costs multiply included gross electricity and heat by their prices, plus
optional reagent and other utility costs per tonne feed. Operating margin is
total revenue minus these included costs. Cost per tonne feed, per kg dried
product and per m³ biomethane each divide **the same gross included cost** by a
different output; no coproduct allocation is implied. Zero denominators return
`null`, not infinity. CHP heat/electricity are reported in process outputs but
are not automatically credited, exported or netted from demand because use and
integration are unresolved.

The annual chart shows revenue/credits positive and included costs negative.
CAPEX, feed purchase/collection, labor, maintenance, transport, financing,
taxes and numerous utilities are excluded. Zero default reagent/utility costs
mean omitted costs, not free inputs. Mass-only drying further omits dryer
utilities. Consequently operating margin is not profit or investment return.

## Environmental arithmetic

Positive values are burdens; negative values are avoided-emission credits.

- Avoided natural gas: recovered CH₄ m³ × displacement factor, negative.
  This uses methane content, not total biomethane product volume.
- Electricity and heat: included gross utilities × their emission factors.
- Fertilizer displacement: selected candidate wet mass × displacement factor,
  negative. Nutrient-equivalent substitution is not validated.
- Methane slip: tracked reject/conditioning methane mass × assumed emitted
  fraction × methane multiplier. Offgas destruction is not assumed. The model
  does not quantify AD fugitives or CHP exhaust methane, nor does it assume
  raw gas from the “none” route is emitted.
- Net CO₂e: sum of these contributions. Intensities divide by processed tonnes
  and dried-product kg, without coproduct allocation.

No cultivation, land-use change, transport, capital equipment or reagent
production inventory is included. Avoided-emission signs are accounting
choices, not proof of a net environmental benefit. The emissions chart shows
the separate contributions, with signed totals and all factors inspectable.

## Baseline illustrative calculation

For the 30,000 t/year baseline documented in
[dashboard reporting](dynamic_dashboard_reporting.md), included annual revenue
is about EUR 1,940,845, included costs EUR 99,925 and margin EUR 1,840,920.
Included cost is EUR 3.33/t feed, EUR 0.909/kg dried product or EUR 0.0717/m³
biomethane (alternative denominators, not allocated costs).

The emissions arithmetic gives approximately −3,095.5 t CO₂e/year,
−103.18 kg CO₂e/t feed and −28.15 kg CO₂e/kg dried product. These large credits
depend directly on unsourced substitution factors and omitted inventories;
they are illustrations of the analysis interface, not validated conclusions.

Release needs sourced location/year-specific factors and prices, complete
utilities/reagents, credible fertilizer substitution and quality evidence,
offgas treatment/fugitive methane measurements, functional-unit/allocation
choices, uncertainty/sensitivity analysis and independent TEA/LCA validation.
