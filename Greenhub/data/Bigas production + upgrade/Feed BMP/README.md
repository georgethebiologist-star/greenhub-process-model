# GreenHub Anaerobic Digestion — Feed & BMP Dataset

## Scope
This package supports `Greenhub/data/Biogas production + upgrade/Anaerobic_Digestion/Feed_BMP/`.
It contains source-traceable feed characterization, biochemical fractionation, methane-yield,
inhibition-screening and digestate data for road-verge grass, grass silage, grass biorefinery
press cake and protein/FOS-depleted grass whey.

## Data rules
- Blank numerical cells are intentional and paired with `data_status=missing`.
- No missing value is replaced by zero.
- Experimental measurements, literature-reported values, source-formula calculations and
  missing data are separated through `data_status`.
- Original units and bases are preserved. SI-normalized values are included only for
  unambiguous conversions.
- The theoretical Buswell/Boyle rows are **not experimental BMP results**.
- Proxy materials are explicitly identified in `material_feed_type` and `transferability`.

## Core files
- `ad_feed_characterization.csv`: TS, VS, pH, TKN, phosphorus, sulfur and selected nutrients.
- `ad_bmp_observations.csv`: measured BMP for grass press cake/de-FOS whey, seasonal
  whole-road-verge grass batch yields (fresh and ensiled; spring/summer/autumn; wet/dry
  fermentation), four fresh/4-month-ensiled Lincolnshire 15-day yields after hydrolysis simulation,
  six post-protein-extraction green-biorefinery brown-juice/press-cake range and model records,
  theoretical source-calculated values, methane fraction and kinetic time markers.
- `ad_biochemical_fractionation.csv`: crude fiber, cellulose, hemicellulose and lignin.
- `ad_inhibition_feed_data.csv`: source-specific K, Na and P plus explicit missing TAN,
  alkalinity, VFA, COD and particle-size requirements.
- `ad_digestate_characterization.csv`: available digestate ratios and explicit missing fields.
- `grassification_roadside_codigestion_pilot_2020_reference.csv`: 98 source-located feed and digestate observations from Grassification D1.4.1 Tables 2–3. The digestate comes from a manure/grass co-digestion pilot and is not a grass-only or GreenHub residual result; keep all rows reference-only.
- `andre_roadside_grass_dry_codigestion_2019_abstract_reference.csv`: six abstract-level records on seasonal roadside-grass/manure methane potentials and a 60 L dry co-digestion pilot. The abstract does not fully map seasonal values to substrate and does not define the inhibition range; retain reference-only and do not map to a GreenHub yield parameter.
- `equation_registry.csv`: exact symbolic equations, Python expressions, units and limitations.
- `assumption_and_missing_data_register.csv`: unresolved required variables without inserted values.
- `source_register.csv` and `ad_source_register.csv`: source metadata and quality notes.
- `dataset_manifest.csv`: file inventory and row counts.

## Integration notes
Use `parameter_id` as the stable row key and `python_variable` as the proposed model mapping.
Before connecting to BioSTEAM/ADM1, select rows by:
1. exact material stream;
2. data status;
3. original basis;
4. operating conditions;
5. transferability.

Do not average across seasons, preservation methods or BMP bases without an explicit,
documented model rule. The Czubaszek et al. seasonal rows and Brown et al. storage comparison
are staged as measured primary evidence (DOIs 10.3390/en16114488 and
10.1016/j.biombioe.2020.105570), not activated in the residual-stream model:
they are whole verge grass, while the modeled AD input is a protein-depleted biorefinery
residual. Brown et al.'s 15-day yields also follow 50 °C/48 h hydrolysis simulation, so they
are not unpretreated BMP endpoints or storage-loss kinetics. The evidence adapter intentionally
leaves these rows metadata-only pending a compatible material boundary or an explicit whole-grass
AD route. Protein, lipid, carbohydrate, inert-solids, TAN, alkalinity, VFA,
full COD fractionation and absolute digestate nutrient concentrations remain important gaps.

Santamaria-Fernandez et al. (2018; DOI 10.1016/j.renene.2017.03.012) additionally
report cross-crop methane-yield ranges for press cake (219–375 mL CH4/g VS) and
residual brown juice (429–539 mL CH4/g VS) after protein extraction from four
organically grown green crops. These are not roadside-grass observations. The
staged brown-juice midpoint is an arithmetic scenario value (484 mL CH4/g VS),
not a measured mean; it can only be selected explicitly in the report-only AD
preview through `DynamicProxyClosurePolicy.bmp_parameter_id`. It is class C for
GreenHub application because crop and separation/fermentation boundaries differ.
The default remains the existing de-FOS-whey proxy. Press-cake values remain
outside the current dynamic AD mixer and are metadata-only. The reported 400
mL CH4/g VS co-digestion value is a red-clover regression-model result, not a
measured roadside-grass yield.

