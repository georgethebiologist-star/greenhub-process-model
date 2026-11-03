# GreenHub PR7: biostimulant recovery route

## Route definition

PR7 is reserved for a phytohormone-enriched biostimulant product separate from
the existing PR1-PR3 protein cake pathway. It offers three membrane concepts:

- **TUF:** tight ultrafiltration, aimed at protein/peptide-bound hormone payloads.
- **LNF:** loose nanofiltration, aimed at free hormones and small peptides.
- **MEUF:** micellar-enhanced ultrafiltration, requiring a surfactant inventory and
  its downstream fate to be represented.

PR7 directly treats clarified juice and excludes the proposed 14-day
pre-membrane anaerobic fermentation/storage step. This does not disable the
separate plant anaerobic-digestion scenario: after PR7, permeate enters the
existing digestion train when that scenario is selected.

The option ranges are recorded in
`Greenhub/data/Protein recovery/Membrane/biostimulant_membrane_options.csv`.
They were supplied in the project prompt and are screening ranges, not validated
GreenHub design inputs.

The latest PR7 parameter block was reconciled against the active registers.
Its nominal fluxes (TUF 22 and LNF 12 L/(m²·h)), hormone-state retentions,
component co-retentions, 10× concentration basis and €1.50–€3.50/L product
price range, membrane replacement interval, resistance terms, diffusivities,
boundary-layer thickness, and reflection coefficients are already represented
in the parameter and evidence CSVs as user-supplied screening values. TUF
hormone retention is state-specific: the supplied 75/50/45% values apply to
bound payload; the free fraction is calculated separately using the supplied
σ/Peclet relation. LNF uses its supplied free-solute values and the supplied
99% crude-protein co-retention as a proxy for carrier-bound payload. These
factors must not be read as independently measured GreenHub performance.

The new CIP note is recorded in
`biostimulant_cip_evidence.csv`: 0.5 wt% NaOH followed by 0.3 wt% citric acid,
once per 48 operating hours. The cycle interval and concentrations remain
screening inputs. Solution volume, rinses, hold time, active chemical demand,
water use, downtime and cleaning recovery are not specified, so no annual CIP
reagent cost is inferred from the solution concentrations. The supplied SDS
MEUF dose (1.2–1.5× 8 mmol/L CMC) and 94.5% recovery are likewise dose/fate
screens; the active route remains gated by surfactant separation and product
residual limits.

The user-supplied €1.50–€3.50/L PR7 concentrate price remains a scenario input,
not a validated GreenHub selling price. A public French supplier listing for a
different vegetable-protein hydrolysate biostimulant gives €2.609/L ex VAT at
1,000 L, with 24% free amino acids and 4.3% total nitrogen. It is recorded in
`biostimulant_product_price_references.csv` as context only and is not used to
price PR7: its composition, strength, product specification, and market basis
do not match a hormone-enriched clarified grass-juice concentrate. The public
listing excludes delivery and notes that professional pricing can vary by
quantity and destination.

The supplied viscosity of 1.35 mPa·s is explicitly for fermented juice at
30 °C. It is excluded from the active PR7 feed model because PR7 currently has
no pre-membrane fermentation. Resistance-based flux therefore remains gated on
a measured viscosity for the actual unfermented clarified juice and operating
temperature; the empirical nominal flux screen remains available separately.
The source identifiers in the pasted parameter block are incomplete and were
not converted into literature-validated citations.

The additional component retention matrix and hydraulic/economic values are in
`biostimulant_membrane_component_retention.csv` and
`biostimulant_membrane_gated_parameters.csv`. Their source labels were supplied
in the prompt but are incomplete identifiers, so they are tagged as
`user_supplied_unverified` rather than literature-validated model defaults.

## Explicit hormone pools

