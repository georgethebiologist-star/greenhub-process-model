# GreenHub Direct Isoelectric Protein-Recovery Dataset Audit and Extension

## Cross-phase pilot benchmark (reference-only)

`green_biorefinery_energy_scale_and_storage_benchmarks_2026_reference.csv`
stages the Tuv green-biorefinery study's aggregate pilot energy (375 kWh
electricity and 138 MJ propane heat per Mg DM; the paper reports 1489 MJ/Mg DM
total), alongside distinct model-design records for facility capacity,
operating schedule, and storage/harvest loss factors attributed by the article
to Hedström (2015). An arithmetic check shows the rounded energy components sum
to 1488 MJ/Mg DM; both the paper's total and the transparent check are retained.
Measured pilot values, modeled design assumptions, and secondarily reported
literature factors have separate evidence labels. The feed is cultivated
Norwegian grass-clover and the process/system boundaries differ from GreenHub.
All rows are reference-only and are not mapped to runtime inputs.

`green_biorefinery_stream_balance_2026_reference.csv` preserves Table 2's
stream-level fresh mass, dry mass, dry-matter concentration, and nitrogen
concentration per 1000 kg DM input. The stream hierarchy is explicit: green
juice is an intermediate, while pulp, protein concentrate, brown juice, and
unrecovered material are reported final streams. Do not count green juice
again when summing its downstream products. The rounded final fresh masses
sum to 5264 kg against 5263 kg input; final dry masses sum to the 1000 kg DM
basis. Nitrogen closure remains incomplete because N concentration in the
unrecovered stream is not reported. This is a cultivated grass-clover pilot
analogue, staged for Phases 2/4/5/7 only and not connected to GreenHub runtime
inputs.

## Scope
This package audits and extends the scientific inputs required for direct isoelectric precipitation in `Greenhub/data/Protein recovery/Isoelectric/`.

It deliberately separates direct observations from proxy-material observations, source equations, manufacturer information, model assumptions, and missing mandatory inputs. Unsupported numerical defaults from the legacy combined dataset were not carried forward as facts.

## Files
The package contains topic-specific CSV files for pI, pH and temperature solubility, ionic strength, titration and reagent demand, precipitation and aggregation kinetics, residence time, recovery, purity, losses, separation, washing, moisture, stability, and equipment/scale/cost demand. It also contains:

- `dataset_manifest.csv`
- `source_register.csv`
- `equation_registry.csv`
- `assumption_and_missing_data_register.csv`
- `validation_report.json`

## Core schema
Observation files use one parameter or observation per row and include:
`parameter_id`, `python_variable`, `value`, `unit`, normalized SI fields, basis, process, material/feed, original protein source, extraction method, operating conditions, data status, full source metadata, exact source location, notes, uncertainty, and transferability.

## Data-status rules
- `measured`: numerical observation reported from an experiment.
- `literature-reported`: numerical or categorical result explicitly reported by the source.
- `calculated_from_source_formula`: calculated only from a cited formula and cited source inputs.
- `manufacturer-reported`: manufacturer specification.
- `fitted_by_source`: fitted by the original source.
- `assumption`: model structure or required input description; numerical value remains blank.
- `missing`: unresolved input; numerical value remains blank.

## Important limitations
1. Final-powder solubility is not treated as raw green-juice equilibrium solubility.
2. Total nitrogen recovery is not automatically treated as true protein recovery.
3. Precipitation yield is not treated as solid-liquid separator capture.
4. No single pI is assigned to the complete grass-protein pool.
5. Generic cost scaling is retained only as a rule-of-thumb equation; equipment-specific costs, power and scale factors remain unresolved unless supported.
6. Kinetic and residence-time constants remain blank because no defensible grass-specific time-series dataset was located in the audited sources.
7. Proxy materials are explicitly labelled and must not be silently transferred.
8. `REC-005` adds a directly reported ryegrass-juice isoelectric precipitation result: 38% of cleared-juice total N precipitated at pH 4–4.5. It is not isolated-protein recovery. The source used a double-press/dilution and clarification boundary; GreenHub's roadside-grass single-press route differs. It is therefore exposed as a scenario-bounded literature proxy and is not a default or activated protein-recovery equation.
8. `REC-005` adds a directly reported ryegrass-juice isoelectric precipitation result: 38% of cleared-juice total N precipitated at pH 4–4.5. It is not isolated-protein recovery. The source used a double-press/dilution and clarification boundary; GreenHub's roadside-grass single-press route differs. It is therefore exposed as a scenario-bounded literature proxy and is not a default or activated protein-recovery equation.

## Integration readiness

The Stødkilde et al. (2020) seasonal ryegrass dataset records spring-cut changes in feed/fraction N concentration and total-N partition. It is an evidence-only cultivated-forage analogue: the reported acid strength and endpoint do not reveal reagent dose, and total-N recovery is not true-protein recovery. See the dataset sidecar for the source scope, conditions, rights caveat and transfer limitations.
The package is immediately usable as a validated evidence layer and missing-data controller. The equilibrium, dynamic, separator, reagent-demand and TEA submodels are only partially parameterized until the critical items in `assumption_and_missing_data_register.csv` are measured or sourced.

The additive `lignosulfonate_precipitation_reference_2019.csv` transcribes all ryegrass and red-clover Table 2 treatment outcomes from la Cour et al. (2019). It is evidence-only: total nitrogen recovery, concentrate crude-protein content, and feed-specific transferability remain distinct, and these rows do not activate or calibrate the GreenHub route.

