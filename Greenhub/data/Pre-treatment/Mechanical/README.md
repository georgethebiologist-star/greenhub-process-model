# GreenHub Mechanical Pre-treatment Dataset Suite

Path: `Greenhub/data/Pre-treatment/Mechanical/`

## Scope
This package covers PT0 no pretreatment, PT1 chopping, PT2 maceration, PT3 wet milling/refining, and PT4 high-shear homogenization before pressing or extraction. Populated experimental rows prioritize fresh grass, clover, lucerne, and mixed green biomass. Dry comminution equations are kept separate and explicitly marked as low-transferability.

## Files
- `mechanical_equipment_parameters.csv`: equipment identities, ratings, dimensions, downstream press coupling, and explicit EU/NL price/scaling gaps.
- `mechanical_particle_size_response.csv`: feed moisture calculations and structured missing rows for PSD, energy and temperature response.
- `mechanical_release_performance.csv`: measured product dry matter, crude protein and ash from fresh-biomass maceration trials, plus reported overall crude-protein recovery.
- `mechanical_dynamic_models.csv`: model registry links and implementation status.
- `mechanical_scenario_controller.csv`: PT0–PT4 scenario routing, required variables and fallback guardrails.
- `dataset_manifest.csv`, `source_register.csv`, `equation_registry.csv`, and `assumption_and_missing_data_register.csv`: package governance and traceability.

## Data-status rules
`measured`, `literature-reported`, `calculated_from_source_formula`, `manufacturer-reported`, `fitted_by_source`, `assumption`, and `missing` are used as requested. Blank numeric cells are intentional and must not be replaced with zero.

## Important limitations
1. The directly relevant maceration report provides strong comparative fresh-biomass evidence but does not publish tabulated initial/final particle-size distributions, net equipment energy values, treatment temperature rise, direct juice yield, or soluble-protein release.
2. Product-composition rows describe downstream fiber press cake and protein concentrate after pressing and heat separation. They must not be interpreted as isolated pretreatment release coefficients.
3. Public EU/Netherlands purchase prices tied to the exact cited equipment and delivery scope were not found. Price and scaling fields remain blank; dated vendor quotations are required.
4. Kick, Rittinger and Bond equations originate from dry mineral comminution. They are included only as candidate equation forms and must not be applied to wet grass without experimental calibration.
5. PT4 manufacturer ratings define a hardware envelope for wet food suspensions, not validated grass-processing performance.

## Integration readiness
The scenario controller, schemas, source registry and equation registry are ready for code integration. Predictive dynamic simulation remains blocked for scenarios lacking measured power, flow, active volume, particle-size response and release-response data. The model should raise a missing-data validation error rather than silently inserting defaults.

`green_biorefinery_fermentation_chemistry_2024_reference.csv` adds 28 Table 3 records from Resch et al. (2024; DOI 10.1111/gfs.12682): pH, lactic/acetic/butyric/propionic acids, ethanol, and ammonia in grass-clover and red-clover silages, press juice, fresh press cake, and re-ensiled press cake. These farm-scale measurements improve staged evidence for storage, pressing, and residual-stream characterization. They concern cultivated Austrian forage, are concentrations rather than stream mass balances, and remain reference-only. Ammonia concentration is not an emission; pH is not acid demand. The accessible article copy did not establish the exact Creative Commons subtype, so the metadata does not claim one.

`ayanfe_2023_full_preservation_press_matrix_reference.csv` adds the complete Table 2 matrix from Ayanfe et al. (2023; DOI 10.1016/j.biteb.2023.101356): two laboratory press types × seven response metrics × seven preservation/additive conditions, with source-reported SEM and significance tests. Measurements remain reference-only. CP/DM/ash retained values are expressed per original fresh material, not as fractions of the feed component inventory. The article reports three replicate press samples per treatment; replicate-level observations are not supplied in this table.

`kurhan_2025_biorefinery_reference/` preserves four unchanged University of Bath workbooks (dataset DOI `10.15125/BATH-01534`; associated article DOI `10.1098/rstb.2024.0161`) for silage chemistry, amino-acid profiles, and twin-screw mechanochemical extraction. `kurhan_2025_bath_workbook_sheet_inventory_reference.csv` records sheet scope, dimensions, populated cells, and formula/cache counts. `kurhan_2025_bath_source_workbook_cells_reference.csv` is a lossless cell-addressed transcription of every nonempty cell (5,804 rows), with all 1,224 source formulas and cached outputs kept separate. These are UK grass-silage and extruder comparators for Phases 1, 3 and 4—not Dutch roadside/VARTA observations or direct calibration of GreenHub's current screw-press/isoelectric route. The RSM workbook has a factor-label/settings inconsistency that remains unresolved; no values are activated or converted into model parameters.

## Validation performed
- Comma-separated UTF-8 files with one parameter or observation per row.
- Unique IDs checked across every file.
- Required traceability fields included in all scientific parameter tables.
- SI normalization supplied only for unambiguous conversions.
- Formula text is stored only in equation/model fields, not numeric cells.
- Material state is explicit; dry and wet datasets are not combined without flags.

### Heller et al. (2023) landscape-grass comparator

