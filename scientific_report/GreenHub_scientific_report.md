# GreenHub Zuid Holland roadside grass biorefinery scientific assessment

Repository based research draft, 1 November 2026. Model revision `a64bdc076c59bea1befcd734d5ddffb7073c2406` with existing uncommitted workspace changes. The requested MSc manuscript was not supplied with the task text; its literature review and original citations cannot be preserved in this edition. All numerical results below derive from the saved runs in this package.

## 1 Abstract

The GreenHub model was audited and its F2 PR3 AD1 BG2 NR4 A structural reference route was simulated at 1,000 kg/h of fresh roadside grass. A July steady state annualized over 8,760 h gives 8,760 t/y feed, 70.19 t/y dry protein product, 9.04 t/y biomethane stream mass, 1.00 t/y phosphorus product stream, and 87.36 t/y ammonium product stream. Electricity and heating demands are 272.88 and 418.82 MWh/y. Numerical mass closure exceeds 99.999999%, but the run reports 15 warnings and uses hundreds of quality class E structural assumptions. Three matched nutrient route comparisons show that adding P and N recovery increases reported product streams and utilities. Installed capital, full operating expenditure, revenue, and climate impact remain incomplete. Consequently, the research question cannot yet be answered as a joint technical, economic and environmental optimum. The combined P and N route is a technically productive pilot candidate, subject to measured yields, utility validation, product quality, vendor costs, and complete environmental inventories.

## 2 Introduction

Roadside grass is a heterogeneous seasonal feedstock whose liquid fraction can support protein, gas and nutrient recovery. GreenHub Zuid Holland requires a configuration decision based on comparable technical, financial and environmental evidence. This report assesses the implemented model, not a commissioned plant. Its primary research question is: which combination of valorization technologies provides the highest technical, economic and environmental performance for the liquid fraction from roadside grass processing? The analysis evaluates what can currently be calculated and the evidence required to answer that question defensibly.

## 3 Literature and evidence context

The repository implements a literature supported engineering model with BioSTEAM streams and custom operations. Its internal documentation describes empirical separation factors, stoichiometric digestion and nutrient reactions, cost proxies and selected climate characterization factors [1–6]. The original manuscript was absent from the supplied files, so this section cannot reproduce its literature synthesis or references. The source register and parameter metadata should be reconciled against that manuscript before academic submission. In particular, an experimentally measured whole grass profile exists in the VARTA input set, while the reference run used the repository's structural workbook mode; these are distinct evidence bases [1, 7].

## 4 Research objectives

The objectives are to (i) reconstruct the implemented process and data boundaries; (ii) quantify one reproducible baseline; (iii) compare nutrient route variants on a common feed and time basis; (iv) identify economic, environmental and model quality gaps; and (v) state what further evidence is needed for configuration selection. The functional unit for intensity interpretation is one tonne of fresh roadside grass entering the plant.

## 5 Materials and methods

### 5.1 Scope and boundaries

The physical model starts at the roadside grass or measured liquid inlet and includes preparation, mechanical separation, protein recovery, anaerobic digestion, gas conditioning/upgrading, digestate treatment and nutrient recovery. The fibre rich press cake exits as a coproduct; downstream fibre panel production is outside the model. The tested F2 PR3 AD1 BG2 NR4 A route uses PEF assisted preparation, combined acid and heat protein recovery, post protein mesophilic digestion, water scrubbing, and combined struvite and ammonia salt recovery in process order A [1, 4]. The reference is a July steady state repeated for 8,760 h; it is not a measured annual availability profile. The TEA is a post process screening account. The LCA layer is a collection to gate inventory and climate screen with explicit exclusions, not an ISO complete, multi impact LCA [2, 3]. Storage, logistics and seasonality have separate opt in interfaces; they are not activated by this steady reference run.

### 5.2 Architecture and equations

