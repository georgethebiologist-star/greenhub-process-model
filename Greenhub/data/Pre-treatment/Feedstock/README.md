# GreenHub PT0 Feed and Baseline dataset suite

## Flemish roadside/nature clipping quality survey

`flemish_roadside_grass_quality_survey_2020_summary_reference.csv` preserves
only the group-level findings reported by Hermans/Eurofins (2021) for about 75
Flemish grass lots sampled in autumn 2020. It records visible-litter patterns
and the counts of sampled locations exceeding the report's cited Keurcompost
heavy-metal limits. The source report says a separate Excel data appendix
exists, but that workbook and the individual analytical concentrations were
not available in the retrieved public copy; this is not a raw analytical
dataset. The Keurcompost comparison is a screening context, not a feed,
digestate, fertilizer, or product specification. No explicit reuse license
was identified. These summary observations are reference-only and are not
connected to intake limits or process defaults. The source, approximate
sampling strata, and limitations are recorded in `source_register.csv` and
the adjacent `.source.json` sidecar.

## Dutch availability and mowing evidence

`roadside_grass_availability_evidence.csv` indexes Dutch roadside-grass field
evidence. The 1.1–6.5 t DM/ha site-productivity range is reported by Bakker et
al. (2026; DOI `10.1111/1365-2664.70289`). The mowing regimes and June/August
standing-biomass study are reported by Bakker et al. (2026; DOI
`10.1111/avsc.70085`). The Zenodo identifiers are not conflicting: DOI
`10.5281/zenodo.15349657` identifies the specific dataset version, while
`10.5281/zenodo.15349656` identifies the concept record. Zenodo version
metadata verifies the dataset's CC BY 4.0 license; the related article has a
separate CC BY-NC license. The repository does not include the cited analysis
script. These are standing-biomass observations, not annual harvested yield, accessible-area
estimates, or delivered-feed quantities. Records remain staged and are not
connected to model defaults or the availability calculation. The field study
documents tested one- and two-cut options, but does not establish that they
are permitted or used for every Dutch road operator. Source sections: Methods
2.2–2.3 and Results 3.1.

The same register now includes the Province of Zuid-Holland's undated official
web article: it reports approximately 10,000 tonnes of verge grass mown per
year, two rounds in June–July and September–October, and removal after the cut
material rests in the field for a few days. The mass basis, reference year,
measurement method, per-round tonnage, and GreenHub contract share are not
given. These rows are regional operating-context evidence only; the mass must
not be converted to dry matter or treated as delivered plant feed. Provenance
is recorded in `source_register.csv`.

Rijkswaterstaat reports more than 18,000 ha of motorway verges and says grass
is mown once yearly in most cases, with cuttings removed. This broad management
summary has route-specific exceptions; it is not a biomass measurement or
GreenHub harvest calendar and remains separate from the provincial schedules.

`hdsr_mowing_material_digestion_projection_2021_reference.csv` records a
separate HDSR proposal for RWZI Nieuwegein: 30,000 t/year of mixed verge- and
ditch-mowing material paired with a projected 3.4 million m³/year of biogas.
These are planning estimates, not measured operating data; the mass basis, feed
split, gas reference conditions, methane fraction, and metered performance are
not reported. Keep the pair reference-only and do not infer an AD yield or
GreenHub supply from it.

`gr4ss_leeuwarden_project_design_reference.csv` links a separate, official
Fryslân permit scope (36,000 t of verge/nature cuttings plus 24,000 t of other
plant residues, with no reporting period stated in the notice), an operator
announcement of up to 60,000 t/year plant-based feed capacity, and the GR4SS
website's biomethane and coproduct targets. The capacity is design information;
the product quantities lack a stated time basis and specifications. This is
not operating performance or the GreenHub route, and remains reference-only.

The source observation file `Biomass.csv` contains 120 site × sampling
month × mowing-treatment records, including one blank biomass measurement
retained as missing. It uses semicolon delimiters. Values remain in source
units (g DM/m²). The version DOI is `10.5281/zenodo.15349657`; its concept DOI
is `10.5281/zenodo.15349656`. Zenodo version metadata verifies the dataset's
CC BY 4.0 license; the related article's CC BY-NC license is separate. The
source-side R script is not vendored here. The derived summaries apply only
the documented dimensional conversion, 1 g DM/m² = 0.01 t DM/ha. These are
measured 2023 standing-biomass observations, not whole-season harvested or
delivered quantities, and are not connected to the active availability or
Pareto calculation.

