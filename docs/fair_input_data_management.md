# GreenHub input data management and FAIR catalog

## Purpose and authority

`Greenhub/data/fair_input_catalog/master_input_catalog.csv` and `.json` are generated indexes of the inputs and evidence files under `Greenhub/data/`. The catalog records file checksum, repository path, role, links to matching source registers, and known dataset readiness. It is an index, not a shadow parameter store: editing the catalog does not change a simulation. Rebuild it with:

```powershell
.\.venv\Scripts\python.exe scripts\build_fair_input_catalog.py
```

The master workbook `Greenhub/data/greenhub_feed_inputs.xlsx` now has additive `FAIR_Catalog` and `Master_Inputs` sheets. The latter is a normalized, read-only snapshot of canonical parameters, feed compounds, economic defaults and prices, TEA cost records, LCA factors, and the opt-in storage-reaction package. Both are browsable snapshots, not new precedence layers. Existing named sheets, sheet names, and control values are preserved; the ReadMe's quality-class definitions were aligned with the current UI, and existing loaders remain unchanged.

## Existing runtime input and override flow

- Grass component defaults shown in the UI come from `Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json`; the UI sends normalized component fractions in the process request. Per-component source classes and assumptions are kept with each component.
- Frontend-only offline/initial preview references are held in `Greenhub/data/frontend/preview_parameter_defaults.json` and labeled in the UI as planning references, not applied to backend runs. They are cataloged for traceability but cannot override the canonical parameter registry, workbook controls, `SimulationRequest`, or user-provided feed composition. The VARTA grass-moisture preview uses 0.857 wet-basis water (14.3% measured dry matter); the formerly stale 0.78 value is removed.
- Workbook sheets remain loaded by their existing named-sheet loaders. `ModelControl` controls and selected sample IDs apply only through the existing workbook-backed feedstock path; they do not silently replace the UI's explicit component request.
- `SimulationRequest` carries process selections, schedules, explicit feed composition and design overrides. `ParameterService` resolves canonical values and explicit parameter overrides through the current registry. The catalog does not alter this order.
- Configure > Economics values are passed in `candidate_economics` / `financial_assumptions` to post-route TEA and LCA. These are report overlays: they do not modify process chemistry, scenario IDs, component or energy balances, or process outputs.
- Reports and exports use the run request and post-route analysis associated with that run. Editing inputs marks the displayed result stale until a new run is completed.

## Evidence classes and missingness

Use A for measured/verified values, B for directly traceable external evidence (peer-reviewed or technical literature, official statistics/tariffs, or supplier/product data), C for project values produced by engineering scaling/allowances, and E for explicit assumptions or structural placeholders. B does not mean high transferability: source fit, geography, scale, year, grade, and cost boundary remain separately reported. D denotes uncertain/quarantined evidence and is not a runtime quality tier. Where an unverified legacy value must remain for structural compatibility, preserve its numeric value only with E class, explicit limitations, and source/provenance notes. An unknown is not zero; values that cannot be supported should remain missing or be clearly identified as a structural-zero assumption, never described as measured absence.

The active grass profile previously had 48 class-D entries: 43 zero placeholders and five trace-level placeholders. Their numbers were preserved and reclassified E with explicit legacy-assumption and uncertainty text. The soluble/suspended protein partition was also reclassified E: the cited roadside-grass paper supports total protein, not the model's 20/80 partition. This change does not upgrade the composition to a fully measured speciation dataset. The current 538-row canonical parameter registry has zero rows with `quality_class = D`; class E assumptions remain and are visibly identified.

The default lifecycle electricity factor uses the JRC Netherlands 2021 life-cycle value (0.406463 t CO₂e/MWh = 0.406463 kg CO₂e/kWh), with upstream electricity supply included. The source workbook, table/cell context, conversion, date, geography, applicability, uncertainty, DOI, and CC BY 4.0 license are recorded in `Greenhub/data/lca/source_data/`. The default Dutch heat-network factor is 0.111456 kg CO₂e/kWh, converted from CE Delft's 2022 end-user total of 30.96 kg CO₂e/GJ (direct plus chain emissions). It is class B literature evidence, a national average rather than site-specific. Neither factor closes other LCA inventory gaps.