The Python service resolves a versioned simulation request, parameter overrides and workbook inputs, forms a BioSTEAM flowsheet, runs the selected units, exports component and utility inventories, then applies read only TEA and LCA services. The decision support service joins those reports and exposes API ready JSON. Quasi dynamic mode rebuilds the empirical process for each daily or monthly feed step and carries storage inventory; it is not a calibrated continuous dynamic model [1, 2, 8]. The frontend uses this API or a separately labelled lightweight screening proxy. Its 2,000 point Pareto display is not 2,000 BioSTEAM runs [9].

For component i at unit j, the reported balance is m_in,i + m_generated,i − m_consumed,i − m_out,i = residual_i (Eq. 1). For a steady state rate q [kg/h] and operating time H [h/y], annual output Q = qH (Eq. 2). Electrical energy E = Σ P_j H (Eq. 3), while positive heat duty in kJ/h is divided by 3,600 before multiplying by H. TEA scales eligible equipment costs as C = C_ref (S/S_ref)^n (Eq. 4), but missing capacities or installation factors leave installed CAPEX undefined. Complete operating margin would be revenue less OPEX (Eq. 5). NPV requires a complete cash flow C_t and discount rate r: NPV = Σ_t C_t/(1+r)^t (Eq. 6). Climate burden requires annual activity a_i and characterized factor f_i: G = Σ_i a_i f_i (Eq. 7); incomplete included inventory prevents a total [2, 3].

Figure 1. Model architecture: input data → feedstock characterization → BioSTEAM process → mass and utility inventories → post route TEA and LCA → feasibility and Pareto screening → decision support. This is a logical architecture; it does not imply that every objective is currently eligible.

### 5.3 Data provenance and quality

The master workbook governs feed and structural process parameters; source registers hold experimental observations, literature estimates, proxies, cost references, price benchmarks and environmental factors. The data layer records source IDs, units, quality classes, warnings and override precedence. The baseline resolved parameter report contains 538 entries whose evidence class is not populated in the decision support summary, so percentages of measured, literature, assumed and proxy parameters cannot be calculated reliably from that report. The warnings separately identify 67, 69, 80, 84 and 134 selected class E entries in the preparation, protein, digestion, gas and nutrient stages. These stage counts are not a deduplicated global evidence census. The LCA factor registry contains three official characterization records and two missing delivered utility factors [3]. These controls improve findability and traceability, but incomplete source metadata, experimental coverage and calibration limit FAIR reuse and interpretation.

Table 1. Data provenance summary.

| Parameter group | Source type | Representative source | Units | Quality or confidence | Application |
|---|---|---|---|---|---|
| Feed composition | Workbook and measured profile | GreenHub feed workbook; VARTA grass CSV | kg/kg wet feed | Mixed; baseline structural | Stream components |
| Separation and recovery | Workbook engineering assumptions | Phase 3 to 7 registers | Fractions, kg/h, kWh | Class E in baseline | Unit yields and duties |
| Equipment costs | Proxy and cost register | TEA cost CSV | EUR, capacity specific | Low to medium; incomplete | Partial direct CAPEX |
| Product prices | Benchmark register | Product price records | EUR per stated sale unit | Opt in screening only | Revenue when activated |
| Climate factors | Official and missing | Climate factor JSON | kg CO2e per activity | Three official, two missing | Partial LCA inventory |

### 5.4 Feedstock, scenarios and validity

The selected feed is 1,000 kg/h of fresh grass in July. Component masses, moisture, N, P, K and contaminants are retained in `streams.json`; complete laboratory validation of those fields is not claimed. The reference run does not activate the assumed normal seasonal availability profile. A 30,000 t/y supply basis appears in a separate frontend screening study and must not be conflated with this 8,760 t/y process run [9]. The tested nutrient variants are NR0 order D (no targeted recovery), NR2 order A (struvite only), NR3 order A (ammonia recovery only), and NR4 order A (both). All retain F2 PR3 AD1 BG2, 1,000 kg/h, July and 8,760 h. NR5 calcium phosphate, NR6 zeolite and NR7 combined K concentration are structurally implemented but not included in these four comparable runs [4]. PR4 to PR6, BG1 and BG6 are data gated [5]. Numerical closure checks test accounting consistency, not physical validation.

