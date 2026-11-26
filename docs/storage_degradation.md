# Storage Degradation Framework (Alpha additive)

What was added

- Greenhub.storage.StorageModel: a lightweight, additive storage inventory model that
  tracks inventory (kg), optional capacity (kg), and optional first-order degradation
  (1/day).
- Each simulation step returns explicit provenance describing which methods were
  applied and any limitations or missing data indicators.
- Focused unit tests under `tests/test_storage.py` demonstrating the not-implemented
  behavior and a basic first-order loss when a degradation rate is provided.

Design choices and assumptions

- Missing degradation parameters are treated as "not implemented" — the model
  does not invent rates or silently convert missing values to zero. This preserves
  scientific traceability and prevents hidden mass losses.
- When `degradation_rate_per_day` is provided, a first-order (exponential) decay
  is applied: mass_after = mass_before * exp(-k * days). This is a commonly-used
  simple representation; any calibrated or mechanistic model must supply its own
  rate or connect a different degradation model.
- Withdrawals are applied before degradation in the step to match a perfectly-mixed
  withdrawal assumption used elsewhere in the seasonal controller.
- Capacity is enforced after degradation; overflow is reported in the step `overflow_kg`.

Limitations and remaining gaps

- The generic `component_retention` path has no validated default degradation
  rate. The separate `grass_reactions` package contains 23 explicit reaction
  rows, but its rate constants are assumed or indirectly transferred, not
  validated roadside-grass kinetics. DOI-linked assumptions are class C under
  the project's A–D evidence scale; they are not class B measured kinetic
  values. The package remains opt-in, and its low/high values are scenario
  bounds, not confidence intervals. The FAIR `Master_Inputs` sheet/catalog
  indexes every reaction and provenance record, but is a generated read-only
  snapshot, not a runtime input source.
- The seasonal controller has two mutually exclusive opt-in paths. If a request
  supplies `storage_conditions`, that selected storage model is applied to arrivals
  and carried inventory. In that case the scalar registry parameter
  `seasonal.storage_degradation_rate_per_day` is not also applied (avoiding double
  counting). If no `storage_conditions` are supplied, the scalar parameter can
  apply a first-order wet-inventory loss; if it is absent or blocked, no such loss
  is applied and the per-step result reports the limitation. Storage capacity is
  independently optional and must be explicitly supplied to calculate overflow.
- The opt-in package includes stoichiometric chemical transformations and
  explicit temperature/moisture assumptions, but not a validated evaporation,
  weather, leaching, or protein-quality model. Its Q10, moisture activity,
  reaction rates, and some transformations remain assumptions; output
  completeness flags must not be read as validation or complete emissions
  accounting.