## Validation performed
- UTF-8 CSV encoding and comma delimiter;
- consistent required columns;
- unique primary IDs in each file;
- numeric values stored one per cell;
- no formulas or multiple numerical values in numeric cells;
- all populated numerical rows include a source ID and exact source location;
- normalized units checked for dimensional consistency;
- filenames cross-checked against the manifest.

## Important limitation
This is a high-confidence starter dataset, not an exhaustive systematic review. The included
sources were selected because they provide directly traceable tables, equations or project
laboratory results relevant to GreenHub streams. Further primary literature should be added
for protein-depleted grass liquid composition, co-digestion mixtures, inhibition thresholds,
ADM1 biochemical mapping and digestate nutrient speciation.

## Additional seasonal roadside-grass evidence (2024)
`ad_roadside_seasonal_biogas_reference_2024.csv` records seasonal composition observations,
methane fractions, and only exact biogas-yield means and standard deviations stated in the
results text of Czubaszek et al. (2024), DOI `10.3390/en17071751`. Source metadata is in the
adjacent `.source.json` sidecar and the feedstock package source register. This is B-class
literature-measured evidence, but it remains reference-only: it is whole grass from Poland,
not GreenHub's post-protein residual. Biogas yield and methane fraction are kept separate;
no synthetic methane yield is calculated. Censored sodium results remain missing, not zero.
The intermediate biogas-yield bars in Figure 1 were not digitized.

## Roadside grass storage-linked BMP comparator (2009)

`roadside_grass_storage_bmp_ovam_2009_reference.csv` records eight Table 13–14 batch biogas yields for roadside-grass samples described as fresh or held about 6 or 17 days before digestion, under separate wet-mesophilic and dry-thermophilic assays, and one measured batch endpoint for ten-week grass mono-silage. The first eight records reproduce Leenknegt (2004) through the OVAM-commissioned Elsen et al. report; those sample lots are not paired, and field storage conditions are not adequately specified. The mono-silage yield remains on the report's sample-added basis, not a VS basis. Methane fraction is blank where unreported; biogas is never relabelled methane. All nine observations are B-class literature evidence, reference-only and disconnected from runtime calculations. No storage loss coefficient, continuous HRT, or GreenHub residual BMP is inferred.

## Additional pilot and large-scale roadside-grass digestion evidence (2024)
`roadside_grass_residual_AD_2024_abstract_reference.csv` records only abstract-reported facts from de Souza et al. (2024), DOI `10.1016/j.wasman.2024.04.018`: three digestion settings, peak biogas yield up to 700 Nm3/t DOM (abbreviation and denominator preserved, not expanded), methane content 49–55%, and qualitative clogging/mixing/acidification issues. Yield and methane fraction are not paired. The article's accessible metadata did not establish a reuse license, and these rows remain reference-only; they are not GreenHub post-protein-residual kinetics or runtime values.

### Full-text roadside-grass pilot and digestate evidence (2024)