### 5.5 Economic and environmental assessment

The TEA cost register selects route relevant equipment, applies compatible size exponents, and records missing sizing and installation inputs. It calculates only supported annual utility cost and partial direct equipment cost in this baseline. The default price registry is not activated, so zero recorded sales means unavailable revenue evidence, not a zero market value. The decision support report also generates a candidate screening overlay with assumed subsidy, tax and annual recovery values. Because underlying CAPEX, OPEX and revenue are incomplete, its `optimized_after_tax_profit_eur_per_year` must not be interpreted as project profit or used for ranking. Official IPCC gas characterization factors are present, but electricity and delivered heat factors and several boundary inventories are missing. Gross, avoided and net GHG totals remain null. No nutrient or gas substitution credits are awarded without a stated counterfactual [2, 3].

## 6 Results

### 6.1 Baseline technical performance

Table 2 summarizes the fresh reference run. The values are deterministic outputs of the selected structural assumptions, not confidence intervals. Product stream masses are not nutrient element masses. Biomethane is recorded as wet stream mass; no dry normalized volume is asserted here because the report's product record has no volume field or complete compositional normalization.

Table 2. Baseline process results.

| Indicator | Value | Unit |
|---|---:|---|
| Grass processed | 8,760 | t/y |
| Dry protein product stream | 70.19 | t/y |
| Biomethane product stream | 9.04 | t/y, mass inventory only |
| Phosphorus product stream | 1.00 | t/y |
| Ammonium product stream | 87.36 | t/y |
| Nutrient rich solids | 49.77 | t/y |
| Purchased electricity demand | 272.88 | MWh/y |
| Positive heating duty | 418.82 | MWh/y |
| Cooling duty magnitude | 116.71 | MWh/y |
| Overall mass residual | −0.0000607 | kg/y |

The near zero residual corresponds to 99.999999999% numerical closure. It is much smaller than feed mass and does not test whether the chosen yields represent GreenHub material. The highest reported stage electric demand is preparation/PEF at about 235.47 MWh/y; protein recovery is about 22.09 MWh/y. Figure library F1 and F2 show product streams and electrical demand. The current results do not give a defensible annual grass seasonality or nutrient element recovery efficiency from this single run.

### 6.2 Screening economics and environmental inventory

The report identifies EUR 50,000 of partial direct CAPEX and EUR 54,329.59/y of partial OPEX, the latter solely a booked electricity tariff line. These are lower bounds on included account lines, not total project costs. Installed CAPEX, full OPEX, sales, operating margin, NPV, IRR and payback are unresolved. The model's partial cost intensity is EUR 6.20/t fresh feed, with the same incomplete boundary. The default LCA gives no complete or partial annual climate total. It reports 15 missing climate inputs, including electricity and heat factors and incomplete material and transport inventories. Climate superiority and avoided burdens therefore cannot be inferred. Figure library F5 summarizes recorded evidence gaps.

### 6.3 Matched nutrient route comparison

Table 3 compares the four modeled routes. The baseline NR4 produces both nutrient streams at the highest heating demand in this set. Relative to NR0, NR4 adds 2.67 MWh/y electricity and 109.18 MWh/y positive heating duty. NR2 adds a phosphorus product stream with approximately 2.60 MWh/y more electricity and no change in heating duty. NR3 adds an ammonium stream and about 109.19 MWh/y heating duty. The phosphorus product mass in NR4 matches NR2, while its ammonium stream is 0.006 t/y lower than NR3, consistent with minor sequencing interaction in the structural model. All four routes retain identical upstream protein and biomethane outputs by construction. Figures F3 and F4 show the matched utility and product contrasts.

