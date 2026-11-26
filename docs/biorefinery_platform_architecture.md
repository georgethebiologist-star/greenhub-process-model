# Broader biorefinery platform: project and data architecture

## Purpose

GreenHub remains the first runnable project, not the platform itself. The shared
platform layer contains project registration, technology-family vocabulary, and
cross-project dataset discovery. Chemistry, process topology, defaults, routes,
and evidence gates stay owned by each project adapter.

```text
Shared biorefinery platform
  ├─ project registry and adapter contract
  ├─ technology-family vocabulary (common names + legacy identifiers)
  ├─ dataset discovery and provenance crosswalk
  └─ shared UI/API shell (future composition point)
       └─ GreenHub project adapter (current runnable implementation)
            ├─ Greenhub/application services and contracts
            ├─ Greenhub/integration.py process builder
            ├─ GreenHub-specific parameter defaults and route gates
            └─ project-scoped grass, site, weather, economics, and process data
```

## Runtime boundary

- `biorefinery_platform/registry.py` defines project descriptors, model adapters,
  and a registry that does not import or implement any project's chemistry.
- `Greenhub/application/project_adapter.py` registers the existing integrated
  GreenHub builder as a project plug-in. Steady-state and quasi-dynamic runs use
  the same adapter, preserving the current process builder and run contracts.
- `SimulationService` selects a project adapter at service-composition time. The
  existing `SimulationRequest.project_id` remains a compatibility/provenance
  field and is not silently repurposed as a model selector. A versioned request
  selector or deployment configuration is required before API clients can choose
  among multiple projects.
- Only `greenhub` is registered and runnable today. A descriptor or dataset
  catalog for another waste stream is not evidence that its process model exists.

## Phase names and compatibility

The new family labels are: Phase 3 **Pretreatment and fractionation**, Phase 4
**Protein recovery**, Phase 5 **Anaerobic digestion**, Phase 6 **Biogas
upgrading** (a child of the digestion-to-biomethane chain), and Phase 7 **NPK
recovery**. “Phase” remains useful as a historical cross-reference, not the
platform's extensibility boundary.

Existing process-area IDs, F*/PR*/AD*/BG*/NR* scenario IDs, workbook tabs, module
names, parameter identifiers, and request/result schemas remain stable. UI/API
labels may use the family vocabulary without changing identifiers or route
behavior. Cross-cutting separation and utilities are mapped as shared families;
they do not introduce new route selections.

## Data organization and transfer rules

`Greenhub/data/platform/technology_families.json` is the controlled vocabulary.
`Greenhub/data/platform/projects/greenhub.json` is the project's registration
descriptor. Regenerate the two Phase 3–7 crosswalks with:

```powershell
python scripts/build_phase_3_7_reuse_catalog.py
```

The generated catalog under `Greenhub/data/platform/catalogs/` keeps two layers
separate:

1. `phase_3_7_dataset_reuse_catalog.*`: staged evidence assets linked to the
   global dataset manifest and source register.
2. `phase_3_7_runtime_input_reuse_catalog.*`: canonical runtime input records
   linked to their source, basis, units, quality class, applicability, and
   existing metadata.

Dataset source sidecars are read in both existing repository forms:
`dataset.source.json` and the legacy `dataset.csv.source.json`. Non-empty source
register fields take precedence, while blank registry fields no longer erase
metadata already recorded in a sidecar. The catalog normalizes common DOI, URL,
locator, license, retrieval-date, evidence, and activation-status field names.
This is an indexing rule only; it does not make a staged dataset runtime-ready.

The cross-project metadata profiles are:

- `biorefinery_platform/schemas/project_descriptor.schema.json` for registering
  a project adapter and its technology-family coverage.
- `biorefinery_platform/schemas/dataset_reuse_record.schema.json` for normalized
  dataset discovery records. Each record carries project ownership, one or more
  technology-family links, an explicit data-scope class, evidence and activation
  status, provenance, and a `metadata_gaps` list.
- `biorefinery_platform/schemas/material_profile_record.schema.json` for
  reusable material profiles. Mutually exclusive mass-balance components are
  separated from analytical properties; pH, conductivity, CFU/g, particles/kg,
  and trace concentrations retain their own unit, method, sample basis, and
  detection limit. Analytical properties are never silently normalized into a
  wet-mass closure, and a non-detect is not a measured zero. Calculated
  analytical interpretations have a separate optional
  `derived_analytical_properties` collection, with equation, input-property
  IDs, method sources, limitations, quality class, and activation state; they
  cannot silently become measured observations or mass-composition components.