Three reference-only files transcribe distinct source tables from Heller et al. (2023; DOI `10.3390/en16248091`): `landscape_management_grass_heller_2023_composition_reference.csv` (Table 1, four pretreatment variants), `landscape_management_grass_heller_2023_harvest_pretreatment_reference.csv` (first-cut yield and Table 2 field work/energy), and `landscape_management_grass_heller_2023_bmp_kinetics_reference.csv` (Tables 3–4 batch methane yields and fitted Gompertz parameters). Each file has a source metadata sidecar and local source-register/manifest entries.

These records add primary evidence across feed characterization (Phase 1), mechanical treatment (Phase 3), and batch methane potential/kinetics (Phase 5). They do not fill the Dutch-roadside-specific evidence gaps for seasonal accessible supply, storage (Phase 2), protein extraction (Phase 4), upgrading (Phase 6), or digestate/nutrient use (Phase 7). The source is German landscape-management grass, from a limited first-cut study; the field comparison has access and plot confounding, and parts of the analytical table have n=1. Harvest energy omits transport and handling. BMP/Gompertz values are not continuous-digester design parameters. All records remain B-class, reference-only, and disconnected from runtime parameters and defaults.

### Damborg (2019) thesis-level screw-press protein partition ranges

`damborg_2019_thesis_press_protein_partition_ranges_reference.csv` contains four ranges stated in the abstract of an Aarhus University thesis: crude-protein mass partition to pulp and protein concentrate, plus rumen-undegraded protein in pulp and raw forage. The input crude-protein denominator is explicit for the process-mass ranges; the rumen-undegraded values are per kg protein. Endpoints are not species-paired, have no abstract-reported SD/SE or sample count, and must not be summed as a closed mass balance. The cultivated Danish forage comparator remains B-tier, D3/reference-only and is not connected to GreenHub calculations. No DOI was identified for the thesis record; see the local source register and `.source.json` sidecar for traceability and limitations.

Source: Damborg (2019), Aarhus University, [institutional thesis record](https://pure.au.dk/portal/en/publications/green-biorefinery-characterisation-and-utilisation-of-the-pulp-fr/).

### Stødkilde et al. (2021) species × harvest × press-fraction tables

`stodkilde_2021_species_harvest_press_fractionation_reference.csv` contains 300 long-form observations from Tables 1–5 of the CC BY article (DOI `10.1016/j.anifeedsci.2021.115016`). It covers five cultivated forage species at four independent first-cut dates: feed DM, N and DM yield; single-/double-pressed pulp and protein-concentrate DM/N concentrations; and source-calculated N partition to pulp and concentrate. Pooled model SEM and Tukey grouping letters are retained; the SEM is not date-specific. Processing was by a lab twin-screw press, with water added before the second press and 12 M phosphoric acid used to reach pH 4 for juice-protein precipitation. Acid volume and complete water/component balances are not reported.

These 2016 Danish plot measurements improve Phases 1, 3 and 4 evidence for crop maturity, press-fraction composition and nitrogen partition; they are not Dutch roadside-grass calibration. Nitrogen recovery is not saleable protein recovery. The paper is an expanded journal publication overlapping the earlier 2020 ryegrass proceedings extract, and some ryegrass recovery values differ between publications; preserve source-specific results and do not pool them without reconciliation. Table cells are least-square means; the paper's species means are not forced to equal arithmetic means across the four displayed harvest means. One Table 1 red-clover DM cell is rendered as `12.81` in the machine-readable PDF text layer; the extract records 128.1 with an explicit reconciliation note because the four-date mean matches the printed species LSmean of 126.5. It is B-tier, D3/reference-only and does not activate a model parameter.

Source: [Aarhus University publication record and CC BY details](https://pure.au.dk/portal/en/publications/enhancing-protein-recovery-in-green-biorefineries-through-selecti/), [DOI](https://doi.org/10.1016/j.anifeedsci.2021.115016), [institutional full text](https://pure.au.dk/ws/files/277690669/1_s2.0_S0377840121002029_main.pdf).

### Heller et al. (2023) landscape-grass comparator

Three reference-only files transcribe distinct source tables from Heller et al. (2023; DOI `10.3390/en16248091`): `landscape_management_grass_heller_2023_composition_reference.csv` (Table 1, four pretreatment variants), `landscape_management_grass_heller_2023_harvest_pretreatment_reference.csv` (first-cut yield and Table 2 field work/energy), and `landscape_management_grass_heller_2023_bmp_kinetics_reference.csv` (Tables 3–4 batch methane yields and fitted Gompertz parameters). Each file has a source metadata sidecar and local source-register/manifest entries.

These records add primary evidence across feed characterization (Phase 1), mechanical treatment (Phase 3), and batch methane potential/kinetics (Phase 5). They do not fill the Dutch-roadside-specific evidence gaps for seasonal accessible supply, storage (Phase 2), protein extraction (Phase 4), upgrading (Phase 6), or digestate/nutrient use (Phase 7). The source is German landscape-management grass, from a limited first-cut study; the field comparison has access and plot confounding, and parts of the analytical table have n=1. Harvest energy omits transport and handling. BMP/Gompertz values are not continuous-digester design parameters. All records remain B-class, reference-only, and disconnected from runtime parameters and defaults.