| Pool ID | Meaning | Basis |
| --- | --- | --- |
| `Indole3AceticAcid` | Free IAA (auxin) | C10H9NO2 analyte-equivalent pool |
| `ProteinBoundIAA` | Bound IAA payload | C10H9NO2 analyte-equivalent pool |
| `Zeatin` | Free zeatin (cytokinin) | C10H13N5O analyte-equivalent pool |
| `PeptideBoundZeatin` | Bound zeatin payload | C10H13N5O analyte-equivalent pool |
| `ZeatinRiboside` | Free zeatin riboside | C15H21N5O5 analyte-equivalent pool |
| `BoundZeatinRiboside` | Bound zeatin-riboside payload | C15H21N5O5 analyte-equivalent pool |

These pools are separate from the ordinary protein and peptide material pools.
Bound-pool IDs track hormone analyte equivalents; carrier/conjugate mass is not
added because the provided matrix does not give conjugate identity or carrier
mass fractions. Zeatin riboside's formula and molecular mass are catalogued by
[PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/6440982).

Phase 4 metrics now report actual feed, retentate, and permeate rates for IAA,
zeatin, zeatin riboside, and total hormone payload, plus capture fractions and
component-specific closure residuals. Seasonal aggregation reports the
corresponding time-integrated masses and capture fractions. PR7 validation
checks each analyte balance across the membrane. These outputs use only named
component pools present in the model streams. Screening concentrations are
never inserted into those streams, so a modelled zero is not evidence of zero
hormone content in real grass juice.

The live result view and plot-data API expose the three analyte pools entering
the membrane and leaving in retentate and permeate. The UI annualizes the
steady-state rates using the run's stated operating hours; the plot API retains
the simulated rate basis. If the feed contains no non-zero hormone pools, the
UI says so and does not present the benchmark screen as a plant result.

The full-plant PR7 route now has an explicit, default-off
`use_hormone_benchmarks` option. When enabled, the user-supplied clarified-juice
concentrations and free/bound feed fractions are converted to analyte-equivalent
kg/h using the modelled clarified-liquid volumetric flow, then passed through a
separate, named BioSTEAM input stream. The request requires a provenance note;
the unit reports this as a screening correction, not a measured GreenHub
composition. The option rejects runs where any named hormone pool is already
present upstream to prevent duplicate mass. Benchmark addition is recorded
separately from the clarified-liquid stream and biomass feed basis. The membrane
still requires retention for all nonzero components. The Gate 3 data provide
state-specific retention factors for named IAA, zeatin, and zeatin-riboside
pools; the process split and benchmark capture calculations apply separate
factors to free and carrier-associated pools. For TUF, free-pool retention is
calculated from the supplied sigma/Peclet relation at the nominal 22 L/(m²·h)
flux (2.9%, 3.3%, and 3.7% for IAA, zeatin, and zeatin riboside); the supplied
analyte-specific TUF values (75%, 50%, 45%) apply to carrier-associated
payload. In the integrated TUF split, free-pool retention is recalculated at
the selected flux. For LNF, free-pool values (96%, 95.1%, 94%) are applied directly, and
the 99% value from the supplied crude-protein co-retention matrix is applied to
carrier-associated payload. These are user-supplied screening values/model
outputs, not independently validated module performance.