Table 3. Matched route outcomes, rounded.

| Nutrient route | P product t/y | Ammonium product t/y | Electricity MWh/y | Heating MWh/y |
|---|---:|---:|---:|---:|
| NR0, no targeted recovery | 0 | 0 | 270.20 | 309.63 |
| NR2, struvite route | 1.00 | 0 | 272.80 | 309.63 |
| NR3, ammonia route | 0 | 87.37 | 272.67 | 418.83 |
| NR4, both routes | 1.00 | 87.36 | 272.88 | 418.82 |

### 6.4 Model warnings and optimization status

The baseline decision support report records 15 distinct warning messages. Their recurring subjects are class E structural parameters, empirical PEF response, missing purchase cost correlations, and unvalidated dryer and gas specifications. A BioSTEAM cost warning separately states that compressor C611 operates at 0.4563 hp, below the cited correlation's 10 hp lower bound; it was emitted during execution and should be treated as an additional runtime cost caution. The process balance passes, but the model declares validated simulation readiness false. The repository implements seeded sampling and Pareto calculations. A separate 2,000 case frontend proxy generates an illustrative profit–climate display under explicit assumptions [9]. None of the four actual runs has a complete NPV or net GHG objective, so an evidence eligible actual-model Pareto frontier or MCDA ranking is not produced here. Figure F6 summarizes baseline warning categories.

## 7 Discussion

### 7.1 Technical interpretation

The combined nutrient route demonstrates process compatibility and a material output advantage within the structural equations. The major incremental duty is heating for ammonia stripping, not phosphorus recovery. Consequently, any design claim for NR3 or NR4 depends strongly on measured heat demand and heat integration. The invariant upstream protein and biomethane results in Table 3 follow from changing only downstream nutrient routing; they do not show that protein extraction is harmless to AD. That interaction requires matched PR0/PR3 simulations and measured COD or BMP data. Pressure, product purity, contaminant fate and operational reliability remain insufficiently validated for pilot design.

### 7.2 Economic interpretation

The current EUR 50,000 direct equipment entry is not plant CAPEX: most selected assets lack compatible capacities or installation factors. Electricity is only one included annual cost. Pricing the products without verifying saleable grade would create an optimistic revenue estimate. Therefore even a positive candidate overlay is not evidence of profitability. Priority cost measurements are vendor quotes for preparation, PEF, protein separation/drying, digester, water scrubber and ammonia stripping, together with process chemicals, labor, logistics and off take prices. An incremental NR4 versus NR0 decision can then compare added capital and operating costs with additional nutrient sales on a common feed basis.

### 7.3 Environmental interpretation

The roughly 109 MWh/y incremental heating duty for ammonia recovery could erode any fertilizer substitution benefit, but its climate effect cannot be quantified without a site specific heat factor and justified fertilizer counterfactual. Electricity, transport, reagents, storage and terminal gas fate likewise need complete inventories. The present analysis provides physical demands and missing data, not a verified GHG benefit. No statement that maximizing recovery improves total sustainability follows from these outputs.

### 7.4 Decision status and next experiments

NR4 is a reasonable combined recovery pilot candidate because it forms both targeted nutrient streams, but no route can be named the highest joint performer. NR2 is a lower heat comparator; NR0 supplies the technical bypass reference; NR3 isolates ammonia recovery. Pilot trials should measure seasonal feed and liquid composition, press and protein split, COD/BMP after protein extraction, nutrient speciation, ammonia stripping heat and chemical doses, product purity/contaminants and terminal methane fate. The model should then be calibrated and rerun with complete installed cost and climate inventories. A matched assumption Pareto study can be performed only after these account gates are met; stakeholder weights should be elicited separately rather than invented.

### 7.5 Uncertainty and limitations

