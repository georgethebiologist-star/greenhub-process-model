# Phase 1–7 data collection status

### Phase 1 — secondary report of Greenhub collection volume (2025-06-20)

Screened and staged the statement in [Duurzaam Gebouwd](https://www.ktgo.nl/artikel/20250620-zuid-holland-maakt-van-bermgras-bouwmateriaal): it reports more than 150 t/year of roadside cuttings collected by Greenhub “in recent years.” The statement is recorded as a threshold claim (150 t/year lower bound), class B/secondary publication, with no exact years, wet/dry basis, collection scope, weighing records, or uncertainty. It is not treated as a point estimate, supply series, or calculation input. It is not directly comparable with the separate 117 t 2024 dry-run figure or the first-party 120 t result with unspecified period; those figures are not summed or reconciled. Source ID `SRC-GHZH-SECONDARY-150T-2025` is linked in the Feedstock source register, dataset manifest, global source register/readiness, and FAIR catalog. No seasonal availability, process, TEA/LCA, UI, or Pareto calculation changed.

The current Greenhub page also reports an undated 100 t of Bokashi used at a nursery; this is recorded as Phase 7 product-use context, not as digestate-derived fertilizer yield, with no nutrient/product assay or substitution credit. A 23 September 2026 [AquaMinerals–Greenhub announcement](https://greenhub-zuidholland.nl/aquaminerals-en-greenhub-zuid-holland-zetten-samen-stap-naar-circulaire-grasketen/) says the first step of the intent-agreement pilot is mapping shareholder grass availability and quality. This is a concrete Phase 1 data-acquisition lead, but no results or underlying dataset are published. The expanded 25-row package remains reference-only; no process or supply calculations were changed.

### Phase 1 — announced autumn roadside-grass quantity; completion unverified (2025)

Added `greenhub_autumn_roadside_grass_600t_announcement_reference.csv` as a separate first-party project announcement. Greenhub said it expected to process approximately 600 t of roadside grass into construction material and soil product that autumn, supplied by two large market parties. The related Greenhub agenda event is dated 7 November 2025, but the social post's exact timestamp is not exposed; the event date is recorded only as context. The 600 t is an approximate announced quantity, not a verified collection/delivery measurement: there are no public weighbridge records, wet/dry basis, delivery dates, supplier split, or confirmation of completion.

Do not confuse it with the distinct 600 t of GKB's own grass reported for Bokashi in the 28 November 2025 dry-run recap. The two sources describe different material/use routes, and the latter does not confirm completion of the roadside-grass announcement. Both remain separate, reference-only records; neither changes feedstock availability or model defaults. Sources: [Greenhub post](https://nl.linkedin.com/posts/greenhub-zuid-holland_van-bermgras-tot-bouwmateriaal-en-bodemproduct-activity-7389307797911478272-BwKN), [Natuurlijke Reststromen report](https://natuurlijkereststromen.nl/aan-de-slag-met-uitvoeringsagenda-greenhub/), and [dated Greenhub event page](https://greenhub-zuidholland.nl/samen-door-de-bermgrasdeur/).

### Phases 1–4 — ReJuice roadside-grass seasonal and ensiled-juice context (2025)

Added `rejuice_wp5_roadside_grass_seasonality_and_ensiled_juice_reference.csv`, a four-record extract from the ReJuice WP5 *Seizoenskalender* draft (April 2025). It records the report's qualitative May–November roadside-grass availability window, its two broad peak windows (mid-June to mid-July and mid-September to mid-October), an approximate 40% juice fraction for pressing ensiled grass, and its qualitative warning that ensiling can make the juice unsuitable for thermal protein precipitation.

These do not form a measured GreenHub seasonal feed curve or a screw-press/protein-recovery calibration: the draft has no monthly tonnage series, and the approximate juice fraction has no reported wet/dry denominator, batch measurements, press conditions, or mass closure. Its broader national biomass figures are attributed to Inagro and RVO (2014) and were not duplicated because the RVO report is already staged separately. Everything remains reference-only. Sources: [ReJuice WP5 draft](https://interregvlaned.eu/uploads/project-downloads/Seizoenskalender_deliverable_DRAFT.pdf) and the already-indexed [RVO 2014 grass report](https://www.rvo.nl/sites/default/files/2014/04/Definitief_Een%20studie%20naar%20kansen%20voor%20grasvergisting.pdf).

### Phases 1, 3, 5 and 7 — ReJuice AWB Schots pilot data-acquisition lead (2026)

Added `rejuice_awb_schots_grass_juice_ad_pilot_plan_2026_reference.csv` as a traceable acquisition lead, not as process results. Interreg reported on 6 February 2026 that a 2.5 m³ CSTR pilot was planned at A.W.B. Schots, with expected grass-juice throughput of 3,000–9,000 t/year and plans to monitor methane potential, biogas yield, sediment effects, and digestate characteristics. The reported throughput is expected juice output—not collected roadside grass. The article does not verify commissioning or publish a measurement series.

The official project news index shows the pilot announcement and later project events, but I found no public follow-up operating dataset in the pages checked on 8 November 2026. The project lists a final event for 22 February 2027, which is a practical retrieval lead for partner records, not proof they will be released. Priority request: actual commissioning/run dates; source/harvest and press feed masses; paired grass–juice–fiber flows and analyses; CSTR HRT/OLR and uptime; calibrated daily gas flow and composition; utility/chemical logs; and flow-weighted digestate analyses. The announced figures remain `not_applicable_project_plan_not_measurement`, reference-only, and disconnected from the GreenHub model. Sources: [Interreg pilot announcement](https://interregvlaned.eu/nieuws/pilootreactor-biogas-bij-awb-schots) and [official ReJuice news/events](https://interregvlaned.eu/rejuice/nieuws-events).

### Phases 1–7 — ReJuice partner trials identified for direct data retrieval (2025–2026)

The June 2025 Aquarama report describes completed project activities that are more useful than the earlier plans alone: VARTA had tested multiple presses at locations in the Netherlands and Flanders and collected samples for Ghent University analyses; Thomas More had tested grass-juice preservation methods; and Innolab had tested the biogas potential of different grass fractions. It gives no numerical observations, sample identifiers, protocols, or downloadable data. The later ReJuice project summary says pressing was tested at pilot and full scale with attention to yield, composition, and seasonal influences, again without publishing the underlying measurements. These are first-party activity reports relayed through project/industry pages, not measurements that can be transcribed into GreenHub parameters. Sources: [Aquarama report](https://www.aquarama.be/nl/artikels/item/873/het-rejuice-project-wil-groene-reststromen-in-vlaanderen-en-nederland-valoriseren), [ReJuice project progress summary](https://www.biorefine.eu/projects/rejuice/), and [Ghent University project scope](https://research.ugent.be/web/result/project/e1b61ec6-fdd5-4b3f-8d86-aba9dfd32108/details/en).

This is now a concrete, phase-linked retrieval route, registered as `SRC-REJUICE-PARTNER-TESTS-AQUARAMA-2025`. The highest-value request is one anonymized, sample-ID-linked export with: (1) supplier/site, cut date, area, harvested and received mass, and as-received moisture; (2) press make/model, operating settings, throughput, power, added water, and weighed juice/fibre outputs; (3) paired raw-grass, juice, fibre, and storage-time assays including DM, ash, total and soluble protein/N, carbohydrates, COD, pH, and nutrients; (4) preservation temperature/time and repeated chemistry; (5) grass-fraction AD feed basis, inoculum, HRT/OLR, uptime, metered gas flow/composition and digestate flow/chemistry; and (6) any upgrading, nutrient-recovery, or product-quality measurements. This connects phases 1–7 without conflating unrelated crop streams. VARTA/UGent are the press/sample-analysis leads, Thomas More the preservation lead, and Innolab/A.W.B. Schots the AD and digestate leads. No request has been sent, no private data were accessed, and no default, equation, route, result, or Pareto data changed. The reported experiments do not establish that all listed assays exist; fields absent from source records must remain missing.

Current FAIR catalog after the latest Phase 5 extract: 805 assets and 897 normalized input records (744 source-linked, 597 DOI-linked; 65 without source-register linkage). The latest Checkpoint 1 activation registry covers 472 datasets (62 blocked, 410 reference-only; zero active/default-eligible) and records 713 audit issues. The separate global readiness inventory covers 501 datasets (444 D3, 29 D2, 28 D1); counts describe register coverage, not scientific completeness.

### Phases 1/3/4 — perennial-ryegrass wet-fractionation mass and protein partition (2026-11-08)

Added `Greenhub/data/Pre-treatment/Mechanical/perennial_ryegrass_wet_fractionation_aakjaer_pedersen_2025_reference.csv` (15 records) from Aakjaer Pedersen et al. (2025; DOI [`10.3390/proteomes13010008`](https://doi.org/10.3390/proteomes13010008), CC BY 4.0). Table 1 reports fresh sample masses and the reported dry-matter and crude-protein concentration/distribution across raw perennial ryegrass, pulp and green juice. Percentages are normalized only by division by 100; reported SDs and the unspecified exact replicate count are retained. The extract and source metadata are linked through the local/global registers, checksum, manifest, and FAIR catalog.

The crop was controlled-grown *Lolium perenne* var. Abosan 1 (batch 2, 50 days), immediately wet-fractionated with a laboratory Angelia 8500 S juicer. This is a B-tier grass comparator, not roadside/VARTA grass, not a GreenHub screw-press validation, and total crude nitrogen × 6.25 is not soluble protein. The printed stream masses leave 7.9 g of wet mass unaccounted for; no water-loss outlet is invented. Source-reported DM and CP distributions sum to 99.9% and 99.7%, respectively, with rounding/measurement uncertainty. Data are D3/reference-only and are not connected to model parameters, defaults, TEA/LCA factors or Pareto results.

### Phase 1 — Greenhub Bermgras Canvas contamination-screening guidance (2025)

Added `greenhub_bermgras_canvas_quality_routing_2025_reference.csv` (7 qualitative records) from the Greenhub Zuid-Holland Bermgras Canvas guide, printed page 22. It records the green/orange/red area-screening classes mapped by the guide to CROW visual-litter grades A+/A, B, and C/D; flags the first metre beside roads and high-use locations for extra cleaning; and distinguishes visible litter/invasive species from invisible chemical or tyre-wear/microplastic contamination. This is operational guidance, not measured contamination data or a biorefinery acceptance standard. No occurrence rates, contaminant concentrations, cleaning efficiencies, mass fractions, or process thresholds are inferred; it remains reference-only and non-runtime.

### Phase 1 — Greenhub South Holland processing-capacity ambitions (2026-11-08)

Added `greenhub_zuid_holland_processing_capacity_ambitions_2026_reference.csv` with two first-party statements: the homepage describes a future ambition of up to 30,000 t/year of roadside verge cuttings within 3–5 years; the separate approach page describes a 30,000 t/year facility for mixed biogenic residuals, including public-space and horticultural sources. These are stored as distinct scopes, not summed or treated as interchangeable. Both remain project targets, not measured supply, installed capacity, or throughput; no mass basis, operating hours, commissioning date, contracts, or realized feed receipts are provided. They are registered as `not_applicable_project_target`, reference-only, and do not change the model's defaults or capacity.

### Phases 3–5 — cell-wall sugars across green-biorefinery fractions (2026-11-08)

Added `grass_clover_alfalfa_cellwall_sugar_fractionation_glazowska_2025_reference.csv` (132 records) from Głazowska et al. (2025; DOI [`10.1007/s13399-023-05125-5`](https://doi.org/10.1007/s13399-023-05125-5)). Table 2 reports HPLC-RI monosaccharides and uronic acids in alcohol-insoluble residue from fresh material, press cake, green juice, fiber filtrate, brown juice and leaf-protein concentrate for cultivated alfalfa and grass-clover. The article states CC BY 4.0.

This adds measured fiber-composition evidence across screw pressing, filtration, fermentation/isoelectric precipitation and centrifugation. It does not provide flow-weighted component recovery, wet-stream concentrations, mass closure, or GreenHub roadside-grass performance. A source inconsistency is preserved explicitly: the Table 2 footnote gives analyte units as µg/mg AIR, while the Total column is labelled µg and the reported Total (%) values do not reconcile with that footnote; methods state a 10 mg AIR sample was used. Values are transcribed literally without correction or conversion. HPLC replicate count and table-level uncertainty are not printed. Records remain B-class, D3/reference-only; no runtime input, default, TEA/LCA value or Pareto result uses them.

### Phases 1 and 4 — harvest method and processing-delay effects on grass-clover protein (2026-11-08)

Added `Greenhub/data/storage/grass_clover_harvest_delay_digestible_protein_laerke_2025_abstract_reference.csv` (16 records) from Lærke et al. (2025; DOI [`10.1016/j.anifeedsci.2025.116336`](https://doi.org/10.1016/j.anifeedsci.2025.116336)). The extract preserves the reported immediate crude-protein SID results, selected calculated digestible-protein yields, and statistical outcomes. The abstract states that 0, 6 and 12 hours were tested, so unreported 6-hour and delayed SID values are represented as blank/tested-but-unreported, not interpolated.

This is Danish cultivated grass-clover, not roadside/VARTA grass. The full article is CC BY 4.0 according to the [Aarhus University record](https://pure.au.dk/portal/en/publications/towards-efficient-grass-clover-biorefining-influence-of-harvestin/), but the underlying experimental data are available on request; only the abstract-level results are staged. The dataset is B/D3, reference-only, and does not activate harvest-delay kinetics or protein-recovery parameters.

### Phases 2, 5 and 7 — co-ensiling, residual digestion and soil nutrient availability (2026-11-08)

Added `nyangau_2023_brown_juice_ensiling_ad_digestate_nutrient_reference.csv` (464 long-form records) from Nyang’au et al. (2023; DOI [`10.1016/j.eti.2023.103248`](https://doi.org/10.1016/j.eti.2023.103248)). The article is open access under CC BY 4.0. The extract covers Tables 1–4: straw/press-cake silage chemistry and dry-matter loss; batch BMP and the authors’ fitted kinetic metrics; raw manure/CSTR digestate chemistry and methane yields; and inorganic-N concentrations over an 80-day soil incubation. Reported units, bases, uncertainty, significance groups, below-detection qualifiers, and blank/not-reported states are retained.

This provides useful cross-phase experimental evidence, especially a time-resolved soil-N response and digestate assays for Phase 7. It is not GreenHub roadside-grass validation: the study uses wheat straw, cattle manure, grass-biorefinery press cake, and brown juice from a heated-protein-precipitation route. Soil-N concentration is not plant uptake, recovered nutrient mass, or an avoided-fertilizer credit. The CSTR methane yields are distinct from batch BMP, and a first-order-rate unit is preserved as printed (“day”) with the paper’s inverse-time equation noted. The extract is B/D3 reference-only and is not mapped to a runtime parameter, default, TEA/LCA credit, or Pareto scenario. Source: [open full text and license](https://pure.au.dk/portal/files/328744571/Nyang_au_et_al_2023b_Brown_juice_assisted_ensiling_of_straw_and_press_cake_for_enhanced_biogas_production_and_nutrient_availability_in_digestates.pdf).

### Phases 3–5 and 7 — clover-grass fraction yields and nutrient recovery/AD summaries (2026-11-08)

Added `clover_grass_nutrient_recovery_and_ad_balance_santamaria_2020_reference.csv` (48 records) as a companion to the existing Santamaria-Fernandez et al. (2020) Table 1/2 extract. It records small-scale red-clover and clover-grass wet product shares; source-reported nutrient recovery bounds for press cake, brown juice, protein concentrate and combined residual streams; plus CSTR digestate concentrations and nutrient outcomes that were present in the paper narrative but absent from the existing 69-row extract. It explicitly separates 56% carbon conversion from the source-calculated 48% organic-matter conversion and keeps the source’s alternative C:N statements quarantined rather than reconciled.

This remains Danish cultivated-forage evidence, not roadside/VARTA or a GreenHub press/precipitation mass balance. Several ranges are grouped across crops rather than crop-specific; narrative concentrations are approximate; and the proof PDF’s Table 2 text layout is malformed. The source record does not verify CC BY reuse, so the sidecar records the university repository’s private-study/source-link notice and external redistribution caution. The companion is B/D3 reference-only and not a runtime default, fertilizer credit or model calibration. Source: [article DOI](https://doi.org/10.1007/s12649-019-00842-3), [Aalborg University full text](https://vbn.aau.dk/ws/files/450867530/e.Proofing.pdf).

### Phases 2 and 5 — roadside-grass silage-duration co-digestion abstract (2026-11-08)

Added the three abstract-reported storage-duration response observations from Homeky et al. (2016), DOI `10.1002/ep.12361`, to `Greenhub/data/storage/roadside_grass_silage_duration_codigestion_homeky_2016_abstract_reference.csv`. Roadside grass was ensiled without additives for 3, 8 and 36 weeks, then batch co-digested with cow slurry. Relative methane yield for the mixtures changed by −14%, −5% and +15% versus slurry-only controls, respectively; each mixture was tested twice and no additional inoculum was used. Duration-in-days is a transparent 7-day/week conversion.

This is abstract-only B-tier primary evidence; full text/raw yields were not accessible. It does not isolate the storage effect on grass, report absolute yield, storage mass loss, slurry:grass ratio, temperature, or uncertainty. It is reference-only and does not activate a storage or AD parameter. Source: [publisher DOI/abstract](https://doi.org/10.1002/ep.12361), [publisher abstract page](https://aiche.onlinelibrary.wiley.com/doi/abs/10.1002/ep.12361).

### Phases 6–7 — full-scale PSA operations and LCA/LCCA comparator (2026-11-08)

Added `Greenhub/data/Bigas production + upgrade/PSA/kohlheb_2020_brandis_fullscale_psa_lca_reference.csv` (49 rows) from Kohlheb et al. (2021 online; DOI `10.1007/s12155-020-10205-9`, CC BY 4.0). This is unusually useful Phase 6/7 evidence: full-scale PSA raw/product gas composition, rated capacity, plant-wide electricity, reported operating pressures, and a cradle-to-gate PSA LCA with functional unit, CML method/version and GWP result; it also reports plant LCCA assumptions/results.

It is a single German energy-crop plant (10–15% grass silage in the digester feed), not GreenHub residual gas. Plant power is not split by unit, price year is absent, and GWP uses an EU-28 grid and a study-specific upgrader-only boundary. The paper's 1.5%/95,265 Nm³/year diagram loss label is kept distinct from its operator-reported 0.2%/12,194 Nm³/year atmospheric methane input; their relation is not reconciled despite an off-gas oxidizer in the process flow. The 16,600 Nm³/day diagram product flow is not reconciled with the separately calculated 127.02 million Nm³ lifetime product. Most other Table 2 impact rows lack category-specific units in the retrieved table text and are quarantined. No parameter, default, TEA/LCA factor, runtime route, UI/API behavior or Pareto result was changed. Source: [DOI](https://doi.org/10.1007/s12155-020-10205-9), [full text](https://d-nb.info/1223080811/34).

### Phases 1–3, 5 and 7 — Dutch roadside-grass dry-digestion field report (2026-11-08)

Added the 156-row `alterra_2015_roadside_grass_dry_ad_reference.csv` extract from Zwart & de Boer, *Droge vergisting van berm- en natuurgras* (Alterra Report 2661, 2015). It records Borger-Odoorn road/management and 2013 seasonal mowing context; ensiling-to-use intervals with unknown exact duration; three ensiled feed samples' moisture, DM, organic matter, ash, N/P/K and metals; potential biogas values plus a separate LUFA autumn sample result; mixed-feed case recipes/yields and approximate mass flow; and compost/digestate composition. The full-text mirror, WUR record, stable report identifier (no DOI), source locations, rights caveat, and uncertainty are in the sidecar. The report's assay/lab and modeled scenario data remain reference-only.

No basis normalization, gas standard-state conversion, mass closure, LCA factor or GreenHub parameter mapping was made. The report's mixed-feed gas values are not attributed to grass; the old modeled GHG comparison is class C and has no reproducible full LCA boundary. It explicitly leaves open-digestate CH4/NH3 emissions unquantified. Table 7's 0.4 kg/t digestate DM discrepancy is preserved, and an ambiguously aligned chromium row is quarantined. No process defaults, calculations, API/UI behavior or Pareto outputs changed. Source: [WUR report record](https://research.wur.nl/en/publications/droge-vergisting-van-berm-en-natuurgras/), [accessible full-text mirror](https://www.researchgate.net/publication/283403753_Droge_vergisting_van_berm-_en_natuurgras).

### Data collection verification snapshot (2026-11-08)

FAIR and governance counts are recorded in the current persistent checkpoint after the latest rebuild. New literature-only data do not resolve project-specific feed, process or market gaps, and are not active/default-eligible.

### Phases 1–3, 5 and TEA — Dutch supply-chain and regional grass/biogas evidence (2026-11-08)

Added two source-located, reference-only extracts to the Feed BMP evidence package. `rvo_2014_grass_supply_storage_chain_cost_reference.csv` transcribes historical Dutch availability estimates and their different boundaries, field-to-silage recommendations, reported silage biogas-potential losses, laboratory packing-density comparators, biogas-yield ranges, and historical chain-cost/SDE+ substrate-price scenarios from the RVO-commissioned Brinkmann Consultancy study. The report states exact national quantities are unavailable; figures combine prior studies, waste statistics and interviews. These are not weighed current supply, GreenHub delivery records, mass-loss kinetics or current TEA prices.

`van_gras_naar_gas_2025_regional_feed_quality_tea_reference.csv` adds the 2025 report's North Netherlands availability allocation, Idafehn planning scenario, six-feedstock quality/emissions comparison, theoretical gas-potential table and grass/manure TEA summary. The table's 67/43/375/31 MNm³ totals do not reconcile with its nearby stated theoretical factor of 580 Nm³ CH₄/t organic DM; the dataset preserves both and flags the inconsistency. The Idafehn 19,500 t/year result lacks moisture and access bases. Table 3 emission factors lack source-level methods and system boundaries; the case-level TEA lacks a complete financial basis. No value is used as a process, storage, supply, TEA or LCA default.

These sources add comparators for Phases 1, 2, 3 and 5, and limited unverified Phase 7 emissions context. They do not fill project-specific gaps in delivered seasonal supply, storage kinetics, GreenHub press/precipitation balance, residual digestion, upgrading, or nutrient recovery. Sources: [RVO-commissioned 2014 study](https://www.rvo.nl/sites/default/files/2014/04/Definitief_Een%20studie%20naar%20kansen%20voor%20grasvergisting.pdf), [Van Gras Naar Gas final report](https://www.hanze.nl/binaries/_cb_1758882594458/content/assets/hanze/nl/onderzoeken/kenniscentra-en-centres-of-expertise/kenniscentrum-biobased-economy/eindrapport-van-gras-naar-gas.pdf).

### Phase 2 — grass ensiling chemistry and aerobic-exposure time series (2026-11-08)

Added `Greenhub/data/storage/high_moisture_grass_silage_fermentation_li_nishino_2013_reference.csv`, a 164-record grass-only transcription of Li and Nishino (2013; DOI [`10.5713/ajas.2013.13175`](https://doi.org/10.5713/ajas.2013.13175)). It includes pre-ensiled dry matter and pH for Italian ryegrass and guinea grass; measured DM, pH, organic acids, 2,3-butanediol and ethanol at 3, 7, 14, 28, 56 and 120 days of sealed storage; and corresponding values after a seven-day aerobic challenge for the 14-, 28-, 56- and 120-day silages. Table-reported row-level SEs and significance markers are preserved. A deterministic builder, source sidecar, source-register/manifest entries, FAIR catalog refresh and focused regression test are included.

This is B-tier primary literature from cultivated high-moisture forage, not roadside/VARTA grass. Triplicate silage bags and duplicate chemical analyses are documented; the sealed-storage temperature is only described as ambient. The seven-day aerobic challenge used uncompacted 150-g portions in uncovered 500-mL bottles at 25 °C. The measurements are concentrations and pH, not inventory loss, emissions, BMP, protein-quality change or elemental balance, so they do not fit storage kinetics or calibrate GreenHub degradation. The paper's Table 1 WSC for Italian ryegrass (124 g/kg DM) conflicts with its Results text (25 g/kg DM); WSC is excluded rather than resolved by assumption. No explicit open reuse license was identified. The extract remains reference-only and is not connected to defaults or calculations. Sources: [DOI](https://doi.org/10.5713/ajas.2013.13175), [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4093406/).

### Phases 3–4 — screw-press protein partition and feed-protein quality ranges (2026-11-08)

Added `Greenhub/data/Pre-treatment/Mechanical/damborg_2019_thesis_press_protein_partition_ranges_reference.csv`, preserving four ranges stated in the abstract of Damborg's 2019 Aarhus University thesis: crude-protein mass retained in pulp (528–669 g/kg input crude protein), crude-protein mass recovered in protein concentrate (170–261 g/kg input crude protein), and rumen-undegraded-protein fractions for pulp and unprocessed forage (353–421 and 214–343 g/kg protein, respectively). The thesis record has no DOI; its institutional page is used as the stable source link. Rows are in the local source register/manifest, global dataset inventory/checksum, FAIR catalog, and provenance sidecar.

This is B-tier primary thesis evidence, but abstract-level only. The feedstocks are cultivated Danish forages, not roadside/VARTA grass; species-to-range endpoints, replicate count, statistical uncertainty, exact press conditions and precipitation route are not available in the abstract. The ranges are not confidence intervals, are not paired with each other, and must not be added as one mass balance. Rumen-undegraded protein is a feed-quality result, not process recovery or product specification. All four rows remain D3/reference-only and do not activate Phase 3 or 4 parameters. Source: [Aarhus University thesis record](https://pure.au.dk/portal/en/publications/green-biorefinery-characterisation-and-utilisation-of-the-pulp-fr/).

### Phase 4 — grass-juice heat coagulation and RuBisCO precipitation comparator (2026-11-08)

Added ten abstract-level observations from Riihinen et al. (2023), abstract P2.1.088 in the [37th EFFoST conference abstract book](https://onfoods.it/sites/default/files/2024-07/Abstract%20book_37th_EFFoST_International_Conference_ISBN.pdf), ISBN 978-90-9037865-7. The extract records the tested heat setpoints (50, 55 and 60 °C), the authors' selected 50 °C coagulation condition for both red clover and timothy, the pH setpoints tested for acid precipitation (5 to 2), precipitate protein contents, the selected-protocol contents (41 and 51 g/100 g precipitate DM), and approximately 10% recovery of the protein present in grass juice into the RuBisCO precipitate. The method also states a 25 mmol sodium-sulphite addition, but gives no juice-volume or biomass denominator.

These are cultivated Finnish forage results reported in a conference abstract, not roadside/VARTA data or a complete mass balance. The best-content test results (45 and 56 g/100 g DM) are intentionally distinct from the selected-protocol contents (41 and 51 g/100 g DM); the abstract does not reconcile them, and does not explicitly restate the pH associated with the timothy best-content result. The approximate 10% denominator is juice protein, not incoming grass protein. No acid dose, residence time, uncertainty, complete stream table or scale-up relation is reported. Rows remain B/reference-only; no parameter, default, runtime calculation, route, TEA/LCA output or Pareto result is changed.

### Phases 1–3, 5 and 7 — roadside-grass pilot digestion and digestate assay methods (2026-11-08)

Added `Greenhub/data/Bigas production + upgrade/AD reactor/guanlao_2019_roadside_grass_thermophilic_ad_reference.csv`, a 118-record extract from Guanlao's 2019 Ghent University master's dissertation ([full text](https://libstore.ugent.be/fulltxt/RUG01/002/791/211/RUG01-002791211_2019_0001_AC.pdf)). Batch 1 is roadside verge grass harvested in Zele, Belgium, dried and ensiled; Batch 2 is a separate managed-grassland batch from Quévy-le-Grand. The records preserve reported feed characterization, source-calculated EPi-test methane potentials, reactor sizes/nominal conditions, observed methane productivity, the separate Batch 2 cellulase trials, and bird-seed sanitation results. The extract also records which digestate assays were performed, while leaving unavailable nutrient-result values blank.

This is a small, single-study Belgian comparator, not Dutch/VARTA feed. The EPi-test potentials are not a standardized measured BMP; the source-reported methane basis is m³/tonne DOM, with standard gas conditions unspecified. Table 6 nominal OLR/HRT differs from averaged Tables 13/15, and Table 16 summary values conflict slightly with the Digester 1 narrative/Table 13; the extract preserves the separate source contexts. An ambiguously aligned Table 9 protein value was omitted. Enzyme tests apply to the grassland batch, not roadside Batch 1. Digestate TAN, total N, phosphorus, pH and conductivity are identified as assays but no numeric nutrient/speciation table is reported, so they remain missing rather than zero. Bird-seed germination is only a sanitation proxy and not a roadside-weed or fertilizer-safety validation. Rows remain B/reference-only and do not change GreenHub defaults, digestion equations, digestate composition, or results.

### Phase 2 — grass-silage mass-loss and aerobic-stability comparator (2026-11-08)

Added `grass_silage_fresh_matter_loss_stability_hindrichsen_2025_reference.csv`, a 26-record transcription from the 2025 International Silage Conference abstract compilation by Hindrichsen, Camargo do Amaral and Witt. It records pooled minimum/maximum/average forage dry matter and crude protein, separate control/inoculant fresh-matter loss summaries during anaerobic storage and aerobic challenge, aerobic-stability ranges/averages, and one explicitly conditioned 2-day wilt / 70-day sealed storage / 30-day aerobic challenge comparison. The source compilation is [publicly accessible](https://conference.ifas.ufl.edu/silage/documents/Silage-2025-Abstract-Compilation.pdf), but no DOI or reuse license was identified; authors are affiliated with the inoculant supplier.

This adds Phase 2 comparator evidence only. The feed is cultivated grass silage from six harvest times at sites in Denmark, Lithuania and Germany, not roadside grass. The pooled sample count and underlying condition-level data are not published. Although the Table 1 caption refers to dry-matter loss, its storage/challenge rows explicitly say fresh-matter loss; the extract follows those row labels and does not convert it to dry-matter loss. Values remain B-tier and reference-only; they do not provide a GreenHub storage kinetic equation or activate a default.

### Phase 1 — official South Holland roadside mowing quantity and calendar (2026-11-08)

Added eight source-linked observations from the Province of South Holland's official management page: approximately 10,000 t/year of grass mown from provincial verges; a 647 km road-network context; an April safety round; two ecological mowing rounds with June–July and September–October windows; a qualitative “few days” field-rest interval; and pickup-wagon collection practice. The webpage is a first-party management narrative, not the underlying weighbridge, contractor, GIS or harvest dataset. The 10,000 t/year mass basis (wet/dry), exact assets included, measurement method and accessible/deliverable fraction are unspecified, so it is not entered as plant feed or annualized/scaled further. The schedule does not contain seasonal tonnage shares. These records are B-tier source-reported evidence, reference-only; the webpage does not identify an explicit open-data license, which is flagged in the sidecar. No model defaults, process calculations, UI settings, TEA/LCA results or Pareto data changed.

### Phases 1/3/7 — incremental seasonal proximate/ultimate and metal-screen evidence (2026-11-08)

Added `czubaszek_2023_fresh_grass_ultimate_and_metals_reference.csv`, a 42-record transcription from Tables 3–4 of Czubaszek et al. (2023; DOI [`10.3390/en16114488`](https://doi.org/10.3390/en16114488)). The incremental extract captures fresh-grass seasonal volatile matter, fixed carbon and elemental C/H/N, plus the paper's seasonal Cr, Mn, Fe, Ni, Cu, Zn, Cd, Hg and Pb screen. Table 3 sulfur and ash are deliberately not duplicated because those same values are already in the feedstock package. Published means, SDs and significance letters are retained. The three `n.d.` entries remain censored blank values, not zero.

This adds feed-quality detail (Phase 1), elemental characterization relevant to process/LCA accounting (Phase 3), and a contaminant-screen comparator for recovered nutrient/fertilizer considerations (Phase 7). It is not Dutch VARTA feed: samples were urban roadside/median grass from Białystok, Poland, collected in 2019. The study's “fresh” samples were air-dried at room temperature for 24 hours and chopped before analysis. Analytical triplicates are not interpreted as independent field replication; elemental nitrogen is not converted to protein; metals are not used to claim regulatory compliance. The data are B-tier measured-literature, CC BY 4.0, reference-only; no runtime input/default, model calculation, UI behavior, TEA/LCA factor or Pareto result changed. Existing Table 1/2/5/BMP data were checked first to avoid re-transcription.

### Phase 6 — farm-scale water-scrubber electricity test points (2026-11-08)

Added `wantz_2023_hpsw_experiment_energy_points_reference.csv`, a 12-record extract of the two electricity-meter test points described by Wantz et al. (2023; DOI `10.1016/j.apenergy.2023.121781`). The records preserve raw-biogas and scrubbing-water flow, absorber and vacuum-regeneration pressure, approximate electrical power, and source-normalized specific electricity for Experiments 31 and 35. The source states that electricity was metered over two hours; the reported electrical demands are approximately 25 and 16.6 kW and the specific consumption is approximately 0.8 kWh/Nm³ raw biogas at both points. The specific consumption is not recomputed from rounded values.

This is a French farm-scale water-scrubber comparator, not GreenHub grass-derived gas. Point-level uncertainty and replication are not reported; tested auxiliary loads/configuration differ from the contemplated model, and the author-uploaded manuscript has no identified reuse license. The source PDF is not redistributed. Records remain B/reference-only; no upgrader parameter/default, runtime calculation, or UI result was changed. The local source register and manifest were updated, the FAIR catalog was rebuilt, and a checksum/rights/applicability sidecar plus focused regression test were added.

The FAIR catalog now indexes 699 assets and 897 normalized inputs (649 source-linked, 529 DOI-linked, 54 without a source-register join). Global governance still reports 458 datasets/checksums, 713 source issues, 62 blocked and 396 reference-only; zero datasets or equations are active/default-eligible. These are repository-wide catalog/audit counts, not Phase 1–7 completeness measures.

### Phase 4 — alfalfa enzyme extraction, acid recovery and protein-accounting evidence (2026-11-08)

Added the 43-row reference extract `alfalfa_enzyme_assisted_protein_isolation_2018_reference.csv` from Kim's 2018 USAFRI research report ([public report PDF](https://alfalfa.org/pdf/USAFRI/Final%20Reports/2018/18Kim.pdf)). It preserves 42 numeric records plus one qualitative comparison: feed proximate composition; enzyme-preparation protein concentrations; source-stated enzyme-dose/blend results; the 2-L extraction and acid-precipitation solids/protein table; product crude-protein and amino-acid content; peptide-hydrolysis outcomes; and the report's air-dried versus fresh-category alfalfa comparison (41.0% versus 46.8% control extraction, and a reported 1.6-fold difference at 10 mg enzyme protein/g). It explicitly separates 62.8% feed-protein solubilization from the 7% final precipitated-protein yield, and retains the source's 110% protein closure with the authors' explanation of double counting between the centrifuged solids and retained liquid. The 91 g liquid-solids figure is marked as source-derived by difference, not as a directly measured output.

This is alfalfa, not roadside grass; the "fresh" category was frozen, lyophilized and ground, so the comparison is not wet-grass storage behavior or a time series. Laboratory mixing/centrifugation conditions do not support GreenHub scale-up. Approximate or convention-ambiguous text results remain qualified, graph-only points were not digitized, the report has no DOI, and no explicit reuse license was identified. It improves Phase 2/4 comparative evidence for drying-state sensitivity and extraction-to-product capture, and records a useful balance warning, but does not calibrate GreenHub chemistry or clear the remaining phase-specific data gaps. The dataset remains reference-only; no runtime, default, route, or result changes were made.

### Phase 4 — condition-level enzyme-assisted protein recovery from grass/clover pulp (2026-11-08)

Replaced the two abstract-only placeholder records for Dotsenko & Lange (2017; DOI [`10.1007/s12649-016-9718-7`](https://doi.org/10.1007/s12649-016-9718-7)) with 134 condition-level reference observations transcribed from the open-access article's Tables 1–5 and supporting results text. The extract includes pulp total-solids and crude-protein properties, four assay-method comparisons, aqueous-extraction and Savinase time courses, dose response, and sequential carbohydrase/protease results. It retains 132 numeric records and two qualitative non-detect records with blank values; the non-detects are not encoded as zero. Table locations, DOI, CC BY 4.0, experimental conditions, and uncertainty are recorded in the dataset and sidecar.

Uncertainty and basis limits are preserved: replicate count is explicit only where the methods state triplicate experiments; the Table 1 count and the statistic behind pulp-composition ± values are unspecified; protein-yield values have no reported SD; and the Table 4 enzyme-mass basis and Table 5 cellulase/hemicellulase component allocation are not further resolved. These are cultivated ryegrass/white-clover laboratory screw-press pulps, not Dutch roadside grass or GreenHub pulp. The dataset remains blocked from runtime/default activation; it supplies no GreenHub scale-up, activity-normalized enzyme demand, utility/reagent balance, downstream product-quality or separation performance. The open article is [available from Springer](https://link.springer.com/article/10.1007/s12649-016-9718-7). No process chemistry, defaults, route configuration, TEA/LCA assumptions, or Pareto outputs were changed.

### FAIR index refresh after the Phase 4 enzyme-reference additions (2026-11-08)

Rebuilt the FAIR input catalog after staging the Dotsenko & Lange table extract and the Kim alfalfa recovery report. The catalog now lists 697 assets and 897 normalized input records; 647 assets join to source-register records, 527 have DOI identifiers, and 54 still lack a source-register join. These are discoverability/provenance counts, not counts of validated GreenHub-calculation inputs. Both additions remain reference-only and do not change activation or defaults.

### Phases 1/5/7 — Swiss roadside-grass availability, BMP, and contamination evidence (2026-11-08)

Added `roadside_grass_bmp_seasonal_contamination_christodoulou_2022_reference.csv` from the Swiss Federal Office of Energy’s MéthaRoad final report (project `SI/502089-01`; no DOI identified). The 91-row extract contains the report’s 20 route-by-campaign BMP observations on both fresh-matter and organic-matter bases; broad reported seasonal total-solids and C:N ranges; censored PAH and metal results; macro-/microplastic table entries; and the report’s selected process-summary and Swiss national resource-estimate records. Every value points to a report page/table; censored and dashed entries are not zeros.

The source is particularly useful as a cross-check for seasonal roadside-grass BMP and contamination screening, but its five samples are selected Vaud, Switzerland road/verge types rather than Dutch VARTA grass. The samples were triplicate lab BMPs at 37 °C, not continuous GreenHub residual digestion. The national `2–3 t fresh matter / total road-km / year` ratio is a C-class compiled author estimate, not measured or accessible feedstock. Conflicting first-campaign C:N text and the report’s below-LOQ zinc statement versus its higher site-specific zinc results are both retained rather than reconciled. No runtime inputs, defaults, equations, TEA/LCA factors, or Pareto results changed. Reuse licensing was not identified and remains flagged for rights review.

### Phases 1/3/7 — timothy feed composition and pre-ensiling press-liquid evidence (2026-11-07)

Added `timothy_feed_and_press_liquid_ayanfe_2025_tables1_5_reference.csv` from Tables 1 and 5 of Ayanfe et al. (2025; DOI [10.1111/gfs.12722](https://doi.org/10.1111/gfs.12722), CC BY 4.0). Its 150 long-form records preserve nine feed properties across five primary-growth/first-regrowth timothy states and 21 liquid-yield, composition, component-capture, macro-mineral, and trace-mineral measures across five pre-ensiling pressing conditions. The same first-regrowth intact feed remains separate for pilot single-screw and double-screw pressing. Units and bases are copied as printed; no conversion, balance closure, missing replicate count, or uncertainty was inferred.

This improves Phase 1 forage-quality context, Phase 3 fresh/pulp/wilted fractionation evidence, and Phase 7 press-liquid nutrient composition. It is cultivated Finnish timothy—not roadside or GreenHub feed—and Table 5 is pre-ensiling rather than storage-degraded material. The source reports 0.4 L water/kg fresh grass for the high-DM primary-growth pressing condition, but its inclusion in the table's fresh-sample liquid-yield denominator is unresolved. All values remain B-tier `reference_only`; no runtime parameter, default, route, UI input, or Pareto output changed. A deterministic local builder, source sidecar, source-register/manifest entries, and focused tests preserve the extraction and prevent accidental activation.

### Phases 2/3 — timothy silage endpoints, effluent and post-ensiling press liquid (2026-11-07)

Added `timothy_silage_fermentation_effluent_and_press_liquid_ayanfe_2025_tables2_4_6_reference.csv` from Tables 2, 3, 4 and 6 of the same Ayanfe et al. (2025; DOI [10.1111/gfs.12722](https://doi.org/10.1111/gfs.12722)) study. It contains 519 long-form records: 4-replicate primary-growth silage means, 3-replicate first-regrowth silage means, pooled spontaneous effluent results, and liquid yield/composition after ensiled first-regrowth biomass was frozen, thawed and double-screw pressed. Reported SEM, factor p-values, Tukey groups, treatment additives and material states are retained. Table 4's treatment samples were pooled; no SEM or inferential statistics are claimed for those values.

This adds measured literature endpoints relevant to Phase 2 storage quality and losses and Phase 3 liquid fractionation after storage. It does not supply a continuous storage time series, component mass recovery, gas emissions, roadside-grass kinetics, or GreenHub-specific process performance. Values are B-tier, reference-only comparators; no kinetic fit, mass-balance closure, runtime/default activation, route change or Pareto update is made. Source licensing, table locations, experimental context, pooling, and the possible observation-limit censoring of aerobic-stability endpoints are recorded in the sidecar.

### FAIR index refresh after the additional Timothy-grass tables (2026-11-07)

Rebuilt the generated FAIR CSV/JSON indexes and synchronized the two read-only workbook snapshot sheets. The catalog now contains 667 assets and 897 normalized records; 618 assets join to a source register and 506 have DOI identifiers, while 53 still lack a source-register join. The new 519-row dataset is discoverable as a reference-only storage asset. The workbook retains all 16 sheets, its other sheet values/formulas are unchanged, and the workbook-wide formula-error scan returned no matches. These are catalog/provenance counts, not a measure of process-data completion or calculation readiness.

### Phase 1 — South Holland parcel area, reported quantity, and yield-potential comparison (2026-11-07)

Added `zuid_holland_bermmaaisel_parcel_areas_and_quantity_comparison_2021_reference.csv` from the main report and Appendix 1 (LCA) of Verrips, van Rengs and Franken (2021), commissioned by Provincie Zuid-Holland. The extract separates four parcel areas; East's reported 1,500 t/year and West's approximate 2,500 t/year; South's explicitly estimated 3,500 t/year, for which the report says primary data were unavailable; the approximate 11,000 t/year four-parcel aggregate; and the report's four theoretical fresh-biomass potentials based on 4 t DM/ha represented as 16 t fresh/ha. It does not infer a North parcel collection amount from the aggregate remainder.

The contractor/provincial tonnages have no stated wet/dry basis, metering year or underlying weigh tickets, and the report warns that ditch debris may be included in South/West. The area-based values are literature-derived potential calculations, not observed supply, and cannot calibrate GreenHub availability. All values remain B/C `reference_only`; no defaults, runtime calculations or scenario inputs changed. The report specifically recommends centralized weighbridge receipts and machine-hour records, matching the key unresolved Phase 1 acquisition need.

### Phase 1 — East Flanders collection-point quantity distribution (2026-11-07)

Added `east_flanders_roadside_grass_collection_points_de_wieuw_2023_reference.csv` with the 41 values from Table 2 of De Wieuw et al. (2023; DOI [10.3390/su151814006](https://doi.org/10.3390/su151814006); CC BY 4.0). The values add point-level heterogeneity to Phase 1 supply/logistics evidence and connect to a source already used for a separate logistics-cost proxy. The article describes the collection-point allocation as hypothetical and based on earlier project estimates, not weighed supply; point IDs are not coordinates and the quantities combine municipal and regional clippings. The 41 values sum to Table 2's stated 9,931 t wet matter, while the paper's Scenario 1 narrative reports 9,841 t; both totals are stored separately and tested rather than reconciled. All records remain B-class `reference_only`; no local supply default, route, TEA quantity, or runtime behavior changed.

### Phases 5–7 — measured component methane emissions across digestion, upgrading and digestate handling (2026-11-07)

Added 11 Table 2 `Presented study` summaries from Wechselberger et al. (2023; DOI [10.1016/j.wasman.2022.12.012](https://doi.org/10.1016/j.wasman.2022.12.012)); its harmonized underlying dataset is at [Zenodo DOI 10.5281/zenodo.7474206](https://doi.org/10.5281/zenodo.7474206). The extract preserves sample counts, medians, ranges and denominators separately: water-scrubber methane slip is 2.94% of utilized methane (n=2; 1.98–3.89%), whereas non-gastight digestate-storage emissions are 2.83% of methane produced (n=8; 0.06–5.62%). It also covers digester leaks, CHP slip and other upgrading equipment emissions. The paper's PSA observations were measured upstream of exhaust treatment while that treatment was out of order; this caveat is attached to that row. Membrane upgrading is deliberately absent because the study says it was not covered.

These are measured European biogas-plant component comparators, largely from energy-crop, manure, biowaste and wastewater-sludge plants—not GreenHub grass-residual measurements. Table 2 sample counts are not treated as representative population distributions; mean values missing from the study's column remain blank. The full 294-point repository data were not imported; only the cited article-table aggregate extract is staged. All rows remain B-tier `reference_only`, with no LCA default, runtime methane-loss factor or process setting changed.

### Phase 6 — paired commercial-upgrader gas composition and methane loss (2026-11-07)

Added `Greenhub/data/lca/source_data/commercial_biogas_upgrader_gas_quality_kvist_aryal_2019_reference.csv`: nine plant-indexed rows for three amine, four water-scrubber and two membrane units, with feed-gas, biomethane and off-gas composition and methane-loss percentages, plus a separate abstract-level RTO follow-up result. The plant table is reproduced in IEA Bioenergy Task 37's 2025 report, which attributes it to Kvist and Aryal (2019); the original article abstract independently reports an overall 0.81% methane loss relative to methane supplied and an RTO reduction of 99.5% of methane in the selected waste gas.

The IEA table does not identify the plant sites or scales and does not state whether gas-composition percentages are on a molar or volume basis. Missing cells remain blank; explicit zeros and printed values are retained, with no normalization. The observations are Danish commercial-biogas comparators, not GreenHub grass-gas factors. They remain B-tier `reference_only`; no upgrader setting, default, LCA factor or scenario output changed. The original paper and IEA report reuse licenses were not identified in the accessed records and are flagged for rights review.

### Phases 3/5/7 — continuous grass/manure digestion, energy, and digestate comparator (2026-11-07)

Added 16 abstract-level observations from Moset Hernandez, Fontaine and Møller (2017; DOI [10.1016/j.energy.2017.08.068](https://doi.org/10.1016/j.energy.2017.08.068)). The source reports thermophilic continuous co-digestion at 25-day HRT in 15 L and 30 m³ reactors, 5% grass in the fresh feed mixture, and excoriated-grass methane-yield increases relative to manure-only operation of 20% and 35% at the two scales. It also reports a roughly 20% volumetric methane-production increase, a 6% reduction in methane concentration in biogas, unchanged N:P:K ratio, higher digestate organic matter and residual methane, lower digestate protein, and mixing energy approximately doubled. The authors state that mixing energy represented 14% of the extra energy produced by excoriated grass.

These remain source-reported relative or qualitative observations. The abstract does not provide absolute methane yield or flow, exact reactor temperature, digestate nutrient concentrations, or absolute energy demand. It does not clarify whether the 6% gas-methane decrease is relative percent or percentage points, and the 14% energy comparison has no complete boundary or scale mapping. The study co-digests natural grass with cattle manure, so it does not calibrate the GreenHub grass-juice, press-cake, or post-protein residual route. All rows remain B-tier `reference_only`; no runtime parameters, defaults, or scenario outputs changed.

### Phase 4 — cultivated perennial-ryegrass protein product quality (2026-11-07)

Added 15 source-linked observations from Ravindran et al. (2021; DOI
[`10.3390/cleantechnol3030039`](https://doi.org/10.3390/cleantechnol3030039),
CC BY 4.0) to the drying/product-quality reference package. The data include
Table 6 crude-protein, crude-fibre and selected amino-acid values explicitly
reported per 100 g feed; proximate-analysis results with their basis limitation;
the approximate 90% DM belt-dried endpoint; gross energy; and the approximate
pressing protein split. The prose partition ranges are not treated as an exact
component balance. This is cultivated Irish ryegrass and a proprietary process,
not a GreenHub roadside-grass specification. All rows remain `reference_only`;
no defaults, runtime equations, price assumptions or process balances changed.

### Phases 1/4 — forage maturity and lactic-acid protein recovery (2026-11-07)

Added five abstract-level observations from Santamaria-Fernandez et al. (2019;
DOI [`10.1016/j.jclepro.2019.01.292`](https://doi.org/10.1016/j.jclepro.2019.01.292)).
The publisher abstract reports 24–42% of plant protein recovered in LPC, up to
86% recovery of protein entering in green juice, and red-clover ranges of 65–98
kg crude protein and 186–235 kg dry LPC per tonne of feed dry matter. It also
states that protein extractability and LPC production decline with plant
maturity. Only aggregate abstract facts were transcribed; no stage-specific
curve was inferred. The crops are chicory, red clover and timothy, not roadside
grass. All records are reference-only, with no runtime mapping. Aalborg's
accepted-manuscript record specifies CC BY-NC-ND 4.0; redistribution rights
remain flagged for review.

### Phase 7 — second-year grass and soil response to recovered struvite (2026-11-07)

Added `demarke_struvite_second_year_grass_soil_szymanska_2020_reference.csv` (185 records) from Szymańska et al. (2020; DOI [10.3390/en13205342](https://doi.org/10.3390/en13205342), CC BY 4.0). It records applied nutrient doses; Table 2 grass N/P/Mg concentrations by soil, treatment and each of four 2018 harvests; Table 3 source-calculated relative fertilizer efficiency; Table 4 post-harvest soil chemistry; and only second-year yield/uptake values stated explicitly in the text. Treatment-level means reported only as pooled values remain pooled. Figure-only uncertainty was not digitized, and blank SD values do not mean zero.

This is a distinct second-year follow-up to the existing 2019 first-year De Marke dataset, not a duplicate. Recovered struvite was made from cattle-slurry digestate at a Dutch farm biorefinery, but fertilizer response was studied in a Polish greenhouse pot trial (n=3) using silty loam and loamy sand; no fertilizer was applied in 2018. It is Phase 7 residual-fertilizer-use evidence, not roadside-grass product validation, a field substitution factor, GreenHub fertilizer credit or runtime parameter. All rows remain B-tier, `reference_only`. Focused tests check table counts, anchor values, units, source/manifest linkage and non-activation.

During the catalog refresh, malformed CSV rows were found in the storage, mechanical-pre-treatment and digestate source/manifest registers. They were corrected to match their declared columns, the Chiumenti manifest counts were restored from its 47-row extract, and one exact duplicate Trotta source-register record was removed. The dataset audit and governance refresh now complete; the FAIR catalog indexes 649 assets and 897 normalized master-input records, with 601 source-linked assets, 490 DOI-linked assets and 51 assets still lacking a local source-register join. The global audit still reports 711 issues across 443 CSV datasets; this does not mean the datasets are complete or runtime eligible.

### Phase 2 — farm-scale high-DM perennial-grass storage endpoints (2026-11-07)

Added `Greenhub/data/storage/williams_shinners_perennial_grass_anaerobic_storage_2014_reference.csv`, transcribing six unpooled treatment rows from Williams and Shinners (2014; DOI [10.1016/j.biombioe.2014.03.037](https://doi.org/10.1016/j.biombioe.2014.03.037)). Tables 1, 3 and 5 report anaerobic storage dry-matter losses after 222 days for switchgrass and 230 days for reed canarygrass, additional loss after 2/7 days of aerobic feed-out, cellulose and hemicellulose composition/recovery, and heating-degree-day indicators. Significance-group suffixes are preserved; Table 5 DM values remain separate from Table 1 removal values where they differ.

This is B-class measured literature evidence from mature, field-wilted, chopped high-DM cellulosic grasses in farm-scale silo bags—not Dutch roadside grass. The aerobic test is sequential feed-out after anaerobic storage, not a separate aerobic-storage scenario. The trial uses one silo bag per species and does not provide a storage time series or independently replicated silo-level effect; no kinetic fit, transfer factor, default, or runtime parameter is derived. The article does not identify an open reuse license. Focused tests check table values, source/manifest linkage, units and reference-only status.

### Phase 1 — Utrecht-region collected and uncollected roadside-grass estimates (2026-11-07)

Added four source-linked records from the ARBOR case-study report *Synergy Parks: collaborative strategies to valorise side streams between companies* (published 05 June 2015): approximately 60,000 t/year reported mown, collected and processed; approximately 70,000 t/year reported left uncollected after mowing; the report's stated 130,000 t/year total potential; and a typical two-cut schedule in May–June and September–October. The region is Province of Utrecht plus Het Gooi. The report gives no underlying reference year, mass basis, weighbridge method, site-level records, or accessible fraction. The 130,000 t total is the report's sum of the first two categories, not a third supply stream. All four records remain B-class staged context, not GreenHub supply defaults or scenario inputs. [ARBOR case-study report](https://www.list.lu/fileadmin/files/projects/ARBOR/ARBOR_Synergypark_Case_Study_Report.pdf).

Expanded the existing Brown et al. (2020) measured-harvest reference with the 2018 vehicle's reported 60 km/h road-travel speed, 5 km/h dry-field harvesting speed, 3 km/h speed in very wet conditions, and 15 t cut-grass capacity. These operational observations are kept separate from the campaign yield and do not define a moisture-response curve, dry-mass capacity, or GreenHub logistics default. They are located in Results §3.4 of the [open article manuscript](https://eprints.whiterose.ac.uk/160532/1/39%20Brown%20et%20al.%2C%202020.pdf).

Added a paired HDSR planning scenario from its 2021 annual report: 30,000 t/year of mixed verge- and ditch-mowing material and approximately 3.4 million m³/year potential biogas at RWZI Nieuwegein. This is not a plant operating result. The report says the procurement process delayed the initiative and the 2022 restart was planned; it gives no wet/dry basis, grass-versus-ditch split, gas reference conditions, methane fraction, or meter data. The two figures are stored as a linked scenario rather than a calculated yield and remain B-class reference-only. [HDSR Bestuursverslag 2021](https://www.hdsr.nl/publish/pages/115513/bestuursverslag_2021.pdf).

Added `Greenhub/data/Pre-treatment/Feedstock/gr4ss_leeuwarden_project_design_reference.csv` as an external project-design comparator. The official Fryslân permit description lists 36,000 t of verge/nature mowing material and 24,000 t of plant residues without a period or wet/dry basis; the operator separately announces up to 60,000 t/year plant-based feed capacity. The project homepage lists biomethane, liquid bio-CO₂, fertilizer, and substrate targets but does not state a reporting period or product specifications. These are permit/design and project-target records, not measurements. Their differing source bases are preserved, no yields are calculated, and nothing is activated in GreenHub. [Official Fryslân permit notice](https://zoek.officielebekendmakingen.nl/prb-2025-12664.html), [GR4SS project information](https://gr4ss.nl/).

### Phases 1/3/4 — harvest-time and press-liquid treatment matrix (2026-11-07)

Added `Greenhub/data/Pre-treatment/Feedstock/timothy_harvest_and_press_liquid_stefanski_2024_reference.csv`, transcribing all 15 treatment means from Table 1 of Stefański et al. (2024), *Grass for biorefinery: Effects of N fertilization and harvest time on liquid yield and composition*, Grassland Science in Europe 29, pp. 131–133. It preserves first-/second-cut dates, nitrogen treatment, grass DM, press-liquid yield per fresh grass, liquid DM and ash, liquid and N yields per hectare, Tukey groups and cut-level SEM. The PDF reports three plot replicates per treatment and a laboratory twin-screw press.

This extends seasonal harvest and fractionation comparison evidence; it does not supply GreenHub roadside availability or calibrate the GreenHub press. The source is cultivated Finnish timothy, experimental fertilizer levels, one growing year, and small laboratory equipment. Table means are not annualized or mapped into model defaults. The conference proceedings provide no DOI or explicit reuse license; this limitation is recorded in the sidecar and source register.

### Phase 4 — formic-acid response table preserved with a basis quarantine (2026-11-07)

Added `grass_liquid_formic_acid_table1_response_stefanski_2024_reference.csv` as a verbatim transcription of the four Table 1 response rows (dry matter, ash, crude protein, true protein) across all five treatments, including SEM and linear/quadratic p-values. Review of the accessible full text confirms that the printed header says `g kg fresh liquid^-1`; however, literal use of that denominator conflicts with the reported sediment mass and component hierarchy. The separate dose/pH dataset also records a tenfold inconsistency between the treatment labels and bottle-scale additions.

The numbers are retained as source-reported B evidence, but the denominator is explicitly unresolved. No dimensionless recovery, stream mass, dose-response equation, reagent demand, or model input is inferred. The companion dataset and sidecar mark the values reference-only and quarantined pending clarification from the authors or a corrected source; the proceedings' reuse rights are also unresolved.

### Phase 1/2/3/5 — year-resolved Kassel roadside-grass reference data (2026-11-07)

Added `Greenhub/data/Pre-treatment/Feedstock/urban_roadside_grass_yield_ifbb_piepenschneider_2016_proceedings_reference.csv`, transcribing 19 observations from Piepenschneider, Hensgen and Wachendorf (2016), *Biomass yield and energy content of grass from urban roadside verges*, Grassland Science in Europe 21, pp. 855–857. The dataset adds 2013 and 2014 dry-matter yields with SD for two-cut, four-cut and mulching regimes, plus the source-reported two-year means; it also records the reported minimum six-week ensiling, 15-minute warm-water mashing and screw-press method, source-specific methane yields, press-cake LHV and gross-energy estimates.

This is measured literature evidence from ten Kassel urban verge sites, not Dutch GreenHub supply or a runtime parameter. The paper does not report full cut-level/site-level observations, per-treatment sample counts, water addition rate/temperature, press settings, specific electricity or continuous digester performance. Its 269 L_N/kg VS press-fluid value remains distinct from the later related journal article's 292 L_N/kg VS maximum pending treatment/test comparison. Reported gross energy is not net energy, TEA or LCA. A focused test checks the transcription, uncertainty fields, provenance and non-activation.

### Phase 7 — De Marke struvite crop-use evidence (2026-11-07)

Added `Greenhub/data/Resource recovery/Phosphorus_Recovery/demarke_struvite_crop_fertilizer_efficiency_szymanska_2019_reference.csv` with 42 records from Szymańska et al. (2019), DOI [10.3390/en12020296](https://doi.org/10.3390/en12020296), licensed CC BY. It includes Table 1 relative N/P fertilizer efficiency for two crops and two soil types; per-pot nutrient doses; and selected apparent nutrient-recovery values stated explicitly in the Results text. The recovery values are not digitized from the figure. Where the paper combines STR and STR+N, the record preserves that grouping.

This is evidence about using a recovered product, not about recovering nutrients from GreenHub digestate: the struvite was made from cattle-slurry digestate at the Dutch De Marke farm biorefinery and then tested in Polish greenhouse pots. Relative fertilizer efficiency is not process recovery or a guaranteed fertilizer-substitution credit. All rows remain B-class reference-only; no model, TEA credit, or default consumes them. The existing adjacent dataset for the same authors' cattle-slurry digestate chemistry remains a separate source/phase-7 dataset.

### Phase 2 — grass/lucerne ensiling setup and endpoint chemistry (2026-11-07)

Added `Greenhub/data/storage/grass_lucerne_ensiling_schmithausen_2022_reference.csv`, transcribing 86 observations from Tables 3.1–3.2 of Schmithausen et al. (2022), DOI [10.1016/j.jenvman.2021.114142](https://doi.org/10.1016/j.jenvman.2021.114142). The rows preserve the four forage/wilting treatments, 120-L barrel replication, reported fresh loading, DM and density, wilting temperature conditions, fresh forage chemistry, and day-149 pH/DM/ash/crude protein/fermentation-acid/NH3-N values with reported SDs and significance groups. The accompanying metadata sidecar records units, sample basis, source pages, geography, methods, retrieval date, uncertainty, and a reuse-rights caveat.

This is measured literature evidence (B), not Dutch roadside-grass data and not a runtime/default parameter. The study deliberately used low-DM conditions to provoke poor silage quality. Fresh samples are not treatment-paired time-zero samples, and the endpoint tables do not report storage mass recovery, leachate, or component-specific losses. Headspace gas concentrations must not be converted into emissions: the authors state that emissions could not be quantified. Targeted tests check transcription anchors, table coverage, traceability, uncertainty blanks, and non-activation.

### Phase 2/5 — grass-clippings silage-storage BMP endpoints screened (2026-11-07)

Added `Greenhub/data/storage/grass_clippings_silage_storage_bmp_yeo_2023_abstract_reference.csv` with eleven traceable records from the accessible English abstract of Yeo et al. (2023), *Journal of Korea Organic Resource Recycling Association* 31(4), 13–28. The abstract reports single-point BMP comparisons for *Poa pratensis*, *Zoysia japonica*, and *Agrostis stolonifera*, plus day-0 and day-180 BMP, NDF, ADF, and crude-protein endpoints for ensiled *P. pratensis*. Intermediate days are named as tested, but their values are not present in the abstract and remain explicitly not reported. No DOI was identified in the KCI record. Units are copied as printed; the accessible abstract does not state the basis of the percentages or BMP reference conditions.

The article record did not expose the full text or raw data in this collection pass. This is B-class abstract-only literature evidence, not GreenHub roadside-grass measurement. It remains reference-only: no storage kinetic fit, aerobic comparison, parameter activation, default, or process/Pareto change. The dataset and metadata sidecar state the rights and basis limitations; a targeted regression test verifies missing intermediate values are not converted to zero or interpolated. Next evidence request: obtain the full text or author data to recover methods, replicate counts/uncertainty, storage conditions, and measured 30/60/90/120-day values.

### Data-acquisition priorities and minimum project measurement package (2026-11-07)

The repository now contains substantial literature and project-reported reference evidence across Phases 1–7. A source-search pass found additional public analogues, but did not find openly downloadable, batch-linked GreenHub measurements that close the remaining route-specific gaps. Literature comparisons must remain distinguishable from GreenHub measurements; they do not justify activating a project default when feedstock, equipment, basis, or process boundary differs.

### Phase 3–5/LCA — screened measured-platform supplementary data lead (2026-11-07)

Screened Gaffey et al. (2024; DOI `10.1016/j.scitotenv.2024.175035`). Added `Greenhub/data/lca/source_data/gaffey_2024_grass_biorefinery_lci_table3_reference.csv`, a direct transcription of all 42 Table 3 LCI flows for four ryegrass/grass-clover × one-/multi-stage scenarios per 1 t DM LPC-CP. The manuscript states that demonstration-platform mass/energy flows and product yields were collected through an integrated PLC, while cultivation burdens, AD/CHP, digestate, substitution and emissions were modelled. Negative CHP and fertilizer entries are explicitly tagged as LCI credits, not physical negative flows. The heat-input row is preserved in the paper's `kW` unit despite the mass-based reference flow, and is not converted or activated. The institutional record identifies a 385 kB supplementary Excel workbook, but its download endpoint returned HTTP 403; this table extract does not substitute for the missing batch-level/supplementary data. It remains a cultivated-feed comparator, not GreenHub roadside-grass evidence or an active parameter set.

### FAIR catalog refresh after Phase 1–7 collection (2026-11-07)

Rebuilt the generated FAIR catalog and its two workbook snapshot tabs after registering the current phase extracts. The index contains 603 assets and 892 normalized master-input records; 555 assets have source links, 454 have DOI links, and 51 still lack a source-register join. All new literature extracts remain reference-only or explicitly quarantined; no model defaults, parameter values, scenario outputs, or route calculations changed. The snapshot refresh now trims surplus rows left by removed assets so the workbook's row count stays synchronized with the CSV/JSON catalog.

To collect the highest-value project data, retain the following linked records for each site, harvest, processing batch, and downstream stream. Use stable IDs to connect samples and outputs; do not pool batches before recording their individual observations.

| Phase | Minimum linked measurements to collect | Units/basis and essential context | Model gap addressed |
| --- | --- | --- | --- |
| 1 — availability | Source/site and route ID; harvested, rejected, and delivered mass; cut date; accessible/contracted area; actual mowing and collection events | t fresh per load/cut, paired kg DM or % DM, ha or km, coordinates or route ID; distinguish standing, cut, collected, accepted, and delivered material | Seasonal supply, harvestability, collection fraction, and feedstock representativeness |
| 2 — storage/logistics | Inbound and withdrawal timestamps; storage mode and aerobic/anaerobic condition; storage temperature, moisture, oxygen exposure where available; input/output mass and leachate; paired feed quality at start/end | days, °C, kg fresh and kg DM, kg leachate, % TS/DM/VS, pH, soluble/insoluble protein, carbohydrate/COD, BMP; identify analytical method and sample linkage | GreenHub storage losses, degradation, quality change, and storage emissions |
| 3 — preparation/fractionation | Same-batch feed, press juice, and press-cake weighing and analyses; dilution/wash water; cutter/macerator/press settings, throughput and electricity | kg/h and kg/batch, kg water/kg feed, kWh/batch or kWh/t, particle-size distribution (mm), % TS/VS, COD, protein and nutrient basis | Press yield curves, water demand, energy and component partition |
| 4 — protein recovery | Green-juice, precipitate, supernatant, wash and final-product masses; titration curve and actual acid/base mass; target and final pH; soluble/insoluble and true-protein/total-N assays | kg stream/batch, mol or kg reagent/kg juice, pH, kg protein on wet and dry bases, product % DM/moisture, temperature/time, centrifuge conditions and replicates | Reagent demand, recovery, purity, product quality, washing losses, and component closure |
| 5 — anaerobic digestion | Actual cake and protein-section residual feed characterization; batch BMP and/or continuous-run time series; gas volume/composition; digestate mass and analysis | kg feed and kg VS, Nm³ gas with stated reference conditions, % CH4/CO2 and H2S, °C, pH, OLR (kg VS m⁻³ d⁻¹), HRT (d), gas-rate time series, digestate kg and nutrients; include inoculum/control and replicates | Residual-specific methane yield, kinetics, inhibition, digester sizing, and digestate flow |
| 6 — gas upgrading | Paired raw-gas and product/tail-gas flow and composition; technology and operating conditions; electricity, heat, water and media/reagent use | Nm³/h on stated reference conditions, component mol/vol %, CH4 recovery and slip %, kWh/Nm³ raw gas, kWhth/Nm³, L/Nm³, pressure (bar), uptime and specification tests | Route-specific upgrader performance, utility demand, methane loss, and product eligibility |
| 7 — nutrient recovery/use | Flow-weighted digestate and liquid/solid fraction quantities and analyses; recovered-product mass, composition and contaminant testing; reagents and water; intended application route | kg stream/batch, total and soluble N/TAN, total and orthophosphate P, K (state oxide/elemental basis), alkalinity, metals/pathogens with methods and detection limits; kg product, % moisture/purity, kg reagent/kg feed | Nutrient partition/recovery, fertilizer quality/compliance, substitution, and nutrient balance |

For every observation, record a unique observation/sample ID, parent batch ID, collection/analysis date, site, material and stream, value, unit, wet/dry basis, analytical or operating method, replicate count, uncertainty or detection limit, source/evidence class, operator/laboratory, and any correction or conversion. Blank means unmeasured/not reported; never encode it as zero. Keep raw lab sheets, weighbridge exports, equipment logs, and processed extracts linked and checksummed. Record deviations and failed/missed samples rather than silently dropping them.

This is a collection specification, not evidence that these measurements have already been collected. It introduces no runtime values, parameter defaults, route changes, or scenario changes. Existing literature records remain reference-only unless their dataset-specific evidence and calculation-connection gates are separately satisfied.

### Phase 7 — agricultural-digestate membrane recovery benchmark (2026-11-07)

Added three CC BY 4.0, B-class reference tables from Rizzioli et al. (2025; DOI `10.1016/j.jclepro.2025.144958`): (1) ten raw-feed digestate characterization values with source-reported SD, (2) 29 stream-composition rows across three preliminary solid-liquid separation / centrifugation / MF-UF-RO or NF-RO configurations, and (3) 15 mass-based nutrient and water recovery means and standard deviations. The study used agricultural digestate from a mesophilic cow-manure and lignocellulosic energy-crop digester in Italy. It reports the Line 2 UF+RO water recovery as 32.75 ± 1.86% of digestate feed mass and ammonium-N recovery in the RO retentate as 46.50 ± 1.14% of initial ammonium-N; these are source-study results, not GreenHub performance assumptions.

All source-reported stream concentrations, units, table numbers, and undetermined EC fields are preserved. K2O is explicitly not elemental K; Table 2 recovery values are distinguished from stream concentrations. The article's ~20 t/day scale-up is a design basis, not an operating demonstration. This adds a comparative Phase 7 membrane/water-recovery evidence point but does not close the GreenHub grass-digestate composition, quality, contaminant, membrane energy/cleaning, or product eligibility gaps. Both files are registered and tested; no runtime parameter, default, route, TEA/LCA value, or Pareto scenario was activated or changed.

### Phase 2 — measured 85-day ryegrass storage recovery and quality outcomes (2026-11-07)

Added `Greenhub/data/storage/annual_ryegrass_bale_silage_85d_crook_2020_reference.csv`, transcribing 26 post-storage means and standard errors from Tables 2 and 4 of Crook et al. (2020; DOI `10.1002/cft2.20015`). The table includes DM recovery, DM concentration, pH, ammonia-N fraction and selected composition by moisture group or wrapping delay. The source reports pooled means, not factorial cell-level pairings; that distinction is preserved in each row. The article's abstract says the cured “DRY” forage had 30 ± 9.5% moisture, while Methods and table notes say 38 ± 9.5%; the discrepancy is flagged rather than resolved. This is an Arkansas annual-ryegrass wrapped-bale experiment, not Dutch roadside grass, and remains reference-only. Ammonia-N concentration is not treated as emissions, and composition concentrations are not treated as component-mass recovery. No storage defaults, equations, Pareto outputs, or runtime behavior changed.

### Phase 5/7 — paired grass-mixture feed and digestate nutrient measurements (2026-11-07)

Added `Greenhub/data/Resource recovery/Digestate_and_Separation/grass_mixture_AD_digestate_macro_nutrients_wahid_2018_reference.csv`, preserving 48 Table 2 observations from Wahid et al. (2018; DOI `10.1016/j.biombioe.2017.12.029`): TN, TAN, P, K, Mg, Ca, S, and Na in feed mixtures and day-70 digestate for lucerne and lucerne–forbs–grass silages. Source units and fresh-matter basis remain intact; blank uncertainty means no SD was reported. The lab feed was diluted 40:60 with water and run in one 52 °C CSTR per feedstock regime. These concentration pairs do not establish flow-corrected nutrient retention or recovery and do not represent GreenHub's roadside feed or post-protein residual. The extract is B-tier reference-only; no fertilizer recovery, default, or model calculation is activated.

### Phase 1 — provincial biomass inventory estimates distinguished from collected supply (2026-11-07)

Added two separate records from the Zuid-Holland provincial biomass inventory report: 46,100 t in its previous inventory and 60,102 t in its current inventory. The report says the berm-grass quantity was calculated from a University of Utrecht report; its authors attribute the difference mainly to different sources and note weather dependence. The underlying reference years, wet/dry basis, calculation inputs, accessibility, and collection fraction are not established. Both B-tier records are staged context only: do not sum them, interpret the difference as measured growth, convert to dry matter, or use them as GreenHub supply or capacity. The existing approximately 10,000 t/year provincial-road report and separate 117/120 t GreenHub project claims remain distinct scopes and are not reconciled with these inventory totals.

### Phase 5/7 — digestate composition and reported removal comparator (2026-11-07)

Added 47 table records from Chiumenti et al. (2019, DOI `10.3390/en12173244`, CC BY 4.0) for fresh, dried, and ensiled spring riverbank grass: digestate solids, VS, pH, redox, acidity/alkalinity, TKN, ammonium, fiber fractions, and published TS/VS/TKN/ammonium removal values. This is an Italian batch study using digestate inoculum from a dairy-manure digester, not GreenHub route data. Reported removal values are concentration-based and cannot be used as flow-corrected nutrient balances or fertilizer yields. No P/K or nutrient recovery step is reported. We excluded the paper's gas-yield figures because abstract, plotted results, and conclusion contain differing fresh-grass values. Dataset remains reference-only and is not connected to defaults or calculations.

### Phase 1 — Greenhub Zuid-Holland project-wide collection result (2026-11-07)

Added a separate record for the current project results page's statement that 120 t of grass/cuttings were collected with five partners. The page does not disclose reporting dates, whether the total is annual or cumulative, wet/dry basis, site split, or weighing evidence. This is not added to or treated as confirmation of the distinct 117 t 2024 dry-run figure. It remains an A-class first-party project-reported observation, reference-only, with no annualization or default activation. The phase summary table below now uses the process sequence consistently: Phase 2 storage/logistics, Phase 3 pretreatment/fractionation.

### Phase 7 — supplementary pilot data repository discovered (2026-11-07)

Corrected the local source record for Proskynitopoulou et al. (2024): four supplementary CSVs are publicly downloadable from Zenodo DOI `10.5281/zenodo.15040664`, contrary to the prior note that underlying data were only available on request. Added a FAIR metadata sidecar listing the record DOI, file URLs, byte sizes and Zenodo-published MD5 checksums, and linked it in both source registers. The Zenodo record has no displayed data license; the related article is CC BY-NC-ND 4.0. Therefore the deposited numerical files were not copied, transformed, or activated. The dataset concerns Greek mixed food-industry/animal/agricultural digestate and remains a Phase 7 comparator, not a GreenHub grass parameter. This closes a data-discovery/provenance gap, not the project-specific nutrient-flow or recovery gap.

### Phase 6 — carbon-membrane pilot performance and energy boundary (2026-11-07)

Added Haider et al. (2018; DOI `10.1016/j.gee.2018.03.003`) to the membrane performance register with source-located purity, maximum methane recovery, and specific-electricity records. The pilot used pretreated food-waste biogas; its 96 mol% product purity and maximum 98% methane recovery are short-term results from a 5 h test, while 192 h describes overall pilot operation and does not establish that the maxima were sustained. The reported 0.13 kWh/Nm³ is explicitly for the high-pressure compressor only, not total upgrading electricity. These values are B-tier, reference-only evidence, not GreenHub setpoints. The source license is CC BY-NC-ND, so the numerical transcription is limited to factual data and the source is linked for verification. No model defaults, equations, or scenario results changed.

### Phase 1 — municipal verge-management area and calendar evidence (2026-11-07)

Added `Greenhub/data/Pre-treatment/Feedstock/municipal_verge_management_reference.csv`, transcribing eight Nuenen 2020–2026 green-plan area-by-mowing-regime records (m²) and two Lansingerland calendar-guidance records (ISO week windows for ecological verge cuts and safety strips). The records remain separate by municipality and evidence type: Nuenen area is not biomass yield, while Lansingerland weeks are not an observed monthly mass profile. No area conversion, yield estimate, sum across municipalities, or interpolation was performed. Both sources are reference-only, no runtime/default mapping was added, and no explicit reuse license was identified. This improves schedule context but does not resolve site-level GreenHub availability, weighbridge tonnes, wet/DM pairing, accessible/contracted area, or actual missed cuts.

The FAIR input catalog now indexes 570 assets and 890 master-input records (524 source-linked assets, 428 DOI-linked assets, 48 without a source-register link). The checkpoint governance audit indexes 403 datasets: 60 blocked, 343 reference-only, and zero active/default-eligible; no scientific values or runtime inputs were changed.

### Phase 1 — verified official South Holland supply context and identifier correction (2026-11-07)

Checked the province's own account against the staged availability records: it reports approximately 10,000 t/year of roadside grass, two annual mowing rounds in June–July and September–October, and collection after a few days' field rest. The page does not state the mass basis, reporting year, metering method, or per-round quantities. These remain official contextual evidence only—not contracted GreenHub supply, DM yield, or plant capacity. Removed a locally coined token from the DOI/persistent-identifier field in the source register; the stable article URL and repository-local source ID remain. The staged record test now checks that no DOI/PID is fabricated. FAIR catalog/workbook refreshed; focused seasonal-evidence, Phase 4 provenance and FAIR tests pass.

### Phase 4 — formic-acid precipitation dose/pH reference (2026-11-07)

Indexed `grass_liquid_formic_acid_precipitation_stefanski_2024_reference.csv` and its source sidecar in the feedstock source register and dataset manifest. The five records preserve the conference paper's 0–10 L/Mg treatment labels, bottle additions, 500 g liquid basis, triplicate counts, and brown-liquid pH means/SEM. The source-reported dose labels conflict tenfold with the bottle-scale amounts; both are retained without choosing a corrected value. The proceeding has no DOI or explicit reuse license identified. Dataset is B-class, reference-only, not calculation-connected, and blocked from reagent-demand/TEA use until dose and rights are clarified.

Rebuilt the FAIR catalog and generated workbook snapshots: 545 assets, 890 normalized input records, 499 source-linked assets, 415 DOI-linked assets, and 48 assets without a source-register link. The newly indexed proceeding has a stable source URL but no DOI. Focused provenance/catalog tests pass. This does not resolve GreenHub-specific juice titration or acid demand.

### Phase 1/2 — measured roadside-grass harvest yield and collection performance (2026-11-07)

Added `Greenhub/data/Pre-treatment/Feedstock/roadside_grass_harvest_performance_brown_2020_reference.csv` from Results 3.1 of Brown et al. (2020; DOI `10.1016/j.biombioe.2020.105570`). The two source-reported campaigns distinguish a 2016 single-cut test harvest (5.9 t collected over a 4.3 km run, 1.1 m swath, 12.5 t fresh/ha, approximately 76% moisture and 3.0 t DM/ha) from the 2018 pilot average (1.2 m swath, 5 t fresh/ha, approximately 25% moisture, 3.75 t DM/ha, 3 t/h at 5 km/h). Unreported fields and uncertainty remain blank; no values were inferred.

This adds measured UK roadside-harvest evidence to Phase 1 yield and Phase 2 feed-moisture context. It does not resolve Dutch per-cut collected supply, site access, ecological retention, contracts, or uncertainty. The 2016 harvest was unusually productive and the 2018 pilot occurred in an unusually cold/dry season; both remain reference-only. These measured campaign values are not the same as the study's modeled Lincolnshire supply scenarios and are not applied to defaults or Pareto availability.

### Phase 1 — Dutch road-verge standing-biomass observations (2026-11-07)

Added `Greenhub/data/Pre-treatment/Feedstock/road_verge_standing_biomass_bakker_2026_zenodo_reference.csv`, transcribed from the CC BY 4.0 Zenodo file `Biomass.csv` for Bakker et al. (2026; publication DOI `10.1111/avsc.70085`; version DOI `10.5281/zenodo.15349657`, concept DOI `10.5281/zenodo.15349656`). It contains 120 treatment × site × month rows from ten Dutch roadside grasslands, six mowing regimes, and June/August 2023 observations. The single source-missing biomass value remains blank. The author's analysis script establishes the source units as g dry matter/m² and converts to t/ha using ×10/1000; this extract preserves g DM/m² without conversion. Exact Zenodo `Biomass.csv` and `Analysis.R` bytes are now preserved in a dedicated source subfolder with checked MD5/SHA-256 sidecars and FAIR entries. The earlier Feedstock-root `Biomass.csv` remains for compatibility; its only byte-level difference is line-ending normalization, and parsed records/values match the exact source.

The article's data-availability statement prints the concept DOI as if it were a version DOI; Zenodo metadata confirms the version/concept relationship above. Values are standing-biomass snapshots before mowing, sampled only in the first block, not collected or delivered tonnes. They are useful as Dutch empirical reference data for site productivity and seasonal pre-cut comparisons, but do not establish accessible area, commercial harvestability, annual yield, or the GreenHub supply profile. This is B-tier measured field evidence, `reference_only`, and not activated as a feedstock default or Pareto availability input.

### Phase 3/5 — Green Valleys brown-juice nanofiltration reference (2026-11-07)

Added `Greenhub/data/Protein recovery/Membrane/green_valleys_brown_juice_nanofiltration_2020_reference.csv` from a public Green Valleys/Aarhus University project presentation (2020; no DOI assigned). The reference contains 30 records: feed/permeate/concentrate Brix and sugar/organic-acid concentrations from a GE HL pilot NF test, plus separate demo-scale feed/concentrate volumes, Brix, pressure, temperature, volume-reduction factor, and pilot/demo membrane areas. The sidecar and local source register distinguish the two trials and preserve `nd` separately from reported 0.00 values.

No solute recovery or rejection was inferred because matched stream flow volumes are unavailable for the pilot table; Brix is not treated as dry matter or sugar mass fraction. No flux, cleaning, runtime, energy, membrane-life or uncertainty data are reported. All values remain B-tier reported project measurements and reference-only; no parameter registry, runtime calculation, or defaults changed.

### Phase 7 — European digestate composition comparator (2026-11-07)

Added `Greenhub/data/Resource recovery/Digestate_and_Separation/reuland_digestate_composition_zenodo_v1_reference.csv`, a row-preserving extract of 1,884 numeric-coded observations from the explicitly licensed Zenodo v1 workbook (DOI `10.5281/zenodo.5526416`; source MD5 preserved in its sidecar). The extract retains original values and workbook row IDs; it adds readable feedstock and digestate category labels but performs no conversion, imputation, aggregation, or filtering for model fit. The paper supplies units for major composition fields and describes its harmonization to dry-matter basis; fields whose units are not resolved remain explicitly unresolved in metadata.

This increases Phase 7 source coverage for broad digestate nutrient composition, but it does not unblock GreenHub recovery calculations: feedstocks are mixed manure/energy-crop/biowaste groups, there is no grass-only cohort, separation technology is not identified consistently, and pathogen/weed-seed reporting units remain unresolved. It remains B-tier contextual evidence and is not runtime-connected or eligible for defaults, route recovery, fertilizer credits, or balance closure. The later Zenodo v2 record is a distinct release and was not substituted because its license metadata was blank during review. CC BY 4.0 for the v1 source was verified via Ghent University Biblio; source/version distinction and limitations are in the sidecar.

### Phase 5 — Green Valleys brown-juice characterization and reactor profile (2026-11-07)

Added `Greenhub/data/Bigas production + upgrade/AD reactor/green_valleys_brown_juice_characterization_and_pilot_profile_2020_reference.csv` from the same report. It contains 32 records for fresh and warmed brown-juice TS, VS, pH, VFA and COD; the reported 90-day batch BMP on VS and COD bases; and all five pilot operating periods (feed load, OLR and HRT). The source identifies a 5.5 m³ packed anaerobic filter, 30–32 °C operation, 55–60 °C pre-warmed feed, and ambient-temperature storage. Printed period and paired-precision values are retained without fitting or interpolation.

The BMP values are not continuous yields; the report's `kg/day` feed-mass basis is unspecified, and raw/warmed samples are not a controlled replicated comparison. It does not report gas composition, period-specific methane yields, energy, or digestate chemistry. These cultivated grass-biorefinery records are reference-only and not calibration for GreenHub roadside-grass residuals.

The refreshed FAIR catalog contains 533 assets, 890 normalized input records, 487 source-linked assets, and 405 DOI-linked assets (48 without a source-register link). Governance reports 383 source datasets/checksums, 323 reference-only, 60 blocked, zero default-eligible datasets, and `scientific_values_modified=false`. This is improved traceability and phase-relevant evidence—not new runtime eligibility.

### Phase 2/3/5 — grass-silage storage, press-juice chemistry and press-cake methane-potential reference (2026-11-07)

Added `Greenhub/data/storage/grass_silage_storage_pressjuice_bmp_steinbrenner_2022_reference.csv` from Steinbrenner et al. (2022), DOI [10.1007/s12649-021-01626-4](https://doi.org/10.1007/s12649-021-01626-4), CC BY 4.0. It contains 147 source-linked records: Table 3 day-90 silage chemistry and VS-loss means/SDs across eight temperature/additive treatments; Table 4 press-juice chemistry/COD/pH; and three numeric press-cake methane-potential results explicitly reported in the article text. Units and wet/dry basis remain separate, and censored `<0.1` observations are retained as text rather than converted to zero.

This is measured cultivated German grass-silage evidence, not roadside grass or the GreenHub protein-depleted residual. Only 90-day endpoint data are transcribed, so they do not establish storage kinetics; no interpolation, figure digitization, activation, default change, or model recalibration was performed. The article states raw data can be provided by the authors on request. Provenance and applicability limits are recorded in the dataset sidecar and storage source register.

### User-supplied GreenHub measurements archived and clarified (2026-11-07)

The original `261027 Nutriënten Grasmonsters VARTA.xlsx` workbook is now archived
beside its English extracts and checksummed in the source register. Its fiber
sheet contains 18 sample rows; its juice sheet contains 3. In the fiber extract,
the legacy column `dry_matter_fraction` stores percentage points (e.g. 14.3),
not a 0–1 fraction. A `dry_matter_percent` alias has been added without removing
the legacy column, and the loader now uses the explicit percent field before
dividing by 100. This is a data-label clarity correction; the calculated profile
is numerically unchanged.

The supplied `bermgrass_report_english.csv` contributed 105 measurement-only
records to `Greenhub/data/Pre-treatment/Feedstock/brs_roadside_grass_pilot_2021_draft_reference.csv`.
The requester's personal metadata was excluded. The extract is not activated:
the original Dutch report/PDF was not supplied for verification, no DOI for that
draft report was established, and its page-7 diagram explicitly says it is not
fully balanced. The 5:1 water-to-sample entry is therefore retained only as a
reported laboratory procedure, not an industrial water-use parameter. The
associated `10.18174/630159` DOI is verified as a different 2023 WUR regional
herbaceous-biomass report and is not claimed as the identity of the 2021 draft.
After indexing these assets, the FAIR catalog contains 526 assets and 890
master input records; 480 assets are source-linked, 402 have DOI metadata, and
48 still lack a source-register link. The five newly indexed source assets
were checked for source-specific attribution: VARTA and the supplied draft
report have no DOI assigned, while the Nielsen datasets point only to
`10.3389/fenvs.2021.619258`.

### Phase 1/4 — cut-level forage yield and protein data (2026-11-07)

Table 1 from Nielsen et al. (2021), DOI `10.3389/fenvs.2021.619258`, is staged
as 40 reference observations in
`Greenhub/data/Pre-treatment/Feedstock/fen_grass_harvest_yield_cp_nielsen_2021_table1_reference.csv`.
It preserves published per-cut and annual-average DM yield and CP concentration
for reed canary grass and tall fescue across one-to-five-cut schedules. This
adds evidence for the link between harvest timing and feed CP (Phase 1) and
potential protein feed quality (Phase 4); it does not provide roadside supply
or GreenHub-specific extraction performance. Fertilization differs for the
one-cut versus 2–5-cut treatments, so the apparent treatment effect cannot be
attributed to harvest frequency alone. All values remain literature class B,
reference-only. The article states raw data are available from authors; this
extract is limited to published Table 1 values.

Tables 3–4 from the same paper are separately staged as eight annual observations
in `fen_grass_biorefinery_fractionation_annual_nielsen_2021_tables_3_4_reference.csv`.
They report DM and crude-protein yields for the feed, screw-press pulp, protein
concentrate and brown juice. This adds a Phase 4 comparator but not a closed
balance: reported mean product streams do not sum exactly to mean feed yields,
and the paper identifies press losses. The lab protocol reports pH, acid
concentration, holding and centrifugation conditions, but not the phosphoric
acid volume/equivalents. Therefore these data do not clear reagent-demand or
GreenHub-specific recovery blockers.

Extended the same source with `fen_grass_biorefinery_fractionation_per_harvest_nielsen_2021_tables_3_4_reference.csv`: 224 records for the 28 reported harvest events in Tables 3–4, with separate DM- and CP-yield observations for biomass, pulp, protein concentrate and brown juice. This adds cut-timed fraction-output evidence for Phases 1, 3 and 4; the existing eight annual rows remain separate and unchanged. The source caption's `t ha^-1 year^-1` unit is retained verbatim even on cut-indexed rows, without deriving a per-cut conversion. Source `NA`, single-replicate missing SDs and `>0.0` at printed precision remain distinct. CC BY 4.0 is stated in the article. The cultivated Danish fen-grass, lab twin-screw-press and acid-precipitation results remain B/reference-only and are not GreenHub roadside calibration or runtime inputs.

Table 2 is staged in
`fen_grass_protein_fraction_extractability_nielsen_2021_table2_reference.csv`
as ten annual CNCPS observations. It adds harvest-regime-dependent B1+B2 and
B1+B2+B3 composition context for Phases 1/4, but these theoretical fractions
must not be interpreted as recovered protein. The article identifies its raw
data as available from the authors; the linked supplementary tables were not
directly retrievable in this pass, so per-cut fraction chemistry remains an
evidence request rather than an estimated dataset.

Updated 2026-11-07. This is an evidence-collection checkpoint, not a claim that Phases 1–7 are fully parameterized. Evidence tier B means literature/official-source evidence; it does not imply direct applicability to every GreenHub material stream. No evidence below is promoted to a runtime default solely because it has a DOI.

### Phase 2/3/4 — cultivated grass-clover pressing and fraction composition (2026-11-07)

Added `Greenhub/data/Protein recovery/Isoelectric/grass_clover_silage_biorefinery_fraction_composition_resch_2024_reference.csv` from Resch et al. (2024), DOI `10.1111/gfs.12682`. The 56 row-preserving observations transcribe Table 1 crude protein, dry-matter concentration, sugars, crude ash and NDF, and Table 3 pH for wilted forage, silage, press juice, fresh press cake and re-ensiled press cake from cultivated grass-clover mixture and red clover. Published units, fresh/dry bases, replicate count and residual SD are retained; juice NDF, which was not analysed, is not converted to zero.

This adds measured Phase 2 preservation/fraction feed-state evidence, Phase 3 pressing/fraction chemistry, and Phase 4 protein-containing juice/cake composition. It does not supply precipitation recovery, reagent demand, a complete mass/component balance, raw replicate data, or GreenHub roadside feed properties. The data remain B-tier, reference-only, and not runtime-connected. Source DOI, article PDF, table locations, applicability limitations, local/global source registers and manifests are recorded. A focused test guards transcription anchors, traceability and non-activation.

### Phase 4 — legume-grass protein concentrate spray-drying observations (2026-11-07)

Added `Greenhub/data/Protein recovery/Drying/legume_grass_concentrate_spray_drying_echeverria_jaramillo_2026_reference.csv` from Echeverria-Jaramillo et al. (2026), DOI `10.1007/s11947-026-04220-5`. It records the paper's pilot Niro and laboratory Yamato dryer conditions (inlet/outlet air temperatures) and Table 2 dry-basis protein means with the source-reported uncertainty magnitude; the statistical uncertainty type is not specified. The University of Copenhagen research portal identifies the final article as CC BY.

The material is an accumulated Danish cultivated legume-grass RuBisCO-rich concentrate produced by screw pressing and membrane filtration, not GreenHub's roadside-grass isoelectric curd. Feed solids, liquid feed rate, air flow, energy demand, powder recovery, final moisture and a closed dryer balance are absent. Particle-size data are excluded because the article text and Table 2 disagree on the LGT2 uncertainty. These two observations are literature measurements, B-tier and reference-only; no default or drying calculation changed.

The dated entries above are the acquisition ledger. The compact matrix below is a representative gap summary, not an exhaustive list of every newly staged file. Recent 2026-11-08 evidence also includes Greenhub first-party collection/processing observations, separate capacity ambitions, and a qualitative Bermgras Canvas contamination-screening rubric (Phase 1); storage and degradation comparisons (Phase 2); Stødkilde fractionation and Glazowska cell-wall chemistry (Phases 3–4); and additional BMP, digestate, and nutrient-availability observations (Phases 5 and 7). These remain distinct from GreenHub route-specific measurements; the project-specific gaps in the matrix remain open.

| Phase | Representative evidence; dated additions above are the complete ledger | Highest-impact remaining data need | Collection decision |
|---|---|---|---|
| 1 — feedstock and availability | Dutch VARTA sample measurements; WUR Dutch verge biomass estimates; Zeeland/MooV supply scenarios; Dutch roadside standing-biomass/mowing observations; seasonal Polish roadside-grass composition in `Greenhub/data/Pre-treatment/Feedstock/roadside_grass_seasonal_composition_2024.csv`; Lincolnshire road-network supply scenarios by radius and swath width in `road_verge_supply_scenarios_lincolnshire_2020.csv`; measured 2016/2018 Lincolnshire harvest performance in `roadside_grass_harvest_performance_brown_2020_reference.csv`; official Zuid-Holland mowing and mixed-green-waste reports; and an attribute-only public Zuid-Holland GIS extraction summarized by asset type, source mowing frequency and mowing descriptor (`roadside_grass_pzh_inventory_2026_summary_reference.csv`). | Spatially screen individual GIS features to determine grass-only/mowable area, rights/access and route eligibility; obtain actual Dutch collected/delivered tonnes by cut and year, contamination/soil fraction, and paired local moisture/composition. Standing biomass, mapped management area, and provincial aggregates are not GreenHub delivered feed. | Use the administrative GIS as a candidate spatial inventory, not as a yield or supply value. Keep literature ranges and reported totals scenario-only until access, contracts, basis, and collected-flow evidence are known. Preserve VARTA as sample-specific; Brown et al.'s measured UK harvest campaigns are reference evidence, while its Lincolnshire supply totals remain modeled scenarios—not Dutch supply measurements. Do not convert mapped polygon area or the Zuid-Holland annual tonnage into GreenHub capacity.
| 2 — storage and logistics | Field-rest decay, collection-delay/logistics evidence, and GreenHub dry-run observations are staged. Li and Nishino (2013) add 164 grass-silage chemistry observations across sealed storage and a seven-day aerobic challenge; Hindrichsen et al. (2025) add 26 pooled/conditioned mass-loss and aerobic-stability observations. | Dutch roadside grass under matched storage conditions: inbound-to-processing timestamps; mode, temperature, oxygen exposure; paired mass/composition/BMP; leachate and emissions; haul distances, payloads and downtime. | Cultivated silage concentrations and fresh-matter-loss summaries are not roadside inventory-loss kinetics. Keep field-rest decay distinct from ensiling/storage loss; no loss/emission factor is inferred.
| 3 — pretreatment and fractionation | Existing composition, physical-property, mechanical pretreatment and equation records; VARTA measurements and pilot ryegrass juice/clarifier records; Brown et al.'s UK roadside harvest campaign; and Damborg (2019) abstract-level screw-press protein-partition ranges. Guanlao (2019) separately records preparation of a Belgian roadside batch and a managed-grass batch. | Matched inlet/outlet component balances, size reduction and press energy at declared scale, wash/dilution requirements, and solids/particle-size measurements for the actual feed. | Preserve basis and feed identity: Damborg ranges are unpaired abstract values, UK/Belgian samples are not Dutch seasonal feed, and pilot juice volumes lacking density are not a closed press/clarifier balance.
| 4 — protein recovery | Staged evidence includes Dotsenko & Lange condition-level enzyme observations, Kim's alfalfa extraction/accounting extract, la Cour's 12 ryegrass/red-clover treatment combinations, the 2026 cultivated-ryegrass pilot press/clarifier dataset, Damborg's abstract ranges, and Riihinen et al.'s separate best-condition versus selected-protocol red-clover/timothy results. | Seasonal raw roadside-grass juice protein/solids characterization; measured titration demand; pH/time/temperature recovery curve; separator capture, wet-cake moisture, and component closure for the selected route. | Total-N partition is not isolated true-protein product yield. Cultivated forage and abstract-level results remain reference-only; target matched GreenHub juice-to-product trials before enabling predictive recovery.
| 5 — anaerobic digestion | A 107-record BMP evidence file includes whole roadside grass, silage and selected residual analogues. Brown et al. (2020) provides roadside-grass proximate/ultimate composition and theoretical potentials; de Souza et al. (2024) provides roadside wet-pilot, dry-pilot and large-scale digestion observations; Guanlao (2019) adds an independent Belgian roadside Batch 1, two pilot CSTRs, Table 11 specific methane productivities, and separate grassland enzyme trials. These sources use different feed states, scales, test methods and gas bases; the methane values are not a single transferable yield curve. | Matched BMP and continuous-reactor data for GreenHub's actual press cake and isoelectric supernatant; feed-specific loading/stability data; full measured gas flow/composition and energy; exact grass-specific ADM1 calibration and inhibition data. | Keep roadside and managed-grass batches distinct; keep whole grass separate from post-protein residuals; distinguish EPi-test calculated potential, standardized BMP, pilot actual yield and unpaired peak biogas results. Do not combine values across incompatible bases or treat small pilot OLR/HRT as full-scale design limits.
| 6 — biogas conditioning/upgrading | Existing water-scrubbing, PSA, membrane, and amine evidence packages include equations and literature/vendor-style inputs. Wantz et al. (2023) adds two farm-scale water-scrubber electrical-meter test points; neither is paired with GreenHub raw-gas composition or a full-scale plant. | Measured raw-gas impurity envelope from Phase 5; matched gas-cleaning/upgrading performance, methane slip/recovery, utilities and biomethane specification at the intended scale. | Do not use generic technology ranges as a universal design point; preserve impurity-, configuration- and scale-specific conditions.
| 7 — nutrient and water recovery | Large staged resource-recovery evidence packages and roadside-grass digestate analogues exist, including de Souza et al. (2024) pilot/landfill digestate observations; Guanlao (2019) confirms TAN, total-N, P, pH and conductivity assays were performed but the thesis does not tabulate the numeric nutrient results. | GreenHub digestate/centrate speciation and solids split; feed-specific recovery tests; reagent titration; product purity, water quality, and buyer/land-manager acceptance specifications. | Keep unreported assays blank; distinguish concentrations from nutrient mass recovery and plant response from product certification. Keep blocked datasets blocked unless basis, units, source location, equations, and route compatibility pass review; row count is not calculation readiness.

Phase 7 source context includes Petrovič et al. (2021), DOI [10.1016/j.jenvman.2021.112593](https://doi.org/10.1016/j.jenvman.2021.112593): P recovery above 99 wt%, N recovery of 85–92 wt%, precipitate above 25 wt% NPK, and qualitative K recovery for zeolite methods. Abstract-level, cross-method results remain text-only and reference-only. A second primary pilot source was located: Proskynitopoulou et al. (2024), DOI [10.1016/j.jenvman.2024.120166](https://doi.org/10.1016/j.jenvman.2024.120166), with digestate characterization, filtration, electrodialysis, and struvite process evidence. Its matrix is predominantly food-industry waste, and its CC BY-NC-ND 4.0 license plus data-on-request statement mean numeric extraction is held pending author data/reuse confirmation. Neither source is a GreenHub grass digestate performance parameter.

## Newly staged source data

Czubaszek et al. (2024), DOI [10.3390/en17071751](https://doi.org/10.3390/en17071751), report seasonal fresh-grass and silage composition in Table 1 and methane fraction in Table 4. The extracted CSV stores 48 composition rows including two censored autumn sodium results as missing, not zero. The accompanying Phase 5 evidence file stores six measured methane fractions and four exact biogas-yield mean/SD values stated in the text. The other plotted yield points were not digitized, and no methane yield was synthesized from biogas yield and a separately reported fraction. Full source metadata, license, collection-year uncertainty, and limitations are kept in the source register/sidecar.

These data are B-class literature measurements but are not GreenHub measurements: they describe whole roadside grass from Poland, not Dutch VARTA grass or the GreenHub post-protein residual. Both files are explicitly `reference_only`; neither changes a default, equation, or Pareto result.

## Verification and next collection targets

### Phase 1/4 — spring-cut ryegrass composition and N partition (2026-11-06)

Added Greenhub/data/Protein recovery/Isoelectric/seasonal_ryegrass_fractionation_stodkilde_2020_reference.csv, transcribing perennial-ryegrass values from Tables 1–3 of Stødkilde, Eriksen and Jensen (2020), Grassland Science in Europe 25, pp. 683–684. Twenty records cover herbage N, pulp and protein-isolate N concentration, and source-calculated N recovery to pulp/isolate across four consecutive spring cut dates. The paper reports 12 M phosphoric acid to pH 4 and an overnight hold at 4 °C, but no acid volume or equivalents; this does not fill the Phase 4 reagent-demand gap. Recoveries are total-N partitioning, not isolated true-protein recovery. The cultivated Danish forage, freezing and laboratory press conditions are not GreenHub roadside-feed data. The package manifest, local source register, sidecar and targeted regression test record these limits; the data remain B-class and reference-only, with no runtime activation.

- `tests/test_seasonal_roadside_grass_evidence.py` verifies record counts, unique IDs, source links, manifests, reference-only state, censored-value handling, and biogas/methane separation.
- The same targeted test now verifies Phase 7 threshold/range strings remain non-numeric and the DOI/source link is present.
- The FAIR input catalog was rebuilt after adding the Phase 1/2, Phase 2/4, and Zuid-Holland Phase 1/3 evidence. Latest snapshot: 474 assets, 889 master input records, 428 source-linked assets, 420 DOI-linked assets, and 48 without a source-register link.
- Data-governance report identifies 59 blocked and 297 reference-only datasets, with zero default-eligible datasets; the audit reports no scientific values modified. Adding sourced measurements is not equivalent to clearing model blockers.
- Next collection priority: phase 4 grass-juice titration/recovery and phase 5 residual-specific BMP/kinetics; then phase 6 matched upgrader performance and phase 7 digestate speciation/recovery. Phase 1/3 remain limited primarily by local supply/contract observations, not by a lack of broad literature ranges.

## Phase 2/4/5/7 — newly transcribed clover-grass pilot reference (2026-11-06)

Santamaria-Fernandez et al. (2020), DOI [10.1007/s12649-019-00842-3](https://doi.org/10.1007/s12649-019-00842-3), is now represented by a source-linked 69-row observation table in `Greenhub/data/Resource recovery/Digestate_and_Separation/clover_grass_biorefinery_partition_santamaria_fernandez_2020_reference.csv`. The full-text Tables 1–2 provide small-scale clover-grass and pilot stream concentrations for fresh biomass, press cake, fermented brown juice and protein concentrate, plus the paired 3 L semi-continuous co-digestion operating/performance means and SDs. Source table values, units, basis, analytical methods, scale, and material identity are retained. The sidecar records article and manuscript metadata, DOI and stable source link, retrieval date, rights caveat, process conditions, and data limitations; the digestate source register links the DOI locally.

This adds Phase 2 press-fraction composition and nutrient partition context; Phase 4 protein-concentrate and residual-liquid composition context; Phase 5 HRT, OLR, solids removal, methane yield and gas methane fraction context; and Phase 7 total nutrient composition context. It does **not** resolve GreenHub's matched roadside-feed or isoelectric-supernatant gaps: the source uses cultivated clover-grass, lactic-acid fermentation rather than isoelectric precipitation, and pilot flow data are insufficient for a complete pilot biorefinery mass balance. Measurements remain class B literature evidence and `reference_only`; they are not canonical runtime parameters or defaults. Source `n.d.` and `<dl` entries remain blank with explicit status, not zero.

Source-layout verification was performed against the accessible accepted-author-manuscript full text. In Table 1 the nutrient columns are mapped as total N, ammonium-N fraction, C:N, P, K and S; values were checked against the reported C:N ratios before they were staged. Targeted tests validate source linkage, unique IDs, nonactivation, missing/censored-value handling, analyte mapping and the AD measurement basis.

### Updated high-impact collection queue

1. Phase 1: Dutch site/contract-level accessible area, actual cut-level collected and delivered fresh mass, contamination/soil burden, and paired moisture/composition. Literature yield cannot substitute for municipal route, access, collection, and delivery records.
2. Phase 2/4: GreenHub roadside-grass press and juice titration campaigns: matched feed, pulp, juice, precipitation liquor and product mass/composition; acid equivalents to target pH; separator capture and washing; moisture and particle size; specific electricity and water.
3. Phase 3: storage records pairing initial/final inventory and component analyses with temperature, moisture, oxygen exposure, packing density, storage type and duration for fresh roadside grass under both aerobic and anaerobic scenarios.
4. Phase 5: BMP plus continuous-reactor trials on GreenHub's own press cake and isoelectric supernatant, with feed basis, inoculum, blank correction, HRT/OLR, gas composition and full C/N/S balances. Literature analogues now improve screening context but do not validate route-specific kinetics.
5. Phase 6: raw-gas impurity characterization from the selected Phase 5 feed and configuration, followed by matched upgrader flow, pressure, methane recovery/slip, product specification, and measured power/water use.
6. Phase 7: paired total/dissolved nutrient speciation and suspended solids on actual digestate and centrate; measured separation partition; reagent demand and product purity/yield for the chosen ammonia, phosphorus, potassium, and water recovery route.

These are collection needs rather than permission to activate proxy values. Each analogue should remain discoverable and useful for screening while the calculation retains its existing fallback and missing-data flags.

## Phase 1 — public South Holland management GIS identified (2026-11-06)

The national open-data catalog lists a public-domain Province of Zuid-Holland GIS inventory of green objects along provincial roads and waterways. Its WFS schema includes route and route-section IDs, managed-object description/type, slope, mowing method, ecological-management flag, maintenance frequency, zone, polygon area (`Oppervlakte`, m²), slope-corrected area (`Opp_correctie`, m²), owner and manager. Dataset UUID: `9B2A50A8-E419-4536-9771-AD2470D66E12`; advertised feature type `verkeer:ABS_W_GROEN`. An English field dictionary and metadata sidecar are staged next to the feedstock data.

An attribute-only read retrieved all 37,188 published features; no geometry was requested. A 33-row table groups three potentially relevant asset classes by source maintenance-frequency and mowing-description labels. It reports berms: 9,726 features, 5,697,043.8 m² mapped / 5,885,056.5 m² slope-corrected; sightline areas: 16,762 features, 3,194,152.1 m²; and grass-paving blocks: 1,884 features, 244,751.8 m². The two area columns are source administrative measurements and are preserved separately. Grass paving and sightline categories are not assumed harvestable; berms also remain unscreened. This closes a *source retrieval and descriptive aggregation* gap, not the feedstock-supply gap. Without geometries, feature-level classification, grass fraction, rights/access, ecology, route access, cut-level collected/delivered mass, contamination, moisture/composition or contracts, these area totals cannot support annual biomass availability or plant capacity. The table is reference-only and not connected to defaults or the model. The label `met meter maaien` is preserved in Dutch because its operational meaning remains unverified.

## Phase 6–7 additions (2026-11-06)

- Phase 6: `farm_scale_vacuum_water_scrubber_2023_reference.csv` records nine discrete abstract-level values from Wantz et al. (2023), DOI [10.1016/j.apenergy.2023.121781](https://doi.org/10.1016/j.apenergy.2023.121781). They are reference-only. In particular, >97% product methane is not methane recovery, and reported +19% recovery/+14% CO2 elimination remain relative changes with unresolved percentage-point interpretation until full-text conditions are checked.
- Phase 7: `dairy_digestate_nf_struvite_pilot_2023_reference.csv` records seven abstract-level observations from Tsaridou et al. (2023), DOI [10.30955/gnc2023.00314](https://doi.org/10.30955/gnc2023.00314). The publisher page reports CC BY 4.0. Because this is dairy-effluent digestate, its concentration, operating conditions, and precipitate mass are reference-only, not GreenHub grass defaults or recovery factors.
- Phase 7: `green_biorefinery_digestate_nutrient_reference_2022.csv` records 59 Table 4 observations from Ravindran et al. (2022), DOI [10.3390/cleantechnol4010003](https://doi.org/10.3390/cleantechnol4010003), including dry-basis elemental/nutrient composition and as-received moisture, total solids, and ammonia. The source is CC BY 4.0 and reports triplicate 1 L BMP digestates from cultivated ryegrass biorefinery co-products. The six textual ratios are preserved separately from 53 numeric values; no source blanks are filled. These are laboratory reference data, not GreenHub continuous digestate or nutrient-speciation measurements.
- Neither addition activates a calculation. Phase 6 still needs GreenHub raw-gas impurity/feed-rate matching and full configuration-specific performance. Phase 7 still needs actual GreenHub digestate/centrate speciation, reagent titration, product quality, and closed component balances.
## Phase 2/3 — wet-grass ensiling evidence (2026-11-06)

Added Greenhub/data/storage/grass_silage_forced_aeration_williams_1997_reference.csv, transcribing 48 mean/SD observations from Williams et al. (1997), Table 4, DOI 10.1111/j.1365-2494.1997.tb02348.x. The source compares five-core samples from compacted and uncompacted ryegrass bunkers before and after 20 days of forced aeration, covering dry matter, water-soluble carbohydrates, organic acids, N, pH and microbial indicators. Values are concentrations/indicators rather than whole-silo inventories; no storage mass loss or kinetic rate is derived. This complements the 2025 ensiling time-point reference but remains a cultivated-forage analogue and reference-only.

Resch et al. report a directly measured wet-grass ensiling experiment in Table 9 of the 2025 Silage Conference proceedings. `Greenhub/data/storage/wet_grass_ensiling_dynamics_reference_2025.csv` preserves nine sample/treatment means: forage baseline and control/LABho treatments at 7, 30, 87, and 192 days. Outcomes include dry-matter concentration and loss, protein loss, ammonia-N, pH, metabolic energy, and fermentation products. The study used first-growth Austrian permanent grassland (>95% grasses), 238 g DM/kg fresh matter, ambient 10–18 °C storage, vacuum bags at 7/30 days, and 60 L barrels at 87/192 days.

This is useful measured evidence for the direction and potential scale of storage changes, but it is not roadside-grass- or GreenHub-specific and container type changes at later time points. It remains reference-only: do not fit a universal kinetic law, use it as a Dutch default, infer aerobic degradation, or treat ammonia-N as emitted ammonia. Protein loss does not resolve soluble and insoluble pools. Provenance and a reuse caveat are in the adjacent `.source.json`; no DOI or explicit reuse license was identified.

## Phase 5/6 — grass-biorefinery residual BMP and raw-gas evidence (2026-11-06)

Ravindran et al. (2022; DOI `10.3390/cleantechnol4010003`, CC BY 4.0) report BMP yields and final weighted gas composition for cultivated Irish perennial ryegrass press cake, grass whey, de-FOS whey, and grass silage. The 47 Table 3 observations are staged in `Greenhub/data/Bigas production + upgrade/Feed BMP/green_biorefinery_residual_bmp_reference_2022.csv`, including biogas/methane yields per VS, DM, and fresh matter; CH4, CO2, O2, H2S, NH3; and reported biodegradability. They provide a useful literature analogue for Phase 5 residual BMP and Phase 6 impurity screening, and are more configuration-specific than the abstract-only roadside AD result.

These are not direct GreenHub inputs: grass is cultivated rather than roadside, the press cake/whey separation differs, and de-FOS whey includes an additional carbohydrate-extraction stage. Table 3 reports L/kg without stating a standard-state convention or uncertainty/replicates; the extract preserves its values without conversion or gas-composition normalization. All rows remain reference-only and no process parameter/default changes.

## Phase 2/4 — roadside-grass press-juice characterization (2026-11-06)

`Greenhub/data/Pre-treatment/Feedstock/grassification_roadside_press_juice_characterization_2018_2019_reference.csv` transcribes selected measurements from Tables 1 and 3–5 of Grassification public deliverable D2.3.1 (version 2.0, 2020-07-06). It covers two screw-press batches: roadside cuttings from a Utrecht highway municipality (8 Nov 2018; rotary mower) and Maldegem (18 Jun 2019; flail mower). Reported liquid/fibre fractions were 42.8/57.4% and approximately 40/60% of fresh mass. Juice values include pH 6.2/4.3, total solids 5.80/11.76%, density 0.98 g/mL, TOC in raw/centrifuged fractions, and Kjeldahl-derived protein 14.90/24.57 g/kg in uncentrifuged juice.

This is unusually relevant roadside-juice evidence, but not a GreenHub or Dutch VARTA route balance. The first session's reported fractions sum to 100.2%; session 2 juice experienced room-temperature handling and possible fermentation; reported ± statistics are not consistently defined; and the authors caution that Kjeldahl nitrogen in the solid fraction may be ammonium salts rather than protein. The deliverable has a stable public URL but no DOI or explicit reuse license identified. Values remain reference-only and are not used to replace the model's default composition, press recovery, or precipitation inputs.

### Phase 1/2 — collection equipment and roadside-clipping quality

`Greenhub/data/Pre-treatment/Mechanical/grassification_mowing_head_field_test_2019_reference.csv` transcribes 36 source-located observations from the companion Grassification D1.1.2 field report. The one-day Maldegem trial compares Vandaele flail and Herder rotary heads, with short-run travel speeds of 3.7–4.07 versus 3.06–3.27 km/h, nominal head widths of 1.6 versus 1.2 m, 12 versus 25 m³ collection containers, and sampled dry matter, sand, and fibre-length distributions. The observed flail/rotary sand results are 2.8/8.7% of DM in Table 4; the prose states 2.9/8.7%, so both flail figures remain separate and flagged.

This is direct roadside collection-quality evidence, but not Dutch feedstock performance or an industrial capacity curve. Speeds are two short 300 m runs, container volumes are not payload mass, one container fill is operator-estimated, and the test changed cut height and machine type together. No annual throughput or machine-specific causal attribution is inferred. Rows remain reference-only.

### Phase 1/3 — Zuid-Holland maintenance flow and mowing windows

The provincial government page [“De bermen in Zuid-Holland komen tot bloei”](https://werkenvoor.zuid-holland.nl/artikelen/de-bermen-in-zuid-holland-komen-tot-bloei/) reports approximately 10,000 tonnes of verge grass mown per year, two annual mowing rounds (June–July and September–October), and removal after the cut material rests in the field for a few days. The undated page does not identify wet/dry basis, reference year, metering method, per-round quantity, or GreenHub's contracted fraction. Two rows were added to `roadside_grass_availability_evidence.csv` with a local source sidecar and register entry; they remain class B staged context only, not converted, not connected to the availability calculation, and not a feed default. Targeted seasonal-evidence and FAIR-catalog checks pass (23 tests); the refreshed catalog contains 474 assets and 889 normalized records. The governance audit still reports 59 blocked, 297 reference-only, and zero default-eligible datasets; no scientific values were modified.

### Phase 5/7 — roadside-grass co-digestion and digestate observations

The 98-record `Greenhub/data/Bigas production + upgrade/Feed BMP/grassification_roadside_codigestion_pilot_2020_reference.csv` transcribes Table 2 feed characterization and Table 3 digestate sampling results from Grassification D1.4.1 (Miserez et al., 2021). The Inagro pilot co-digested ensiled roadside grass with VeDoWS manure and pig slurry; it is not a grass-only digestion trial and does not match GreenHub's post-protein residual stream. Feed and digestate values, reported bases, and an ambiguous final sample date are preserved without conversions. The Table 2 ammonium-N value (0.73 ± 13.13) is explicitly flagged as anomalous and excluded from quantitative interpretation. The report describes pilot interruption/instability, so no kinetic or continuous yield factor is inferred. The dataset is B-class, reference-only, and has a source-linked JSON provenance file; no DOI or explicit reuse license was identified. It adds contextual evidence for roadside feed composition and mixed-feed digestate nutrients, but does not close GreenHub's feed-specific residual BMP, nutrient speciation, or recovery gaps.

### Phase 5 — seasonal roadside-grass dry-digestion evidence

Six abstract-level records from André et al. (2019; DOI [10.1016/j.biortech.2019.121737](https://doi.org/10.1016/j.biortech.2019.121737)) are staged in `Greenhub/data/Bigas production + upgrade/Feed BMP/andre_roadside_grass_dry_codigestion_2019_abstract_reference.csv`. The abstract reports laboratory methane potentials of 202.9 and 167.9 Nm³ CH₄/t VS for two series conducted in June and October 2016, a 60 L dry-batch pilot comparing layered and mixed filling, and an inhibition-associated 34.8–44.4 Nm³ CH₄/t VS range. The abstract does not fully map the seasonal values to substrate lots or define the inhibition range; these uncertainties are explicit, with no curve, loss, or pilot yield calculated. All rows are B-class, abstract-level, and reference-only. This is relevant to Phase 5 seasonality/operability but not a transferable GreenHub residual-digestion parameter.

### Phase 1/2 — Flemish roadside/nature clipping quality survey (2026-11-06)

Added `Greenhub/data/Pre-treatment/Feedstock/flemish_roadside_grass_quality_survey_2020_summary_reference.csv` from the public 2021 Eurofins/Natuurinvest report. Its summary covers approximately 75 grass lots sampled in Flanders from 24 September to 16 November 2020 across nature grassland, motorway verges, regional-road verges, and waterway verges. The report’s conclusions quantify cadmium threshold exceedances by group (1, 2, 2, and 1 locations respectively) and report one waterway-verge location exceeding both chromium and nickel; no exceedances were reported for arsenic, copper, lead, mercury, or zinc. Visible-litter findings are retained at the same group-summary level.

This adds contamination-screening evidence for Phases 1–2, not numerical concentrations or a Dutch feed acceptance rule. The report references a separate Excel appendix, but that workbook and sample-level laboratory results were not available from the accessible public copy. Sample counts are approximate, the cited Keurcompost criteria are not GreenHub material specifications, and no explicit reuse license was identified. The 11 rows remain reference-only; the dataset is not mapped to process inputs or model defaults.

### Phase 2/3/4 — green-biorefinery pilot energy, scale and loss references (2026-11-06)

Added `Greenhub/data/Protein recovery/Isoelectric/green_biorefinery_energy_scale_and_storage_benchmarks_2026_reference.csv` from Elshani et al. (2026; DOI [10.1038/s44264-026-00189-y](https://doi.org/10.1038/s44264-026-00189-y), CC BY 4.0). The article reports Tuv pilot aggregate electricity (375 kWh/Mg DM) and propane drying heat (138 MJ/Mg DM), with a separately reported total of 1489 MJ/Mg DM. The rounded components sum to 1488 MJ/Mg DM, so this rounding discrepancy is preserved and tested, not silently adjusted. The study also describes a modeled facility capacity/schedule and stage-specific loss factors attributed to Hedström (2015); these rows are separately marked as design assumptions or secondary literature factors, never as pilot measurements.

This is a useful Phase 2/4 energy and process-scale analogue and a Phase 3 loss-factor reference, but it concerns cultivated Norwegian grass-clover and an integrated dairy biorefinery. It does not provide GreenHub unit-level energy or roadside-grass storage kinetics. All records remain reference-only.

### Phase 2/4/5/7 — pilot stream mass and nitrogen distribution (2026-11-06)

Added `Greenhub/data/Protein recovery/Isoelectric/green_biorefinery_stream_balance_2026_reference.csv`, transcribing Table 2 of Elshani et al. (2026; DOI [10.1038/s44264-026-00189-y](https://doi.org/10.1038/s44264-026-00189-y), CC BY 4.0). It reports fresh mass, DM mass, DM concentration and total nitrogen concentration for cultivated grass-clover feed, pulp, green juice, protein concentrate, brown juice and unrecovered material, normalized to 1000 kg feed DM. The hierarchy is explicit: green juice is an intermediate subsequently split into protein concentrate and brown juice, not an additional final product. The four final reported streams sum to 5264 kg fresh mass versus 5263 kg input (1 kg difference consistent with integer rounding) and exactly 1000 kg DM. Nitrogen closure is still incomplete because the unrecovered stream's N concentration is not reported. This is Phase 2/4 fractionation, Phase 5 residual-stream, and Phase 7 nutrient evidence—not roadside grass, and not runtime-active.

### Phase 2/3/4/5/7 — measured silage-biorefinery fermentation chemistry (2026-11-06)

`Greenhub/data/Pre-treatment/Mechanical/green_biorefinery_fermentation_chemistry_2024_reference.csv` stages 28 Table 3 observations from Resch et al. (2024; DOI [10.1111/gfs.12682](https://doi.org/10.1111/gfs.12682)): pH, lactic/acetic/butyric/propionic acids, ethanol, and ammonia in grass-clover and red-clover silage, press juice, fresh press cake, and re-ensiled press cake. This adds measured fraction chemistry relevant to storage state, green-juice and press-cake composition, and residual handling. The study is an Austrian farm-scale cultivated-forage analogue—not roadside grass—and the measurements are concentrations, not total material flows. Ammonia is not an emissions measurement, and pH does not determine titration demand. Records remain reference-only; exact CC license subtype was not confirmed from the accessible article copy. A focused integrity test checks row/source/stage coverage and interpretation guards.

### Phase 2/4 — Resch et al. (2024) Table 5 campaign mass balance transcribed (2026-11-07)

Added `Greenhub/data/Pre-treatment/Mechanical/green_biorefinery_mass_balance_resch_2024_table5_reference.csv` with 30 Table 5 records for reported DM, crude-protein, NDF, sugar, crude-ash and VOC yields across wilted forage, silage, press juice, fresh press cake and re-ensiled press cake. GCM and red-clover means and reported residual SD are stored in source units (kg/ha); the two not-analyzed/omitted entries are blank and separately labeled. This extends the already-staged Table 3 chemistry to source-reported component-yield evidence for Phase 2 fractionation and Phase 4 protein partition. The study is one Austrian cultivated-forage campaign, not roadside grass; hectare yields cannot be transferred to GreenHub supply, and this subset is not a complete mass/element closure. It remains B-class, reference-only, with no runtime parameter or default activation. The article's data availability statement says underlying data are available from the corresponding author on reasonable request, so no unreported raw values or uncertainty distributions were inferred.

The FAIR catalog/workbook snapshot was regenerated after staging this dataset: 535 indexed assets, 890 normalized master input records, 489 source-linked assets, and 407 DOI-linked assets; 48 assets still lack a source-register link. The new evidence is discoverable in the catalog but is not normalized as a runtime parameter, which is intentional. Focused Resch Table 3/Table 5 and FAIR catalog tests pass (20 tests). The adjacent legacy governance tests still contain fixed expectations of 363 package datasets/checksums while the current source tree produces 383; those two assertions fail independently of this dataset and are not changed here.

### Latest collection validation (2026-11-06)

- Added the full Ayanfe et al. (2023) Table 2 preservation × press evidence matrix (14 source-table rows; seven treatment conditions × seven response metrics for each of two press types), including SEM and treatment-effect p-values. CC BY 4.0, DOI 10.1016/j.biteb.2023.101356. It remains comparative literature evidence, not a GreenHub runtime default.
- Added three aggregate, source-reported annual roadside-grass yield observations from Piepenschneider et al. (2016; DOI 10.1016/j.biombioe.2015.12.012): repeated mulching, four-cut, and two-cut management in Kassel, Germany. This fills a small Phase 1/3 comparative evidence gap but is not Dutch collected supply; no uncertainty statistics were transcribed from the abstract, and no runtime default was changed.
- Added the same study's abstract-level maximum press-fluid methane yield (292 L_N CH4/kg VS) under Phase 5. This is a maximum with no abstract-level protocol or replicate spread; it is separated from whole-grass and continuous AD yields and remains reference-only.
- Phase 7: added nine measured phosphate-adsorption isotherm points from the BioDEN Task 3.2 factsheet, with all values retained on the reported synthetic-solution basis. Its separate chicken-manure digestate test (230 mg/L PO4-P; 2–52 g/L adsorbent; up to 93% removal) is explicitly text-level only and not joined to the synthetic isotherm. No DOI or reuse license was identified; all evidence remains reference-only.
- Corrected the interpretation of Ayanfe CP-retention records: source values are `g CP/g original fresh material`, not a fraction of initial CP. Numeric observations did not change. Targeted regression verifies the published numerator/denominator basis.
- After these additions and correction of source-to-file matching, the FAIR catalog reports 497 assets, 889 normalized input records, 451 source-linked assets, 386 DOI-linked assets, and 48 assets without source-register links. The lower DOI count removes package-level DOI over-attribution; it does not mean source records or model parameters were removed. These are catalog coverage counts, not completeness or activation metrics.

The roadside-AD evidence files contain 98 and 6 rows; the Flemish clipping-survey summary contains 11 rows; the green-biorefinery energy/scale/loss dataset has 18 rows; and the pilot stream-balance dataset has 24 rows. Focused tests check their widths, IDs, sources, manifest links, evidence classes, flow hierarchy, blank missing values, and rounding/closure checks. The malformed Phase 6 H₂S equation-registry row was repaired without changing its cited equation: columns are correctly mapped, its duplicate ID is now unique, and its former ID is retained in provenance. The dataset audit reports no malformed CSV rows and passes. The refreshed FAIR catalog reports 487 assets, 889 normalized master-input records, 441 source-linked assets, 433 DOI-linked assets, and 48 assets without a source-register link. Governance reports 59 blocked and 301 reference-only datasets, with zero default-eligible datasets; 192 equations comprise 182 blocked and 10 reference-only, with no active datasets/equations; `scientific_values_modified=false`. The focused Phase 1–7 collection suite passes 42 tests. These counts describe catalog coverage/governance, not completeness or model activation.

### Phase 7 — Dutch farm-scale nutrient recovery comparator (2026-11-06)

Added `Greenhub/data/Resource recovery/Phosphorus_Recovery/demarke_manure_digestate_nutrient_recovery_2019_reference.csv`, transcribing 18 measurements from Szymańska et al. (2019), DOI [10.3390/en12010155](https://doi.org/10.3390/en12010155), CC BY 4.0. This Netherlands De Marke study sampled a cattle-slurry biorefinery in 2017 and reports liquid digestate composition, mixed struvite quality, dilute ammonium-sulfate solution composition, and source-reported nutrient-recovery efficiencies.

It is a Dutch unit-process/product comparator, not roadside-grass evidence. The source's 43.8% P and 43.2% N efficiencies are concentration differences between input and final effluent, not closed flow-weighted mass recoveries; the N result combines struvite precipitation and ammonia stripping. The recovered struvite is impurity-bearing (39.4 g P/kg wet product), while ammonium sulfate is dilute (66.4 g/kg, pH 2.1). All observations remain B-class, reference-only, and excluded from model defaults, TEA prices, and route recovery calculations. This improves realistic product-quality context but does not clear the Phase 7 blockers for GreenHub digestate speciation, flow-weighted recovery, reagent titration, or market-grade acceptance.

### Phase 4/7 — mineral partition across green-biorefinery fractions (2026-11-06)

Added `Greenhub/data/Protein recovery/Isoelectric/green_forage_fraction_mineral_partition_hansen_2022_reference.csv`, transcribing all 20 forage-by-fraction rows from Hansen et al., *Grassland Science in Europe* 27 (2022), pp. 164–166, Table 1. It covers K, Ca, Mg, P, Zn and Cu concentrations in whole plant, pulp, green juice, green protein and brown juice from white clover, red clover, lucerne and perennial ryegrass. The source reports 52 samples pooled across July, September and November, with least-square means and table-wide SEM/p-values preserved in the sidecar.

This adds source-backed component-fate context for Phases 4 and 7, but concentrations cannot be interpreted as element mass recovery without stream flow and DM data. Protein/brown-juice fractions from November were unavailable, and the source used staged heat precipitation rather than the isoelectric route. Cultivated Danish forage and an unstated proceedings reuse license make these values reference-only; no GreenHub calculation/default changes.

### Phase 1 — Zuid-Holland municipal green-waste context (2026-11-06)

Added \`AV-ZH-MUNICIPAL-GREEN-WASTE-TOTAL\` to \`roadside_grass_availability_evidence.csv\` from the Province's public-domain open-data catalog (dataset identifier \`0f08e50f-6483-4d62-8a29-16a049e5c5ec\`). The catalog reports 76,084 t/year of municipal green waste for Zuid-Holland and was updated 2026-08-13. Its scope includes verge clippings, pruning residues, and vegetation from public green spaces, watercourses, parks, and nature areas.

This is a useful independently published regional scale comparator, not an estimate of grass-only feedstock. The catalog summary does not establish reporting year, wet/dry basis, measurement method, material-category split, or GreenHub allocation. It is B-class official reported aggregate evidence and remains staged/reference-only; it must not be converted to dry matter or used as plant capacity. Dataset provenance, public-domain status, and limitations are recorded in the feedstock source register and sidecar.

The targeted roadside-grass evidence test passes. The rebuilt FAIR catalog contains 505 assets and 890 master input records; the new aggregate is indexed without changing the simulation, scenario defaults, or feedstock-resolution behavior. Phase 1's primary unresolved need remains site/route-level grass-only collected mass by cut, with basis and access/contract constraints.

### Phases 1–5 — Greenhub Zuid-Holland dry-run operational evidence (2026-11-07)

Added `greenhub_zuid_holland_dry_run_operational_evidence_2024_2026_reference.csv`, a structured extraction from three first-party project reports. The 2024 report gives an aggregate 117 t collected by five contractors, and qualitative operational observations on contract-specific field-rest periods, the first metre safety strip, weather-related inability to mow, a 15 cm chopping requirement associated with heating, and ensiling. A companion process report describes screening foreign material, pressing into fibre/grass-juice fractions, flocculation, and exploratory downstream routes. These are project-reported pilot observations, not the underlying weighbridge tickets, laboratory results, or process records.

A 2025-published article supplies later short-chain routing figures (15 t paper, 95 t pot-stall use, and 600 t GKB own grass to Bokashi), but its section heading labels the dry-run as 2026. That temporal conflict is retained explicitly; the 600 t is also explicitly identified as GKB's own grass, not roadside cuttings. None of these quantities are summed into roadside supply or assigned wet/dry basis. All rows remain quality A as project-reported primary observations, reference-only, and disconnected from calculations. No defaults, seasonal profiles, process yields, or Pareto inputs were changed.

This source adds Phase 1 availability/collection constraints and useful Phase 2–5 chain context, but it does not clear the key quantitative gaps: weighbridge records by contractor, route, date, and verge zone; paired moisture/DM/composition; storage duration/loss and leachate; and press/fractionation flow and component balances. Dataset row-width, source linkage, year/basis caveats and non-activation are tested.

### Phases 3/5/7 — roadside-grass juice digestion and digestate abstract evidence (2026-11-07)

Added `roadside_grass_juice_continuous_digestion_chopda_2026_abstract_reference.csv` from Chopda et al. (2026; DOI `10.1007/s12649-025-03274-4`). The abstract directly describes screw-press separation of roadside grass into fibre and grass juice, continuous digestion of the juice, and a reported biogas potential of 39.9 Nm³/t fresh matter. It also reports a digestate plant-use assessment and flags high electrical conductivity and potential allelopathic effects for grass-juice digestate.

The denominator stream for the 39.9 value is not defined in the accessible abstract, and the result is biogas rather than methane. Methane fraction, reactor conditions, mass balance, component flows and uncertainty are therefore unavailable. The publisher page is copyright-restricted and the institutional record says underlying data cannot be shared; only a minimal abstract-level factual extract is staged, with no article/supplementary data reproduced. All four rows are B-class, reference-only, and not mapped to a runtime parameter. This is a useful new roadside-specific digestion/digestate pointer, but it does not clear Phase 5 yield calibration or Phase 7 nutrient/product qualification.

### Data index refresh — 2026-11-07

The two new reference datasets from this collection pass are now represented in their local manifests and source registers, the global source checksum/readiness package, and the FAIR catalog. Current counts: 392 global source datasets/checksums, 653 source issues, 424 quarantined rows, 60 blocked and 332 reference-only global datasets; zero active or default-eligible datasets. FAIR catalog: 551 assets, 890 normalized input records, 505 source-linked assets, 419 DOI-linked assets, and 48 assets without a local source-register link. No scientific values or runtime behavior were changed.

### Phase 1 — South Holland WFS attribute extraction (2026-11-06)

### Phase 1/2 — Maldegem roadside site-access observations (2026-11-07)

Added `grassification_maldegem_site_access_observations_2019_reference.csv` from Appendix 1 of Grassification deliverable D1.1.2. The 30-record English extract preserves ten site observations (slope, manual pin penetration, and visual litter class) at Dijkstraat, Maldegem. Source coordinates are retained where unambiguous; point 4 coordinates are blank rather than guessed. The extract records directly observed field conditions but is not a Dutch regional accessibility sample. The manual pin test is not a standardized soil-strength or compaction measurement, and the qualitative litter class is not a mass-based contamination factor. Dataset is B-tier, reference-only, and has no runtime mapping; no supply, access, or harvesting defaults changed.

Retrieved all 37,188 feature records from the official `verkeer:ABS_W_GROEN` WFS as attributes only (no geometry), then grouped the three potentially relevant classes by source maintenance-frequency and mowing-description labels. The 33 output groups are in `Greenhub/data/Pre-treatment/Feedstock/roadside_grass_pzh_inventory_2026_summary_reference.csv`; query details and limitations are in its `.source.json` sidecar. The grouped counts and area totals are validated by `tests/test_phase1_to_7_clover_grass_reference.py`: berm, 9,726 features and 5,697,043.8 m² mapped / 5,885,056.5 m² slope-corrected; sightline area, 16,762 and 3,194,152.1 m²; grass paving, 1,884 and 244,751.8 m². These are source administrative area fields, not grass biomass or accessible supply. Geometry, grass-cover classification, ecological/operational constraints, land access, delivery, yields, cut-level mass and composition remain missing. The original Dutch mowing label `met meter maaien` remains untranslated pending confirmation. No runtime defaults, parameter-registry values, routes or scenario results changed.

The refreshed FAIR catalog contains 513 assets, 890 normalized input records, 467 source-linked assets, 395 DOI-linked assets and 48 assets without a source-register link. Governance reports 60 blocked and 314 reference-only datasets, with zero default-eligible datasets; it also reports 374 source datasets/checksums and `scientific_values_modified=false`. The focused Phase 1–7 reference plus FAIR-catalog tests pass (24 tests). Counts indicate traceability coverage, not model readiness.

### Phase 5 — grass-silage ADM1 kinetic-fit reference (2026-11-06)

Filled the source-table transcription gap for four grass-silage disintegration/hydrolysis constants. The values are fitted (not directly measured) parameters from Biernacki et al.'s 2013 article, transcribed from the author's open 2014 dissertation, Table 17, p.102. The table reports `k_dis = 1.7433 d^-1`, `k_hyd_ch = 0.7366 d^-1`, `k_hyd_pr = 0.0104 d^-1`, and `k_hyd_li = 0.0149 d^-1`; the source batch calibration was at 38 °C for 15 days. They are recorded in `Greenhub/data/Bigas production + upgrade/AD kinetics/grass_silage_adm1_biernacki_2013_reference.csv`, with exact locations, normalized SI conversions, fit method, absent uncertainty, and transferability limits in the CSV and sidecar. The local article DOI typo was corrected to `10.1016/j.biortech.2012.09.128`, and the dissertation is registered separately.

This resolves the *literature-table retrieval* gap, not the GreenHub-specific calibration gap. GreenHub's post-press cake and isoelectric residual remain compositionally and kinetically distinct from grass silage; no fitted literature value was copied into the runtime parameter registry or activated as a default. The remaining-data register now names the residual-specific calibration need explicitly. Regression checks verify the transcription, d^-1→s^-1 conversion, provenance, empty uncertainty field, and non-activation.

### Phase 4 — comparative alfalfa protein-recovery benchmark (2026-11-07)

Added `Greenhub/data/Protein recovery/Isoelectric/alfalfa_protein_recovery_methods_coburn_2021_reference.csv`, transcribing Table 5 from Coburn et al. (2021; DOI [10.1002/agg2.20184](https://doi.org/10.1002/agg2.20184)). Five recovery methods are represented with APC mass yield per kg herbage DM, product crude protein/fat/sugar/fiber/limiting amino acids per kg APC, treatment conditions, triplicate count, and the published Fisher-LSD significance groups. The publisher labels the article Open Access; its specific reuse-license subtype was not confirmed in accessible article text and is recorded as such.

This is a controlled alfalfa press-filtrate comparison, not a roadside-grass parameter. APC mass yield is not true-protein recovery, and pH endpoints do not establish acid/base dose. No values were activated in GreenHub calculations, defaults, price assumptions, or runtime registries. A focused test checks the transcription, basis separation, source linkage, FAIR catalog indexing, and non-activation.

After indexing this dataset and its sidecar, the FAIR catalog contained 515 assets, 890 normalized input records, 469 source-linked assets, 397 DOI-linked assets, and 48 assets without source-register links. These historical counts describe discoverability/traceability, not evidence of model completeness or runtime activation.

### Data collection checkpoint — 2026-11-07

The latest FAIR catalog rebuild after the Phase 1/2 harvest-performance extract contains 541 assets, 890 normalized input records, 495 source-linked assets, 413 DOI-linked assets, and 48 assets without a source-register link. The Bakker Zenodo version/concept DOI roles and dataset license are now verified in the source sidecar and source register; the article's separate license is not inferred from the dataset license. Focused source-traceability and FAIR-catalog tests pass. No staged reference dataset was promoted into a runtime default.

The next highest-value data collection remains Dutch site/route-specific delivered tonnes by cut with paired wet/dry basis, contamination, and composition (Phase 1/2), followed by actual GreenHub juice titration and protein-product component balances (Phase 4), and residual-specific continuous digestion plus flow-weighted digestate nutrient recovery (Phases 5/7). Current public datasets are useful comparators, not substitutes for those missing project measurements.

### Phase 2/7 — roadside grass press-liquid nutrient and contaminant composition (2026-11-07)

Added `Greenhub/data/Resource recovery/Phosphorus_Recovery/roadside_grass_liquid_fraction_nutrient_metals_scott_2023_reference.csv` from Scott et al. (2023; DOI `10.1002/jpln.202200308`). The 18-row extract preserves Table 1 means and standard deviations on both fresh-matter and dry-matter bases for 18 constituents, with n=3 and source-reported fertilizer MPCs where provided. It retains P2O5 and K2O as reported, does not convert them to elemental P/K, and preserves displayed zeros at the reported precision.

This is a direct Belgian roadside press-liquid comparator and adds real nutrient/metal composition evidence for fractionation and resource-recovery context. The source is CC BY-NC; this restriction is recorded and requires review before commercial redistribution or use. The sample is from one June 2019 location, is not GreenHub digestate or brown juice, and does not establish flow-weighted partition, recoverable product, fertilizer acceptance, or sale value. The paper also reports plant harm with untreated liquid fraction, so nutrient concentration alone is not taken as proof of fertilizer suitability. Dataset remains reference-only; no model defaults or credits changed.

### Phase 2 — roadside cuttings left in field before pickup (2026-11-07)

Added `roadside_cutting_field_decay_schaffers_1998_reference.csv` from Tables 1 and 3 of Schaffers, Vesseur & Sýkora (DOI `10.1046/j.1365-2664.1998.00316.x`). Eight Dutch roadside plots preserve initial dry-matter yield and N/P/K/C composition, plus source-fitted asymptotic remaining-fraction parameters and fit statistics for dry mass and N/P/K. The sidecar records the equation, units, experimental timing/weather, DOI/source locations, data handling, and fit-quality caveats. Missing or failed-fit fields remain blank.

This fills a distinct Phase 2 evidence niche: cut grass that is left on the verge for up to six weeks before removal. It is not silage storage kinetics, not a raw time series, and not transferable as a GreenHub default. The article's accessible record says “Free Access” but does not identify a reuse-license subtype; this is explicitly unresolved. The dataset is B-class published primary field evidence, reference-only and not calculation-connected. The focused transcription/provenance test and FAIR-catalog tests pass. The refreshed catalog now contains 547 assets, 890 normalized records, 501 source-linked assets, 417 DOI-linked assets, and 48 assets without source-register linkage.

### Phases 1/5/7 — Grassification consequential-LCA comparator (2026-11-07)

Added `Greenhub/data/lca/grassification_flanders_roadside_grass_lca_2021_reference.csv` with source-located scope, counterfactual, impact results, contribution values, and LCI-availability records from the public 2021 Flanders project report. It specifies 1 t mowed grass as functional unit and a consequential cradle-to-farm-gate boundary; its project case ensiles roadside grass and co-digests with burden-free manure fractions. The extract keeps impact results (including negative net avoided-burden results) distinct from contributions and physical emissions. It covers climate change, combined freshwater/terrestrial acidification, USEtox human-health medians, and LANCA land-use scores. It is not a GreenHub route result or characterization factor. The deliverable says the full inventory is available on GitHub on request; no inventory was obtained or reconstructed, so the underlying LCI remains an explicit data gap. Rows are B-tier, reference-only, and not calculation-connected.

### Data index refresh after Maldegem site-access extract (2026-11-07)

The new 30-row site-access reference has been added to the mechanical pretreatment manifest and source register, the global dataset manifest/readiness/checksum package, and the FAIR asset catalog. Current governance counts are 393 source datasets, 653 issues, 424 quarantined rows, 60 blocked datasets and 333 reference-only datasets; no datasets are active or default-eligible. The FAIR catalog contains 553 assets and 890 normalized master-input records, with 507 source-linked assets, 419 DOI-linked assets, and 48 assets lacking a local source-register link. These are index/governance counts, not evidence that phases 1–7 are complete; the new data remain reference-only and do not alter model outputs.

### Data index refresh after consequential-LCA reference (2026-11-07)

The 2021 Grassification LCA records and local source-register entry are now included in the FAIR catalog and global audit scope (`lca` added to the dataset inventory). Current counts are 396 source datasets/checksums, 653 source issues, 424 quarantined rows, 60 blocked and 336 reference-only; none are active/default-eligible. The FAIR catalog contains 555 assets, 890 normalized records, 509 source-linked assets, 419 DOI-linked assets and 48 assets without a local source-register link. The LCA asset is reference-only. Its negative climate figures are net consequential results with avoided-burden credits and must not be plotted as gross CO2 emissions.

### Phase 4 — pilot green-biomass protein-fraction quality (2026-11-07)

Added `pilot_fraction_protein_quality_nynas_2024_reference.csv`, transcribing Table 3 of Nynäs et al. (2024; DOI `10.1021/acsfoodscitech.3c00426`, CC BY 4.0). It reports mean and standard deviation of soluble and insoluble SE-HPLC protein concentrations for seven pilot fractions (unfractionated biomass, pulp, green juice, green protein, white juice, white protein, and brown juice), with the source significance groups retained. The study processed eight cultivated leafy biomass materials from Scania, Sweden, at a pilot facility; it is not roadside-grass evidence.

The study reports screw-pressing at approximately 250–300 kg/h, green-protein heat coagulation at 55 °C, and white-protein precipitation using 40% w/v citric-acid solution to pH 4. It does not report the acid volume consumed, so pH is not converted into reagent demand. The HPLC values are concentrations per dry mass, not stream flow, total component mass, or recovery. All records remain B-class reference-only; no runtime parameter, default, product specification, or Pareto result changed. A regression test checks the table transcription, unit basis, provenance, catalog linkage, and non-activation.

The refreshed FAIR index contains 557 assets and 890 normalized input records, 511 source-linked assets and 421 DOI-linked assets; 48 assets lack a local source-register join. The global audit contains 397 source datasets/checksums and 653 issues (60 blocked, 337 reference-only, none active/default-eligible; `scientific_values_modified=false`). These counts describe indexing and governance, not scientific model completeness.

### Phase 1 — seasonal verge-grass harvest-potential estimates in Zeeland/Flanders (2026-11-07)

Added `2seas_verge_grass_seasonal_harvest_potential_2021_reference.csv`, a 30-row transcription of Table 1 from the Interreg 2 Seas/VITO mobilisation report. It preserves summer, autumn, and source-reported annual totals for theoretical and technical fresh-mass quantities across five road/waterway management classes, including the Zeeland PZ category. The report states that technical potential is 70% of theoretical potential to account for obstacles and topography. Theoretical values are classified B as published project estimates; technical values are classified C because they embed the report's assumed accessibility factor.

These are regional estimates, not sampled site yields. The source provides no moisture/DM measurement for these values, so no dry-matter conversion was made. They do not quantify current contracts, ecological retention, source-separated grass area, collection losses, or GreenHub-accessible supply. The existing source-register record was reused; no second source record or runtime/default mapping was added. The report's public PDF metadata did not provide an explicit reuse license, so that uncertainty is recorded in the sidecar. Focused tests check the transcription structure, units/basis, evidence tier, source ID, and non-activation.

Also added `2seas_zeeland_regional_seasonal_feedstock_supply_2021_reference.csv` from the same report's Tables 9–11 and 23 and Figure 42. The 45-row extract separates manager-reported road length/area, 2018 mapped standard/ecological acreage, seasonal modeled theoretical and technical potential, source-reported 33%-DM totals, the one-cut scenario, and a historical circa-1% collection scenario. Table 9 estimated area (2,987 ha) is intentionally not merged with the Table 10/23 mapped scenario area (2,360 ha): the report gives different source bases, including an explicit 2 m width assumption for Province acreage. The two-cut 42,300 t fresh/year and one-cut circa 25,300 t fresh/year are scenario potentials, not actual delivered supply; circa 250 t collected represents the report's historical as-is case, not a current estimate. Scenario outputs are class C and remain reference-only. A separate test checks the flow/area hierarchy and historical-vs-scenario separation.

### Cross-phase collection checkpoint — 2026-11-07

Added two source-located roadside-grass batch-digestion milestones to `grassification_roadside_codigestion_pilot_2020_reference.csv`: 60% of the reported batch biogas potential at day 3 and 90% at day 8 (Figure 9). They are B-tier source-reported observations, not a fitted kinetic curve, continuous-reactor HRT, methane yield, or GreenHub post-protein-residual parameter. The extract remains reference-only. Also corrected the Sandoval et al. (2026) Phase 3/4 pilot-data sidecar so its `dataset_file` matches the actual cultivated-ryegrass CSV; a regression assertion now guards that link. Source: [Grassification D1.4.1 report](https://www.biorefine.eu/wp-content/uploads/2021/03/d1.4.1_anaerobic_co-digestion_of_roadside_grass.pdf) and [Sandoval et al. (2026)](https://doi.org/10.1038/s41538-026-00831-6).

The current evidence base and the next *decision-relevant* collection target by phase are:

| Phase | Useful evidence now staged | Highest-value unresolved project data |
| --- | --- | --- |
| 1 — availability | South Holland area/maintenance context; Zeeland seasonal potential; Dutch standing-biomass observations; roadside harvest and collection campaigns | Delivered weighbridge tonnes by site, route and cut; accessible/contracted area; wet mass and paired DM; ecological/access exclusions; actual cut dates and missed cuts |
| 2 — storage/logistics | Field-rest decay and grass/silage storage analogues; storage benchmarks and operational observations | GreenHub inbound-to-processing timestamps, storage mode/temperature, mass and leachate losses, paired composition/BMP over time under aerobic and anaerobic conditions |
| 3 — preparation/fractionation | Roadside collection-quality and press references; VARTA measurements; cultivated pilot and brown-juice filtration data | Matched GreenHub feed/juice/cake weighing and lab analyses, water addition, machine settings, throughput and electricity by unit; particle-size and contamination acceptance data |
| 4 — protein | VARTA grass samples; seasonal fractionation and pilot protein-quality references; acid-precipitation observations | VARTA/GreenHub titration curves and acid/base mass by batch, true-protein versus total-N assays, matched stream flow/component balance, recovery, wash-water and final product grade/moisture |
| 5 — digestion | Roadside grass BMP and mixed-pilot data; green-biorefinery residual BMP/continuous-reactor analogues; batch-time milestones | BMP and continuous performance on GreenHub's actual press cake and protein-section residual, with feed TS/VS/COD, methane fraction, loading/HRT, gas rate, digestate mass/nutrients and replicate uncertainty |
| 6 — gas upgrading | Technology-specific literature and vendor/design references for water scrubbing, membranes, PSA and amines | Raw-gas composition/flow/pressure, measured methane recovery and slip, product specification, parasitic energy/heat/water, media/reagent consumption, downtime and tail-gas emissions for a selected configuration |
| 7 — nutrient recovery | Roadside press-liquid nutrients; Dutch, European, and French agricultural mixed-digestate composition references; recovery-technology studies and product references | Flow-weighted GreenHub digestate and liquor analyses (TAN, soluble/total N, orthophosphate/total P, K, alkalinity, metals), capture and product mass/purity, reagent demand, water use and fertilizer compliance testing |

### Phase 7 — French agricultural digestate aggregate comparator (2026-11-07)

Added `Greenhub/data/Resource recovery/Digestate_and_Separation/ferti_dig_french_digestate_summary_caradec_2025_reference.csv`: 13 aggregate values from Caradec et al. (2025; DOI `10.1016/j.dib.2025.111550`), including the French collection's published median dry matter and total/ammoniacal nitrogen, K2O, P2O5, carbon, organic matter and pH (n=608; samples from 165 agricultural AD plants, 2006–2022). The paper is CC BY 4.0; the associated data.gouv repository (DOI `10.57745/M1JSU5`) has separate custom non-commercial terms and a download-notification/citation condition. Only statistics published in the open article are transcribed; no raw restricted dataset files were downloaded or copied.

This is a heterogeneous French agricultural digestate comparator, not roadside grass or GreenHub's post-protein residual. Concentrations and population medians do not establish flow-weighted nutrient recovery, reagent demand, or fertilizer grade. All values are B-tier, reference-only, and disconnected from calculation defaults. The local source register, dataset manifest, metadata sidecar, and focused regression test preserve provenance and reuse limits.

These priorities distinguish observed/project-specific evidence (A), directly reported literature measurements (B), literature-derived or scenario assumptions (C), and unsupported placeholders (E in the current workbook convention). Existing references improve discoverability but do not justify replacing the still-required Phase 3–7 parameter rows: the phase parameter sheets currently contain 0 B-class required rows in Phase 3, 4, 5 and 7, and only 1 in Phase 6; the many B-class files are mostly comparator evidence with different feed, equipment, or process boundary. No evidence was promoted to a runtime default by this collection pass. The master workbook and API/UI override precedence remain unchanged.

### Phases 1 and 5 — residue-grass field and AD evidence (2026-11-07)

Added bedoić_residue_grass_field_and_AD_reference_2019.csv (46 source-located observations) from Bedoić et al. (2019; DOI 10.1016/j.jclepro.2018.12.224). The Phase 1 subset records April quadrat yields for uncultivated land, riverbank and highway verge, alongside selected moisture, ash and ultimate-analysis values on their reported fresh/dry bases. The Phase 5 subset records theoretical COD and C/N, measured 40-day BGP/BMP values for three residue-grass samples and five co-digestion controls, the MRG2-fitted ADM1 kinetic constants, and the study's modeled BGP comparison.

These are B-class primary-literature observations or explicitly source-calculated/fitted values, all reference-only. Field yield is not annualized; BMP is on TS basis and is not continuous reactor performance; co-digestion controls contain manure and/or maize; and MRG2-specific fitted kinetics are not GreenHub residual defaults. No parameter registry, workbook input, simulation, default, or Pareto result was changed. DOI, author manuscript, source table locations, methods, uncertainty gaps, applicability and transferability limitations are recorded in the sidecar; local/global source registers and manifests, governance checksums, and the FAIR catalog were refreshed. The resulting audit indexes 400 datasets (60 blocked, 340 reference-only; 0 active/default-eligible) and 653 documented issues; the FAIR catalog has 563 assets and 890 normalized master-input records. A focused regression test checks transcription anchors, provenance, registration, and non-activation.

### Phase 1 — seasonal event scheduling and Pareto refresh (2026-11-07)

The dated harvest-event schedule is now carried into annual decision-support runs and the Pareto UI configurations as explicit harvest, delay, and process-release dates. Harvest quantities and the annual/seasonal regional supply evidence retain their existing evidence provenance. The event placement on specific calendar dates is a scenario-design assumption (C tier), not a measured harvest calendar; it must not be cited as a validated local operating schedule. This lets availability and storage inventory be calculated from dated arrivals without reclassifying the regional supply evidence as site-specific measurement.

Published Pareto preview and API result were synchronized byte-for-byte after rebuilding the frontend projection from the active results. The published run represents 16 physical designs per route group, expanded across support/grass-bonus sensitivities: protein-enabled has 384 evaluated financial cases; protein-bypass has 200 candidates, of which 192 are evaluated and 8 product-ineligible cases are rejected. The UI preview exposes 100 dated configurations in each route group (200 total). A subsequent exhaustive replay checked all 283 unique configuration IDs across the two selectable catalogs and selected Pareto candidates, covering 10 physical route/season designs. Every replay matched the Configure decision-support service on TEA, LCA, product/utility/balance outcomes, process inputs, monthly biomass availability, harvest, release, and inventory fields. To avoid redundant BioSTEAM runs, the verifier reuses only a completed result for an identical canonical process request; TEA/LCA are recomputed for each finance overlay. Optimization plots were regenerated from the synchronized result set; active Pareto artifacts remain below 100 MB (largest route batch approximately 50.4 MiB). None of this changes the evidence class of assumed event dates or turns them into empirical data.

The current expanded screening batch contains 584 candidates (384 protein-enabled and 200 bypass); 8 bypass candidates fail the saleable-product eligibility gate, leaving 576 evaluated cases. No evaluated case has positive proxy NPV. The best enabled proxy NPV is approximately -€676,183 at 60% CAPEX-grant sensitivity and €50/wet tonne grass-utilization bonus; its annual operating profit after that bonus but excluding public support is approximately -€11,678, and its annual public operating support is approximately €10,258. For that case, proxy NPV without public support is approximately -€1.738 million, and without public support or the grass bonus is approximately -€5.435 million. This comparison keeps the three cash-flow categories separate and shows no observed positive-NPV/negative-operating-profit case in this batch. Its CAPEX and OPEX completeness statuses are partial, so these are scenario-screening proxies, not decision-grade investment KPIs; installed CAPEX, missing OPEX, and validated revenue assumptions must be completed before investment claims.

### Phase 7 — cow-digestate nutrient recovery experiment (2026-11-07)

Added `cow_digestate_struvite_ammonia_recovery_trotta_2023_reference.csv`, transcribing ten flask/crystallizer operating cases and their reported mean ± SD phosphorus-removal/recovery and ammonia-stripping outcomes from Tables 4–5 of Trotta et al. (2023; DOI `10.1016/j.rineng.2023.101478`). The source concerns raw Italian cattle-manure/agricultural-by-product digestate; its measured laboratory outcomes are B-tier primary literature but only reference comparators. The dataset is linked through a DOI/source register, detailed sidecar metadata, manifest entry, and test. It is not connected to model inputs or defaults. Chemical consumption, process energy, captured ammonium-product mass, and industrial scale-up remain absent; do not use the removal percentage as a GreenHub fertilizer-product yield.

After registering this extract, the generated FAIR catalog contains 588 assets and 892 normalized master-input records; 542 assets link to a registered source, and 445 assets carry DOI identifiers. These are catalog counts, not a count of project-specific active parameters or proof that all missing inputs have been filled.

### Phases 3–4 — PEF-assisted grass-clover pilot extract (2026-11-07)

Added `grass_clover_pilot_press_PEF_protein_separation_guo_2022_abstract_reference.csv` from the accessible abstract of Guo et al. (2022; DOI `10.1016/j.fufo.2022.100173`). It captures the stated 70:30 fresh ryegrass:white-clover blend, approximate relative juice and crude-protein yield increases with PEF, 400 L raw-juice batch, pH 5.0 and 60 °C precipitation, and 37.3 g crude protein/100 g DM in precipitated material. Relative gains are kept explicitly relative to the untreated control; product protein concentration is not construed as recovery yield or purity. This is B-tier published abstract evidence, not a complete dataset. Full methods, absolute stream masses, uncertainty, PEF energy, acid demand, and complete balances are not collected, and no values are activated in GreenHub calculations.

The post-addition FAIR catalog indexes 590 assets (544 source-linked; 447 DOI-linked) and 892 normalized master-input records. These catalog totals do not mean that all of the model's missing inputs have been resolved.

### Phase 6 — two-stage polyimide upgrading pilot comparator (2026-11-07)

Added `Greenhub/data/Bigas production + upgrade/Membrane/two_stage_polyimide_pilot_koutsiantzi_2024_reference.csv` with ten abstract-level records from Koutsiantzi et al. (2024; DOI `10.1016/j.envres.2023.118080`) and the related 2024 doctoral dissertation (DOI `10.12681/eadd/57788`). The journal abstract reports a 20 Nm3/h design, five-month campaign, average feed methane composition of 55%, measured average methane recovery of 95.7%, average final-gas methane composition of 82.4%, and 17.5% nitrogen in product gas. The abstracts also report nitrogen-free modeled cases; the journal abstract gives 67% methane recovery while the dissertation abstract gives 87.8%. These results are kept separate because the accessible abstracts do not establish that the cases or definitions are identical.

This is Phase 6 equipment/performance evidence from wastewater-sludge biogas, not grass-derived biogas. Composition percent basis, uncertainty, paired flow data, exact pressures/stage cuts, and complete balances are absent from the accessible abstracts; the dissertation PDF requires registration and its content is copyright-protected. The extract is B-tier, reference-only, and not a GreenHub default or calculation input. The membrane local manifest's relative paths were aligned with the files' current location so they resolve on disk; no data files were moved. A focused regression test checks row-level source identity, the unresolved model discrepancy, and manifest path integrity.

The FAIR catalog was rebuilt after both Phase 6 registrations and now indexes 607 assets, 892 normalized master-input records, 559 source-linked assets, and 458 DOI-linked assets; 51 assets still lack a source-register link. These counts describe discovery/provenance coverage, not calculation readiness or resolution of GreenHub's process-data gaps.

### Phase 6 — long-duration membrane pilot observations (2026-11-07)

Added `bench_scale_long_run_pilot_stern_1998_reference.csv` (13 records) from the publisher abstract of Stern et al. (1998; DOI `10.1016/S0376-7388(98)00238-5`). The extract preserves the wastewater-biogas methane fraction, feed-pressure range, two module-specific pressure/stage-cut/feed-flow ranges, >1,000 h per-module test duration, long-run retentate methane composition, a separate short-term 97 mol% result, and permeate methane composition. It intentionally does not infer methane recovery, methane slip fraction, or flow-normalized SI values.

This long-run bench pilot expands Phase 6 evidence on stability and contaminants, but remains a wastewater-treatment comparator with unspecified membrane polymer and no GreenHub feed match. The public abstract does not pair pressure, stage cut, flow, and composition point-by-point. The extract is B-tier and reference-only, linked to the local source register and FAIR catalog; no model defaults or calculations use it. As printed, the publisher describes the article as open archive under a Creative Commons license, but the exact license subtype was not independently confirmed.

### Phase 1 — Rijkswaterstaat motorway mowing frequency (2026-11-07)

Extended the existing roadside availability register with Rijkswaterstaat's official management statement that motorway grass is mown once per year in most cases and removed. The source separately reports more than 18,000 ha of motorway verges; this is an asset-area lower bound, not grass-only or harvestable area. The frequency is national operating context, not a universal route schedule: local vegetation and road-safety requirements cause exceptions, and the page gives no per-cut mass or dates. This B-class staged record does not alter GreenHub event scheduling or feed availability. [Rijkswaterstaat Bermonderhoud](https://www.rijkswaterstaat.nl/leefomgeving/leefbaarheid-en-milieu/bermonderhoud).

The most recent FAIR catalog refresh indexes 611 assets, 897 normalized master-input records, 563 source-linked assets and 458 DOI-linked assets; 51 assets still lack a source-register join. These are findability/provenance counts, not a measure of data completeness or runtime readiness.

### Phases 1, 3 and 5 — landscape-grass composition, field energy and batch BMP (2026-11-07)

Added three table-level extracts from Heller et al. (2023; DOI `10.3390/en16248091`): four treatment-specific composition records (Table 1), first-cut yield plus field harvesting and mechanical-treatment work/energy records (Table 2 and Results §§3.1/3.4), and treatment-specific batch methane yield and modified-Gompertz fit records (Tables 3–4). The source reports German orchard/lowland-meadow landscape grass; these are not Dutch roadside measurements. The first-cut yield is not annualized, and a normally occurring second cut is excluded. Harvest energy excludes transport and handling, and the in-field Amazone Grasshopper treatment was used on less-accessible plots, so equipment contrasts are not fully matched. The chemistry table reports n=3 for TS/VS, n=2 for acetic acid, and n=1 for other chemistry without standard deviations. BMP and fitted batch kinetics are not continuous-reactor parameters. All values are B-class literature measurements or source-fitted results, with explicit bases and source locations, and remain `reference_only`; no model defaults, parameter registry, or calculations were changed.

Validation recorded in `tests/test_heller_2023_landscape_grass_reference.py` (2 focused tests pass). The refreshed FAIR catalog indexes 617 assets and 897 normalized master-input records; 569 assets are source-linked, 464 include DOI identifiers, and 51 still lack a local source-register link. These counts are discovery/provenance indicators only and do not imply readiness for calculation.

### Phases 2 and 5 — Belgian roadside-grass silo states and storage-linked batch BMP (2026-11-07)

Added `Greenhub/data/storage/roadside_grass_ensiling_quality_ovam_2009_reference.csv` and `Greenhub/data/Bigas production + upgrade/Feed BMP/roadside_grass_storage_bmp_ovam_2009_reference.csv` from Elsen et al.'s January 2009 OVAM-commissioned report (public PDF, no DOI or explicit reuse license identified). Table 29 records seven final silo treatment states, including final dry matter concentration and pH after a ten-week ensiling campaign; only one treatment is grass-only, and the remaining rows include inoculant or co-streams. The pH stability thresholds are separately identified as criteria cited by the report, not new measurements. The report explicitly says silo mass loss could not be quantified from its setup.

The second extract records eight Table 13–14 first-cut roadside-grass biogas-yield observations for fresh versus approximately 6- or 17-day uncontrolled interim holding, separated by wet mesophilic and dry thermophilic batch tests, plus the report's single 23-day mesophilic batch result for ten-week grass mono-silage. The short-hold rows reproduce Leenknegt (2004) as a secondary source; the source cautions that fresh/stored samples were different roadside lots, so these numbers do not support causal storage-loss percentages. One mono-silage yield is per sample added with no explicit wet/dry denominator, so it is not normalized to VS. Batch duration is not continuous HRT, and biogas is not methane.

The Phase 2 and 5 CSVs have local manifests, source-register entries and metadata sidecars; the three new extracts are covered by focused regression tests, and none is calculation-connected. The targeted Heller, OVAM, and FAIR-catalog checks pass (25 tests). The refreshed FAIR catalog indexes 623 assets and 897 normalized master-input records; 575 assets are source-linked, 464 carry DOI identifiers, and 51 lack a local source-register join. Index counts are provenance measures, not phase-completion or runtime-readiness measures.

The same report also adds `Greenhub/data/Pre-treatment/Feedstock/ravels_roadside_grass_collection_conditions_ovam_2009_reference.csv`: a single, explicitly campaign-level Phase 1 summary of four incoming loads and qualitative mowing/collection, freshness, sand and litter conditions. The approximate load size is preserved with its “slightly below” qualifier and unresolved moisture basis; no total tonnage or hectare yield is calculated. It adds operational context but does not resolve Dutch route-level accessible area, contracts or seasonal delivered supply.

### Phases 1 and 2 — wilted ryegrass feed properties, ensiling, and aerobic exposure (2026-11-07)

Added three table-level extracts from Assis et al. (2026; DOI `10.37496/rbz5520250112`, CC BY 4.0): Table 1 pre-ensiling feed properties at 32% and 45% dry matter targets (14 property rows), Table 2 fermentation/composition after 62 days (19 property rows), and Table 3 fermentative loss and aerobic-exposure outcomes (14 property rows). The published table grouping by harvest target and inoculant is retained. Significance letters, P-values, censored `<10^4` values, units and separate 60 °C/105 °C DM bases remain explicit. Table 1 reports one value per harvest despite duplicate sampling; no standard deviation is given.

The source is cultivated Italian ryegrass grown in Paraná, Brazil, not Dutch roadside grass or VARTA feedstock. It is useful as measured literature comparator evidence for Phases 1–2, but it does not establish roadside storage kinetics or GreenHub defaults. The 62-day endpoint is not converted into a rate. Negative DM/gas losses in the 32% DM INO treatment are retained literally. Table 3's aerobic-stability endpoint uses the paper's 26 °C threshold in a 20-day bucket test; its aerobic DM loss is measured after 10 days. The paper reports missing pH samples between days 10 and 18, and no values are interpolated. All three datasets are B-class literature measurements, `reference_only`, and have no runtime parameter mapping. Source: [SciELO full text and tables](https://www.scielo.br/j/rbz/a/FjJbkQK3bR7T9FKXtYznJSq/?lang=en), [DOI](https://doi.org/10.37496/rbz5520250112).

### Phase 4 — green-leaf fractionation yields and nitrogen composition (2026-11-07)

Added `green_leaf_fractionation_yields_and_nitrogen_content_nynas_2021_reference.csv`, a 189-row transcription of Nynäs et al. (2021; DOI `10.3390/foods10112533`, CC BY 4.0). It separates the source's Table 2a nitrogen yields relative to initial-biomass N (54 rows), Table 2b yields relative to N entering each process step (36 rows), and Table 2c stream nitrogen concentrations on a dry-matter basis (99 rows). Replicate counts, reported uncertainty, statistical groups, and the table-specific denominator are kept explicit. The unreported carrot P4 concentration is blank and marked `not_reported`, not zero.

This is Phase 4 evidence from seven Swedish leafy-crop residues, first-cut lucerne, and retail spinach, not Dutch roadside grass. Lucerne is the closest forage comparator but not a validated GreenHub feed proxy. The paper reports nitrogen rather than protein because a material-specific N-to-protein factor was unknown. It reports pH 4.5 and 1 M HCl for precipitation, but not acid volume or consumption. The extract is B-tier and reference-only; no parameter, default, calculation, UI behavior, or scenario result was changed.

The same source's Table 1 was separately collected in nynas_2021_green_biomass_feed_nitrogen_and_dry_matter_reference.csv as 18 Phase 1/4 feed-property observations: N on a dry basis and DM concentration on an as-received basis for nine source materials, with taxonomy and sample date/context. The source reports spinach at 4.8% N in Table 1 while Table 2c lists 5.1% for its BM fraction; the table-specific values are preserved separately rather than averaged or overwritten. These are crop/forage comparator measurements, not Dutch roadside-grass composition or supply data. No runtime parameter or default was changed.

### Phases 1, 5 and 7 — full-text Belgian roadside-grass digestion and digestate evidence (2026-11-07)

Expanded the abstract-only de Souza et al. record (2024; DOI `10.1016/j.wasman.2024.04.018`) into `roadside_grass_AD_2024_fulltext_process_reference.csv` (81 records) and `roadside_grass_AD_2024_fulltext_digestate_reference.csv` (12 records). The process extract covers four Table 1 feed characterizations and wet continuous, dry batch and landfill-cell operations and gas outcomes. The digestate extract covers reported liquid/fiber recovery ranges, pilot nutrient concentrations, landfill-leachate nitrogen/chloride, a qualitative pollutant statement and an author-synthesized regional fiber estimate. Source locations, exact reported bases, experiment identity and caveats are preserved in row data and metadata sidecars.

All values remain B-tier literature evidence and `reference_only`. Table 1 EPi-test potentials conflict with narrative pilot potentials; the dry-pilot inoculum basis differs between Methods and Results; and digestate fractions are not paired on compatible denominators. The article prints 1,808 kg K/t DM, an impossible concentration; the literal value and related N:P:K ratio are quarantined rather than corrected by guesswork. Raw chart workbooks were unavailable, so no time series was digitized. No explicit reuse license was identified. These extracts do not establish GreenHub-specific supply, post-protein AD performance, digestate flows, nutrient recovery or fertilizer quality; no runtime defaults or equations changed. Sources: [Ghent University accepted-manuscript record](https://biblio.ugent.be/publication/01J3Z7596RHF1WVC93MQ8DG8J8); [article DOI](https://doi.org/10.1016/j.wasman.2024.04.018).

### Phases 1, 3 and 7 — Kassel roadside-grass elemental composition (2026-11-07)

Added `urban_roadside_grass_elemental_composition_piepenschneider_2015_reference.csv`, with the 34 table cells for yield-weighted two-cut and four-cut composition in dissertation Table 3. It covers Ca, K, Mg, N, Na, P, S, Al, Cd, Cl, Cr, Cu, Mn, Pb, Si, Zn and ash. Censored Cd/Pb values remain below-detection-limit records; missing four-cut S/Si are explicitly not reported. Methods identify dried plant material for analysis, but the table does not explicitly label every denominator as dry matter, so the basis is flagged unresolved rather than silently normalized.

The source is Piepenschneider et al. (2015), DOI `10.1007/s11356-014-3881-9`, with values verified against the University of Kassel dissertation Table 3. These are B-tier measured literature comparators from ten urban German verge sites, not Dutch or VARTA feed measurements. The table provides weighted means but not site-level values or SDs. The source license is not explicit. No runtime parameter or default was changed. [Article DOI](https://doi.org/10.1007/s11356-014-3881-9), [University of Kassel dissertation](https://www.uni-kassel.de/fb11agrar/index.php?eID=dumpFile&f=4041&t=f&token=a6f955f9e347af6f248e809ec8f4715e83fa4cd6).

### Phases 3 and 5 — IFBB press-cake quality and roadside-grass BMP variability (2026-11-07)

Added `urban_roadside_grass_press_cake_quality_piepenschneider_2016_reference.csv` (14 rows from Table 12) and `roadside_verge_bmp_summary_statistics_piepenschneider_2016_reference.csv` (18 rows from Table 11). The first records C/H/N, ash, reported K2O/CaO index and source-calculated HHV/LHV for two harvests. The source did not test between-cut differences; the second-cut press-cake samples were non-random and came only from sites with sufficient growth. The BMP dataset records volatile solids, methane fraction, and specific methane yield with reported SDs for six silage/press-fluid harvest categories. Table sample counts (site-derived samples) are kept separate from laboratory digestion replicates (two for silage and three for press fluid). Test duration, temperature, stirring, inoculum correction and normalized gas conditions are recorded in metadata.

Both datasets are B-tier reference-only observations from the Kassel 2013–2014 roadside-grass study, not Dutch defaults or full-scale performance. Press-fluid and whole-silage BMP results remain separate; no extrapolation to continuous digestion, process recovery, product-grade eligibility, or TEA/LCA is made. Source article DOI `10.1016/j.biombioe.2015.12.012`; table values were checked in the linked University of Kassel dissertation. The source does not identify an explicit open reuse license. [Article DOI](https://doi.org/10.1016/j.biombioe.2015.12.012), [University of Kassel dissertation](https://www.uni-kassel.de/fb11agrar/index.php?eID=dumpFile&f=4041&t=f&token=a6f955f9e347af6f248e809ec8f4715e83fa4cd6).

The FAIR catalog was rebuilt after these additions. It currently indexes 645 assets and 897 normalized master-input records; 597 assets are source-linked and 486 have DOI links. These are catalog counts, not a measure of how many model phases are complete.

### Phases 2–3 — timothy-silage fermentation, effluent, and press-liquid data (2026-11-07)

Added `timothy_silage_fermentation_effluent_and_press_liquid_ayanfe_2025_tables2_4_6_reference.csv`, a 519-record table-level extract from Ayanfe et al. (2025; DOI `10.1111/gfs.12722`, CC BY 4.0). It preserves Table 2–3 ensiling/aerobic-stability outcomes, Table 4 pooled effluent chemistry, and Table 6 post-ensiling press-liquid yields and composition, with reported bases, treatment context, SEM/p-values where available, and missing/censored caveats. The table-level statistics are not represented as replicate-level data.

This is cultivated Finnish timothy, not Dutch roadside grass or the user's VARTA feedstock. Its 88-day experimental endpoints, pooled effluent samples, and post-freeze/thaw pressing are not converted into GreenHub rates, mass-balance coefficients, or defaults. All records remain B-class, reference-only. The source dataset sidecar records DOI, license, geography, retrieval date, table locations, uncertainty and applicability; the CSV SHA-256 is verified by a focused regression test. No runtime parameter, process calculation, UI override, or scenario was changed.

The catalog now indexes 666 source assets and 897 normalized input records (618 source-linked, 506 with DOI links, and 52 without a source-register join). The embedded master workbook is intentionally excluded from its own asset index because its generated snapshot is inside the workbook; its underlying sheets and normalized records remain indexed, and the workbook's original input precedence is unchanged. These are catalog coverage counts, not evidence that Phases 1–7 are complete or calculation-ready.

### Phases 2–5 — post-protein grass-pulp ensiling and BMP aggregate evidence (2026-11-07)

Added `post_protein_grass_pulp_ensiling_larsen_2019_abstract_reference.csv`, with 16 source-located records from Larsen et al. (2019; DOI `10.1016/j.indcrop.2019.111576`). The accessible abstract reports starting total solids for grass-clover and ryegrass pulp, lab/pilot ensiling durations, two effluent-runoff values, component and methane-potential recovery ranges, and qualitative effects of processing-to-ensiling delay, sucrose, and BMP test duration. Numeric ranges remain ranges; no treatment pairing, storage kinetics, absolute methane yield, or effluent mass-loss coefficient was inferred.

This is cultivated green-biorefinery pulp, not roadside grass or GreenHub's isoelectric-precipitation residue. Only abstract-level aggregates were accessible; replicate values, uncertainty, storage temperature, detailed conditions, and the denominator for reported runoff percentages are unavailable. The 98–116% methane-potential recovery is retained as the paper's relative recovery metric, not a physical fraction. The dataset is B-tier, reference-only, with no runtime mapping. DOI, publisher/institutional links, checksum, applicability, and license uncertainty are recorded in the source sidecar. The source audit found the earlier Ayanfe Phase 2–3 manifest lacked a matching readiness row; that registration was reconciled without changing its scientific data.

The FAIR catalog now indexes 668 source assets and 897 normalized input records (620 source-linked, 508 with DOI links, and 52 lacking a source-register join). Global governance covers 445 datasets with 711 existing validation issues; both newly staged source datasets remain reference-only, and the governance run reports zero active/default-eligible datasets. No calculation, default, UI override, route, or Pareto result was changed. These counts measure catalog and audit coverage, not Phase 1–7 completeness.

### Phases 1–7 — cross-phase meadow-grass comparator (2026-11-08)

Added `Bigas production + upgrade/Feed BMP/meadow_grass_pretreatment_bmp_digestate_chopda_2025_reference.csv`, a 63-row direct extract from Chopda et al. (2025; DOI `10.1007/s13399-024-05776-y`). The data cover feed identity and reported composition (Phase 1); controlled laboratory ensiling conditions and post-treatment TS/VS endpoints (Phases 2–3); an alternative acid/enzyme hydrolysis and lactic-acid fermentation route (Phase 3 and a non-protein Phase 4 comparator); triplicate batch BMP and raw-gas methane fraction (Phases 5–6); and reported N/P/K digestate amounts (Phase 7). Source ID, manuscript section/table locations, reported values and ranges, units, denominator caveats, uncertainty notes, retrieval date, DOI, checksum, reuse notice, and phase-specific transfer limits are recorded in the CSV, sidecar, and local/global registers.

This is B-tier evidence from cultivated meadow grass harvested in Ireland, not roadside/VARTA grass or GreenHub's post-protein streams. Several feed-composition percentage bases are not stated in the paper. The 3-week ensiling results are endpoints, not storage-loss kinetics; BMPs are batch potentials, not continuous-reactor yields; N/P/K values do not establish nutrient availability or fertilizer substitution. The study does not provide GreenHub protein extraction or biogas-upgrading performance. Its accepted manuscript is subject to DTU repository terms that prohibit further distribution; no open reuse license was identified. All rows remain `reference_only`, D3, and unconnected to runtime parameters. The extract does not promote any dataset to D4 or change calculations, UI defaults, routes, or Pareto results. Sources: [DTU record](https://orbit.dtu.dk/en/publications/from-grass-to-lactic-acid-and-energy-evaluating-pretreatment-tech/), [accepted manuscript](https://backend.orbit.dtu.dk/ws/files/368289470/Final-GrassBiorefinery_2.pdf), [DOI](https://doi.org/10.1007/s13399-024-05776-y).

This addition improves cross-phase comparison evidence but does not resolve GreenHub-specific gaps: Dutch delivered seasonal tonnes and paired feed properties (Phase 1); aerobic/anaerobic storage mass and composition time series with losses/emissions (Phase 2); compatible screw-press component and energy balances (Phase 3); roadside-juice reagent demand, precipitation recovery, and product quality (Phase 4); post-protein residual BMP and continuous-digester calibration (Phase 5); methane recovery/slip and upgrading energy (Phase 6); and flow-weighted nutrient speciation, capture, and fertilizer compliance (Phase 7). These remain the next collection priorities rather than being filled by cross-crop assumptions.

After registration, the FAIR catalog indexes 670 assets and 897 normalized input records: 622 source-linked assets, 510 assets with DOI links, and 52 without a source-register join. Global governance covers 446 datasets and 711 validation issues: 62 blocked and 384 reference-only, with zero active/default-eligible datasets. These are provenance/readiness counts, not a measure of scientific completeness. The workbook's generated FAIR_Catalog and Master_Inputs snapshot sheets are refreshed from the catalog; all other sheets and the input/default/override precedence remain unchanged.

### Phases 2 and 5 — anaerobic storage solids-level comparison (2026-11-08)

Added `storage/ryegrass_ensiling_storage_methane_yield_pakarinen_2008_reference.csv`, a six-observation, limited extract of the no-additive ryegrass-dominant laboratory treatments in Table 2 of Pakarinen et al. (2008; DOI `10.1016/j.biortech.2008.01.007`). It preserves the reported low-solids (0 h pre-wilting) and high-solids (48 h pre-wilting) conditions at 0, 2, and 6 months: pH, SCOD, TS, VS, VS/TS, VS loss, methane potential where separately tested, and methane yield both per current wet tonne and per original wet tonne. That distinction matters: the original-feed yield accounts for storage mass/VS losses, while the current-wet-mass basis does not answer the same question.

This is B-class primary literature evidence from a cultivated Finnish ryegrass-dominant crop with oat as a companion crop, not roadside/VARTA grass. The laboratory silos were N2-flushed and stored at 20 °C; no aerobic storage was tested. The source footnote says initial methane potential was measured only for the low-solids, no-additive sample, so the high-solids baseline value is blank rather than borrowed. The extract is intentionally limited to six values rows; the paper's reuse license was not identified, so the source PDF/table is not copied into the repository. Values remain `reference_only`, D3, and unconnected to runtime parameters, storage kinetics, defaults, routes, or reports. No calculation or default changed. Sources: [article DOI](https://doi.org/10.1016/j.biortech.2008.01.007), [University of Jyväskylä repository full text](https://jyx.jyu.fi/bitstreams/ac243a25-b5f4-42db-8bcd-02e12eebb3c2/download).

This addition strengthens the Phase 2 comparator evidence and provides a clear example of why methane potential per kg VS must not be confused with methane yield per original feed tonne after storage losses. It does not resolve the GreenHub-specific need for paired initial/final inventories, composition, effluent, and emissions under Dutch roadside storage conditions. Phase 1 delivered seasonal tonnes, Phase 3 compatible press balances, Phase 4 roadside-juice titration/recovery, Phase 5 post-protein continuous digestion, Phase 6 upgrader recovery/slip and utilities, and Phase 7 flow-weighted digestate nutrient speciation and product compliance remain open collection priorities.

After this registration, the FAIR catalog indexes 672 assets and 897 normalized input records (624 source-linked assets, 512 DOI-linked assets, and 52 without a source-register join). Governance indexes 447 datasets, with 711 existing validation issues; the new six-row dataset remains reference-only and no datasets/defaults are active. These are indexing and governance counts, not completeness measures. Only the workbook's generated FAIR snapshot sheets were refreshed; named input sheets and existing precedence remain unchanged.

### Phase 5 — pilot brown-juice anaerobic-filter COD removal and unresolved methane metric (2026-11-08)

Added `Bigas production + upgrade/AD reactor/feng_2021_brown_juice_anaerobic_filter_abstract_reference.csv`, a two-row, DOI-linked extract from the abstract of Feng et al. (2021; DOI `10.1016/j.psep.2020.12.026`). It preserves the reported maximum of up to 80% influent-COD removal at 5.5-day HRT and the abstract's “specific CH production” value of 230 with its printed `mL gCOD^-1 d^-1` expression. The methane metric has no normalized value because the abstract-level dimensional and gas-species interpretation cannot be resolved safely. Pilot feed was grass-clover brown juice used without co-substrate; the study is not a GreenHub roadside-grass measurement.

The source register, local/global manifests, readiness record, sidecar, deterministic builder and focused tests are included. The extract remains B-tier D3/reference-only and is not connected to calculations. A secondary review attributes 409.6 L CH4/kg VS to Feng's continuous 5.5-day operation, but that figure is not substantiated by the primary abstract and matches the separately staged Green Valleys 90-day batch BMP value; it is excluded pending primary full-text reconciliation. No defaults, balances, routes, TEA/LCA values, or Pareto scenarios changed.

### Phases 1, 3 and 4 — clover-grass pilot feed, pressing and membrane-stream measurements (2026-11-08)

Added `Protein recovery/Membrane/clover_grass_membrane_stream_composition_and_conditions_echers_2026_reference.csv`, a 45-record extract from Echers et al. (2026; DOI `10.1039/D5FB00771B`) and the publisher SI. It includes Table 1 dry matter and crude-protein concentrations (including explicit not-recorded S2-permeate and diafiltration-permeate values), selected screw-press and two-stage membrane conditions, and text-reported pigment concentrations/depletion comparisons. Each record carries phase, process stage, stream, basis, source location, evidence class, uncertainty or missingness, and transfer limitations.

This is a single cultivated Danish clover-grass pilot batch, not roadside/VARTA feed. The table's n=2 and pigment triplicates are retained as analytical replication context, not treated as independent process campaigns. Stream concentrations and pigment depletion are not mass recoveries: paired stream flows and a closed water/DM/protein balance are absent. The reported 1:2 stabilizer ratio is preserved without assigning an uncertain numerator. DF C is a liquid concentrate (0.48% DM), not dried product. The source is CC BY-NC 3.0, so commercial reuse requires a rights review. The dataset is B-tier D3/reference-only with no runtime mapping, default, calculation, route, or Pareto change. Its builder and focused regression tests preserve these gates. Sources: [publisher article](https://doi.org/10.1039/D5FB00771B), [publisher supplementary information](https://www.rsc.org/suppdata/d5/fb/d5fb00771b/d5fb00771b1.pdf).

The new evidence modestly improves Phase 1 composition and Phases 3–4 process-condition/stream-quality coverage, but does not establish Dutch seasonal availability, press recovery, protein mass yield, membrane flux/rejection under GreenHub feed conditions, or product drying. Across Phases 1–7, the priority missing primary evidence remains local seasonal feed receipts and paired composition; storage inventories and loss/emission time series; component-resolved pretreatment and press balances; roadside-juice reagent titration and protein recovery; post-extraction residual BMP/continuous AD data; upgrading methane recovery/slip and utilities; and flow-weighted digestate nutrient speciation and compliance.

### Phase 2 — post-opening silage CO2/ethanol emission summaries (2026-11-08)

Added `storage/silage_feedout_co2_ethanol_emissions_shan_2026_abstract_reference.csv`, a six-record extract of the abstract from Shan et al. (2026; DOI `10.1016/j.jece.2026.121987`). Four records preserve the printed initial 0–10 h area-normalized CO2 and ethanol summaries for maize and ryegrass silage, including the reported ± terms without assigning an unsupported SD/SE interpretation. Two records preserve the approximate emission-signal lags during the aerobic-unstable period (about 40 h for maize and 100 h for ryegrass).

The experiment used 1.5-L cultivated-crop silage jars exposed to air, with and without a commercial additive. The abstract does not identify the statistic for the ± terms, replicate count, treatment aggregation, or a feed-mass denominator; the underlying time series are stated to be available on request. Values are therefore B-tier, abstract-only, D3, reference-only comparators. They are not normalized to GreenHub feed mass, fitted to storage kinetics, or connected to runtime/LCA calculations. This is evidence about post-opening feed-out, not sealed storage degradation, and it does not close the Dutch roadside-grass storage data gap. Sources: [publisher article](https://doi.org/10.1016/j.jece.2026.121987).

### Phase 1 — South Holland municipal mixed-green-waste spatial context (2026-11-08)

Added `Pre-treatment/Feedstock/pzh_municipal_green_waste_cbs_2022_reference.csv`, containing 50 municipality-level values from the provincial WFS attribute year 2022. The service values sum to 90,321 t/year and match the municipal table in the PZH biomass inventory report; the DataOverheid catalog description reports 76,084 t/year. The source-version/metadata discrepancy is recorded but not reconciled. These are CBS-derived municipal mixed-green-waste estimates, not measured roadside grass; no grass/verge fraction is separated. They remain B-tier, reference-only regional context, with no runtime/default or seasonal-availability use. Sources: [official WFS](https://geodata.zuid-holland.nl/geoserver/energie/wfs?service=WFS&version=2.0.0&request=GetCapabilities), [DataOverheid catalog](https://data.overheid.nl/en/dataset/0f08e50f-6483-4d62-8a29-16a049e5c5ec), [PZH report](https://circulair.zuid-holland.nl/wp-content/uploads/2021/12/Biomassa-reststromen-analyse-Zuid-Holland-eindverslag-V3-Robin-de-Roo.pdf). This improves regional context only; local contracted verge-grass quantities, harvest frequency, access constraints, seasonal delivery profiles, and paired composition remain missing.

### Phases 1–2 — open field-trial records for grass-clover yield and cut-level composition context (2026-11-08)

Imported the original three-file, CC0 DataverseNO package from Elshani et al. (dataset DOI `10.18710/F5Z8BR`; related article DOI `10.1016/j.scitotenv.2025.180373`) into `Pre-treatment/Feedstock/elshani_2025_grass_clover_field_data/`. The main semicolon CSV contains 192 treatment/location/year summaries from eight Norwegian field experiments conducted during 2009–2013, with three cuts per season, 0/80/160/240 kg N ha⁻¹ treatments, and 10/20% red-clover seed-mixture treatments. The linked location file supplies eight coordinate/soil records, joined by `Exp_no`. The original README reports DM yield in g m⁻² and encodes N-rate values as 0/8/16/24; it identifies `.` as missing and says analytical samples/yields were pooled or averaged over three replicates.

This is measured field-trial evidence published in the literature (B-tier), not roadside grass or a GreenHub feed-receipt sample. The source README does not define units for the crude-protein and clover columns, so those raw values are retained without conversion. The dataset is useful for harvested-cut and cultivated grass-clover comparison only; it cannot supply roadside availability, local seasonal collection, or GreenHub-specific composition. The package is CC0, byte-preserved with source MD5 checksums, registered locally and globally, and remains D3/reference-only with no runtime, default, UI, route, TEA/LCA, or Pareto connection. Sources: [DataverseNO dataset](https://doi.org/10.18710/F5Z8BR), [related article](https://doi.org/10.1016/j.scitotenv.2025.180373).

### Phases 1, 5 and 7 — field-grass yield, BMP and digestate-fertilisation response (2026-11-08)

Added `Bigas production + upgrade/Feed BMP/field_grass_digestate_fertilisation_yield_nutrients_bmp_jurgutis_2021_reference.csv`, a 205-row, long-form extract of Jurgutis et al. (2021; DOI `10.1016/j.biombioe.2021.106211`). It preserves fresh field yield under five digestate treatments and reported years/means; grass N/P/K, total solids and volatile solids; all ten treatment-year Table 5 BMP observations across biogas yield, methane fraction and two reported bases; separated solid/liquid digestate chemistry; selected soil response; and protocol/context records. Table/figure locations, source-reported units, uncertainty notation, treatment identity, checksum, source links and applicability limits are retained in the sidecar and local/global registers.

This is measured literature evidence (B), but it is from a Lithuanian semi-natural grassland dominated by switchgrass, not Dutch roadside/VARTA grass, and its full-scale digestate came from a mixed-feed digester. It is therefore D3/reference-only and has no runtime, default, route, TEA/LCA, or Pareto connection. Missing values are not imputed: Table 4 lacks a 2020 unfertilised-control TS/VS row. Two source inconsistencies are explicitly retained: methods place harvest in the first week of July while Results §3.3.1 says the second half of September; and the 85 kg N ha⁻¹ liquid-digestate mean yield is 10.10 in Figure 4 versus 10.11 in the results text. We did not select a canonical value. The table's ± terms are preserved without assigning SD/SE, and BMP gas reference conditions are not supplied in the extracted table. No open reuse license was identified; review before external redistribution. Sources: [article DOI](https://doi.org/10.1016/j.biombioe.2021.106211), [public institutional dissertation containing the article](https://www.lammc.lt/data/public/uploads/2021/11/lino-jurgucio-disertacija.pdf).

The Phase 1 value is a fertilizer-response yield, not natural roadside availability. Phase 5 is batch BMP, not GreenHub post-protein residual or continuous-digester performance. Phase 7 informs grass nutrient response and comparator digestate composition, but not GreenHub nutrient recovery, fertilizer grade, compliance, or substitution. The outstanding project evidence remains local delivered/collectable roadside tonnes with paired composition; roadside storage loss/emission time series; compatible GreenHub press/recovery balances; post-protein continuous AD data; upgrader recovery/utilities; and flow-weighted GreenHub digestate nutrient partition and product testing.

After source registration, the FAIR index contains 692 assets and 897 normalized input records (642 source-linked, 526 DOI-linked, 54 without a source-register join). Governance indexes 456 datasets, with 713 catalogued source issues; 62 remain blocked, 394 are reference-only, and none are active/default-eligible. The new extract is D3/reference-only; these are indexing/readiness counts, not a completeness score.

### Phases 1, 3 and 4 — full species/date-resolved screw-press fractionation evidence (2026-11-08)

Added `Pre-treatment/Mechanical/stodkilde_2021_species_harvest_press_fractionation_reference.csv`, a 300-row extract from Tables 1–5 of Stødkilde et al. (2021; DOI `10.1016/j.anifeedsci.2021.115016`; CC BY). It records five forage species × four spring first-cut dates, including fresh-feed DM/N/DM yield, single- and double-press pulp and protein-concentrate DM/N concentrations, and source-calculated N recovery to each fraction. Source pooled model SEM and significance groups are retained; the pooled SEM is explicitly not date-specific. The study used a laboratory twin-screw press, a second press after diluting 200 g pulp with 400 mL water, and juice-protein precipitation with 12 M phosphoric acid to pH 4. Acid volume, complete process water/component balances, energy use and residual-juice composition are not available.

This is B-tier measured research from cultivated Danish forage, not roadside/VARTA feed. It improves Phase 1 quality/maturity context and Phase 3–4 press partition/composition evidence, but N recovery is not saleable-protein recovery. The journal article expands an earlier ryegrass proceedings extract already in GreenHub; some overlapping recovery values differ, so publication-specific records remain separate and must not be pooled or averaged without reconciliation. Table values are least-square means, and species means are not forced to equal the arithmetic mean of the four displayed harvest means. The May 17 red-clover DM cell is rendered as `12.81` by the machine-readable PDF text layer; the extract records 128.1 with a dedicated OCR-reconciliation status because it matches the paper's four-date species LSmean (126.5). It remains D3/reference-only and does not change model parameters, defaults, calculations, UI overrides, routes, or scenario IDs.

The Alterra roadside dry-AD extract (156 rows) and Brandis full-scale PSA/LCA/LCCA comparator (49 rows) were also staged in this collection increment; their basis, mixed-feed, boundary, and transferability limitations remain explicit. Focused source/catalog/governance tests passed (26). Current FAIR counts are 723 assets/897 normalized input records (673 source-linked, 537 DOI-linked, 54 without a local source-register join). Governance indexes 467 datasets/checksums with 713 issues (62 blocked, 405 reference-only, zero active/default-eligible); equations remain 194 (184 blocked, 10 reference-only, zero active). The refreshed checkpoint reports `scientific_values_modified=false`.

### Phase 1 — provincial road-verge and ditch-bank management GIS (2026-11-08)

Retrieved the Province of Zuid-Holland public-domain `verkeer:ABS_W_GROEN` WFS layer (37,188 total management objects), then preserved the 16,358 features classified as `berm` or `slootkant` in `Pre-treatment/Feedstock/pzh_provincial_roadside_and_ditch_management_inventory_2026_reference.csv`. The subset retains the source feature IDs, road and road-segment references, type, mowing/frequency fields, management zone, owner/manager/maintenance-team text, and planimetric and slope-corrected area. The companion `pzh_provincial_roadside_and_ditch_management_by_frequency_2026_reference.csv` contains 29 derived groups.

The provincial layer reports 9,726 berm objects and 5,885,056.46 m² (588.51 ha) of slope-corrected managed area; it separately reports 6,632 ditch-bank objects and 1,752,562.27 m² (175.26 ha). The official catalog defines the area fields in m² and identifies the collection as public domain. The evidence is B-class official administrative information, not A-class project measurement: mowing-frequency codes are not actual event records, and the geometry inventory does not establish harvested mass, grass fraction, supplier access, contract availability, or plant deliveries. Ditch banks are not folded into roadside berm area. No conversion to tonnes, seasonal profile, runtime feed input, or default was made.

The builder records the WFS query/filter, retrieval timestamp, source feature count, stable catalog identifiers, field units, rights basis, limitations, and per-file SHA-256; source, local/global manifests and readiness registrations were added. Focused tests reconcile feature counts and corrected-area sums against the frequency aggregation. Priority Phase 1 evidence still required is executed, date-stamped mowing/removal plus weighbridge mass, moisture, route/contract availability and paired composition for project-relevant sites. This increment does not close the source-supply or Phase 2–7 mass-balance gaps and changes no scientific/runtime values.

After indexing, the FAIR catalog contains 729 assets and 897 normalized input records (679 source-linked, 539 DOI-linked, 54 without a local source-register join). The new administrative feature data are included as discoverable reference assets, not normalized simulation parameters.

### Phases 1, 5 and 6 — additional Dutch roadside-grass source screening (2026-11-08)

Screened the Province of Drenthe's official mowing page. It reports a June 1–30 safety cut limited to a 1.50 m verge strip, a September 1–October 31 full-verge cut, and an estimated 150,000 m³/year of green gas from processed verge cuttings. It also says part of the annual cuttings is available to local businesses. These are useful cross-province management and product-output comparators, not GreenHub measurements: no feed mass, wet/dry basis, collection fraction, plant boundary, reference period, gas reference conditions, methane fraction, or metered output is supplied. The source is therefore not converted to a yield or activated. Source: [Province of Drenthe, Maaien bermen](https://www.provincie.drenthe.nl/onderwerpen/verkeer-en-vervoer/wegen/maaien-bermen/).

The HDSR 2019 announcement confirms a six-month pilot intended to digest roadside grass without manure and to measure gas yield/quality plus digestate quantity/composition. The public announcement contains no pilot results. This is a high-value project-specific retrieval lead for Phases 1, 5 and 7; the underlying weighbridge, process, gas-meter and lab records would need to be obtained from the partners, rather than reconstructed from the announcement. Source: [HDSR, “Van bermgras tot biogas”](https://www.hdsr.nl/@86208/praktijkproef/).

### Phase 7 — raw digestate database access and reuse gate (2026-11-08)

The Ferti-Dig dataset associated with Caradec et al. (2025; article DOI `10.1016/j.dib.2025.111550`) contains 608 French plant digestate observations and 198 literature observations, with physicochemical properties, process metadata, contaminants and agronomic indicators. The existing GreenHub package stages the article's aggregate summary only. The raw Recherche Data Gouv package (`10.57745/M1JSU5`, latest files identified by `_20241220`) is governed by custom terms for research/teaching/policy support, non-commercial use, attribution and download notification; one file is restricted. No raw data were copied in this screen. A future download requires confirming the intended GreenHub use fits those terms and completing the stated notification; it must not be treated as unrestricted CC-BY data. Source: [dataset record](https://doi.org/10.57745/M1JSU5), [open-access data article](https://doi.org/10.1016/j.dib.2025.111550).

Also screened the Irish Grass Clover Dataset (VistaMilk; DOI `10.5281/zenodo.14191859`). Its field ground-truth includes harvested dry herbage mass and grass/clover/weed fractions, but it is cultivated Moorepark pasture, not roadside grass; the full deposit is 10.3 GB of imagery and carries CC BY-NC-SA 4.0 terms. It was not downloaded or used as a GreenHub feed profile. Source: [Zenodo record](https://doi.org/10.5281/zenodo.14191859).

These screens add source-discovery leads, not new model inputs. Current direct-data priorities remain executed GreenHub cut/load receipts with paired composition; matched storage start/end inventories and emissions; same-batch pretreatment and press balances; juice titration/recovery; residual-specific continuous digestion; paired upgrader gas/utility measurements; and flow-weighted digestate nutrient and contaminant analyses. No scientific values, default inputs, UI/API behavior, routes, scenario IDs, or Pareto outputs were changed.

### Phases 1–2 — regional harvested-grass inventory and farm-scale silage-loss comparator (2026-11-08)

Added `Pre-treatment/Feedstock/monbio_2023_flanders_roadside_grass_inventory_reference.csv`, a five-row, short factual extract of Table 27 in the ILVO/VITO MONBIO 2.0 report. The reported Flemish roadside-grass subtotal is 72,032 t DM/year across AWV (17,809), municipalities (44,527), De Vlaamse Waterweg (6,798), and Infrabel (2,898). The associated managed area is reported by actor, but the table does not give a total roadside area. Methods and source periods are retained per actor: AWV ticket/invoice fresh weights converted using a 50% factor; 257-municipality 2010 data extrapolated to Flanders; 2008 Waterway data; and a modeled railway estimate using assumed verge width and yield. The aggregate is therefore a mixed-year, mixed-method inventory—not a single-year measured delivery total, current Netherlands supply, or GreenHub default. It is C-tier and reference-only; no mass, seasonal profile or model parameter is inferred. No explicit open-reuse license was identified, so the repository stores only a concise factual extract with attribution, not the report.

Added `storage/koehler_2013_farm_scale_grass_bunker_silo_storage_reference.csv`, a 13-row extract of the reported grass subset in Köhler et al. (2013; DOI `10.23986/afsci.6715`). It records 26 grass silos, mean DM loss 9%, reported range −2% to 26%, density/feed-out summaries, corresponding Pearson correlations, at least six weeks sealed, and average three-month feed-out. The source explicitly attributes negative calculated loss to measurement/accounting precision; it is retained for audit only and must not be treated as physical mass gain. Total-in/total-out spans ensiling/storage and feed-out, so the 9% is not a storage-only degradation coefficient or a duration curve. The German farm silos are not Dutch roadside material or GreenHub storage. This is B-tier, D3/reference-only, with no default activation. The source is copyrighted and no open reuse license was confirmed; only a concise factual summary is stored with attribution.

Both extracts have deterministic builders, source sidecars, local/global source-register and manifest rows, checksums, and focused tests. They add regional context and a farm-scale comparator, but do not close the project’s Phase 1 gaps (current site contracts, harvest/delivered mass, paired moisture/composition and collection availability) or Phase 2 gaps (GreenHub storage inventory, leachate, emissions, composition/protein quality through time, and condition-specific loss kinetics). No model inputs, runtime parameters, defaults, balances, or scenario outputs were changed.

### Phase 4 — lucerne pulp water re-pressing nitrogen outcomes (2026-11-08)

Added `Protein recovery/Isoelectric/nynas_2026_lucerne_second_press_water_dilution_reference.csv`, a 63-record extract of Table 3A from Nynäs et al. (2026; DOI `10.1016/j.jafr.2026.102842`). It covers fresh and frozen lucerne pulp re-pressed after water dilution at 1:1 and 1:2 w/w, plus five frozen-pulp soaking-time/temperature conditions. Source-reported N concentrations and N-flow means, SDs, significance groups, and n=3 are retained. Hour durations are normalized to minutes; the “ice” temperature remains categorical rather than receiving an invented numeric value. The soluble-associated nitrogen flow is the authors' difference calculation; it is not direct isolated-protein mass or a true-protein recovery factor.

The final article is CC BY 4.0 according to the Swedish University of Agricultural Sciences repository record. This cultivated-lucerne, lab-scale secondary-press experiment is a relevant process comparator, but not Dutch roadside/VARTA feed and not a calibration of GreenHub's current single-press route. The dataset is B-tier, D3/reference-only; no runtime parameter or default changed. Its sidecar contains the DOI, repository and full-text links, table location, retrieval date, license, checksum, extraction scope, uncertainty, and transfer limitations.

### Phase 1 — 2017 Flemish GR3 mowing-supply inventory (2026-11-08)

Added `Pre-treatment/Feedstock/ovam_2017_gr3_flanders_mowing_supply_inventory_reference.csv`, a 17-record transcription of OVAM's GR3 Table 36 and its separately identified Natuurpunt footnote. It preserves managed grassland versus road-verge actor rows, reported subtotals, area, DM yield, and annual dry/fresh mass. The report derives fresh mass using 27% DM and warns that estimated areas may not all be mown and some cuttings may remain in place. The displayed grassland actor rows sum to 26,554 t DM/y while the printed grassland subtotal is 26,553; this unexplained 1 t difference is retained. The complete actor rows sum to the printed overall 61,438 t DM/y total.

The report permits reuse with clear citation (printed p. 6); the sidecar records the report URL, supporting-data DOI `10.5518/1154`, table/page, retrieval date, checksum, and reuse basis. This is a B-tier historical Flemish estimate—not current Dutch delivered supply, not GreenHub site data, and not directly mergeable with MONBIO 2.0's mixed-year inventory. It is cataloged as D3/reference-only and has no runtime parameter mapping. No default, route, balance, or scenario output changed.

### Phases 5–7 — underlying biogas-plant methane-emission measurements (2026-11-08)

Added the source-verbatim Zenodo v2 package for Wechselberger et al. (2023): 294 data records across 32 fields, its 32-variable glossary, and the authors' R Markdown summary code. The CSV checksum matches the Zenodo record; its Windows-1252 encoding and source `NA` tokens are retained without conversion. The dataset includes substrate-reception/storage, biogas-production, utilization, and miscellaneous plant-stage records; the article describes harmonized on-site measurements at 33 plants across Austria, Germany, Sweden and Switzerland. The data include both primary and secondary observations, with row-level citations in the original file.

This raw package complements (does not duplicate or replace) GreenHub's existing 11-row Table 2 aggregate extract. Zenodo v2 says the data are unchanged from v1; CC BY 4.0 is recorded on the v1 source record. The primary harmonized campaign covers Austria, Germany, Sweden and Switzerland; the combined file also retains secondary observations from Canada and Denmark, as identified by its row-level citations. Because substrates and technologies vary, these observations are reference-only for Phase 5 AD emissions, Phase 6 utilization/upgrading leakage, and Phase 7 digestate-storage emissions—not grass-specific factors, GreenHub calibration, probability distributions, or runtime defaults. Raw data, glossary, code, rights/version caveat, checksums and source-register links are indexed separately; no model result changed.

### Phases 1–3 and 5 — GR3 Belgian roadside/nature-grass case evidence (2026-11-08)

Added a 16-record extract from the GR3 final report's Noord Limburg and Brussels Airport cases (Laub et al., 2016; printed pp. 25 and 27). It captures historical annual fresh-grass estimates and disposal rates, the stated yield basis for the Noord Limburg supply estimate, seasonal spring/autumn digestion observations, ensiling and particle-size guidance, approximate grass dry matter, a reported biogas-per-fresh-tonne range, and airport mowing seasonality/haul distance. Every row labels whether it is an estimate, case-reported rate, qualitative pilot observation, operating guidance, or case calculation. The source's printed `<1 mm` wet-digester size guidance is preserved verbatim but explicitly flagged for source verification; the biogas range is not interpreted as methane yield because methane fraction and gas reference conditions are absent.

This B-tier historical Belgian project-report extract has no identified open license, so the report is not redistributed and no license is claimed. It is D3/reference-only, not Dutch availability, a GreenHub route factor, current price, or runtime default. The exact 16-row file, per-record page locations, source wording, rights caveat, source registers and checksum are recorded; no model defaults or results changed.

### Phase 2 — roadside-cutting field-delay model and composition regressions (2026-11-08)

Added `Pre-treatment/Feedstock/roadside_cutting_field_decay_schaffers_1998_tables4_5_reference.csv` with 92 records transcribed from Tables 4–5 of Schaffers, Vesseur & Sýkora (1998; DOI `10.1046/j.1365-2664.1998.00316.x`). Table 4 stores model-estimated community-level remaining fractions for dry mass, N, P and K through six weeks, asymptotes and fitted rate constants. Table 5 stores the reported composition-regression coefficients, R² and p-values. The rows complement the existing plot-level Table 1/3 extract and remain reference-only.

This is Dutch fresh-cut litterbag field-delay evidence, not ensiling or storage. Table 4 values are model-estimated community means rather than replicate observations. The article explicitly flags extrapolation risk for high-C:N nitrogen predictions and says the potassium regressions are weak/nonsignificant, with no satisfactory asymptotic fit. These limitations are stored per row and in the sidecar; no equation/default or GreenHub storage kinetics were activated.
### Phase 1/3/4 — Kurhan et al. (2025) University of Bath source workbooks (2026-11-08)

Preserved four unchanged CC BY 4.0 source workbooks from the University of Bath Research Data Archive (dataset DOI `10.15125/BATH-01534`; associated article DOI `10.1098/rstb.2024.0161`) under `Greenhub/data/Pre-treatment/Mechanical/kurhan_2025_biorefinery_reference/`. The archive describes silage dry matter/ash, carbon/nitrogen, amino acids and B vitamins; amino-acid comparisons before/after extraction; and twin-screw extruder response-surface and single-factor data. A generated 10-sheet inventory records sheet scope and dimensions, populated-cell counts, and formula/cached-result counts. A second CSV transcribes all 5,804 nonempty workbook cells with original workbook/sheet/cell references; all 1,224 formula expressions and cached outputs are separate. The original workbooks remain unchanged.

This adds discoverable primary research evidence for feed chemistry and a mechanochemical extraction comparator. The material is UK pasture silage, not Dutch roadside/VARTA grass, and the extruder is not GreenHub's existing screw-press/isoelectric route. The RSM workbook appears to contain a factor-label/operating-setting mismatch, which is explicitly flagged for source-paper verification. The workbooks and derived inventory/cell transcription are B/reference-only, D3, and not calculation-connected; no defaults, parameter registry entries, process chemistry, scenario IDs, or outputs changed. Source sidecars, local/global registers, checksums, FAIR catalog entries, and focused regression tests were added.

### Phase 1 — Polish spatial roadside-supply and collection-capacity comparator (2026-11-08)

Added two reference-only extracts from Duczkowska et al. (2026; DOI `10.3390/en19174185`): 35 long-form municipality/metric rows from Table 2 and three capacity-allocation outcomes (southern-center capacities of 3000 t, 5000 t and equal 5875 t per center, associated with 25, 36 and 41 assigned nodes). Table 2 values are transcribed as published; only mowed-mass Gg/a is additionally expressed as t/a using 1 Gg = 1000 t. The paired cases retain positional A/B labels because named scenario and wet/dry basis are not safely established. This is a Polish spatial-planning comparator, not Dutch supply evidence.

The article estimates are derived from road/mowing records, aerial eligibility screening and stated assumptions; they were not validated by field measurement. The source does not provide node-level road data in the cited extract. The CC BY 4.0 statement is linked to the Opole University institutional record. Records are B-tier published scenario evidence, D3/reference-only, and not connected to GreenHub parameters, site availability, logistics costs or route configuration. Capacity values for the other center in the 3000 t and 5000 t cases are not given in the cited source locations and remain blank. No defaults or model outputs changed.

### Phases 2 and 4 — wet green-protein paste storage quality (2026-11-08)

Added `storage/wet_green_protein_paste_storage_santamaria_stodkilde_2019_2021_reference.csv` as a compact reference package from an Aarhus University pilot report and an OK-Net EcoFeed practice abstract. It records initial wet-paste DM/OM for alfalfa, red clover and ryegrass; two reported 12-month pH endpoints; clover-grass concentrate initial DM/protein/methionine/lysine; tested storage design; and the abstract's author-reported maximum stable durations of 2 months at 24 °C and 3 months at 4 °C. Only values stated in prose were transcribed; plotted points were not digitized and no kinetic curve or stability threshold was inferred.

This is extracted-product storage evidence, not raw roadside-grass storage or GreenHub product validation. The abstract does not define the acceptance criterion for “stable,” and uncertainty and replicate counts are not supplied for its reported values. Neither source identifies an explicit data-reuse license. The source PDFs are not vendored; the compact extract is B-class/D3/reference-only, and rights review is required before external redistribution. The 2017 report's bag-count statement does not reconcile with its stated per-condition/time/crop bag count; that inconsistency is recorded rather than used to assert a replicate n. No runtime parameters, equations, defaults, balances, TEA/LCA values, or Pareto outputs changed.

### Phase 2 — Jinmu grass ensiling quality time series (2026-11-08)

Added `Greenhub/data/storage/jinmu_grain_grass_silage_storage_time_tang_2025_reference.csv` (72 records) from Tang et al. (2025; DOI [`10.3390/microorganisms13091973`](https://doi.org/10.3390/microorganisms13091973), CC BY 4.0). Tables 1–2 provide storage-time means, SEM, p-values and significance letters at 0, 3, 7, 15, 30 and 60 days. Table 2 covers pH, NH3-N/TN and lactic, acetic, propionic and butyric acids. Table 1 composition metrics are also retained, but because the table omits their units/bases they are explicitly marked unknown rather than interpreted by convention. The experiment sampled five vacuum bags at each time point; storage temperature and experiment year are not reported.

The source material is cultivated Jinmu/Pennisetum forage from Xinjiang, China, not Dutch roadside/VARTA feed. It offers a useful measured fermentation comparator but no whole-storage mass-loss, leachate or emission balance. Concentration trends are not converted to retention rates or kinetics. The data are B-tier, D3/reference-only and not mapped to runtime parameters, defaults or Pareto scenarios. Source methods, values, license, extraction policy, limitations, checksum, manifests and FAIR-catalog linkage are recorded. No model chemistry, route, scenario ID, UI/API contract or result changed.

### Phases 3–4 — Trojan ryegrass GPC yield, product composition and process conditions (2026-11-08)

Added `Greenhub/data/Protein recovery/Isoelectric/kaur_2021_trojan_ryegrass_gpc_yield_composition_and_protocol_reference.csv` (31 records) from Kaur et al. (2021; DOI [`10.3390/foods10020331`](https://doi.org/10.3390/foods10020331), CC BY 4.0). It preserves the approximate acid-route powder yield (2.22% of fresh-grass mass), enzyme-route powder yield (11% of dry-grass mass), the article's approximate 85% protein-recovery statement, Table 1 proximate/mineral composition, and the reported wet-disintegration, precipitation and enzyme conditions. The two route yields have different denominators and are not compared as equivalent efficiencies.

Protein was measured by Kjeldahl using N × 5.83. Table 1 does not further identify the basis for all product composition values and those bases are left unresolved; categories are not a closed mass balance. The chemical route uses NaOH and repeated pressing; it is not GreenHub's existing route. The study does not provide an acid dose/titration curve, full stream/component balance, centrifuge capture conditions, or drying energy; enzyme-route water additions lack a feed batch mass for normalization. This is cultivated New Zealand ryegrass, not roadside/VARTA feed, and freeze drying is not spray drying. The data remain B-tier/D3/reference-only, with no parameter, default, TEA/LCA value, or Pareto scenario activated.

### Phases 2–4 — cultivated-grass ensiling and protein-quality time series (2026-11-08)

Added `storage/cultivated_ryegrass_festulolium_ensiling_proteolysis_muhandiram_2023_reference.csv` (264 long-form records) from Muhandiram et al. (2023; DOI [`10.1002/fes3.475`](https://doi.org/10.1002/fes3.475), CC BY 4.0). It transcribes Tables 1–3: fresh forage before wilting and Cut 2/Cut 4 laboratory ensiling observations for DM, pH, water-soluble carbohydrates, total N, soluble N and ammonia-N at 0 h, 9 h, 1, 2, 3, 14 and 90 days. The extract keeps the two cultivars and harvest cuts separate, preserves pooled time means, means across time, factorial SEMs/p-values and source significance annotations, and converts day labels to elapsed hours only by 24 h/day for sorting.

The experiment used cultivated Aberystwyth ryegrass and Festulolium harvested in 2016, 24-hour wilting, *Lactobacillus plantarum* inoculation, 30 mm target chop, and triplicate 100 g laboratory tube silos at 21 °C. The table gives measured concentrations/pH, not total mass retention, leachate, emissions or a closed nitrogen/protein balance; no kinetics or storage-loss rates are fitted. This is B-tier measured literature evidence and D3/reference-only, not Dutch roadside/VARTA calibration or a runtime parameter. No process, TEA/LCA, defaults or Pareto values changed.

### Phase 2 — Paiaguás silage storage losses, effluent and composition (2026-11-08)

Added `storage/paiaguas_grass_silage_storage_loss_effluent_saute_2021_reference.csv` (114 records) from Saute et al. (2021; DOI [10.1590/1678-4162-12197](https://doi.org/10.1590/1678-4162-12197)). The extract transcribes Tables 2–4 marginal means for 90-day dry-matter loss, effluent loss/production and quality, silage chemistry/digestibility by theoretical particle size and compaction density; it also retains five initial-forage values and the paper's stated `<2 °C` temperature-rise bound during 216 h of aerobic exposure. The journal reports CC BY 4.0. The source DOI identifies the article; the derivative table has a repository-local URN and checksum.

This is measured literature evidence from cultivated tropical *Brachiaria brizantha* in 13 L laboratory silos in Paraná, not Dutch roadside/VARTA grass. The factorial paper reports marginal means, not the nine treatment cells; no interaction cells or Figure 2 points were inferred. COD/BOD units and percentage/tonne denominators that are unclear in the paper are preserved as printed and flagged. The extract is B-tier, reference-only and not connected to runtime parameters, defaults or scenarios. It adds a Phase 2 storage comparator, not a validated roadside storage equation.

### Phase 6 — measured membrane-upgrader energy and controlled methane slip (2026-11-08)

Added `Bigas production + upgrade/Membrane/variable_methane_feed_membrane_upgrading_energy_slip_buivydas_2024_reference.csv` (24 records) from Buivydas, Navickas and Venslauskas (2024; DOI [10.3390/su16083323](https://doi.org/10.3390/su16083323), CC BY 4.0). Tables 1–2 report four cases at 50%, 60%, 70% and 80% inlet methane, including upgrader flow, electricity-consumption rate, biomethane flow and methane purity, plus methane slip and reported deviations. The dataset adds measured Phase 6 evidence, not a GreenHub-specific performance factor.

The inlet was blended with recycled upgraded gas to change methane concentration, while the reported 35 Nm³/h is the blended upgrader inlet—not net digester biogas. The slip value was held at a control limit of 0.5% of inlet methane; it must not be mistaken for an uncontrolled membrane-loss curve. The tables do not identify whether “deviation” means SD, SE or another statistic, and their `% vol` slip label is not reconciled with the methods denominator; those ambiguities are retained. Records remain B-tier/reference-only. No runtime parameter, default, equation, unit balance, TEA/LCA factor or Pareto scenario changed.

### Phases 3–5 — alfalfa fractionation, acid/heat precipitation and pulp side-stream observations (2026-11-08)

Added `Protein recovery/Isoelectric/alfalfa_green_biorefinery_press_and_precipitation_zhou_2023_reference.csv` (56 records) from Fa Zhou's 2023 DTU doctoral thesis. The extract covers Table 1.2 treatment outcomes for 1 M HCl, 1 M lactic acid and heat treatment, plus the §4.4.6/Figure 4.6 alfalfa wet-fractionation batch, acid-solution addition, protein-pellet labels, brown-juice volume, and selected pulp/brown-juice sugar and lignin masses. Table 1.2 reports mean and standard deviation of technical replicates, but the extracted thesis does not state the replicate count; the dataset preserves that uncertainty metadata as missing.

This is cultivated-alfalfa comparator evidence, not roadside/VARTA grass or a GreenHub operating recipe. The 135.7 g value is the mass of 1 M HCl solution in one batch—not pure acid mass and not a normalized demand. The prose reports feed water content of 85.6%, while Figure 4.6 reports 177.2 g DM per 1000 g feed; these conflict and are retained separately. Likewise, 193.0 g wet protein pellet in prose/theoretical figure labels differs from the figure's 186.2 g actual value. Source-table dashes remain nonnumeric and are not treated as zero. No source reuse license was identified, so redistribution rights require review. Records are B-tier, D3/reference-only; no parameter, default, equation, route chemistry, TEA/LCA factor, or Pareto output changed. The reproducible builder, sidecar, local/global source registers, manifests, checksums, FAIR catalog entry, and focused regression test are included.

### Phase 5 — alfalfa press-residue sugar platform and brown-juice fermentation (2026-11-08)

Added `Pre-treatment/Thermal_Enzymatic/alfalfa_press_residue_sugar_platform_zhou_2024_abstract_reference.csv` (16 records) from Zhou et al. (2024; DOI [`10.1016/j.indcrop.2023.117927`](https://doi.org/10.1016/j.indcrop.2023.117927)). The abstract reports sodium-chlorite delignification and glucan/xylan retention, cellulase loading and hydrolysis time/conversion, hydrolysate glucose/xylose concentrations, and lactic-acid concentrations from brown-juice fermentation with and without pulp-hydrolysate supplementation. The supplement endpoints are retained as the abstract links them (15% v/v → 17.4 g/L; 70% v/v → 28.8 g/L).

This is a peer-reviewed article but an abstract-only transcription: the record does not expose replicate count, uncertainty, complete balance, utilities, or the percentage basis for the 6% sodium-chlorite treatment. It is cultivated alfalfa and a sugar-fermentation residual pathway, not GreenHub roadside grass or the currently configured post-protein AD route. No explicit reuse license was identified on the DTU record; publisher terms require review before redistribution. Records are B-tier/D3/reference-only; no route, parameter, default, TEA/LCA factor or Pareto output changed.

### Phase 1–7 collection checkpoint (2026-11-08)

The current collection contains separate evidence packages across all seven stages, but the best public comparators do not replace GreenHub operating records. Phase 1 has Dutch road-verge area/management data and measured roadside biomass studies; the recent Bakker 2026 Dutch mowing study's 120 observations were verified as already staged, avoiding duplication. Phase 2 has several storage-time and loss/composition comparators, but no paired GreenHub inventory/emissions series. Phases 3–4 now include press-stream composition and precipitation data from cultivated forages, plus the new DTU alfalfa batch extract; no source establishes normalized acid demand or GreenHub press/protein capture. Phase 5 has roadside and green-biorefinery BMP/AD comparators, but no matched continuous reactor run on GreenHub's post-protein residuals. Phase 6 has multiple upgrader comparators, but not a matched raw-gas composition, flow, recovery/slip and utility dataset for the selected GreenHub route. Phase 7 includes roadside press-liquid fertilizer screening and digestate/nutrient-recovery analogues; actual GreenHub digestate nutrient speciation, separation partition, product quality and field-use response remain unmeasured. The next highest-value collection is therefore one linked GreenHub campaign: cut/receipt and feed assays; storage inventory; unit-level press/precipitation masses, titration and energy; residual BMP/continuous AD; raw/product gas and utility meters; and flow-weighted digestate/centrate analyses. Public-source screening should continue for useful comparators, but no proxy should be relabelled as project measurement.

### Phases 1, 3 and 5 — alfalfa press, pretreatment and fermentation tables (2026-11-08)

Added `Pre-treatment/Thermal_Enzymatic/alfalfa_sodium_chlorite_and_sugar_fermentation_tables_zhou_2023_reference.csv` with 207 records from Zhou's DTU thesis: Table 4.1 raw/pressed-feed assays and pulp recovery by pressing stage (Phase 1/3); Table 4.2 dose-response measurements at 0–10% sodium chlorite, including composition, solid recovery, component losses, delignification/deacetylation and color (Phase 3); Tables 4.3–4.4 sugar use, lactic/acetic acid and ethanol for six brown-juice/hydrolysate mixtures under two distinct fermentation configurations (Phase 5). Published means, SDs, Fisher-LSD groups, units, source conditions and table/page locations are retained. Six Table 4.2 `na` cells and the Table 4.1 recovery dash remain explicit and are not interpreted as zero; the three Table 4.1 temperatures remain source ranges. The thesis says results used at least biological replicates but does not report exact n.

This dataset is a B-tier, D3 reference comparator for cultivated alfalfa, not GreenHub roadside grass. The 14 h sealed-bottle and 48 h shake-flask fermentation runs are kept separate and are not continuous-process or AD results. The related peer-reviewed article DOI is linked, but no reuse license for the thesis-table transcription was identified. The dataset, sidecar, local/global source and readiness registers, checksum, activation matrix and FAIR index are updated; it remains reference-only, with no parameter, process calculation, default, workbook, UI, TEA/LCA or Pareto result changed. The currently uncommitted master workbook was left untouched to avoid overwriting its existing edits; the FAIR catalog files were refreshed independently.

### Phases 1 and 3 — expanded Smit roadside-grass characterization and provenance repair (2026-11-08)

Registered 13 additional records from Table 1 of Smit et al. (2022; DOI [10.1021/acssuschemeng.2c00838](https://doi.org/10.1021/acssuschemeng.2c00838); [open TNO-hosted article](https://publications.tno.nl/publication/34639501/OO02n8/smit-2022-biomass.pdf)): water- and acetone-soluble extractives; glucan; xylan, arabinan, galactan, mannan and rhamnan; total AIL+ASL lignin; ash; liquor-absorbing capacity; and acid-neutralizing capacity. A 24.0% hemicellulose total is stored as a transparent sum of the five reported polymeric sugars, not as an independent measurement. The combined composition file now contains 200 records: 138 direct observations, 15 indirect comparators, one derived record, and 46 explicit missing records.

The Table 1 sample is a roadside-grass comparator, not Dutch GreenHub/VARTA feed. The table reports `% w/w` but does not repeat its basis row-by-row; the dry-basis normalization follows the adjacent composition section/Figure 2 and is flagged as an interpretation. Location, season and row-level uncertainty remain unreported. The additions are B-tier reference evidence only; no feed default or runtime parameter was changed. The FAIR catalog and source manifests were refreshed. During that refresh, local article/dataset source IDs were reconciled for the Bakker mowing study, the missing local MooV/VITO source link was added, and Zeeland estimate records now retain the source URL while statistical uncertainty is explicitly marked as unquantified. Local/global source-register row counts and checksums were synchronized. Targeted Smit, FAIR-catalog and source-link regression tests pass; the broader process suite was not run in this data-only increment.

### Phase 2 — pilot wet-lowland grass-silage storage losses (2026-11-08)

Added `storage/wet_lowland_grass_silage_storage_losses_kristensen_feng_moller_2016_reference.csv` with 72 records from Kristensen, Feng and Møller (2016), Tables 1–3. The source reports wet-mass loss and dry-matter loss for tall fescue, Festulolium and reed canary grass after 144, 223 and 304 days, for no-additive, Sill-All Fireguard and Biotal Axcool Gold treatments. Source-reported across-species averages are retained separately from species-level table values. Methods describe three 60 L airtight barrels per species/treatment/duration, chopped to a theoretical 10 mm and manually compressed. Initial moisture values and table/page locations are recorded.

The paper does not report dispersion statistics or define the denominator/calculation for its table percentages. Small negative mass-loss values are retained as printed; the authors discuss weighing accuracy and moisture increases, so these are not interpreted as biomass gain. The grass was cultivated on wet Danish peatland and is not roadside/VARTA material. No kinetic fit, emission allocation, runtime input, or default was inferred. The public Aarhus University source record and full paper are linked, but an explicit data-reuse license was not found. The dataset, sidecar, local/global registers, manifest, checksum, activation matrix, FAIR catalog entry and focused test were added; status is B/D3/reference-only.

### Phases 1–2 — low-dry-matter grass-clover silage loss and density data (2026-11-08)

Added `storage/grass_silage_storage_system_losses_randby_bakken_2021_reference.csv` with 67 traceable records from Randby and Bakken (2021; DOI [`10.1016/j.anifeedsci.2021.114868`](https://doi.org/10.1016/j.anifeedsci.2021.114868); open-access CC BY 4.0). The extract includes the article's reported crop-DM lows for three 2017 harvests, bunker-versus-bale density comparisons, and Table 3 treatment means for offered silage, wasted silage and combined invisible losses. Both `g/kg crop` and `g/kg crop DM` bases are retained separately, along with the printed group SEMs, treatment labels and replicate counts. A data test checks that each Table 3 offered/wasted/invisible set closes to 1000 within source rounding.

This is a cultivated Norwegian grass-clover comparator, not Dutch roadside/VARTA or GreenHub material. Invisible losses combine respiration, effluent, fermentation, aerobic deterioration and gaseous losses; no pathway allocation is inferred. Round-bale losses include the authors' estimated effluent correction, and the pooled treatment rows do not provide one common numeric storage duration. The dataset is registered B/D3, reference-only, and not connected to storage kinetics, process defaults, TEA/LCA or Pareto calculations. The storage README, local/global source registers, manifests, checksum and activation matrix were updated. No workbook, model equation, scenario ID, UI/API contract or baseline result was changed.

### Phase 1 — Copernicus mowing-event and mowing-date acquisition leads (2026-11-08)

Registered the official CLMS GRAME and GRAMD products in the feedstock source register, including separate DOIs, official metadata/product links, access route, use conditions and limitations. GRAME classifies annual mowing-event counts and provides a confidence layer; GRAMD provides four event-date layers with day-of-year values. Product documentation describes 10 m annual rasters over EEA38 and a 0.25 ha minimum mapping unit. The official CLMS release notice confirms 2022–2023 mowing datasets were released in December 2025; the EEA metadata record also exposes older service vintages, so the exact usable year set must be verified when extracting.

This is source discovery and metadata registration only: no raster payload or pixel-derived observations were imported, and no value was added to seasonal supply or model defaults. These satellite products map detected mowing on herbaceous cover, not roadside verges specifically, grass yield, material removal, collection, contracts or access. Their minimum mapping unit may omit narrow roadside strips. A valid Phase 1 analysis would require matched verge geometries and local field/weighbridge measurements to translate event timing into available mass. The sources are openly reusable subject to Copernicus attribution/modification notices. The source-register changes and checksums are in the local/global catalogs; no model or UI behavior changed.

Sources: GRAME DOI [10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9](https://doi.org/10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9), GRAMD DOI [10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0](https://doi.org/10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0), [CLMS product page](https://land.copernicus.eu/en/products/high-resolution-layer-grasslands?tab=grassland_mowing_events), [EEA metadata record](https://www.eea.europa.eu/en/datahub/datahubitem-view/69a59cd8-d22f-4b76-a672-867ce92e1855), and [2022–2023 release notice](https://land.copernicus.eu/en/news/hrl-grasslands-releases-new-mowing-datasets).

### Phase 3–7 platform catalog and measurement collection plan (2026-11-09)

Registered four open, primary-literature comparators: Hansen et al. (2022)
alfalfa screw pressing, Lin et al. (2020) pasture-grass extraction, Brown et al.
(2022) grass HTC process-water BMP, and Hoyos et al. (2026) pilot carbonate gas
upgrading. They are linked to the new technology-family vocabulary, retain
source table/section locators and reuse licenses, and remain reference-only.
None is a matched GreenHub measurement or activated model parameter.

The normalized Phase 3–7 reuse catalog indexes 487 dataset assets and 538
canonical runtime inputs. It explicitly separates context-independent data
(none of the current empirical assets qualify) from technology, material, and
site-dependent evidence. Its per-source metadata gaps remain visible. The
runtime input quality distribution has not changed: Phase 3 has 69 D records,
Phase 4 has 80 D, Phase 5 has 81 D, Phase 6 has 10 B and 164 D, and Phase 7 has
134 D. Those counts describe the canonical phase-input registry, not the
separate shared UI/backend feed-composition profile. No workbook-registry value
was promoted in this catalog build; the UI profile updates are recorded below.

A FAIR-indexing correction now reads both `dataset.source.json` and legacy
`dataset.csv.source.json` sidecars; blank global-register fields no longer mask
non-empty sidecar metadata. After rebuilding the catalog, 435 assets still have
at least one provenance gap, 122 have no linked source record, and 151 lack a
DOI or stable identifier. Those groups overlap. The digestate recovery
comparator by Trotta et al. (2023; DOI
[`10.1016/j.rineng.2023.101478`](https://doi.org/10.1016/j.rineng.2023.101478))
is now explicitly linked to both anaerobic digestion and NPK recovery. Its
article states CC BY 4.0 on page 1; the sidecar records the table/page locators
and clarifies that assay triplicates do not establish the number of independent
process-run replicates. It remains reference-only. An exact duplicate row in
its local manifest was removed; no data values or process defaults changed.

Also added the open Hafner et al. (2026) interlaboratory BMP validation extract:
619 author-calculated bottle records from six reference substrates and 31 labs,
preserving the published `mL CH4/g substrate VS added` basis. The repository's
CC BY 4.0 license, article DOI, exact file locator, methods scope and
uncertainty limitation are indexed. It is tagged as technology-specific assay
validation and reference-only—not as a grass BMP value, process yield, or
runtime input. The Phase 3–7 input count and all runtime quality classes remain
unchanged; no D4 promotion was made.

The concise measurement checklist is stored in
`Greenhub/data/platform/catalogs/phase_3_7_measurement_acquisition_register.csv`
and its Excel version under `outputs/`. It covers matched feed/stream assays,
unit settings and utilities, protein recovery/product quality, routed-residual
BMP and continuous AD, upgrading gas balances and methane slip, and digestate,
nutrient-product, contaminant, and field-use measurements. Route-specific items
are marked conditional. These are acquisition requests, not filled values.

### UI feed composition and Phase 4 evidence increment (2026-11-09)

The UI and backend continue to read the same canonical
`greenhub_feed_composition_defaults.json`; no API payload, workbook, or default
override path was changed. The profile now includes a class-C nitrate-ion
proxy derived from Della Rosa et al. (2022; DOI
[`10.1093/jas/skac223`](https://doi.org/10.1093/jas/skac223)), Table 1 FR0:
618 ± 155 mg nitrate-N/kg DM is converted with the NO3-/N molecular-weight
ratio and the separately measured VARTA 0.143 dry-matter fraction. The source
is cultivated New Zealand ryegrass, not a matched roadside/VARTA sample; the
transfer uncertainty remains unquantified. Its mass is removed from the
unmeasured closure residual, which remains D-class and explicitly a bookkeeping
pool. UI-profile D entries therefore decreased from 63 to 62 (the change is a
proxy upgrade, not a GreenHub measurement).

Protein recovery now exposes two PR1-only opt-in literature candidates from la
Cour et al. (2019; DOI
[`10.3389/fsufs.2019.00112`](https://doi.org/10.3389/fsufs.2019.00112)):
ryegrass total-N precipitation (0.38 of N in clarified juice) and the upper
endpoint (pH 4.5) of the reported pH 4.0–4.5 range. Both are C-class for the
model-facing inputs because total-N precipitation is not soluble-protein
recovery, and selecting a scalar endpoint from a range is an assumption.
Literature candidates require explicit literature-default or expert-override
mode; structural workbook values and run-specific user override priority remain
unchanged. The studies use cultivated ryegrass and a water-assisted second
press/clarification step, so neither closes the project-specific measurement
gaps.

The new Della Rosa and la Cour records remain material/process-specific within
the broader platform architecture. Their DOI-backed source observations are
not portable defaults. The existing 34-item Phase 3–7 measurement acquisition
register remains the source of required project measurements, especially
REQ-GH-P3-06 through P3-10 for matched composition, protein form, nutrient
speciation, contaminants, and individual soluble acids/sugars, and REQ-GH-P4-01 through P4-04 for juice,
titration, recovery/loss and product quality. No new GreenHub assay was
available, so these measurements remain open rather than being imputed.

### Additional composition and FAIR-index increment (2026-11-09)

The shared feed profile connects the VARTA whole-grass chloride result to the
model's chloride-ion pool. The workbook reports 330 mmol/kg dry matter and
11.7 g/kg dry matter for the same July 2026 sample. At 14.3% measured dry
matter, this is 0.0016731 kg chloride/kg wet feed. This is a sample-specific
class-A measurement, not a seasonal or regional mean. The laboratory extraction
method and replicate uncertainty were not supplied, and other ions remain
unresolved, so the complete inorganic charge balance is still open. The
profile partitions this mass out of the literature ash proxy to avoid counting
it twice; the resulting residual ash remains class C and is not a measured
VARTA ash result.

The shared feed profile also replaces its unsupported heavy-metal placeholder
with a class-C contaminant proxy from Czubaszek et al. (2023; DOI
[`10.3390/en16114488`](https://doi.org/10.3390/en16114488)), Table 4, summer
cutting. The five reported means (Cr, Ni, Cd, Hg and Pb; 12.97 mg/kg dry
matter total) are multiplied by the VARTA measured 0.143 kg dry matter/kg wet
feed, giving 1.85471e-6 kg/kg wet feed. The source measurements are B-tier, but
the GreenHub application is C because it transfers a Polish 2019 roadside
sample to a Dutch July 2026 sample; triplicate lab analyses are not field
replicates, aggregate covariance is unknown, and the result is not a compliance
or speciation assessment. The profile subtracts this trace mass from the
literature total-ash proxy to avoid double counting, so the resulting ash value
is also class C. Feed mass closure remains 1.0 and user overrides retain their
existing priority.

The profile now has three justified upgrades: one D-to-A same-sample
measurement (chloride) and two D-to-C literature proxies (summer roadside
trace metals and aggregate grass pesticide residues). The pesticide proxy is
derived from Prechsl et al. (2022; DOI
[`10.3389/fenvs.2022.1062333`](https://doi.org/10.3389/fenvs.2022.1062333)):
334 detections × 0.0645 mg/kg per detected residue ÷ 399 grass sample analyses,
then converted to kg/kg fresh grass. Non-detects and below-LOQ values are set
to zero, so the estimate is a lower bound. It is C-class because South Tyrol
public-site grass is not the GreenHub Dutch roadside sample; it is not a safety
or compliance result. The latest profile review has 57 D-class component
records, of which 17 have nonzero structural/proxy allocations and 40 are
zero defaults; the active UI exposes 53 D-class fields (17 nonzero). A later
class-C acetic-acid proxy from Heller et al. is based on 0.09 g/kg fresh
landscape grass and does not resolve the remaining species-level inputs.
Zero defaults mean “not resolved,” not measured absence. These changes do not
alter the 538-row canonical Phase 3–7 runtime registry. The Czubaszek source asset is indexed as
partially D4 because its five cited rows are calculation-connected, tested and
reported through the shared profile; all other rows remain reference-only.

The same review caught and corrected a 1000-fold SI conversion error in two
reference-only PAH records in `roadside_grass_composition_scientific.csv`:
370 µg/kg is 0.37 mg/kg and 3400 µg/kg is 3.4 mg/kg. Both are site maxima, not
means, from a UK roadside study (Mason et al., DOI
[`10.1007/s12649-018-00557-x`](https://doi.org/10.1007/s12649-018-00557-x)); the
dataset remains blocked/reference-only and its checksum was refreshed. These
PAH observations were deliberately not mapped to the profile's
`PersistentOrganics` input because that model component is the PFAS pool, not a
PAH pool. No matched GreenHub PFAS assay was found, so that value stays D.

The broader project/tool split remains explicit in
`docs/biorefinery_platform_architecture.md`: source measurements are globally
discoverable, but project adapters own derived defaults and transferability.
The Phase 3–7 measurement acquisition register remains open for matched Dutch
feed/contaminant assays and Phase 4–7 stream and product measurements.

### Free-sugar composition proxy and current UI D count (2026-11-10)

Masaki and Ohyama (1976; DOI
[`10.2508/chikusan.47.205`](https://doi.org/10.2508/chikusan.47.205)) report
Italian-ryegrass dry-basis ranges for glucose, fructose, sucrose and fructosan.
Their abstract describes LC for mono-/disaccharides and anthrone colorimetry
for fructosan, but supplies neither per-stage means nor replicate statistics.
The source values are therefore retained as class-B ranges, not point
measurements.

The UI/backend default profile now uses those four range midpoints only as
relative weights to partition Smit et al.'s (2022; DOI
[`10.1021/acssuschemeng.2c00838`](https://doi.org/10.1021/acssuschemeng.2c00838))
7.2% DM roadside-grass extractive-sugar aggregate. The derived profile values
are class C, because the sugar proportions are transferred from cultivated
Italian ryegrass and normalized against a separate roadside-grass aggregate.
At the VARTA sample's 0.143 DM fraction, the mass-conserving split is glucose
0.001872, fructose 0.001976, sucrose 0.001664, and residual `EntrappedSugars`
0.004784 kg/kg wet feed. Their sum remains 0.010296 kg/kg wet feed (7.2% DM);
profile total remains 1.0. The UI reads the same JSON profile and explicit
`feed_composition` overrides retain their existing route and normalization.

This updates three UI-active fields from D to C and moves the aggregate
remainder from B to C; it does not claim a same-sample sugar assay. The current
profile has 74 components (A=2, B=4, C=14, D=54); 70 are exposed in the feed
composition panel (D=50, including 17 nonzero structural/proxy allocations).
Zero D entries still mean unresolved, not measured absence. `REQ-GH-P3-10`
remains open for matched water-soluble organic-acid and individual-sugar
measurement; the staged ranges do not close it. The source has no reuse
license stated in its publisher record, so redistribution rights remain to be
checked.

The profile range asset is indexed as partial D4 only because the range records
are now linked to the tested calculation and reported profile. The source
ranges themselves remain B and are not represented as GreenHub observations.
No Phase 3–7 canonical runtime-register row was changed by this feed-profile
update: the 538-row registry and its D count remain unchanged. The sugar split
is GreenHub adapter data, not a context-independent platform default.

### UI feed composition and cross-project catalog refresh (2026-11-11)

Added the source-located Table 2 starch calibration/validation summary from
Gierus et al. (2024), DOI
[`10.3390/agronomy14010168`](https://doi.org/10.3390/agronomy14010168), as
`Greenhub/data/Pre-treatment/Feedstock/perennial_ryegrass_starch_gierus_2024_reference.csv`.
The source reports mean starch of 34 g/kg DM across n=100, observed range
1–169 g/kg DM, NIRS R²=0.77, SEC=1.45, and SEV=2.23 g/kg DM. These are
calibration/validation summary statistics for cultivated perennial ryegrass
accessions in northern Germany, not raw sample-level values or a GreenHub
roadside-grass measurement. The observed range is not treated as a confidence
interval or probability distribution.

The UI/backend feed profile now uses 34 g/kg DM × the separate VARTA GreenHub
sample's measured 0.143 dry-matter fraction = 0.004862 kg starch/kg wet feed.
This is a C-class cross-material adapter proxy; the source observation remains
B-class and reference-only. The previous secondary-source 18.8 g/kg DM proxy
is retained in the proxy-candidate inventory for traceability. The closure
residual is recalculated to 0.0060741704 kg/kg wet feed so the profile still
sums to one; it remains an unmeasured bookkeeping residual. This deliberately
changes the active composition input, not a process equation or API contract.

The current feed profile has 74 component records: A=2, B=0, C=18, no D
assignments, 49 unmeasured compatibility fallbacks (M), one derived closure
residual (R), and four structural initial states (S). The 70 UI-visible fields
therefore comprise A=2, B=0, C=18, M=49, and R=1. The cellulose,
hemicellulose, and ADL-based lignin amounts are unchanged but now class C at the
GreenHub profile level: their underlying cultivated-ryegrass measurements are
B, while transfer to roadside grass and conversion with VARTA moisture are
literature-derived assumptions. M/R/S are status/role labels,
not evidence grades; their numeric compatibility values do not mean measured
presence or absence. The class-C proxy, source CSV, sidecar, local source
register, dataset manifest, generated FAIR catalog, and tests now cross-link.

A further literature screen on 2026-11-11 found detailed fresh-forage ryegrass
composition experiments and urban roadside-grass elemental analyses, including
[Radojevic et al. (1994)](https://doi.org/10.1071/AR9940901),
[Olszewska (2021)](https://doi.org/10.3390/agronomy11030468), and
[Piepenschneider et al. (2015)](https://doi.org/10.1007/s11356-014-3881-9).
These remain evidence-only: the forage experiments are cultivated pasture
under different species/management conditions, and roadside total-element
assays do not determine dissolved/particulate ion speciation. None safely
replaces the 49 unmeasured UI compatibility fallbacks or the closure residual
and structural process states. Matched GreenHub assays are still needed for
individual protein forms, sugars/acids, ionic speciation, and contaminant
fractions.

The direct roadside-grass comparator already transcribed in
`roadside_grass_composition_scientific.csv` provides a useful analytical
cross-check: Brown et al. (2020, Table 3) report fresh road-verge total nitrogen
of 2.1 ± 0.3% DM, matching the VARTA sample's measured total nitrogen of 21
g/kg DM numerically. This is agreement between separate samples, not a matched
calibration or proof of identical species composition. The paper's proximate
and ultimate analyses do not resolve the UI's mutually exclusive organic-N,
soluble-protein, amino-acid, ionic, and carbohydrate pools; they therefore do
not justify relabeling those fallback values as measured or assigning them
arbitrary shares. The comparator remains source-specific and does not change
the VARTA default. [Brown et al. (2020)](https://doi.org/10.1016/j.biombioe.2020.105570).

The reset UI profile was also reconciled against the VARTA whole-grass total
element assays. Model-implied wet-basis amounts are the sum of each profile
component fraction times its elemental mass fraction in
`Greenhub/component_metadata.py`; lab amounts are the measured g/kg DM times
the sample's 0.143 DM fraction. This is a diagnostic of the reset profile, not
a correction or a live calculation after user overrides:

| Element | Reset-profile implied (g/kg wet) | VARTA total (g/kg wet) | Finding |
|---|---:|---:|---|
| N | 3.3856 | 3.0030 | Profile is 12.7% higher |
| P | 0.2107 | 0.4004 | Profile is 47.4% lower |
| K | 0.5056 | 4.1613 | Profile is 87.9% lower |
| S | 0.1699 | 0.7150 | Profile is 76.2% lower |
| Ca | 0 | 1.9877 | No model component pool |
| Mg | 0 | 0.3146 | No model component pool |
| Na | 0 | 0.1859 | No model component pool |
| Cl | 1.6731 | 1.6731 | Matches the directly mapped chloride result |

These totals are not interchangeable with process species. Total N cannot be
assigned wholly to protein; total P cannot be divided among organic,
particulate, and dissolved phosphate; total K/Ca/Mg/Na cannot be presumed
water-soluble; and total S cannot be treated as sulfate. The reset composition
is therefore not elementally reconciled to the VARTA result; downstream
elemental and nutrient outputs retain this limitation. The highest-value
paired assays are true/soluble/insoluble protein plus non-protein-N speciation;
soluble versus particulate/organic P and K; water-extractable versus total
Ca/Mg/Na/S/Cl; and dry matter, ash, fiber, and sugar measurements on the same
sample. The UI lab-reference note now flags the mismatch explicitly, and no
component values or defaults were rescaled. A regression test recomputes this
comparison from the profile and authoritative component metadata.

The VARTA row reports total nitrogen (21 g/kg DM) but leaves the direct crude-
protein result blank. The UI now additionally shows a separate class-C estimate
of 131.25 g crude-protein equivalent/kg DM using the conventional N × 6.25
calculation documented by Aakjaer Pedersen et al. (2025; DOI
[`10.3390/proteomes13010008`](https://doi.org/10.3390/proteomes13010008),
Methods §2.2). It is not relabeled as an assay, is not used to replace the
existing 10.7% DM literature-based protein profile, and is not connected to
process calculations; non-protein nitrogen may make the equivalent differ from
true protein. The raw VARTA crude-protein field remains “not reported.”

The broader platform catalog refresh reports 500 Phase 3–7 dataset assets and
538 canonical runtime input records (Phase 3: 69 D; Phase 4: 80 D; Phase 5:
81 D; Phase 6: 10 B and 164 D; Phase 7: 134 D). The complete FAIR input index
contains 864 assets and 918 normalized records. A targeted taxonomy correction
now preserves unsupported defaults as class E instead of translating them to
D; a DOI string alone does not promote a value to C. Class C remains an
explicitly reviewed literature-linked assumption. This correction changes no
numeric value, activation state, runtime precedence, or evidence status. The
feed profile remains incomplete, and Phase 3–7 class-E defaults remain
unresolved assumptions. No dataset was promoted to context-independent
evidence, and the broader platform still has no empirical context-independent
Phase 3–7 dataset.

The 2026-11-11 FAIR refresh adds 19 source-backed, scenario/mode-qualified
parameter candidates (15 B and 4 C) to the normalized input records. This fixes
a prior reporting omission where the FAIR snapshot showed a canonical fallback
but hid a route-specific candidate that runtime could select. In particular,
the PR3-only pH 5.0 and 60 °C precipitation conditions are reported as class C with Guo et
al.'s DOI, workbook row, selector applicability, and D4 readiness; the shared
all-route fallback remains D and is not presented as supported for other
protein technologies. They come from the same reported 70:30 perennial-ryegrass/
white-clover PEF and screw-press pilot condition; transfer to GreenHub roadside
grass is explicitly a screening proxy, not a project measurement. A paired
structural PR3 run changed only the reported pH setpoint from 4.5 (E) to 5.0
(C); the compared KPIs were unchanged: mass residual −9.1083e−10 kg/h,
dry-protein product 1.543506 kg/h, and electricity 5.516020 kW. The default
uses direct-yield recovery and a fixed empirical acid dose. Thus
pH-dependent recovery and reagent demand remain unvalidated until titration and
route-specific recovery data support those modes. The parameter activation export now retains candidate
values and evidence metadata, and the master-input catalog records candidate
identity separately from the canonical parameter. Workbook provenance hashes
are based on the relevant authoritative input sheet values, not the entire XLSX
container, so refreshing the embedded generated FAIR tabs does not change the
hashes of the source parameter records. This was checked before and after the
snapshot refresh. In that FAIR refresh, the PR3 pH entry was the only appended
process-input row; all other source sheets/formulas were checked unchanged. The
two generated FAIR tabs were rebuilt without further altering process inputs,
and the other 14 non-FAIR sheets were verified unchanged during that refresh.

A subsequent Phase 5 evidence pass added three AD1-scoped records to
`Phase5Parameters` rows 88–90: 35 °C mesophilic CSTR operation (B; Pakarinen et
al., 2011, DOI `10.1016/j.biortech.2011.07.020`), the 1.5 kg VS/m³·d tested OLR
(B; Egwu et al., 2022, DOI `10.1016/j.rser.2022.112092`), and pH 7.2 (C), an
explicit transfer assumption using the upper endpoint of Egwu et al.'s reported
pH-control interval of 6.8–7.2. These observations do not establish an optimum
or stable design: the cited systems use different silage/feed mixtures and
feeding regimes, and the Pakarinen initial 2 kg VS/m³·d, 30 d HRT combination
was reported unstable. The workbook's numeric AD1 settings were not changed;
the new evidence is limited to AD1 and does not upgrade the shared fallback or
AD2/AD3. The workbook validator and per-sheet comparison passed after the
append. The historical literature-candidate index title for AD-001–003 was
also corrected to match the paper title; candidate values and opt-in status are
unchanged.

The existing platform schemas and project adapter remain the extension point:
shared source observations and technology-family descriptions are discoverable
across projects, while each project owns its material profile, route mapping,
parameter adapter, applicability limits, and overrides. GreenHub remains the
only runnable project. User-supplied feed-composition overrides still take
precedence over the canonical profile; the UI and backend reset defaults read
the same profile. The master workbook's generated FAIR snapshot tabs were
refreshed without changing source-input sheets, workbook parameter defaults,
scenario IDs, or result contracts.

The runtime loader resolves the AD1 temperature, pH, and OLR records with
their stated B/C evidence and D4 candidate provenance; targeted resolver and UI
feed-reference tests pass. The generated cross-project catalog continues to
report 538 canonical Phase 3–7 inputs. The selector-qualified candidates are
listed separately from canonical defaults. Parameter exports and generated
FAIR input snapshots were subsequently refreshed; their summary tabs do not
change workbook source inputs or runtime precedence.

### Phase 7 — digestate struvite design candidates (2026-11-11)

The calculation-connected NR2 struvite candidates now include two explicitly
limited observations from Tsaridou et al.'s dairy-effluent digestate pilot
([DOI](https://doi.org/10.30955/gnc2023.00314)). The reported N:Mg:P ratio is
1:1.5:1.5, so the model's Mg:P input is exactly 1.0 mol/mol (not 1.5); the
reported approximately 30-minute precipitation time is also available as a
candidate. Both are class C transfer assumptions, despite B-tier source
observations, because the source is nanofiltration retentate from dairy
digestate rather than GreenHub grass digestate. They are D4 and scoped only to
NR2 and literature-default/expert-override modes. The current structural
defaults (Mg:P 1.2 and 60 min) are unchanged.

The paper's reported pH 10 remains reference-only: the present model does not
use target pH to calculate base demand, supersaturation, or precipitation
recovery. Selecting pH 10 now would therefore imply chemistry the equations do
not implement. The targeted test checks source-row identity and ratio ordering,
candidate scope and provenance, unchanged structural defaults, and the effect
on the actual NR2 crystallizer ratio and sizing. This is a limited design
connection, not validated GreenHub recovery performance. The candidate records
are included in the refreshed FAIR input snapshot; neither structural defaults
nor other workbook source sheets were changed.

### Current input-class audit and feed-profile update (2026-11-11)

The reset UI feed profile contains 74 component rows: 2 class A, 3 class B,
15 class C, 49 unmeasured compatibility fallbacks (M), four structural
initial-state rows (S), and one closure residual (R). It has no component row
labeled D. This does not mean composition is complete: the VARTA total N/P/K/S
results are not fully reconciled to model species, and the crude-protein assay
is still unreported. Sixteen M values are nonzero and active in the reset
composition for compatibility; 33 are zero. A separately displayed class-C
N×6.25 crude-protein equivalent is reference-only and does not alter the reset
component vector.

The canonical Phase 3–7 parameter registry contains 547 records: 528 class-E
structural placeholders (Phase 3: 69; Phase 4: 80; Phase 5: 81; Phase 6: 164;
Phase 7: 134), 10 class-B records, 2 with no quality class, and 7 project
controls. The class-E values remain unresolved model placeholders. Readiness
D4/D5 is a separate calculation-maturity label, not data quality.

The normalized `Greenhub/data/fair_input_catalog/master_input_records.csv`
snapshot contains 923 records: A=15, B=154, C=49, E=597, unclassified=101,
and project controls=7; it emits no D-class records. The Phase 3–7 runtime
catalog contains 538 rows: 528 E-class structural placeholders (Phase 3: 69;
Phase 4: 80; Phase 5: 81; Phase 6: 164; Phase 7: 134) and 10 B-class inputs.
The E rows have no stable identifier or source URL; 17 contain numeric zero
and 15 have blank values. These records remain unresolved, and D4/D5 denotes
calculation maturity rather than evidence quality.

The activation registry contains 15 active D4 B/C candidate records matching
10 of the 528 E parameter IDs (8 B source records and 7 C GreenHub-facing
assumptions). They cover a timothy-grass press-yield observation, PR3 protein
precipitation conditions/recovery, AD1 temperature/pH/OLR/HRT, and NR2
struvite Mg:P ratio/residence time. These candidates are scoped alternatives,
not proof that the GreenHub defaults are measured or transferable. The other
518 E parameter IDs have no matched active B/C D4 candidate currently
registered; that is a catalog-coverage count, not proof that no literature
exists.

The raw profile, registry and catalog labels were normalized without changing
model composition values, route defaults, user overrides, or run contracts.
This is not an evidence promotion and closes none of REQ-GH-P3-06 through
P3-10 or the route-specific Phase 4–7 measurement requests.

