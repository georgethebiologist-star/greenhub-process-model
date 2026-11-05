# GreenHub RVO Pareto analysis methodology

## Reproducing the analysis

From the model repository root, run:

```powershell
$env:GREENHUB_PARETO_DESIGNS='128'
$env:GREENHUB_PARETO_WORKERS='2'
.\.venv\Scripts\python.exe scripts\run_rvo_pareto_analysis.py
.\.venv\Scripts\python.exe scripts\append_rvo_baseline_references.py
.\.venv\Scripts\python.exe scripts\generate_rvo_pareto_pngs.py
.\.venv\Scripts\python.exe scripts\verify_pareto_replay.py
```

The runner explicitly sets `feed_preparation=F1` in every request. It creates separate paired batches for active protein recovery (PR1–PR3) and protein bypass (PR0). Each sampled process design is evaluated once, then paired with 24 post-route finance overlays: four hypothetical CAPEX-grant levels (0%, 30%, 45%, 60%) crossed with grass-utilization bonuses of €0, 10, 20, 30, 40 and 50 per wet tonne processed. The UI's shared economic defaults are read from `Greenhub/data/greenhub_economic_defaults.json`. Seed, configurations, raw model outputs, selected candidates, objectives, warnings and limitations are retained in `Greenhub/results/pareto_rvo_2026/`.

When a scenario does not supply an explicit `feed_composition`, the runner pins all 74 fractions from `Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json` into the saved configuration. Explicit scenario values have priority. The manifest records the profile ID and SHA-256 so that candidate replay is not silently changed by a future default-profile edit.

## Sampling and optimization

The design space samples annual wet grass throughput log-uniformly from 1,000 to 30,000 t/y at 8,760 operating h/y. It samples active process routes: AD0/AD1/AD3, BG0/BG2/BG3/BG4, NR0/NR1/NR2/NR3/NR4/NR6/NR7, active protein routes PR1–PR3 or PR0, and process order A–C where allowed. Original modeled sales and partial OPEX are used unchanged. No assumed labour, logistics or energy reductions and no protein-yield or nutrient-recovery revenue uplifts are sampled or applied. Legacy improvement settings are ignored. The operating-profit objective is sales minus partial OPEX before public support, tax and capital recovery. PEF is excluded. Each design is run through BioSTEAM once; its same process, TEA and LCA result is then paired with four recalculated finance overlays, so support cases cannot change the physical outputs.

For each protein group, nondominated fronts are calculated for (1) net carbon minimized and NPV maximized, (2) present value of assumed support minimized and NPV maximized, and (3) all three objectives simultaneously. Separate net-carbon/NPV fronts are also calculated for each of the 24 grant × grass-bonus combinations. A fixed-process grass-bonus sensitivity compares the six bonus values without changing process configuration. Nondominance is bounded to the saved random sample and does not imply a global optimum. Numerically complete rows are retained even when technical evidence gates are conditional; gate status and rejection reasons remain attached to each row. Negative operating margins and dominated rows are retained in the underlying batch.

Up to 25 representatives are selected from each combined or two-objective front and from each of the 24 support-case fronts; actual counts can be lower when the nondominated set is smaller. They are ordered across the observed front, including the high-NPV and low-carbon ends. Candidate labels use `Protein–Biogas–N–P–K`; `X` indicates bypass. In the website and figures, the selected endpoints are highlighted.

Pareto eligibility requires at least one positive annual flow (>1e-9 in the reported model basis) among dry protein, biostimulant, biomethane, phosphorus, ammonium, potassium concentrate, or nutrient-rich solids. Productless cases remain in the saved batch as rejected records with an explicit reason; they are excluded from all fronts and selected-candidate lists. This is an output gate, not a claim that the remaining products meet commercial quality specifications.

## Financial support cases

These are user-defined what-if assumptions, not RVO awards or verified tariffs. CAPEX grant levels remain an independent scenario dimension. Biomethane value and the grass-use bonus are separate annual support overlays:

| Case | Hypothetical upfront CAPEX grant | Biomethane value proxy | Grass utilization/logistics bonus |
|---|---:|---:|---|
| C30 | 30% | €1.87/Nm³ modeled biomethane for 15 y | €0–50/wet t for 20 y |
| C45 | 45% | €1.87/Nm³ modeled biomethane for 15 y | €0–50/wet t for 20 y |
| C60 | 60% | €1.87/Nm³ modeled biomethane for 15 y | €0–50/wet t for 20 y |
| C0 | 0% | €1.87/Nm³ modeled biomethane for 15 y | €0–50/wet t for 20 y |