The primary uncertainty is not numerical solution error. It is the evidence basis: structural class E parameters, unverified product quality, proxy cost entries, missing factor records, and no calibration against an operating GreenHub line. The July yearlong extrapolation suppresses seasonal shifts, storage degradation and downtime. The four route comparison is deterministic and narrow, not a global search. Its rounded utility differences are robust only within the implemented structural equations. The shape and location of any future Pareto frontier are unresolved. Sensitivity or Monte Carlo ranges would require credible parameter bounds and correlations; arbitrary ranges would make the apparent precision misleading.

## 8 Conclusions

The reference route produces modeled protein, biomethane and nutrient streams at 8,760 t/y grass intake with 272.88 MWh/y electricity and 418.82 MWh/y positive heating duty. Combined P/N recovery adds about 2.67 MWh/y electricity and 109.18 MWh/y heating compared with nutrient bypass. Those numbers identify ammonia stripping heat as a practical validation hotspot. Complete investment and climate metrics are unavailable, so the central research question has no defensible single optimum at present. GreenHub should pilot NR0, NR2 and NR4 on matched feed, resolve product quality and nutrient speciation, validate heat integration, and obtain complete costs and environmental factors before investment or sustainability ranking.

## 9 References

[1] GreenHub repository, `README.md`, `Greenhub/integration.py`, `Greenhub/application/simulation_service.py`, revision recorded above.

[2] GreenHub repository, `docs/tea_post_route_integration.md`, `Greenhub/application/tea_service.py`, `Greenhub/data/tea/tea_cost_register.csv`.

[3] GreenHub repository, `docs/lca_inventory.md`, `Greenhub/application/lca_service.py`, `Greenhub/data/lca/climate_factors.json`. The registry identifies IPCC AR6 Working Group I Chapter 7 Table 7.15 for direct gas characterization (https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/); the model uses only those recorded factors, not a complete impact method.

[4] GreenHub repository, `docs/phase7_scenarios.md`, `Greenhub/phase7_systems.py`.

[5] GreenHub repository, `docs/scenario_reference.md`.

[6] GreenHub repository, `docs/audit/model_completeness.md`, `docs/advanced_model/dataset_activation_matrix.md`.

[7] GreenHub repository, `Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_fiber_measurements.csv`, `docs/varta_grass_input_release_notes.md`.

[8] GreenHub repository, `Greenhub/application/seasonal_service.py`, `docs/alpha_0_2_checkpoint_3c/release_notes.md`.

[9] GreenHub repository, `docs/pareto_screening.md`, `frontend/src/components/DecisionSupport.tsx`.

## 10 Appendices

### Appendix A Reproducibility

Run `\.venv\Scripts\python.exe -m scientific_report.reproduce` and then `\.venv\Scripts\python.exe -m scientific_report.compare_routes` from the repository root. Run `\.venv\Scripts\python.exe scientific_report\make_figures.py` after the CSV files exist. The package saves exact requests, full reports, component and account CSVs, run IDs, source hashes, software versions and the Git revision. The workspace contained pre existing uncommitted edits during execution; the Git commit alone therefore does not fully identify executable code. Preserve the working tree or archive a patch for byte exact replication.

### Appendix B Unavailable requested indicators

Annual liquid fraction, dry normalized biomethane volume, elemental N/P/K recovery, water recovery, complete CAPEX and OPEX, product revenue, EBITDA, NPV, IRR, payback, net GHG, impact categories beyond climate, stakeholder MCDA scores and an eligible actual-model Pareto set are not reported as numerical conclusions here. Some may exist as intermediate streams or optional service outputs, but their final basis, annualization, completeness or evidence status requires additional extraction and validation. The report does not substitute arbitrary values.

### Appendix C Figure catalogue

`figure_catalogue.csv` indexes nine SVG and PNG figures by purpose, source, KPI and suggested section. The image library is deliberately separate from the manuscript so that figures can be selected after scientific review.