The staged isoelectric-recovery dataset has record-level metadata in `Greenhub/data/Protein recovery/Isoelectric/recovery_metadata.json`. REC-004's DOI was corrected to `10.1016/j.biteb.2022.101190`. REC-001 may be selected as a literature candidate (class B, proxy transferability), but it measures total nitrogen recovery from grass-clover rather than recovery of the model's soluble-protein pool. REC-002/003 also include nitrogen in fiber and are not precipitation-efficiency measurements. These basis mismatches are explicit; the structural default remains unchanged and class E unless the user selects the literature candidate. The literature evidence does not validate a direct roadside-grass precipitation model.

## FAIR status and limitations

### Biomethane price provenance correction (2026-11-05)

The UI's selected biomethane price remains the user's supplied €0.88/m³ assumption (quality E); it is not relabeled as literature evidence. Its record is linked to the supplied Dutch gas-price page and retains the supplied unit. Separately, the ACER 2025 waste-derived biomethane TTF+GO benchmark is recorded as €60.51/MWh (quality B), with a €49.87–75.10/MWh reported range and source location Slide 27, [ACER data item 1226](https://aegis.acer.europa.eu/chest/dataitems/1226/view). This is a market benchmark, not a direct €/m³ replacement or proof that the product grades are equivalent. The frontend labels the selected assumption and benchmark separately.

The current generated catalog contains 430 assets and 755 normalized records: 664 E, 53 B, 27 C, 2 A, 7 project controls, and 2 blank/missing values. The latest targeted backend provenance/catalog/TEA checks passed (26 tests); frontend TypeScript lint, decision-support check, fallback check, and production build passed. The production build still emits Vite's existing large-chunk advisory. These checks do not constitute the final full-suite run.

### Feed-profile source link behavior

The feed profile stores literature links under `source_url`, while the older feed editor expected `url`; DOI text could appear without a clickable link. The editor now resolves `url`, `source_url`, or DOI URL and renders a compact source link on the corresponding feed row. This is presentation-only: composition amounts, evidence classes, override values, reset-to-default behavior, normalization, and run payload are unchanged. Frontend lint and the decision-support rendering/evidence/request-payload checks pass with a regression assertion for the field-name mapping.

The runtime canonical parameter registry currently has 538 entries: 529 E, 7 project controls, and 2 missing values, with no D labels. These registry counts must not be confused with the separate feed-profile evidence classes or the catalog's source coverage. The phase workbook parameter sheets presently label all their rows E and leave reference fields blank; their parameter metadata needs value-level evidence review before any B promotion. A citation attached to a broader or related measurement is not enough to promote a model partition or placeholder.

### VARTA feed selection boundary

The backend option list advertises `grass_varta_default`, and `load_roadside_grass_specification()` can resolve that sample into VARTA total solids and wet-basis N/P/K aggregates. The current Run Simulation UI instead submits the explicit 74-component profile from `greenhub_feed_composition_defaults.json`; its quasi-dynamic request also submits `biomass_schedule`. In `SimulationService`, a supplied `biomass_schedule` bypasses `feed_supply_profile_id`, and the explicit `feed_composition` takes precedence over the model's workbook feed. Therefore, VARTA's separately measured N/P/K aggregates are available in the workbook-backed feed path but are not currently selected as those aggregates by the main explicit-composition UI run. Do not imply that the VARTA N/P/K measurements are independently active in the 74-component composition: the profile contains derived/assumed molecular allocations. Exposing a selectable feed profile while preserving exact override precedence requires a deliberate end-to-end request-to-report change and is still an integration gap.

- Findable: the catalog has a stable catalog identifier, content-addressed asset identifiers, file paths, hashes, source IDs, DOI fields and URLs. Asset identifiers are repository-local content identifiers, not registered DOIs. No DOI is fabricated. To mint externally persistent identifiers, archive a release in an appropriate repository (e.g., Zenodo) and record the resulting DOI.
- Accessible: CSV and JSON catalog formats are open and retrievable in the public repository over HTTPS; the original sources remain at their source-specific locations where linked.
- Interoperable: UTF-8 CSV/JSON, explicit SI/financial units where source files provide them, common DOI/URL identifiers, and stable column names support programmatic reuse. Unit/basis gaps are flagged as record-specific rather than inferred.
- Reusable: checksums, repository-relative provenance, runtime role, source-register linkage, DOI/URL, rights warning, and override notes are included. Rights are intentionally marked “not inferred”; the repository license does not automatically relicense third-party sources.

At the current catalog build, there are 430 input assets and 755 normalized input records; 385 assets have a source-register or adjacent local metadata link and 281 contain a DOI-like source identifier. Forty-five assets have no source-register link, although some contain inline metadata. Transient Office lock files are excluded; retained phase workbooks are indexed as archived snapshots, not active input sources. Directory-level links do not prove that every citation supports every file in that directory. The next evidence-management improvement is to map each dataset record to exact source rows/pages/tables, license and access conditions rather than infer support from a neighboring register.

The canonical parameter registry currently has 538 records: zero class D, 529 class E, seven project controls, and two missing values. The normalized master record set currently contains 664 E, 53 B, 27 C, two A, seven project-control, and two blank/missing records. Fourteen frontend-preview references are included as explicitly non-backend-authoritative records. The 55 TEA cost records are graded in `Greenhub/data/tea/tea_cost_quality_review.json`: 33 directly sourced benchmarks are B, 18 scaled/combined engineering values are C, and four unsupported/user-provided amounts remain E. B describes source evidence, not project transferability; the cost register retains source status, applicability, confidence and cost-boundary limitations. The 23 storage reaction inputs are all E-class opt-in assumptions; their citations do not validate the numerical kinetics for roadside grass. Thus “no D” means the uncertain/quarantined tier has been removed from active runtime classification; it does not mean the model has no assumptions or that all parameters are literature-grade. E includes explicit assumptions and structural placeholders. D4/D5 labels elsewhere describe evidence/readiness gates, not quality class D.

The active grass starch profile is recorded as class B with an explicitly low-transferability literature basis: Guțu et al. (2025) reports 1.88% DM for *Phleum pratense* while attributing the value to Chornolata et al. (2018); the 2025 study itself does not measure starch in its Table 1. GreenHub converts 1.88% DM to 18.8 g/kg DM and applies the VARTA measured dry-matter fraction (0.143) to obtain 0.0026884 kg/kg wet feed. The 2018 reference is bibliographically identified as “Carbohydrate fractions in the green mass of forage crops,” *Feeds and Feed Production* 85, 132–137 (in Ukrainian), but its full text, methods, DOI and uncertainty range remain unverified. The catalog and workbook retain the 2025 article URL, exact page/section, geography, year, primary-reference citation and local source-register ID `SRC-GUTU-2025` for this component.

The dynamic raw-press evidence report now exposes records `RAW_0001`–`RAW_0009` with the cited *Lolium perenne* study's DOI URL, Table 1 location, record identifier and source quality B. B here denotes source evidence quality; the report separately identifies transferability and warns that these lab-scale, fresh ryegrass results are not validated for roadside-grass industrial operation. This is not a change to the empirical baseline press defaults.

Catalog identifiers (`urn:greenhub:dataset:sha256:…`) are content-addressed repository identifiers, not globally registered persistent identifiers. There is currently no DOI for the combined GreenHub input collection. A DOI should be added only after depositing a versioned release in a repository such as Zenodo; until then, repository URLs, hashes, source DOIs and local record IDs provide traceability but not a minted global identifier.

## Regeneration and review

1. Add or update the authoritative source file and its record-level provenance first.
2. Keep values, bases, uncertainty, applicability, source location, retrieval date and quality distinct; never replace missing data by zero without an explicit assumption.
3. Rebuild the catalog and refresh the workbook catalog sheet.
4. Review changed hashes and unmatched sources. Re-run the input/override and reporting tests before release.

See `docs/fair_data_pareto_release_notes.md` for this checkpoint's changes and limitations, and `docs/fair_data_pareto_checkpoint_2026-11-05.md` for the persistent handoff state.