- `biorefinery_platform/examples/material_profiles/ryegrass_press_juice_varriale_2024.json`
  is a worked example of a technology- and material-specific liquid profile.
  It keeps concentrations as analytical properties, has no asserted mass
  composition or closure, and remains reference-only.
- `biorefinery_platform/examples/material_profiles/varta_2026_greenhub_whole_grass.json`,
  `varta_2026_reterra_road_verge_grass_n36.json`, and
  `varta_2026_greenhub_grass_juice.json` preserve three user-supplied, sample-
  specific laboratory records. Total nutrient assays remain analytical
  properties rather than exclusive component masses. The grass-juice sample
  has no confirmed parent-feed link or yield, so it cannot calibrate a
  separation calculation. These examples are reusable material records, not
  new UI defaults or active process streams.
- `biorefinery_platform/examples/material_profiles/perennial_ryegrass_silage_maus_2020.json`
  preserves an external literature material profile for its own AD context;
  it is not a raw-roadside-grass substitute or a GreenHub runtime input.
- `biorefinery_platform/schemas/parameter_equation_record.schema.json` for
  parameters, equations, physical constants, and methods. Reuse requires an
  explicit unit, basis, applicability domain, input dependencies, and
  provenance. A generic equation may be portable while its empirical
  coefficients remain material-, site-, or technology-specific.

## Declarative route templates

`biorefinery_platform/schemas/process_route_template.schema.json` defines the
platform-level shape of a route without moving process chemistry into the shared
layer. A route references technology-family IDs, project-owned technology
instances, material-state transitions, parameter identifiers, and activation
gates. It stores no parameter values and does not call a solver. The GreenHub
project descriptor references
`greenhub-grass-protein-biogas-npk-reference-v1`, a `reference_only` example
under `Greenhub/data/platform/routes/`. It shows where the broader tool can
compose alternative technologies while preserving the current GreenHub adapter
as the only executable project.

The route template records the current resolution order—request override,
selected project material profile, project parameter registry, declared
structural state, then explicitly missing—and requires missing-value handling to
block or remain report-only. This is descriptive metadata, not a new override
implementation. The request/result schemas, workbook columns, scenario IDs,
defaults, and adapter execution path are unchanged. Each future project owns its
route graph, material profiles, parameter mapping, and activation gates; a
shared technology-family label never transfers a GreenHub feed value or
performance coefficient.

Data scope uses five reusable labels: `context_independent`,
`technology_specific`, `material_or_site_specific`,
`technology_and_material_specific`, and `context_specific_unclassified`.
Classifications inferred from the existing portability text are marked for
review. Context independence is never inferred from a dataset's subject alone.
The current 3–7 asset catalog contains no empirical asset classified as
context-independent. A physical constant or general balance equation belongs
in a separately defined parameter/equation record, with units and applicability
limits, rather than being represented as a transferable empirical dataset.

Portability labels are explicitly marked as inferred until reviewed. Feedstock,
digestate, and site-dependent values remain context-specific. Generic equations,
physical constants, and balance methods should be represented as separately
qualified parameter/equation records; an empirical dataset is never treated as
context-independent merely because it concerns a reusable technology.

Material state is part of the data identity, not a display label. Raw feed,
pressed juice, press cake, clarified juice, digestate, and recovered products
must be represented as separate profiles. A unit operation may connect those
profiles only through a declared stream transformation with its own measured
or explicitly modeled yield and component-partition basis. Similar names or
shared species do not make concentrations transferable across those states.
The Varriale 2024 press-juice example demonstrates this rule: its filtered-juice
concentrations are discoverable as a source-backed comparison, but do not
populate the GreenHub raw-feed UI fields or imply a press yield. A future
project adapter can select an appropriate material profile and technology
route while retaining source IDs, process-state lineage, measurement basis,
and user-override precedence.

Keep source observations separate from project-activated derived inputs. A
project adapter may define a transparent proxy conversion from one or more
source rows, but that derived record must carry its own basis, units, equation,
quality class, uncertainty, applicability and source-row links. For example,
GreenHub's nitrate-ion profile proxy is derived from measured nitrate-N in
cultivated ryegrass plus the separate VARTA dry-matter fraction; it remains
project/material-specific and must not be inherited as a default by another
biorefinery project. Shared UI controls should bind to the selected project's
derived input profile while preserving project-level overrides and provenance.

The GreenHub profile also maps the project-supplied VARTA chloride result for
the same July 2026 whole-grass sample to the model chloride-ion pool. The
reported 11.7 g/kg dry matter is converted using that sample's measured dry
matter. This is project-specific measured evidence, not a global grass default;
the assay method and full ion/charge balance are not available.

