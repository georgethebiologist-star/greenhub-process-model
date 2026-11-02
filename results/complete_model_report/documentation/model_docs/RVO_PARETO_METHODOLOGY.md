# GreenHub RVO Pareto analysis methodology

## Reproducing the analysis

From the model repository root, run:

```powershell
$env:GREENHUB_PARETO_DESIGNS='128'
$env:GREENHUB_PARETO_WORKERS='8'
.\.venv\Scripts\python.exe scripts\run_rvo_pareto_analysis.py
.\.venv\Scripts\python.exe scripts\generate_rvo_pareto_pngs.py
```

The runner uses the stored no-PEF F1 configuration in `results/report_figures/no_pef_F1.json`; it explicitly sets `feed_preparation=F1` in every request. It creates separate paired batches for active protein recovery (PR1–PR3) and protein bypass (PR0). Each sampled process design is evaluated under each of four financial support cases. Its seed, configurations, raw model outputs, selected candidates, objectives, warnings and limitations are retained in `Greenhub/results/pareto_rvo_2026/`.

## Sampling and optimization

The design space samples annual wet grass throughput log-uniformly from 1,000 to 30,000 t/y at 8,760 operating h/y. It samples active process routes: AD0/AD1/AD3, BG0/BG2/BG3/BG4, NR0/NR1/NR2/NR3/NR4/NR6/NR7, active protein routes PR1–PR3 or PR0, and process order A–C where allowed. Labor, logistics and utility reductions and product-yield uplifts are sampled as candidate-level screening variables bounded by the runner. They are assumptions, not fitted or experimentally verified retrofit effects. PEF is excluded. Each design is run through BioSTEAM once; its same process, TEA and LCA result is then paired with four recalculated finance overlays, so support cases cannot change the physical outputs.

For each protein group, nondominated fronts are calculated for (1) net carbon minimized and NPV maximized, (2) present value of assumed public support minimized and NPV maximized, and (3) all three objectives simultaneously. Nondominance is bounded to the saved random sample and does not imply a global optimum. Numerically complete rows are retained even when technical evidence gates are conditional; gate status and rejection reasons remain attached to each row. Negative operating margins and dominated rows are retained in the underlying batch.

The representative 11 candidates in the combined comparison are selected from the three-objective nondominated set (carbon, NPV, support PV), then ordered from rank 0 at the highest-NPV end toward rank 10 at the lower-carbon end. The separately saved two-objective fronts remain available for interpretation; scenario-specific subsidy/NPV candidate selections are sampled along their own fronts. Candidate labels use `Protein–Biogas–N–P–K`; `X` indicates bypass. In the website and figures, the selected endpoint colors are rose for rank 0 and green for rank 10.

## Financial support cases

The cases are user-defined what-if assumptions only. They are named with the Netherlands Enterprise Agency (RVO) to identify the requested awarding authority; none is represented as an approved grant or verified tariff:

| Case | Upfront CAPEX grant | Annual operating-support proxy | Named programme/authority |
|---|---:|---:|---|
| A | 30% | €20/t wet grass for 15 y | RVO DEI+ / RVO SDE++ |
| B | 45% | €40/t wet grass for 15 y | RVO DEI+ / RVO SDE++ |
| C | 60% | €60/t wet grass for 15 y | RVO DEI+ / RVO SDE++ |
| D | 0% | €50/t wet grass for 15 y | RVO SDE++ proxy only |

The DEI+ official programme page describes project categories and maximum grant amounts but does not establish the user-supplied percentages as generally applicable rates. SDE++ renewable-gas support is tied to qualifying grid injection and corrected market prices; a generic €/t feed proxy is not the official tariff calculation. These runs do not check eligibility, award probability, cost ceilings, market corrections, or co-funding. See [RVO DEI+ circular economy](https://www.rvo.nl/subsidies-financiering/dei/circulaire-economie-en-grootschalige-biobased-projecten), [RVO renewable gas SDE++](https://english.rvo.nl/subsidies-financing/sde/aanvragen/renewable-gas), and [RVO SDE++ features](https://english.rvo.nl/subsidies-financing/sde/features).

NPV is a 20-year, 8% discount-rate, pre-tax constant-account screening calculation. It uses high direct uninstalled equipment CAPEX, a 15-year operating-support period, current model partial operating margin, and the upfront grant. It excludes financing, escalation, replacement, working capital, residual value, installation costs and taxes. This is a scenario-comparison metric, not the report's full project NPV or investment-grade TEA.

## Climate and carbon objectives

The operational climate inventory is gate-to-gate and includes modeled electricity, process heat and modeled vented process emissions. Electricity is evaluated at 0.264 kg CO2e/kWh (midpoint of the supplied 0.254–0.274 range); heat uses the supplied Dutch average 30.96 kg CO2e/GJ converted to 0.111456 kg CO2e/kWh. Other upstream, equipment, transport, feedstock production and downstream burdens are excluded; exclusion is not a zero-burden claim.

`net_carbon` is defined as operational climate load converted to elemental carbon equivalent (`t CO2e × 12/44`) minus retained product carbon. It credits 100% of modeled press-cake carbon to furniture and 10% of nutrient-rich-solids carbon as retained in soil. Protein carbon receives no storage credit because its feed/biostimulant fate is unresolved. Furniture manufacturing loss and end-of-life release are not included. Thus this is a screening proxy for a mixed operational burden and assumed carbon stocks; it is not a complete LCA climate impact or a durable-removal claim.

The methane volume shown in candidate product figures converts the model's biomethane mass using 0.716 kg/Nm3, a pure-methane density basis at 0 °C and 1.01325 bar. The conversion does not equate raw biogas, methane and biomethane volumes; raw biogas composition and upgrading losses remain determined by each model result. Figure labels state the Nm3 basis.

## Figures and quality checks

The PNG generator uses the existing GreenHub report palette and records figure, source batch, scenario, units and file path in `results/report_figures/rvo_pareto_figure_index.csv`. It creates two-objective fronts, 3D three-objective fronts, selected-candidate comparison plots and per-candidate product, utility and KPI summaries in `08_candidate_comparison/`. Run visual inspection on the exported images before publication; numerical model warnings and incomplete evidence are retained in output metadata, not drawn over the figures.

The web chart reads the latest analysis through `/api/v1/decision-support/pareto/latest`. It displays the two-objective projections and selected candidate table. A fully interactive 3D view is not implemented; the static 3D PNG is the 3-objective visualization.