The additive `lignosulfonate_precipitation_reference_2019.csv` transcribes all ryegrass and red-clover Table 2 treatment outcomes from la Cour et al. (2019). It is evidence-only: total nitrogen recovery, concentrate crude-protein content, and feed-specific transferability remain distinct, and these rows do not activate or calibrate the GreenHub route.

Recommended integration logic:
- Load only rows whose `data_status` is compatible with the selected scenario.
- Filter by `material_feed_type`, `protein_source`, `extraction_method`, and operating conditions.
- Do not use proxy rows unless the scenario explicitly allows proxies.
- Treat textual ranges as ranges; do not convert them to midpoints automatically.
- Fail validation when a mandatory variable has no direct value for the chosen feed class.

`green_forage_fraction_mineral_partition_hansen_2022_reference.csv` records all 20 Table 1 forage-by-fraction rows from Hansen et al. (2022), including K, Ca, Mg, P, Zn and Cu concentrations for cultivated white clover, red clover, lucerne and perennial ryegrass. Analyte-specific units, dry-matter basis, and Mg/Cu significance groups are retained; table-level SEM and p-values are in the source sidecar. These data improve Phase 4/7 component-fate evidence but are concentrations, not material flows or nutrient recoveries. The study used heat precipitation and Danish cultivated forages, so rows remain reference-only and cannot parameterize the GreenHub roadside-grass/isoelectric route.

`alfalfa_protein_recovery_methods_coburn_2021_reference.csv` records Table 5 means for five alfalfa press-filtrate protein-recovery methods, including APC yield per kg herbage DM and product composition per kg APC. Treatment conditions and significance groups are preserved; the source sidecar states that reagent dose and numeric uncertainty are unavailable. This Phase 4 comparison is reference-only, is not true-protein recovery, and is not mapped to GreenHub runtime parameters.

`green_leaf_fractionation_yields_and_nitrogen_content_nynas_2021_reference.csv` transcribes Table 2a–c from Nynäs et al. (2021): initial-biomass-relative nitrogen yields, local step yields relative to nitrogen entering each step, and fraction nitrogen concentrations on a dry-matter basis. The denominator is explicit per panel; nitrogen is not converted to crude protein. The 189-row extract includes nine green biomasses, one explicitly unreported carrot P4 value, source-reported replicate counts and uncertainty where given. Lucerne is a cultivated forage comparator, not roadside grass. HCl consumption is not reported. The dataset is CC BY 4.0, B-tier, and reference-only; see its sidecar for the full procedure, provenance, and transfer limits.

`riihinen_2023_finnish_grass_protein_precipitation_reference.csv` records ten observations from conference abstract P2.1.088 on heat coagulation and acid precipitation in cultivated Finnish red clover and timothy. It deliberately separates best-content tests from selected-protocol product composition and preserves the approximately 10% recovery basis as protein in juice, not protein in whole grass. The stated sodium-sulphite amount is not normalized because its denominator is absent. Abstract-only, B-tier, reference-only; it does not activate GreenHub precipitation, reagent-demand, or recovery parameters.

`halophyte_green_juice_protein_recovery_aquacombine_2022_reference.csv` records Tables 3–4 and text-reported fermenter outcomes from public H2020 deliverable AQUACOMBINE D5.6. It separates saline *Salicornia ramosissima* and *Tripolium pannonicum* batches, HCl acidification, heat coagulation, and lactic-acid fermentation. The HCl amount is only `<1 mL of 7.7 M HCl per 200 mL juice` to pH 3.5; this is retained as a strict source bound, not converted into an exact acid demand. The Table 3 PEC-yield denominator is unspecified; CP is total-N×6.00 and may include non-protein N. B-tier, material-and-technology-specific, reference-only; it does not parameterize GreenHub. The report is public-use dissemination, but no separate data-reuse license was identified.

`nynas_2021_green_biomass_feed_nitrogen_and_dry_matter_reference.csv` separately records Table 1 feed N and dry-matter concentration, botanical identity, and collection context for the same nine materials. The 18 observations retain N as percent of dry matter and DM as percent of as-received biomass. The Table 1 biomass values are not reconciled with Table 2c values; they remain distinct reported sample records. This is Phase 1/4 B-tier comparator evidence, reference-only, and not a GreenHub roadside-grass feed default.

`nynas_2021_green_biomass_feed_nitrogen_and_dry_matter_reference.csv` separately records Table 1 feed N and dry-matter concentration, botanical identity, and collection context for the same nine materials. The 18 observations retain N as percent of dry matter and DM as percent of as-received biomass. The Table 1 biomass values are not reconciled with Table 2c values; they remain distinct reported sample records. This is Phase 1/4 B-tier comparator evidence, reference-only, and not a GreenHub roadside-grass feed default.

`green_leaf_fractionation_yields_and_nitrogen_content_nynas_2021_reference.csv` transcribes Table 2a–c from Nynäs et al. (2021): initial-biomass-relative nitrogen yields, local step yields relative to nitrogen entering each step, and fraction nitrogen concentrations on a dry-matter basis. The denominator is explicit per panel; nitrogen is not converted to crude protein. The 189-row extract includes nine green biomasses, one explicitly unreported carrot P4 value, source-reported replicate counts and uncertainty where given. Lucerne is a cultivated forage comparator, not roadside grass. HCl consumption is not reported. The dataset is CC BY 4.0, B-tier, and reference-only; see its sidecar for the full procedure, provenance, and transfer limits.