- Published grass-silage studies provide useful contextual bounds, but do not
  directly identify the GreenHub wet-inventory rate or roadside-grass reaction
  constants. Williams et al. (1997; DOI
  [10.1111/j.1365-2494.1997.tb02348.x](https://doi.org/10.1111/j.1365-2494.1997.tb02348.x))
  estimated only 0.3% and 0.9% aerobic dry-matter loss over 120–150 days in two
  carefully sealed ryegrass bunker silos. Rees (1982; DOI
  [10.1002/jsfa.2740330602](https://doi.org/10.1002/jsfa.2740330602)) reported
  laboratory relationships between temperature rise, duration/depth, and
  aerobic grass-silage dry-matter loss. Neither result is a transferable
  first-order loss constant for fresh roadside grass, and neither is used as a
  GreenHub default. Storage capacity is likewise a project/equipment input, not
  a literature constant. These two seasonal registry fields therefore remain
  explicitly missing until a project value or a validated, basis-matched model
  is supplied.

## Evidence reviewed (2026-11-05; updated 2026-11-06)

- Williams, A.G., Hoxey, R.P. & Lowe, J.F. (1997), “Changes in temperature and
  silo gas composition during ensiling, storage and feeding-out grass silage,”
  *Grass and Forage Science* 52(2), 176–189. DOI above. Evidence describes two
  approximately 12 t ryegrass bunkers and explicitly notes that loss may be
  lower than farm-silo losses because sealing was unusually thorough.
- Rees, D.V.H. (1982), “The aerobic deterioration of grass silage and its effect
  on the water-soluble carbohydrate and the associated heat production,”
  *Journal of the Science of Food and Agriculture* 33(6). DOI above. The
  reported lab equations depend on exposure/temperature geometry and are not
  copied into the current storage model.
- Evidence class for those publications is literature (B) as source records;
  applicability to the present roadside-grass process is low. This distinction
  does not upgrade the model's kinetic assumptions, which remain E.
- Yang et al. (2026; DOI [10.1038/s41598-025-34190-1](https://doi.org/10.1038/s41598-025-34190-1)) report multi-site, 3/6/9-month aerobic and nominally anaerobic storage measurements for energycane and biomass sorghum. Their fitted whole-feed dry-matter-loss surfaces use average wet-basis moisture and storage duration in months (Figure 4; n=1,344; R² 0.72 aerobic and 0.61 anaerobic). The coefficients and pooled 9-month endpoints are catalogued in `Greenhub/data/storage/storage_loss_literature_benchmarks.csv` as B-class, reference-only evidence. The study is not Dutch roadside grass, operates at a different scale and climate, and notes that anaerobic bags did not reliably maintain oxygen-free conditions. Its raw observations are available on request, not as an openly downloadable dataset. Consequently these equations are not activated, not converted into first-order component rates, and do not replace missing GreenHub storage kinetics.
- Crook et al. (2020; DOI [10.1002/cft2.20015](https://doi.org/10.1002/cft2.20015)) measured annual-ryegrass round-bale silage after 85 d of wrapped storage. Table 2 reports dry-matter recovery of 97.8 ± 3.10% (dry treatment, n=18) and 92.7 ± 3.10% (wet treatment, n=20), alongside endpoint pH, ammonia-N/total-N, and crude-protein concentration. These direct measurements are added to the same benchmark register as quality-B, reference-only observations. The article's abstract and Methods differ on the dry-treatment moisture label; the register follows the Methods/Table 2 basis and records the discrepancy. This is a useful grass-silage comparison, but the single-site/year baled and wrapped system, 85-day duration, and feed-composition basis do not match loose roadside-grass storage. No first-order constant is inferred from a single endpoint, and no runtime default or protein/DM component-retention rate is activated.
- Brown et al. (2020; DOI [10.1016/j.biombioe.2020.105570](https://doi.org/10.1016/j.biombioe.2020.105570)) provide direct roadside-verge-grass evidence in Table 4: two Lincolnshire sites, fresh and farm bale-ensiled after four months, with moisture, VS/TS, and 15-day experimental BMP. Fresh/ensiled BMP values were 260/276 and 244/249 mL CH₄ g⁻¹ VS at the two sites; the authors report no statistically significant ensiling effect. The benchmark register preserves the reported endpoint values and variability. Because the study does not report matched storage mass recovery, BMP per gram VS cannot establish methane potential retained per original tonne; moisture endpoint differences also do not close a water balance. This is the closest source in the current register to roadside grass, but it still does not justify activating a Dutch storage-loss kinetic equation or a full-scale AD yield.
- Andrade et al. (2024; DOI [10.3303/CET24109019](https://doi.org/10.3303/CET24109019)) measured green-biorefinery outputs from two Danish grass-clover mixtures at harvest-to-processing delays of 0.5–12 h. Table 2 reports LPC crude-protein and ash concentrations; the Results text explicitly gives selected DM- and CP-recovery endpoints, transcribed in `Greenhub/data/storage/harvest_to_processing_benchmarks.csv`. In-field-cut CP recovery declined from 21.0% to 14.0% after 12 h for the 2021 mixture and from 9.2% to 5.5% after 6 h for the 2022 mixture. Stationary-cutting results were not uniformly monotonic, and the authors describe a possible precipitation/quality mechanism and call for further study. These results directly support the importance of harvest-to-processing time and handling in a green biorefinery, but they are not roadside-grass storage kinetics or a retained-protein mass balance. Intermediate figure values were not digitized; no interpolation, fitted rate, or runtime activation is justified.
- Elsen et al. (2009), an OVAM-commissioned Belgian report, provides a useful roadside-grass silo comparator: Table 29 gives seven final 10-week silo pH/DM states, and explicitly says that storage mass loss could not be quantified with the experiment's setup. The grass-only treatment ended at pH 5.5 and 35.6% DM, but it is one heterogeneous field campaign and is not a GreenHub storage factor. Rows and limits are in `Greenhub/data/storage/roadside_grass_ensiling_quality_ovam_2009_reference.csv`.
- The same report reproduces Leenknegt (2004) batch biogas values after fresh versus approximately 6- or 17-day uncontrolled interim holding, and reports one 10-week grass-silo batch result. The table's held and fresh samples are not matched feed lots, oxygen/temperature conditions are absent, assay duration is not continuous HRT, and the source output is biogas (not methane). These rows are in `Greenhub/data/Bigas production + upgrade/Feed BMP/roadside_grass_storage_bmp_ovam_2009_reference.csv`. No storage loss fraction or degradation rate is calculated from them.

Provenance and traceability

- Each call to `simulate_step` returns a `provenance` dict with keys `methods`,
  `limitations`, and `sources` describing what was applied and what was missing.
  This makes it suitable for inclusion in the model's `assumptions` or `warnings`
  collections by the caller.

How to use (example)

```python
from Greenhub.storage import StorageModel

s = StorageModel(capacity_kg=10000.0, initial_inventory_kg=500.0)
step = s.simulate_step(inflow_kg=200.0, outflow_kg=50.0, days=7.0)
print(step['inventory_kg'], step['provenance'])
```

Next steps for v1.0

- Obtain roadside-grass storage time series (mass, DM, WSC, acids, protein-N,
  methane/CO2/N losses) under defined moisture, temperature, packing, and oxygen
  conditions; fit and validate pool-specific rates before replacing E-class
  package values.
- Decide whether the opt-in seasonal degradation hook should become part of the
  public seasonal workflow, API, or reporting surface.
- Expand to include temperature- and moisture-dependence, and multi-pool
  (dry-matter/water) accounting when data permit.
