# F1 CAPEX and recorded OPEX by throughput

## Basis

The schedule in `capex_breakdown_by_flow.csv` describes the active F1 grass route with PEF disabled at nominal wet-grass throughputs of 0.5, 1, 2, and 3 t/h. Each row is from an independent completed GreenHub/BioSTEAM simulation and downstream TEA resolver run, listed by `run_id` in the CSV. The `TEA-013` digester working volume is read directly from each run's unit `R501` `Working volume` design result: 107.8803, 215.7607, 431.5213, and 647.2820 m³, respectively.

The user's density convention, 1 kg wet grass = 1 L, is used only for liquid hydraulic capacities where the TEA register requires a liquid flow/volume capacity. It is not applied to raw biogas, biomethane, solids, nutrient products, or energy.

## Resolver calculations

For equipment with a reference capacity, each run's formed capacity is passed through the same TEA resolver relationship:

`direct CAPEX = reference cost × (project capacity / reference capacity)^scaling exponent`

Every flow-rate row was simulated separately; equipment capacities were read from that run rather than inferred from the 1 t/h case. Unscaled reference packages remain fixed at their register price because the register does not provide a compatible capacity basis. They are explicitly marked as unscaled and their capacity match is unverified.

For `TEA-013`, each run's formed R501 volume is priced at the user-provided Dutch tank range of €1,200–1,800/m³. The midpoint €1,500/m³ is used for `capex_mid_eur`; low/high columns vary this digester tank rate only. The source supplied for this range is [Energy Solutions, anaerobic-digestion economic analysis](https://energy-solutions.co/articles/sub/anaerobic-digestion-economic-analysis-2027-2035). It is a secondary screening source; it does not establish installed plant cost.

Each equipment row includes the TEA register's source title, source URL, reference cost, reference capacity and unit, project capacity, and scaling exponent. The total is the sum of priced selected F1 TEA lines in the regenerated baseline. A row with `installed_capex=False` is direct equipment/package cost only: installation, buildings, piping, electrical integration, engineering, contingency, land, and financing are excluded. The baseline's overall CAPEX remains partial because several equipment selections lack a defensible capacity or price basis.

## OPEX price update

The user-provided magnesium chloride price is USD 573/metric tonne. It is converted using the model's explicit screening FX assumption of 0.92 EUR/USD to EUR 527.16/t, or EUR 0.52716/kg. The linked ChemAnalyst page is a price inquiry form and does not display that quote publicly; the price and exchange-rate basis are therefore identified as screening inputs, not independently verified market data. The quote's grade/hydration basis is unspecified.

TEA-051 uses annual R711 `Magnesium reagent` design mass multiplied by modeled operating hours. For the current F1 NR4 BioSTEAM runs, R711's orthophosphate feed is zero and the resulting MgCl2 demand is zero apart from negligible floating-point residuals (< 2e-14 kg/year). The priced TEA-051 line therefore adds effectively EUR 0/year to recorded OPEX. No stoichiometric dose is inferred from total phosphorus. Annual OPEX in the CSV is the model's recorded **partial** OPEX; other selected consumable quantities remain unresolved, so this is not a complete operating-cost estimate.

## Interpretation

These values are screening CAPEX, not a vendor quotation or investment-grade estimate. Unscaled packages should be replaced with vendor quotations and confirmed design capacities before financial decisions. The 1 t/h values match the decision-support TEA resolver; other flow rates use their own BioSTEAM run and resolver results.