`mowing_regime_biomass_summary.csv` reports reproducible month × treatment
summaries from those 120 source rows (mean, sample standard deviation, range,
and non-missing n). The source's documented conversion is applied once; no
seasonal yields are summed or imputed. November standing biomass was not
measured, and the single missing August value is reflected by n=9 for that
group. Summary rows are class A measurements/derived summaries but remain
staged evidence because harvest-height, collection, area, and site-to-project
transfer parameters are unresolved.

`roadside_grass_site_productivity_2023.csv` exposes the ten site productivity
values from the source's Productivity field, converted once to t DM/ha. It is
an ecosystem standing-biomass measure averaged across June and August, not an
annual yield or a supply estimate. The version and concept DOI roles and
dataset license are documented in the source sidecars.

`zeeland_availability_scenarios.csv` records the VITO/Interreg MooV supply
assessment for Zeeland (2021 report; stable URL in `source_register.csv`). It
separates the report's ~250 t fresh/year current collection estimate, ~25,300 t
fresh/year one-cut technical potential, and future two-cut 100%-collection
potential (~42,300 t fresh/year; reported summer/autumn split 25,300/17,000).
These are regional estimates with different scenario meanings; the larger
potentials must not be treated as current available feed or generalized to the
Netherlands. The seasonal periods are broad and do not establish calendar-month
biomass fractions. The summer (25,300 t fresh/year), autumn (17,000 t fresh/year),
and annual two-cut total are now read by the Pareto runner as a Zeeland-specific
screening scenario. The source-month allocation is an explicit class-C assumption:
calendar-day weighting is applied within June–August and September–November 1–15
because the regional report gives seasonal totals rather than monthly amounts.
Dutch roadside-grass mowing windows are informed by the 2026 field study
([DOI 10.1111/avsc.70085](https://doi.org/10.1111/avsc.70085)); it does not measure
monthly delivered supply. This profile is embedded in each saved Pareto request
and is replayable from the UI. It does not alter application defaults or imply
current contracted supply. The other Zeeland evidence rows remain staged.
The MooV/VITO report metadata does not identify an explicit reuse license; the
register records the public source URL and attribution but does not claim a
license to redistribute the report itself.

Target path: `Greenhub/data/Pre-treatment/Feed_and_Baseline/`

This suite contains source-traceable observations for untreated green biomass and the PT0 no-pretreatment case.

## Rules
- One observation per row.
- Source units are preserved; SI-normalized values are only supplied for unambiguous conversions.
- Missing values remain blank and use `data_status=missing`.
- Proxy meadow data are explicitly labelled and must not be treated as roadside-grass defaults.
- Source-fitted equations are not universal laws and must not be extrapolated.

## Files
`pretreatment_feed_composition.csv`, `pretreatment_feed_physical_properties.csv`,
`seasonal_feed_variability.csv`, `no_pretreatment_baseline.csv`,
`source_register.csv`, `equation_registry.csv`,
`assumption_and_missing_data_register.csv`, `optional_calculated_summary.csv`,
and `dataset_manifest.csv`.

## Integration readiness
The schemas and identifiers are ready for ingestion and provenance checks. The package is not yet fully parameterized because direct grass-juice physical properties, soluble/insoluble protein, sugars, COD, untreated pressing yield, untreated release, cell-disintegration index, and PT0 energy demand remain unresolved.

`czubaszek_2023_lignocellulose_reference.csv` adds 12 seasonal fresh roadside/median-grass measurements from Czubaszek et al. (2023; DOI `10.3390/en16114488`, Table 5, p. 8): crude fiber, ADL/lignin, hemicellulose (NDF−ADF), and cellulose (ADF−ADL). The observations are class B for the Polish study material and `reference_only`; analytical triplicates are not independent roadside-site replicates. Crude fiber overlaps the cell-wall fractions, and the calculated cellulose/hemicellulose fractions have assay limitations. They are not added to the GreenHub UI mass profile or treated as GreenHub-batch measurements. The active cultivated-ryegrass cellulose, hemicellulose and ADL-derived lignin values remain numerically unchanged but are now class C at the GreenHub profile level because transferring them to roadside grass is an assumption; their underlying source measurements remain B.

## Limitations
Roadside-grass composition comes from one seasonal experimental study. Structural carbohydrate data use a managed meadow proxy. No graph values were digitized; only equations printed by the source were transcribed. “Immediate” processing from the DCA report is retained without inventing a numeric storage limit.

`ravels_roadside_grass_collection_conditions_ovam_2009_reference.csv` adds one campaign-level summary from the 2008 Ravels roadside-grass silo study reported by Elsen et al. (2009). It records four delivered loads, the report's approximate just-under-25-tonne load description, flail mowing with direct suction, short cutting, qualitative sand/litter observations and an approximately three-day contractor-reported maximum interim hold. Individual load weights, mass basis, moisture, area/yield and route data were not reported; the summary is not annualized and remains reference-only.

`perennial_ryegrass_seasonal_wsc_cp_olszewska_2021_reference.csv` transcribes 36 marginal means from Olszewska (2021; DOI `10.3390/agronomy11030468`), Tables 2–4: water-soluble carbohydrates, crude protein, and their ratio by cultivar, nitrogen rate, harvest time, and cut over 2013–2015. Measurements are on a dry-matter basis; WSC used the anthrone method and crude protein the Kjeldahl method. The paper's table values are B-tier literature measurements, but this is cultivated Polish perennial ryegrass, not roadside grass. Marginal means are not joint treatment observations, and the tables do not report SD/SE. This is a project-neutral, material-specific comparator for future feedstock adapters only; it is not mapped to GreenHub UI defaults, protein-solubility pools, or runtime calculations. See the `.source.json` sidecar for full source and applicability metadata.

The local source register now includes the official Copernicus GRAME (mowing-event count) and GRAMD (mowing dates) products as Phase 1 acquisition leads. They provide annual 10 m satellite-derived classifications for mapped herbaceous grassland, with a 0.25 ha minimum mapping unit; the GRAMD product has up to four day-of-year layers, and GRAME has a confidence layer. The 2022–2023 release was announced by CLMS in December 2025. Only product metadata and access links are registered here: no raster pixels were downloaded or interpreted. These products cannot establish verge-specific mowing, collected tonnes, biomass yield, removal, access or contracts; their mapping threshold may also miss narrow verges. Confirm the exact release vintage and retain confidence/nodata information before any future geospatial extract. Sources: GRAME DOI [10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9](https://doi.org/10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9), GRAMD DOI [10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0](https://doi.org/10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0), [CLMS product page](https://land.copernicus.eu/en/products/high-resolution-layer-grasslands?tab=grassland_mowing_events), [EEA metadata record](https://www.eea.europa.eu/en/datahub/datahubitem-view/69a59cd8-d22f-4b76-a672-867ce92e1855), and [2022–2023 release notice](https://land.copernicus.eu/en/news/hrl-grasslands-releases-new-mowing-datasets).

The local source register now includes the official Copernicus GRAME (mowing-event count) and GRAMD (mowing dates) products as Phase 1 acquisition leads. They provide annual 10 m satellite-derived classifications for mapped herbaceous grassland, with a 0.25 ha minimum mapping unit; the GRAMD product has up to four day-of-year layers, and GRAME has a confidence layer. The 2022–2023 release was announced by CLMS in December 2025. Only product metadata and access links are registered here: no raster pixels were downloaded or interpreted. These products cannot establish verge-specific mowing, collected tonnes, biomass yield, removal, access or contracts; their mapping threshold may also miss narrow verges. Confirm the exact release vintage and retain confidence/nodata information before any future geospatial extract. Sources: GRAME DOI [10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9](https://doi.org/10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9), GRAMD DOI [10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0](https://doi.org/10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0), [CLMS product page](https://land.copernicus.eu/en/products/high-resolution-layer-grasslands?tab=grassland_mowing_events), [EEA metadata record](https://www.eea.europa.eu/en/datahub/datahubitem-view/69a59cd8-d22f-4b76-a672-867ce92e1855), and [2022–2023 release notice](https://land.copernicus.eu/en/news/hrl-grasslands-releases-new-mowing-datasets).

`fen_grass_biorefinery_fractionation_per_harvest_nielsen_2021_tables_3_4_reference.csv` complements the sibling annual-average extract with 224 per-harvest DM/CP-yield records from Tables 3–4. It retains the source's common `t ha^-1 year^-1` caption on cut-indexed rows, `NA` entries, one-replicate missing SDs and `>0.0` reporting thresholds without conversion or imputation. The data describe cultivated reed canary grass and tall fescue from a Danish fen-peatland experiment with lab-scale twin-screw pressing and acid precipitation; they are not roadside-grass or GreenHub route calibration. The article states CC BY 4.0. The deterministic builder, checksum, sidecar and tests preserve the transcription.

`roadside_cutting_field_decay_schaffers_1998_tables4_5_reference.csv` adds the published community-level field-decay model outputs and composition regressions from Tables 4–5. These supplement the existing plot-level Tables 1/3 extract and apply to short roadside field delay, not ensiling or storage. The table-fitted means, nitrogen extrapolation warning, and weak potassium regressions remain explicitly flagged; no model activation is allowed from this extract alone.

`pzh_municipal_green_waste_cbs_2022_reference.csv` preserves 50 municipal mixed-green-waste estimates from the Province of Zuid-Holland public WFS (attribute year 2022). The values sum to 90,321 t/year, while the related DataOverheid catalog description reports 76,084 t/year; this discrepancy remains unresolved. The stream includes multiple vegetation and pruning sources and is not a roadside-grass supply estimate. It is a traceable regional context dataset only, with no runtime/default use. Sources: [provincial WFS](https://geodata.zuid-holland.nl/geoserver/energie/wfs?service=WFS&version=2.0.0&request=GetCapabilities), [DataOverheid catalog](https://data.overheid.nl/en/dataset/0f08e50f-6483-4d62-8a29-16a049e5c5ec), [PZH biomass inventory report](https://circulair.zuid-holland.nl/wp-content/uploads/2021/12/Biomassa-reststromen-analyse-Zuid-Holland-eindverslag-V3-Robin-de-Roo.pdf).

`pzh_provincial_roadside_and_ditch_management_inventory_2026_reference.csv` is a public-domain extract of provincial management features classified as roadside berm (`berm`) or ditch bank (`slootkant`). It preserves WFS feature IDs, road/route-segment references, mowing-frequency codes, mowing-description text, and source areas in m². The companion `pzh_provincial_roadside_and_ditch_management_by_frequency_2026_reference.csv` groups feature counts and area totals by those source classifications. The 9,726 roadside-berm records cover 5,885,056.46 m² (588.51 ha) of slope-corrected managed area; the 6,632 ditch-bank records cover 1,752,562.27 m² (175.26 ha) and remain separate. These figures describe an administrative management inventory, not mowing actually performed, tonnes of grass, supplier contracts, plant access, or seasonal feedstock. No area-to-yield conversion is made. Maintenance-frequency codes are preserved as supplied, including blanks and non-annual codes; they are not converted to monthly schedules. These are B-class official administrative data (not measured biomass), D3, and reference-only. Metadata, selection filter, units, license basis, retrieval timestamp, limitations and SHA-256 checksums are in adjacent sidecars and source registers. Sources: [DataOverheid catalog and field definitions](https://data.overheid.nl/en/dataset/53300-areaal-beheer---groen), [Province of Zuid-Holland WFS](https://geodata.zuid-holland.nl/geoserver/verkeer/wfs?service=WFS&version=2.0.0&request=GetCapabilities), [National Geo Register feature catalog](https://www.nationaalgeoregister.nl/geonetwork/srv/dut/catalog.search#/metadata/9B2A50A8-E419-4536-9771-AD2470D66E12).

`elshani_2025_grass_clover_field_data/` preserves the three original files from Elshani et al.'s DataverseNO CC0 deposit (dataset DOI `10.18710/F5Z8BR`), linked to the 2025 article (DOI `10.1016/j.scitotenv.2025.180373`). The main file contains 192 treatment/location/year summaries from eight Norwegian cultivated grass-clover trials (three cuts; 2009–2013), and the second CSV provides the eight-location crosswalk. The source README defines DM-yield units and N-rate codes but does not define the CP and clover observation-column units; those values remain unchanged and unconverted. Rows summarize three-replicate treatments rather than raw replicates. This is useful Phase 1/seasonal-cut context, not roadside supply. It remains B-tier D3 reference-only with no runtime/default use. All three files are retained byte-for-byte and checked against DataverseNO MD5 values.

`elshani_2025_grass_clover_field_data/` preserves the three original files from Elshani et al.'s DataverseNO CC0 deposit (dataset DOI `10.18710/F5Z8BR`), linked to the 2025 article (DOI `10.1016/j.scitotenv.2025.180373`). The main file contains 192 treatment/location/year summaries from eight Norwegian cultivated grass-clover trials (three cuts; 2009–2013), and the second CSV provides the eight-location crosswalk. The source README defines DM-yield units and N-rate codes but does not define the CP and clover observation-column units; those values remain unchanged and unconverted. Rows summarize three-replicate treatments rather than raw replicates. This is useful Phase 1/seasonal-cut context, not roadside supply. It remains B-tier D3 reference-only with no runtime/default use. All three files are retained byte-for-byte and checked against DataverseNO MD5 values.

`ravels_roadside_grass_collection_conditions_ovam_2009_reference.csv` adds one campaign-level summary from the 2008 Ravels roadside-grass silo study reported by Elsen et al. (2009). It records four delivered loads, the report's approximate just-under-25-tonne load description, flail mowing with direct suction, short cutting, qualitative sand/litter observations and an approximately three-day contractor-reported maximum interim hold. Individual load weights, mass basis, moisture, area/yield and route data were not reported; the summary is not annualized and remains reference-only.
