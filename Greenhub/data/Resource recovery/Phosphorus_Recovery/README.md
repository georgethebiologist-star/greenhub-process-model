# GreenHub phosphorus-recovery datasets

This package covers struvite and defensible calcium-phosphate precipitation routes for digestate,
centrate and agricultural wastewater.

## Equilibrium-basis rule
Activity-based constants must be compared with ionic activities. Concentration-based empirical
constants may only be used in their original matrix, temperature and ionic-strength range.
The two bases must never be mixed.

Total P is not treated as orthophosphate. Dissolved orthophosphate, TAN, Mg, Ca, pH, temperature,
alkalinity and ionic strength are required scenario inputs.

No unsupported numerical assumptions were inserted. Missing kinetics, product properties,
separation performance and equipment cost inputs remain blank and are registered explicitly.

Use `parameter_id` as the provenance key and `python_variable` as the BioSTEAM-facing key.
Filter by route, matrix, operating conditions, equilibrium basis and transferability.

## Phase 7 reference evidence

`fe_modified_biochar_phosphate_isotherm_bioden_reference.csv` transcribes nine measured Table 1 points from the BioDEN Task 3.2 public factsheet. They are synthetic phosphate solutions at pH 7 and 24 h, and must not be treated as a real-digestate or GreenHub adsorption isotherm. The factsheet separately describes a chicken-manure digestate test (230 mg/L PO4-P, 2–52 g/L biochar, up to 93% removal); that is retained in the provenance sidecar as text-level context, not mixed into the synthetic dataset. DOI and explicit reuse license were not identified. All values remain reference-only.
`phase7_cattail_digestate_recovery_reference.csv` records only abstract-level results from
Petrovič et al. (2021), DOI `10.1016/j.jenvman.2021.112593`: P recovery reported above 99 wt%,
N recovery 85–92 wt%, precipitate above 25 wt% NPK, and a qualitative positive K-recovery finding
for zeolite methods. These are cross-method results for liquid digestate from sewage-sludge and
cattail co-digestion with rumen-fluid enhancement. They are not route-specific GreenHub efficiencies.
Ranges and thresholds are preserved as text with numeric cells blank; no midpoint, route allocation,
or default parameter is inferred. Obtain the full paper tables and feed-specific speciation before
considering any calculation connection.

## Additional pilot source located
Proskynitopoulou et al. (2024), DOI `10.1016/j.jenvman.2024.120166`, reports digestate
composition and pilot results for MF/UF/RO, selective electrodialysis, UV/ozonation, and struvite
precipitation. The digestate is mainly food-industry waste with animal and agricultural co-substrates,
not GreenHub grass digestate. The article is CC BY-NC-ND 4.0 and states underlying data are available
on request. It is registered for discovery, but numeric tables are not copied into a new dataset here;
request the authors' data and confirm reuse rights before any extraction or calculation use.

## Dutch farm-scale nutrient recovery comparator (Phase 7)
`demarke_manure_digestate_nutrient_recovery_2019_reference.csv` transcribes 18 measurements and source-reported efficiencies from Szymańska et al. (2019), DOI `10.3390/en12010155` (CC BY 4.0). The 2017 samples came from the De Marke cattle-slurry farm biorefinery in the Netherlands. Records cover liquid digestate pH, total solids, N/NH4-N/P/Mg; recovered mixed struvite nutrient content; and ammonium-sulfate solution composition. The study is useful for product-quality context: its recovered product contained 39.4 g P/kg wet product, while ammonium sulfate was dilute (66.4 g/kg; pH 2.1).

The source-reported 43.8% P and 43.2% N efficiencies are differences between feed and final-effluent concentrations, not closed, flow-weighted elemental recoveries; the N figure combines struvite precipitation and ammonia stripping. All rows remain `reference_only`: cattle slurry is not roadside-grass digestate, and these records do not supply GreenHub reagent demand, product sale grade, or a validated recovery factor.