The supplied benchmark concentrations are loaded from
`Greenhub/data/Protein recovery/Membrane/biostimulant_hormone_benchmarks.csv`:
IAA 65.5 µg/L, zeatin 18.2 µg/L, and zeatin riboside 24.5 µg/L. They are
user-supplied screening benchmarks, not GreenHub measurements. The source text
discusses the supplied free/bound distribution in a 14-day anaerobic state,
whereas the selected PR7 boundary has no pre-membrane fermentation. Therefore
the paired fractions are not validated for this active fresh/unfermented feed;
the full-route benchmark injection remains off by default and should only be
used as an explicitly documented sensitivity case until fresh-feed fractions
are measured. State-specific values and
their nominal weighted total retentions are stored for TUF and LNF. In the
integrated TUF split, free-state retention is recalculated from sigma/Peclet
at the selected flux; the weighted values in the CSV and summary figure are
nominal 22 L/(m²·h) references. MEUF uses the midpoint (87.5%) of the
user-provided 80–95% generic retention range because no analyte-specific MEUF
values were supplied. Primary NF experiments on
natural hormones also show retention can change with membrane adsorption,
solution chemistry, and filtration stage, so nominal analyte retentions remain
screening inputs rather than validated design performance
([Nghiem et al., 2004](https://doi.org/10.1021/es034952r); [Schäfer et al., 2003](https://doi.org/10.1021/es0102336)).

The cited 2025 Scientific Reports study is specifically on alfalfa brown juice
and uses 48-hour lacto-fermentation. It reports IAA changes but explicitly
states cytokinins were not assessed. It therefore does not validate the table's
grass-juice concentrations, zeatin/zeatin-riboside values, or free/bound
fractions; with the current no-fermentation boundary, all three analyte inputs
remain provisional proxies
([study](https://doi.org/10.1038/s41598-025-03896-7)).

`Greenhub.biostimulant_screening.calculate_hormone_capture` calculates
analyte-equivalent captured and permeated mass per year from an explicit annual
clarified-juice volume and membrane option. It does not estimate total retentate
mass or product purity.

Additional screening functions provide: the resistance-based flux equation
(`calculate_resistance_flux`), the sigma/Peclet retention equation
(`calculate_film_retention`), a TUF/LNF/MEUF component split
(`split_component_flows`), and membrane-area/gross-revenue estimates at the
specified VCF (`calculate_membrane_area_and_revenue`). The component split
returns an incomplete result when an active component is outside the supplied
matrix; callers must provide explicit retention overrides for those components.
MEUF class retentions for proteins, peptides/amino acids, sugars and salts are
not supplied and remain unresolved unless explicit evidence-noted overrides
are provided. The MEUF hormone-capture screen uses the supplied generic
80–95% range midpoint (87.5%); that does not establish bulk-component
co-retention.

The added PR7 parameter register stores the supplied viscosity, intrinsic and
fouling resistances, gel-resistance relation, boundary-layer thickness, free
analyte diffusivities, reflection coefficients, and empirical flux references.
The 1.35 mPa·s viscosity is specifically described as fermented grass juice;
it is kept as reference data but is not used for the active no-fermentation
route. The resistance-flux function therefore requires a measured viscosity
for the actual unfermented clarified juice and its evidence note. Membrane,
fouling, and gel parameters remain user-supplied, unverified screening inputs.
The free-solute film-retention function reads its populated parameters from
the register. The integrated PR7 UI/API lets the operator select either an
empirical flux with a source note or the resistance equation with explicitly
supplied TMP, the `Cf/C0` ratio, measured unfermented-juice viscosity, and
evidence notes. The two flux methods are mutually exclusive. The supplied
gel-resistance equation uses the concentration ratio directly, so separate
absolute `Cf` and `C0` values are not required if the ratio itself is
documented. Neither the ratio nor unfermented-juice viscosity is defaulted;
fresh-feed viscosity remains missing for the active feed. MEUF remains on its
empirical flux basis because the resistance parameters are only registered for
TUF and LNF.
An internet search for fresh-grass-juice rheology did not identify a quantitative
viscosity matched to the PR7 clarified feed and its temperature/shear conditions.
The 2026 fresh clover-grass membrane study reports 60 nm UF flux and protein
selectivity, but its accessible record gives no feed-viscosity value; that flux
is not substituted for the tighter PR7 membranes. Vegetable-juice rheology
literature shows strong dependence on matrix, concentration, temperature, and
shear, so cross-feed viscosity values are not assigned to PR7 ([Mattsson et al.,
2026](https://doi.org/10.1016/j.seppur.2026.138129); [Salehi et al., 2021
review](https://doi.org/10.1111/jfpp.15326)).
The film model requires a measured/sourced bound-state diffusivity and
therefore remains gated for bound hormones. The empirical analyte retentions
and sigma/Peclet predictions are different model bases; the screening mass
split uses the empirical retention table and does not silently replace it
with the film-model prediction. All newly supplied constants remain labelled
unverified. In particular, the 1.35 mPa·s viscosity note refers to fermented
juice and is not used for the active no-fermentation PR7 route.
For the current `clarified_protein_rich_liquid` sample in
`Greenhub/results/clarified_liquid_composition.csv`, water, glucose, ammonium,
potassium, soluble/suspended protein, peptides, and amino acids are covered by
the supplied classes. Several other nonzero pools still block a complete split:
structural carbohydrates and pectin, starch, lipids, other biodegradable and
non-biodegradable organics, suspended/inert solids and ash, organic and
particulate nitrogen, particulate phosphorus/potassium, entrapped sugars,
heavy metals, persistent organics, pesticides, microplastics, pathogen
indicators, sand, and litter. These need measured retention or traceable
per-component overrides. Acids are zero in that particular sample, but require
retention data if present in another feed.

The newer user-supplied Gate 3 matrix was checked against this sample and is
already represented in the component-retention register; its TUF/LNF hormone
retentions, empirical flux references, resistance terms, and cleaning inputs
are also already registered. The 1.35 mPa·s viscosity is still marked
reference-only because its stated basis is fermented juice and the active route
has no pre-membrane fermentation/storage step.

Primary membrane studies do not justify filling the remaining generic-pool
gates with single retention values. A clover-grass juice UF study reports
protein selectivity and strong retention of chlorophyll-binding/photosystem
proteins, but not total lipid or the model's generic dissolved-organic pools
([study](https://doi.org/10.1016/j.seppur.2026.138129)). Pesticide NF studies
report compound-specific rejection and membrane adsorption, affected by water
matrix composition ([Boussahel et al., 2002](https://doi.org/10.1016/S0011-9164(02)00394-6)). PFAS rejection likewise varies with membrane MWCO/charge and
individual PFAS chemistry ([study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11295905/)).
Measurements of dissolved organic nitrogen show that NF can separate some
organic nitrogen from inorganic nitrogen, but the GreenHub
`OrganicNitrogen` component is an N-equivalent bookkeeping pool, not a defined
DON mixture ([study](https://pubmed.ncbi.nlm.nih.gov/20619437/)). These results
support retaining explicit gates until component identity, phase, and feed-
specific membrane data are available; they do not support assigning generic
retention coefficients. The source-by-source applicability assessment is in
`Greenhub/data/Protein recovery/Membrane/biostimulant_retention_evidence_assessment.csv`.

Koschuh et al. (2005) screened nanofiltration and fine ultrafiltration on
fermented grass-biorefinery silage juice, measuring amino acids, lactic acid,
sugars, salts, and colouring substances. Their abstract reports NF fluxes up
to 6.5 L/(m²·h) and high transmission of amino acids and lactic acid through a
PES004H UF membrane ([study](https://doi.org/10.1016/j.memsci.2005.01.049)).
This supports the qualitative possibility that small solutes pass a UF stage,
but the silage feed, membrane, and operating conditions do not match PR7's
current unfermented clarified juice or TUF/LNF membrane options. The paper
reports no phytohormone retention values, so none of its results are used as
active PR7 factors. The source register record S6 has been corrected to the
article's verified DOI.

`Greenhub.phase4_units.BiostimulantMembraneRecovery` is connected as PR7 in the
main Phase 4 → Phase 7 flowsheet. Clarified juice enters the membrane unit;
retentate is `biostimulant_product` and permeate proceeds to anaerobic
digestion/nutrient recovery. No fermentation is inserted. The request must
select a membrane, positive operating flux, and evidence notes for both the
flux and retention matrix. Every nonzero component needs a class retention or
a sourced per-component override for complete allocation. In diagnostic mode,
unmapped mass is conserved at a separate unresolved outlet and completeness is
marked failed; strict validation blocks incomplete runs. The route is
supported for steady-state and seasonal simulation. The unit preserves
component-wise mass and elemental flows and calculates nominal area from
permeate flow / flux. AD2 is incompatible because it bypasses Phase 4; choose
AD0 to leave PR7 permeate undigested, or AD1/AD3 to digest the post-membrane
permeate.

The main-run membrane unit can optionally calculate idealized permeate-side
pressure work from sourced transmembrane pressure and pump-efficiency inputs.
This electricity enters the BioSTEAM utility ledger and can flow into TEA and
LCA; when the pair is absent, the run marks pressure-work energy as unresolved.
The unit still has no crossflow
recirculation, CIP, membrane replacement, installed cost, MEUF surfactant
balance, or product conditioning model. PR7 mass/product flows are simulated,
while full-route energy, CAPEX/OPEX, and qualified-product sales remain
incomplete. `biostimulant_product` is recognized by annual aggregation and TEA
product matching, but revenue remains absent until a product price is explicitly
entered in TEA assumptions. The separate screening endpoint continues to
provide isolated hydraulic/energy/revenue screens and does not change the plant
simulation.

TEA reports a separate membrane-module materials range in EUR using the
BioSTEAM membrane area and supplied technology-specific USD/m² quotations
converted with the dated ECB rate in the register. It is not installed CAPEX.
When full area is resolved, the conservative annual replacement upper bound
(high module price divided by the 2.5-year low lifetime) is included in OPEX;
an area floor alone does not trigger full-area replacement cost. Optional CIP
reagent use and cost are calculated only when solution volume and make-up
fraction have evidence notes. CIP water, heating, labor, downtime, wastewater,
and replacement-event timing remain outside this screen. Crossflow electricity
and pressure-work estimates require their separate sourced inputs. LCA includes
available attributional utility burdens and can include screened CIP chemical
production burdens; unresolved crossflow/auxiliary electricity, membrane
manufacture, CIP waste fate, MEUF surfactant production/recovery, and product
use or substitution remain explicit gaps.

## Input gates before simulation

The integrated PR7 mass-split route is configurable, but the following gates
remain before it supports defensible product-quality, energy, TEA, and LCA
claims:

1. Project measurements to replace or validate the provisional benchmark
   concentrations and free/bound fractions.
2. Per-component retention values for every active clarified-juice component;
   only listed classes are mapped. The current composition leaves structural
   carbohydrates/pectin/starch, lipids, other biodegradable and non-
   biodegradable organics, suspended/inert solids and ash, organic/particulate
   N/P/K, entrapped sugars, heavy metals, persistent organics, pesticides,
   microplastics, pathogen indicators, sand, and litter unmapped. Against the
   checked-in clarified-liquid composition, the exact nonzero unmapped IDs for
   each membrane are `Ash`, `Cellulose`, `EntrappedSugars`, `HeavyMetals`,
   `Hemicellulose`, `InertSolids`, `Lignin`, `Lipids`, `Litter`,
   `Microplastics`, `NonBiodegradableOrganics`, `OrganicNitrogen`,
   `OtherBiodegradableOrganics`, `ParticulateBiodegradableOrganics`,
   `ParticulateNitrogen`, `ParticulatePhosphorus`, `ParticulatePotassium`,
   `PathogenIndicators`, `Pectin`, `PersistentOrganics`, `Pesticides`, `Sand`,
   `Starch`, and `SuspendedSolids`.
3. Product specification and qualified offtake evidence before screened gross
   revenue can be interpreted as saleable product sales. The supplied
   €1.50–€3.50/L range assumes 10× VCF and remains a user-provided screening
   benchmark; it is not a validated market quote or product qualification.
4. Installed membrane-skid and supporting equipment quotations, installation
   boundary, replacement-event labor/downtime/disposal, and project-specific
   CIP operating data remain necessary for complete CAPEX/OPEX. The 2.5–3 year
   lifetime and 48-hour CIP interval are provisional user-supplied screens.
   Current CIP chemical cost requires explicit solution volume and make-up
   fraction; water, heating, labor, downtime, wastewater, and recovery are not
   included. MEUF additionally requires process-grade surfactant price, acid
   identity/stoichiometry, recovery energy, residual limits, and waste fate.
5. Reconciliation of resistance-based flux predictions with the separately
   supplied baseline fluxes and film-model retention with empirical analyte
   retention.

The current route boundary is clarified juice. No fermentation stage is
included.

## Equations and current model boundary

The supplied flux relation is

`dVp/dt = Jv Am = ΔP / (μ (Rm + Rf + Rg))`.

The supplied retention relation is

`R = 1 - Cp/Cf = σ(1 - exp(-Pe))/(1 - σ exp(-Pe))`,
`Pe = Jv δ/Dm`.

GreenHub does not yet have measured viscosity, membrane resistance, fouling or
gel-layer resistance, boundary-layer thickness, analyte diffusivity, or
reflection coefficients for project-specific grass juice. The new dataset now
contains prompt-supplied candidate values, but not a project validation basis.
The resistance equation also requires `Cf/C0`; neither concentration is
supplied. The written gel-resistance description mentions cross-flow velocity,
but the provided equation has no velocity term. Bound-state diffusivity is
missing, so the film equation can only predict free-state retention unless a
bound diffusivity is supplied.

The supplied values do not currently form one self-consistent dynamic model.
For an explicit diagnostic only, using TMP midpoints (4 bar TUF, 9.5 bar LNF)
and `Cf/C0 = 1` gives resistance-model fluxes about 128.5 and 194.9
L/(m²·h), versus baseline fluxes 22 and 12 L/(m²·h). At the empirical LNF
baseline flux of 12 L/(m²·h), the sigma/Peclet equation predicts free IAA
retention about 75%, versus the supplied 96% total analyte retention. These
comparisons are kept separate; neither set silently overwrites the other.

A recent clover-grass juice study reports an average flux near 22 L/(m²·h) at
VCF 3 and TMP near 0.3 bar, but it uses a 60 nm ultrafiltration membrane and
reports crude-protein rejection around 52%. It does not validate the supplied
1–3 kDa TUF or loose-NF hormone retention values; membrane and feed conditions
must match before those data can be transferred
([study](https://doi.org/10.1016/j.seppur.2026.138129)).

The area/revenue screen uses `permeate = feed × (1 − 1/VCF)` and divides by
selected flux and operating hours. It does not predict flux decline, cleaning
downtime, or product purity. Product revenue is gross sales only, based on the
assumed target VCF product volume. It is not calculated from the BioSTEAM
retentate volume and remains hypothetical until the retentate achieves a
validated sale specification.
The screening references are 22 L/(m²·h) for TUF and 12 L/(m²·h) for LNF;
MEUF uses the supplied-range midpoint 22.5 L/(m²·h). These are user-supplied
screening inputs, not GreenHub-validated design values. An empirical flux and
the resistance model are mutually exclusive per request. Resistance flux
requires an explicit TMP, Cf/C0 ratio, measured unfermented clarified-juice
viscosity, and evidence notes.

Target-hormone capture, nominal membrane area, gross revenue, and an uninstalled
membrane-module CAPEX range can be screened under the stated assumptions.
Supplied USD/m² prices are converted to EUR/m² using the dated ECB reference
rate recorded in the parameter register. Membrane module material and annual
replacement screens are reported separately from installed CAPEX; they exclude
skid, installation, labor, downtime, removal, and disposal. They are not a full
installed CAPEX estimate or project discounted cash-flow result. When full
membrane area is resolved, the conservative annual replacement upper bound is
included in OPEX; it is not added when only a known-stream area floor is
available. Complete OPEX and LCA are not calculated. No fermentation
conversion is included.

## API and interface

The Configure page provides a separate PR7 screening panel and full-plant PR7
route controls. Selecting PR7 runs the full plant using the monthly seasonal
feed schedule and the configured membrane split before downstream digestion
and nutrient recovery. The proposed 14-day pre-membrane fermentation and
storage step is excluded; the separate AD selection remains active for the
permeate route.
Annual product mass and volume are integrated across active months, and module
replacement screening is based on peak monthly membrane area. The separate
screen does not modify the plant simulation. The API
also accepts a `biostimulant_route` request object with technology, flux,
evidence notes, and optional retention/source maps for unmapped components.
The transport API exposes:

- `GET /api/v1/biostimulant/options` for the boundary, screening technologies,
  nominal fluxes, and limitations.
- `POST /api/v1/biostimulant/screen` with `feed_volume_m3_year`,
  `technology_id` (`TUF`, `LNF`, or `MEUF`), and `operating_hours_year`; optional
  overrides are `concentration_factor`, `price_EUR_L`, and `flux_L_m2_h`.
  TUF/LNF may use `resistance_flux_model` with sourced positive values for
  TMP (bar), `Cf/C0`, and measured unfermented-juice viscosity (Pa·s). The
  empirical-flux and resistance-model methods are mutually exclusive. MEUF
  requires empirical flux. The response reports the selected `flux_basis`.
  Callers may also provide `component_flows_kg_hr` and explicit
  `component_retention_overrides` with matching `component_retention_override_sources`
  for every overridden ID; nonzero uncovered species are returned as blockers
  instead of being omitted from a claimed full mass split. Caller-supplied flow
  maps require a `component_flows_source` note; the UI labels these as clarified-
  juice flow rates in kg/h and checks their implied volume using 1 kg ≈ 1 L.
  Alternatively,
  `run_id` selects the `clarified_protein_rich_liquid` stream from a completed
  GreenHub run as the component-flow basis (do not combine it with manual flows).
  The UI can submit its latest completed Python run and reports entered annual
  volume versus the volume implied by that run's liquid mass flow and resolved
  density; differences over 5% are marked for review. The TUF/LNF/MEUF
  comparison also retains each isolated BioSTEAM result and compares retentate,
  unresolved mass, area bounds, and mass closure when component flows are
  available, alongside the annual area/revenue/module-cost screens.

Selecting PR7 without route configuration remains gated. Every nonzero
clarified-juice component must have a mapped retention for a complete product
allocation. Unmapped components are conserved in a separate unresolved outlet
and reported with IDs and flows; they are never silently omitted. The Configure
UI requests a diagnostic result so mass-balanced streams remain inspectable,
while the result reports completeness validation as failed. Generic API clients
retain strict validation by default and may explicitly request diagnostic mode.
The separate membrane screen remains available independently.
When all component classes and elemental metadata are covered, the response
includes feed/retentate/permeate mass plus C/N/P/K flows and closure errors.
Elemental totals are withheld if nonzero species remain unmapped or lack model
component metadata.

The POST response returns analyte-equivalent capture by hormone, nominal
membrane area, concentrate volume, gross sales, a membrane-module cost range,
an optional energy-cost and energy-climate subtotal, and explicit TEA/LCA readiness lists. It marks the calculation as
screening-only. Full PR7 mass-flow simulation is active when component
co-retention is complete; energy, full TEA, and LCA remain gated on their own
inputs. If model-stream component flows (or explicit component flows) are
included and all nonzero components are mapped, the response also contains an
isolated BioSTEAM membrane-unit result with retentate/permeate composition,
annualized mass throughput, membrane area, and mass/C-N-P-K balance status. If
mapping is incomplete, only the screening result and exact component blockers
are returned. Blockers include the actual clarified-juice component flow in
kg/h, allowing retention data to be gathered for the real feed inventory.
Benchmark hormone capture remains separate from the feed-stream component
split unless the selected model stream itself contains those hormone pools;
the UI labels this boundary explicitly.

Energy-related TEA/LCA inputs are opt-in: annual electricity/heat, energy prices,
and emission factors must be explicitly supplied with a source note for every
numeric field. The API computes only energy cost and energy-associated climate
burden, and returns missing activity/factor/price fields separately. A complete
energy-only result is not a complete PR7 TEA or LCA; it excludes membrane and
chemical life-cycle impacts, cleaning and surfactant inventories, direct
process emissions, waste treatment, and product substitution/use.

For the energy screen, callers may instead provide a sourced TMP and pump
efficiency to estimate idealized permeate-side pressure work:
`E = ΔP × V_permeate / η`, converted to kWh, with
`V_permeate = V_feed × (1 − 1/VCF)`. This is a lower-bound hydraulic estimate;
it excludes retentate crossflow recirculation, pressure losses, cleaning,
controls, and auxiliary loads. The input gate does not default pump efficiency,
and prevents also supplying annual electricity when this estimate is selected.
The resulting electricity estimate may be combined with sourced electricity
price and emission factors in the existing energy-only TEA/LCA screen.


## Current boundary and literature evidence

PR7 treats clarified juice directly. The currently selected route includes no
pre-membrane fermentation or storage. The later plant anaerobic-digestion route
is independent and may receive PR7 permeate when selected.

The attached hormone and co-retention values are stored as user-supplied,
unverified screening inputs. TUF uses the supplied bound-payload retention
factors (IAA 75%, zeatin 50%, zeatin riboside 45%); its free-pool term is
calculated separately from the supplied sigma/Peclet inputs at the selected
flux. LNF uses the supplied free-solute factors (96%, 95.1%, 94%) and the
supplied protein co-retention for carrier-bound material. The supplied
class-based TUF/LNF co-retentions are registered as nominal screening values;
MEUF class co-retentions remain unresolved where the source did not provide
them. These are not independently validated GreenHub measurements.

The supplied 1.35 mPa·s viscosity is explicitly for fermented grass juice and
is not applied. A search found no numeric viscosity matched to unfermented
clarified GreenHub grass juice and its operating shear/temperature. A pressed
perennial-ryegrass/tall-fescue study states that viscosity was measured but its
accessible full text provides no numeric result or test conditions
([Özköse et al., 2016](https://doi.org/10.15835/nbha44210405)). A separate
study reports 1.50–2.55 mPa·s for ultrasound-treated, non-grass green juice at
100 s⁻¹ across 25–5 °C; it is a context-only comparator and is not transferred
to PR7 ([Öner, 2024](https://doi.org/10.1177/10820132231176872)). These
references are listed in
`Greenhub/data/Protein recovery/Membrane/biostimulant_feed_property_references.csv`.

## Main remaining gates

### Membrane-manufacturing LCA references

The figure and source register keep available manufacturing references visible
without applying them to PR7 totals. Yadav et al. report 3.120–4.399 kg
CO₂-eq/m² for hollow-fiber PSF fabrication under two solvent systems
([study](https://doi.org/10.1016/j.memsci.2020.118987)); these are not the
project's PES spiral-wound TUF or PA thin-film-composite spiral-wound LNF
modules. A later review reports 92.5 kg CO₂-eq per new NF module and 188 kg
CO₂-eq per new UF module, but does not establish a PR7-compatible membrane
area and inventory basis ([review](https://doi.org/10.3390/membranes12090864)).
Consequently, neither per-area nor per-module figures are annualized or added
to the attributional LCA. A matched module bill of materials, area, fabrication
inventory, lifetime/replacement schedule and end-of-life route are still
required.

- Complete measured retention/fate for the nonzero clarified-feed pools,
  including unresolved organics, lipids, nitrogen, pesticides, and other
  constituents; current full-plant diagnostic mode conserves uncovered mass in
  the unresolved outlet.
- Feed-specific unfermented-juice viscosity, TMP, and Cf/C0 for resistance
  flux. The empirical flux option remains available as a labeled user-supplied
  screening input.
- Complete membrane area and installed-skid CAPEX, membrane handling and
  replacement event costs, crossflow and auxiliary energy, and CIP solution
  volume/make-up basis.
- Sale specification and qualified market price for the concentrate. Gross
  revenue screens are hypothetical and do not establish saleable yield.
- Full product/use and waste inventories for complete attributional LCA;
  available utility and CIP screens remain partial and are not netted against
  avoided-product credits.

No missing datum is replaced by a fabricated distribution or default. New
figures use the current design identity and are generated by the reproducible
PR7 figure script; unresolved values are excluded from numeric plot series.