The companion files `roadside_grass_AD_2024_fulltext_process_reference.csv` (81 records) and `roadside_grass_AD_2024_fulltext_digestate_reference.csv` (12 records) expand the source using the accepted manuscript linked by the [Ghent University repository record](https://biblio.ugent.be/publication/01J3Z7596RHF1WVC93MQ8DG8J8) and the article DOI. The process extract transcribes Table 1 feed characterization and reported wet continuous, dry batch and landfill-cell operating/gas observations. The digestate extract preserves liquid/fiber recovery ranges, nutrient concentrations, leachate N/Cl and the regional fiber estimate. Experiment identity, units, denominators, qualifiers and source locations are retained row by row.

These are distinct study-specific observations, not matched GreenHub streams or transferable defaults. Table 1 EPi-test potentials conflict with some narrative potentials; the conflicts remain visible and unaveraged. The pilot inoculum basis is inconsistent between Methods and Results. Digestate fractions lack compatible paired denominators, and the printed 1,808 kg K/t DM exceeds a physical mass bound; the literal value and related ratio are quarantined pending correction. Raw chart workbooks were unavailable, so no time series was reconstructed. No explicit reuse license was identified. Neither companion is connected to runtime calculations.

## Green-biorefinery residual BMP and gas composition (2022)
`green_biorefinery_residual_bmp_reference_2022.csv` transcribes Table 3 from Ravindran et al. (2022; DOI `10.3390/cleantechnol4010003`, CC BY 4.0): biogas and methane-yield values on VS, DM, and fresh-matter bases for grass press cake, grass whey, de-FOS whey, and a grass-silage comparator, plus reported weighted biogas CH4/CO2/O2/H2S/NH3 composition and biodegradability. This supplies stronger B-class reference evidence for residual-feed BMP (Phase 5) and impurity screening (Phase 6).

All 47 rows remain `reference_only`. The source feed is cultivated Irish perennial ryegrass processed through a Grassa biorefinery; de-FOS whey includes additional FOS extraction and is not GreenHub isoelectric supernatant. Table 3 reports L/kg without an explicit standard-state designation and no uncertainty/replicate count is preserved here. Methane values are BMP gas volumes, not upgraded saleable biomethane. Raw gas percentages are preserved as reported, not normalized to 100%. No runtime mapping, parameter default, or chemistry has changed.

## Continuous grass/manure co-digestion and digestate comparator (2017)
`grass_manure_continuous_codigestion_moset_2017_abstract_reference.csv` records abstract-level conditions and relative results from two thermophilic continuous co-digestion experiments at 15 L and 30 m³. The source reports a 25-day HRT, 5% grass in fresh matter, scale-specific relative methane-yield increases for excoriated grass, a reported decrease in biogas methane concentration, qualitative digestate N:P:K/organic-matter/protein findings, and relative mixing-energy statements.

This is a manure-plus-natural-grass comparison, not a GreenHub protein-depleted residual test. The abstract supplies no absolute methane yield, exact temperature, nutrient concentrations, or absolute energy demand. The reported 6% gas-methane decrease is not clarified as relative percent or percentage points; the 14% mixing-energy comparison is not a transferable energy coefficient. All rows remain B-class `reference_only`; no runtime mapping, default, or route calculation changed.

## Co-ensiling, residual digestion and digestate soil-N response (2023)
`nyangau_2023_brown_juice_ensiling_ad_digestate_nutrient_reference.csv` transcribes Tables 1–4 from Nyang’au et al. (2023; DOI `10.1016/j.eti.2023.103248`, CC BY 4.0): straw/press-cake and silage chemistry, batch BMP/model fits, CSTR manure/digestate chemistry, and an 80-day soil inorganic-N concentration series. It is reference-only, not a Dutch roadside-grass or GreenHub process balance. Keep the batch BMP separate from the CSTR last-HRT methane yield; the soil assay is not recovered N mass, crop uptake, or a fertilizer credit. Missing/detection-limited values remain explicitly blank/status-coded. The extract does not activate process inputs.

## Dutch supply-chain and regional grass/biogas comparators (2014 and 2025)
`rvo_2014_grass_supply_storage_chain_cost_reference.csv` records historical national grass-availability estimates, differences between total grass arising and material transported off-site, field-to-silage practices, source-reported preservation losses, ensiling-density test points, and 2014 chain-cost/substrate-price comparators from the official RVO-commissioned study. The report states that exact national quantities are unavailable and synthesizes older studies, waste statistics, and stakeholder interviews. It is not a current supply measurement. Reported storage losses refer to biogas potential, not mass loss; two JansenWijhe yield examples repeat the same 30% DM label for different outputs and are retained without correction.

`van_gras_naar_gas_2025_regional_feed_quality_tea_reference.csv` records the 2025 report's regional dry-matter availability table, Idafehn planning scenario, cross-feedstock quality/emissions table, theoretical gas-potential table, and grass/manure TEA case. The table's green-gas totals do not reconcile with its nearby stated 580 Nm³ CH₄/t organic-DM factor; no upgrading efficiency is inferred. The Idafehn scenario lacks moisture and access bases. Table 3 emission factors lack row-level source lineage and LCA boundaries, while the TEA case lacks a comparable cost year and complete financial basis. Both files remain B-class, `reference_only`, and disconnected from model defaults, process calculations and Pareto inputs. Source URLs, rights status and record-level locations are in their sidecars.

## Dutch roadside-grass dry digestion and product assays (2015)
`alterra_2015_roadside_grass_dry_ad_reference.csv` contains 156 row-level records from Zwart & de Boer, Alterra Report 2661. It adds local management/harvest and ensiling context; spring/autumn roadside and Sellingen nature-grass DM, organic matter, ash and nutrient assays; potential biogas estimates and the separately reported autumn LUFA result; feed contaminant measurements with report-era limits; Dörpen/Ostrhauderfehn mixed-feed recipes and approximate case mass flows; and compost/digestate composition.

The assays describe local 2013 samples, not GreenHub/VARTA feed. Wet-mass basis, replicate uncertainty and gas reference state are incomplete. Mixed-feed results cannot be assigned to grass alone. The historical Dörpen climate scenario is class C/reference-only, not a reproducible LCA result; open digestate methane/ammonia and the Ostrhauderfehn balance are explicitly unquantified. Table 7's 0.4 kg/t meadow-digestate DM vs organic-matter-plus-ash discrepancy is preserved; the chromium row is quarantined due to ambiguous extracted column alignment. No default, runtime equation, TEA/LCA factor or Pareto input was activated. Source metadata and exact pages are in the sidecar; report record: https://research.wur.nl/en/publications/droge-vergisting-van-berm-en-natuurgras/.

## Dutch supply-chain and regional grass/biogas comparators (2014 and 2025)
`rvo_2014_grass_supply_storage_chain_cost_reference.csv` records historical national grass-availability estimates, differences between total grass arising and material transported off-site, field-to-silage practices, source-reported preservation losses, ensiling-density test points, and 2014 chain-cost/substrate-price comparators from the official RVO-commissioned study. The report states that exact national quantities are unavailable and synthesizes older studies, waste statistics, and stakeholder interviews. It is not a current supply measurement. Reported storage losses refer to biogas potential, not mass loss; two JansenWijhe yield examples repeat the same 30% DM label for different outputs and are retained without correction.

`van_gras_naar_gas_2025_regional_feed_quality_tea_reference.csv` records the 2025 report's regional dry-matter availability table, Idafehn planning scenario, cross-feedstock quality/emissions table, theoretical gas-potential table, and grass/manure TEA case. The table's green-gas totals do not reconcile with its nearby stated 580 Nm³ CH₄/t organic-DM factor; no upgrading efficiency is inferred. The Idafehn scenario lacks moisture and access bases. Table 3 emission factors lack row-level source lineage and LCA boundaries, while the TEA case lacks a comparable cost year and complete financial basis. Both files remain B-class, `reference_only`, and disconnected from model defaults, process calculations and Pareto inputs. Source URLs, rights status and record-level locations are in their sidecars.

## Cross-phase meadow-grass pretreatment, BMP, and digestate comparator (2025)
`meadow_grass_pretreatment_bmp_digestate_chopda_2025_reference.csv` records 63 source-located facts from Chopda et al. (2025; DOI `10.1007/s13399-024-05776-y`): Irish meadow-grass identity and lignocellulosic composition; milling and laboratory ensiling conditions; post-treatment TS/VS endpoints; batch methane-potential results; alternative acid/enzyme hydrolysis and lactic-acid fermentation conditions/yields; raw BMP-gas methane range; and reported digestate N/P/K amounts. Each row preserves the reported value, unit, basis, treatment, condition, uncertainty note, and source location.

This is B-class, reference-only evidence from cultivated Irish meadow grass, not roadside grass, VARTA samples, or GreenHub's protein-depleted process streams. Composition and selected loading bases remain unresolved where the article does not define them. Laboratory endpoints are not converted into storage kinetics, full-scale press performance, continuous-AD yields, upgrading efficiencies, fertilizer credits, or defaults. The lactic-acid route is an alternative hydrolysate pathway, not protein extraction; raw methane fraction is not upgrading evidence. The accepted manuscript's repository notice restricts redistribution; see the source sidecar before any external reuse. [DTU research record](https://orbit.dtu.dk/en/publications/from-grass-to-lactic-acid-and-energy-evaluating-pretreatment-tech/), [DOI](https://doi.org/10.1007/s13399-024-05776-y).

## Continuous grass/manure co-digestion and digestate comparator (2017)
`grass_manure_continuous_codigestion_moset_2017_abstract_reference.csv` records abstract-level conditions and relative results from two thermophilic continuous co-digestion experiments at 15 L and 30 m³. The source reports a 25-day HRT, 5% grass in fresh matter, scale-specific relative methane-yield increases for excoriated grass, a reported decrease in biogas methane concentration, qualitative digestate N:P:K/organic-matter/protein findings, and relative mixing-energy statements.

This is a manure-plus-natural-grass comparison, not a GreenHub protein-depleted residual test. The abstract supplies no absolute methane yield, exact temperature, nutrient concentrations, or absolute energy demand. The reported 6% gas-methane decrease is not clarified as relative percent or percentage points; the 14% mixing-energy comparison is not a transferable energy coefficient. All rows remain B-class `reference_only`; no runtime mapping, default, or route calculation changed.