## Agricultural digestate membrane/water recovery benchmark (Phase 7)
Three Rizzioli et al. (2025) CC BY 4.0 tables (DOI `10.1016/j.jclepro.2025.144958`) preserve raw-feed characterization, 29 measured stream compositions across MF/UF/RO and NF/RO configurations, and 15 reported mass-based nutrient/water recovery means with SD. The source used Italian cow-manure/energy-crop digestate, not grass. Its Line 2 UF+RO reported water recovery (32.75 ± 1.86% of feed mass) and RO-retentate ammonium-N recovery (46.50 ± 1.14% of initial ammonium-N) are comparison data only. Separate sidecars bind each CSV to the exact source ID/DOI, and SHA-256 values are recorded; no value is activated as a GreenHub assumption or default.

## Agricultural digestate membrane/water recovery benchmark (Phase 7)
Three Rizzioli et al. (2025) CC BY 4.0 tables (DOI `10.1016/j.jclepro.2025.144958`) preserve raw-feed characterization, 29 measured stream compositions across MF/UF/RO and NF/RO configurations, and 15 reported mass-based nutrient/water recovery means with SD. The source used Italian cow-manure/energy-crop digestate, not grass. Its Line 2 UF+RO reported water recovery (32.75 ± 1.86% of feed mass) and RO-retentate ammonium-N recovery (46.50 ± 1.14% of initial ammonium-N) are comparison data only. Separate sidecars bind each CSV to the exact source ID/DOI, and SHA-256 values are recorded; no value is activated as a GreenHub assumption or default.

## Dairy-digestate nanofiltration/struvite pilot (Phase 7)
`dairy_digestate_nf_struvite_pilot_2023_reference.csv` transcribes seven abstract-level results
from Tsaridou et al. (2023), DOI `10.30955/gnc2023.00314`. The publisher page identifies the
proceedings content as CC BY 4.0. The pilot treats dairy-processing-effluent digestate, not
grass-derived digestate; the records remain `reference_only`. The reported retentate composition,
precipitation conditions, and precipitate mass are not defaults, transferable recovery factors,
or a closed nutrient/product balance.

## Green-biorefinery digestate reference composition (Phase 7)
`green_biorefinery_digestate_nutrient_reference_2022.csv` transcribes 59 reported Table 4
observations from Ravindran et al. (2022), DOI `10.3390/cleantechnol4010003` (CC BY 4.0).
The source digestates came from triplicate, 1 L batch BMP tests of cultivated perennial-ryegrass
press cake, grass whey, and de-FOS whey. As-received versus dry-mass bases follow the table
footnote. These data remain `reference_only`: total P is not orthophosphate/speciation, elemental
K is not K2O grade, and laboratory digestate is not a GreenHub continuous-digester balance.

## Second-year struvite fertilizer-use comparator (Phase 7)
`demarke_struvite_second_year_grass_soil_szymanska_2020_reference.csv` transcribes 185 records from Szymańska et al. (2020), DOI `10.3390/en13205342` (CC BY 4.0): application doses, second-year grass N/P/Mg concentrations over four harvests, source-calculated relative fertilizer efficiencies, soil chemistry, and selected yield and nutrient-uptake values stated in the text. This extends the first-year De Marke pot-study dataset without repeating it. The struvite came from cattle-slurry digestate at a Netherlands farm biorefinery, while use was tested in a Polish greenhouse with three pot replicates. No fertilizer was applied in the second year. Figure-only uncertainty was not digitized, pooled means are not split into treatments, and all records remain reference-only; this dataset does not support a GreenHub fertilizer credit or field-scale substitution factor.

## Additional pilot source located
Proskynitopoulou et al. (2024), DOI `10.1016/j.jenvman.2024.120166`, reports digestate
composition and pilot results for MF/UF/RO, selective electrodialysis, UV/ozonation, and struvite
precipitation. The digestate is mainly food-industry waste with animal and agricultural co-substrates,
not GreenHub grass digestate. The article is CC BY-NC-ND 4.0 and states underlying data are available
on request. It is registered for discovery, but numeric tables are not copied into a new dataset here;
request the authors' data and confirm reuse rights before any extraction or calculation use.