The same rule applies to contaminant proxies: GreenHub's summer roadside-grass
Cr/Ni/Cd/Hg/Pb aggregate uses Czubaszek et al. source rows plus VARTA dry matter,
and remains a GreenHub profile value with class C transferability—not a general
grass default or a compliance result. The raw source observations retain their
own B evidence class. A future project must use its own contaminant assay or
explicitly select a separately qualified source proxy.

The GreenHub pesticide input is likewise a project-profile proxy, not a shared
grass constant. Its current class-C estimate is derived from Prechsl et al.'s
reported detection count and mean residue concentration in South Tyrol public-
site grass; non-detections are treated as zero, making the estimate a lower
bound. It is not a roadside-grass or VARTA measurement. The measurement
acquisition requirement remains open for analyte-specific assays on matched
incoming and cleaned GreenHub feed, with detection limits and removed-material
balance. Other projects must not inherit this value by default.

Biological acidification with lactic-acid bacteria is represented as a
protein-recovery technology subfamily, not as a new shared chemistry model.
The AQUACOMBINE halophyte dataset is indexed under the protein-recovery family
with material-and-technology-specific scope and remains reference-only. Its
saline *Salicornia*/*Tripolium* outcomes and `<1 mL` HCl bound must not be
transferred to grass juice or used to infer a GreenHub acid dose. A future
project may add its own adapter route and measured inputs while reusing the
family vocabulary and provenance profile.

The UI feed profile's acetic-acid default now uses the untreated landscape-grass
measurement reported by Heller et al. (2023, Table 1): 0.09 g/kg fresh matter,
converted directly to 0.00009 kg/kg wet feed. The study reports two analytical
replicates but no standard deviation. The publication is class-B evidence; its
transfer from German orchard/lowland-meadow grass to the Dutch roadside/VARTA
profile is class C only. This is a replaceable proxy, not a VARTA measurement.
The same amount is deducted from the unmeasured closure residual, so total wet
mass remains one. See [the source article](https://doi.org/10.3390/en16248091).

The legacy `PersistentOrganics` model component represents the PFAS pool, not
all persistent organic chemicals. Its former unsupported placeholder is now a
class-C estimate derived from the control first-cut orchard-grass values in
Kosiarski et al. (2025, Table 2). Three replicate sums, the ND-as-zero rule,
the dry-to-wet conversion, and source/transfer limitations are recorded in the
profile and CSV sidecar. This greenhouse control is not a Dutch roadside or
VARTA assay, not a compliance result, and not evidence that PFAS are absent.
Matched, analyte-resolved assays on incoming grass and process fractions remain
required. The source article is CC BY-NC 4.0, so reuse must respect its
non-commercial terms; the proxy is GreenHub-specific and is not a shared
platform default.

The current index does not automatically promote staged datasets, calculate
missing measurements, or alter defaults. D4 remains reserved for evidence
connected to a calculation, covered by tests, and reported by the application.
One source asset now has a partial D4 designation: only the five Czubaszek
summer metal observations used by the tested GreenHub profile proxy. The source
dataset as a whole remains reference evidence, and canonical Phase 3–7 runtime
parameters have not been promoted to D4 by that change. Stable IDs currently
resolve only within this repository; a public FAIR release still needs a
repository/DOI or other persistent identifier, license metadata, retrieval
dates, and complete table/page locators.

The measurement acquisition register is
`Greenhub/data/platform/catalogs/phase_3_7_measurement_acquisition_register.csv`.
It is a project-scoped list of open measurements, not measured values. The
CSV records distinguish GreenHub field needs from reusable measurement
patterns and are conditional on the selected technology. The companion human
checklist is
`outputs/019fb031-1e4e-70f1-ba3b-498e77233c06/phase_3_to_7_measurement_acquisition_canonical.xlsx`.
It is a concise working view, not a replacement for the CSV's full method,
sampling, metadata, and owner fields. Five Phase 3 feed-composition entries
cross-reference the canonical `REQ-GH-P3-06` through `REQ-GH-P3-10` IDs. A
literature comparator does not close a GreenHub measurement gap unless its
material, route, basis, and operating conditions actually match.

The active feed-composition panel exposes 70 compound fields. The profile has
74 records: A=2, B=0, C=18, no D-class assignments, 49 unmeasured numeric
fallbacks, one calculated profile-closure residual, and four structural/model-
state initializations with no evidence class. Sixteen visible M values are
nonzero compatibility fallbacks, not observations or evidence of presence or
absence; 33 are zero fallbacks. The R value is a baseline mass-closure residual,
not a measured or separately identified pool. Four profile records are not user-editable: two downstream
protein-product zeros and the degraded-protein and digester-biomass initial
states. These S records describe model boundaries rather than incoming grass
assays. The directly measured VARTA total N, P, K, Ca, Mg, Na, S, and trace nutrients are preserved in
`analytical_reference` and the Phase 3 feed specification, but they are not
chemical-species measurements and therefore do not justify assigning those
elements to ammonium, phosphate, potassium-ion, or particulate pools. The
current species-level UI defaults remain a confirmed measurement/representation
gap. No proxy was promoted on the basis of total-element data alone. M, R, and S
describe missingness, calculated closure, and model state; none are A/B/C/D
evidence grades. Numeric fallbacks remain active for compatibility and must not
be mistaken for measured or literature-supported values.

The shared material-profile and parameter/equation schemas now distinguish
`quality_class` from `value_status`: a measurement, literature value,
literature-derived assumption, fitted value, unmeasured numeric fallback,
derived residual, and structural state can be represented without conflating
evidence, observation status, and runtime activation. The parameter/equation
field is optional for backwards compatibility. Project adapters still own
whether any fallback is eligible for a calculation; the shared schema does not
authorize transferring GreenHub values to another material or technology.

The dynamic evidence adapter additionally exposes Ravindran et al.'s measured
grass-whey BMP as an explicitly selected, report-only comparison. It is a
cultivated-ryegrass co-product diluted two-fold with wash water, not GreenHub
isoelectric supernatant; it is not a continuous-reactor yield, and the source
does not state the Table 3 gas reference condition. It does not replace the
default BMP record, alter process balances, or make GreenHub's AD model
calibrated. This illustrates the shared pattern: source observations can be
catalogued once and selected by a project adapter only under explicit
material/technology and evidence gates.

At the 2026-11-11 refresh, the catalog contains 503 Phase 3–7 dataset assets
and 538 canonical runtime input records. Phase 3 has 69 records, Phase 4 has
80, Phase 5 has 81, Phase 6 has 174, and Phase 7 has 134. No canonical
runtime-parameter D4 promotions were made. At the source-asset level, VARTA
and Czubaszek have partial D4 readiness; Hoekstra's ryegrass nitrogen-fraction
means and the opt-in protein-recovery records are D4, each with the stated
transfer/applicability limits. These source-asset states do not promote a
canonical runtime parameter. An earlier pre-normalization snapshot used D for
unsupported entries. The rebuilt 2026-11-11 runtime
catalog contains 538 records: 528 E placeholders and 10 B inputs, with zero D
grades in any phase. E means unverified/unsupported numeric fallback; blank
means no value. The normalized input catalog maps legacy D/E to E without
changing values, activation, or runtime precedence. A DOI by itself does not
upgrade a record: the source, basis, method, and applicability must support the
specific value. Evidence grade, observation/fallback status, transferability,
and D1–D5 calculation maturity remain separate axes. The runtime catalog's
source-assets index reports 503 assets, 123 without a linked source-register
record, 151 without a DOI/stable identifier, and 442 with at least one
provenance gap; these groups overlap. The per-record
`metadata_gaps` field distinguishes missing source links from missing fields on
a linked source. Dataset sidecars can carry multiple source records; these are
matched to global source-register rows by source ID or DOI instead of copying
one paper's metadata across every linked paper. The five-paper drying-energy
evidence asset now has complete source-level metadata and remains reference-only
with its distinct reported bases.

### Shared versus project-owned evidence

The platform is a registry and data-contract layer, not a shared repository of
universal process coefficients. Reuse is governed by four distinct questions:

| Layer | Reusable across projects when… | Project-owned responsibility |
| --- | --- | --- |
| Measurement and data vocabulary | Units, identifiers, analytical methods, and metadata are standardized | Map local laboratory labels and document method/basis differences |
| Material observations | The material identity and sample state match | Select a material profile; never promote a roadside-grass measurement to another feedstock by default |
| Technology-family equations | The equation form, units, validity domain, and operating envelope match the selected equipment | Supply coefficients, route topology, calibration, and process-specific validation |
| Site and project assumptions | Usually not portable: climate, supply, tariffs, labor, price, policy, and contracts are location/time dependent | Own the scenario defaults and provenance |

At the current catalog build, `context_independent_empirical_assets=0`. This is
intentional: none of the collected grass, juice, digestate, or equipment-run
observations has passed a review for context-independent empirical reuse.
Shared unit definitions and metadata schemas exist, but a property or equation
is not context-independent merely because it is physically general; its
validity range, material/technology domain, and source must be recorded.

The standard data flow is `project descriptor → project adapter → material
profile and parameter registry → technology-family route → simulation outputs`.
The adapter performs explicit unit/basis mappings and applicability checks;
it cannot silently inherit another project's defaults. The catalog is globally
searchable, while calculation activation remains project-local. A second
project should become runnable only after its adapter has material/technology
coverage, closure and route tests, and explicit missing-data behavior. The
shared UI/API selector remains a future composition step, not a promise that
the present GreenHub API can already run other contexts.

### Food-composition evidence correction

The active cellulose, hemicellulose, and ADL-derived lignin values are unchanged,
but are now labeled class C at the GreenHub-profile level. Their source
measurements are class B from cultivated Polish perennial ryegrass; using them
for the VARTA roadside-grass profile and converting with its measured moisture
is a literature-derived transfer assumption. Czubaszek et al. (2023), Table 5,
adds seasonal measurements from Polish roadside/median grass as B-class,
reference-only records. They are not applied to the UI defaults: seasons are
not weighted by GreenHub supply, the assays overlap, and replacing the three
fractions would violate the current profile closure. No composition numbers or
run payloads changed in this correction.

The broader-project data flow is deliberately asymmetric: globally discoverable
observations and reusable methods are evidence, not shared defaults. A project
adapter selects a material profile, maps source rows through explicit
unit/basis conversions, and owns the resulting defaults, applicability,
scenario gates, and missingness. Technology-family equations can be reused
only when their units, inputs, validity domain, and required evidence are
declared. User-entered run overrides remain higher priority than the selected
project profile, which remains higher priority than the existing registry or
structural fallback according to the current service path. GreenHub is the
only runnable project; broader context registration does not imply the UI or
API can yet switch runtime projects.

New feed-composition references must carry a material scope. For example,
Olszewska (2021; DOI `10.3390/agronomy11030468`) reports multi-year,
cultivar- and management-group marginal observations for cultivated perennial-
ryegrass WSC and crude protein. These B-tier source measurements can support
comparisons in a future ryegrass adapter, but they are neither
context-independent constants nor roadside-grass defaults. The source tables do
not expose joint treatment observations or uncertainty spreads, so the data
catalog retains the reported marginal summaries and their applicability limits
instead of fitting a seasonal equation.

## Adding another project

1. Define its project descriptor, context, supported technology families, and
   data ownership; do not copy GreenHub's feed or site defaults.
2. Implement a project-local adapter for the standard model-build boundary.
3. Register it in the application composition layer with an explicit project ID.
4. Add project-specific datasets and applicability metadata; cite the sources and
   distinguish measured, direct-literature, proxy, and assumption evidence.
5. Add balance, route, parity, and missing-data tests before exposing the project
   in the shared UI/API.
6. Only after multiple projects exist, add a versioned client-level project
   selector. Do not use arbitrary historical `project_id` strings to dispatch
   process chemistry.

For another context, reuse the project-neutral descriptor and normalized
metadata profiles, then add source records under that project's own identifier.
Do not copy GreenHub's feedstock values, grass-specific degradation evidence,
site tariffs, temperature series, product assumptions, or fitted performance
into a second project's defaults. Reuse methods and equations only when the
recorded basis and applicability match.

## Current Phase 3–7 evidence snapshot

The generated catalog reports current counts directly from the repository
manifests. It is a discoverability and transferability index, not a completeness
claim. Source DOI coverage, unlinked assets, metadata gaps, and runtime quality
classes are exposed in `catalog_manifest.json` and the per-asset CSV rather than
being silently filled.

### Project-local sugar profile example

Source ranges for Italian ryegrass sugars (Masaki & Ohyama, DOI
`10.2508/chikusan.47.205`) remain class-B range observations. The GreenHub
adapter uses normalized range midpoints only to split the separate roadside-
grass aggregate from Smit et al. (DOI `10.1021/acssuschemeng.2c00838`); the
resulting values are class-C GreenHub proxies, with total sugar mass conserved.
The range dataset is indexed as partial D4 because this mapping is tested and
reported, not because the ryegrass observations became GreenHub measurements.
Another project's feed adapter must select its own aggregate and allocation
rather than inherit the GreenHub sugar ratios. This illustrates the platform
boundary: global source discovery is reusable, while each project owns its
material-specific defaults, transfer assumptions and override precedence.