The DEI+ official programme page describes project categories and maximum grant amounts but does not establish the user-supplied percentages as generally applicable rates. SDE++ renewable-gas support is tied to qualifying grid injection and corrected market prices; a generic €/t feed proxy is not the official tariff calculation. These runs do not check eligibility, award probability, cost ceilings, market corrections, or co-funding. See [RVO DEI+ circular economy](https://www.rvo.nl/subsidies-financiering/dei/circulaire-economie-en-grootschalige-biobased-projecten), [RVO renewable gas SDE++](https://english.rvo.nl/subsidies-financing/sde/aanvragen/renewable-gas), and [RVO SDE++ features](https://english.rvo.nl/subsidies-financing/sde/features).

The annual biomethane-value support is calculated from each candidate’s modeled biomethane mass divided by 0.716 kg/Nm³, multiplied by €1.87/Nm³. The grass-use bonus is rate × annual wet tonnes actually processed; it does not change process outputs, chemistry, or emissions. C0 has zero CAPEX grant but may still receive either operating-support assumption. Neither value is verified programme income or awarded public support.

`scripts/verify_pareto_replay.py` replays five NPV strata (minimum, 25th percentile, median, 75th percentile, maximum) for both protein-route groups at each of the six C0 grass-bonus rates, plus the same strata for C60-GB50. It compares revenue, OPEX, direct CAPEX, public-support present value, NPV, IRR, and payback against the saved batch using `DecisionSupportService`, the evaluator used by the UI. This is an internal consistency check, not independent validation of the financial assumptions.

NPV uses the same post-route TEA calculation as standalone Configure: annual modeled product sales, annual OPEX, high direct CAPEX screening basis, tax rate 25.8%, 20-year life, 8% discount rate, and the appropriate finite support terms (15 years for the biomethane value proxy, 20 years for the grass bonus). Support is counted once. Annual capital recovery is not deducted again from NPV cash flows. If product revenue is incomplete, investment KPIs including NPV/IRR/payback remain blocked rather than treating missing prices as zero.

The UI's selected-point action replays the exact saved process request and its finance assumptions through the same backend TEA evaluator. Cost overlays are idempotent; paired support cases do not add labor or utility costs a second time. Grass-bonus duration and biomethane-bonus duration are stored/restored independently; `opex_support_years` is a legacy shared-duration fallback only when the specific biomethane duration is absent. To regenerate finance and fronts for identical saved process designs, run `python scripts/reprice_saved_rvo_pareto.py`, followed by the PNG generator. To regenerate the sampled process designs, run `python scripts/run_rvo_pareto_analysis.py`, then `python scripts/append_rvo_baseline_references.py` and the PNG generator. The generator can republish its completed batches without repeating simulations by setting `GREENHUB_PARETO_PUBLISH_SAVED_BATCHES=1`; large JSON artifacts are streamed to avoid holding an extra serialized copy in memory.

NPV remains a screening proxy, not investment-grade TEA. It uses a high-direct-CAPEX basis where installed equipment costs are unavailable and excludes financing, escalation, replacement CAPEX, working capital, residual value and unverified grant eligibility. Results inherit any incomplete source cost or product-price assumptions shown with the candidate.

## Climate and carbon objectives

The inventory includes modeled process energy and vented process emissions. Electricity uses the JRC Netherlands life-cycle electricity factor of 0.406463 kg CO2e/kWh (2021, Table3_EU_LC), including upstream electricity supply-chain emissions; the source is [JRC dataset DOI 10.2905/JRC.4800KC0](https://doi.org/10.2905/JRC.4800KC0). Heat uses the supplied Dutch average 30.96 kg CO2e/GJ converted to 0.111456 kg CO2e/kWh. Other upstream materials, equipment, transport, feedstock production and downstream burdens are excluded; exclusion is not a zero-burden claim. The electricity factor is a national 2021 life-cycle value, not a supplier-specific current-year factor. Net carbon and LCA completeness must not be conflated.

`net_carbon` is defined as operational climate load converted to elemental carbon equivalent (`t CO2e × 12/44`) minus retained product carbon. It credits 100% of modeled press-cake carbon to furniture and 10% of nutrient-rich-solids carbon as retained in soil. Protein carbon receives no storage credit because its feed/biostimulant fate is unresolved. Furniture manufacturing loss and end-of-life release are not included. Thus this is a screening proxy for a mixed operational burden and assumed carbon stocks; it is not a complete LCA climate impact or a durable-removal claim.

The methane volume shown in candidate product figures converts the model's biomethane mass using 0.716 kg/Nm3, a pure-methane density basis at 0 °C and 1.01325 bar. The conversion does not equate raw biogas, methane and biomethane volumes; raw biogas composition and upgrading losses remain determined by each model result. Figure labels state the Nm3 basis.

## Figures and quality checks

The PNG generator uses the existing GreenHub report palette and records figure, source batch, scenario, units and file path in `results/report_figures/rvo_pareto_figure_index.csv`. It creates two-objective fronts, 3D three-objective fronts, selected-candidate comparison plots and per-candidate product, utility and KPI summaries in `08_candidate_comparison/`. Run visual inspection on the exported images before publication; numerical model warnings and incomplete evidence are retained in output metadata, not drawn over the figures.

The web chart reads the latest analysis through `/api/v1/decision-support/pareto/latest`. A freshly started API serves `Greenhub/results/pareto_rvo_2026/latest_ui.json`, an atomically refreshed projection containing report fields and selected scenarios without the full evaluated-sample ledger. The UI exposes CAPEX-grant and grass-logistics-bonus filters, loads up to 25 representative candidates per selected front, and provides a scenario selector in addition to clickable graph points. Productless scenarios are excluded before display. The full `latest.json` is the detailed scenario ledger; per-group batch files and `rvo_pareto_manifest.json` retain route-specific records. A fully interactive 3D view is not implemented; the static 3D PNG is the three-objective visualization.
