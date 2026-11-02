# Post-route inventory and climate screening

GreenHub provides a life-cycle **inventory and climate screening layer**, not a
validated or multi-impact LCA. `Greenhub/application/lca_service.py` consumes a
completed `SimulationResult` after route simulation. Steady-state and the existing
seasonal inventory controller use the same adapter. It does not change process
chemistry, yields, utility demand, route formation, scenario IDs, or defaults.
The earlier `dynamic_economic_environmental.py` illustrative analysis remains a
separate proxy; its unsourced displacement factors are not imported here.

## Scope and functional units

The default boundary is collection to the factory gate. Included groups are
purchased electricity, heat, materials, transport, storage emissions, process
emissions, and waste. Cultivation/land-use change, embodied equipment, and product
use/end of life have explicit exclusion notes. Exclusion means outside this
declared boundary; it does not mean zero environmental burden. Equipment or
feedstock production can be included using additional traceable inventory rows.

The report has no product allocation: it describes the whole plant. Intensities
divide the complete declared-boundary climate total by tonnes of wet feed or dry
feed actually processed. Dry feed is wet feed less water, on the process feed
basis; a missing moisture/water basis must leave dry-feed intensity missing.
Press cake is an external coproduct, never an AD feed by environmental convention.
No wet fertilizer candidate, press cake, recovered water, protein, or biomethane
automatically earns an avoided-burden credit.

`operating_hours_per_year`, `annual_throughput_kg`, and `annual_dry_feed_kg` are
explicit project-basis values. The decision-support facade reconciles these with
simulation quantities and rejects inconsistent post-route throughput overrides.
The common project location/reference year are reported. A factor's source year
remains its actual source year; a project year does not redate that evidence.

## Equations and time integration

For each annual activity `q_i` and compatible factor `f_i`:

```text
burden_i [kg CO2e] = q_i [activity unit] * f_i [kg CO2e/activity unit]
attributional climate = sum(characterized burden_i)
substitution scenario = attributional climate - sum(eligible credit_i)
wet-feed intensity = attributional climate / (annual wet feed kg / 1000)
dry-feed intensity = attributional climate / (annual dry feed kg / 1000)
```

Static electricity is positive purchased demand in kW multiplied by actual
operating hours. Static positive heat in kJ/h is divided by 3600 and multiplied
by operating hours, giving kWh. Negative heat denotes cooling, not a heating
credit; its upstream cooling-service impact needs separate inventory. Negative
electricity/generation is not automatically netted against gross demand.
Self-consumption/export dispatch and substitution require explicit inputs.
Unknown utility demand or an absent utility inventory stays unknown.

Seasonal utility totals are already timestep-integrated kWh and are not
multiplied by operating hours a second time. Seasonal terminal-gas and storage
ledgers are summed across actual periods. Static storage and terminal-gas
ledgers are on the simulated hourly feed basis and are multiplied by operating
hours once. The decision-support facade prevents partial-year simulation totals
from qualifying as complete annual objectives; it does not invent off-season
production.

## Atmospheric fate, storage and nutrients

Process terminal streams (`uncaptured_biogas`, `reject_gas`, `phase7_offgas`, and
`chp_exhaust`) are read once at the external boundary. An internal stream is not
an atmospheric emission. `terminal_gas_fate="unresolved"` is the default and
blocks characterization of a positive climate-relevant gas quantity. Selecting
`"emitted"` is an explicit no-flare/no-recovery scenario, not evidence of actual
venting. A methane fraction alone does not establish leakage mass or its raw-gas
basis; the corresponding inventory remains incomplete.

Storage has two ledgers: incoming residence and carried-inventory reactions.
Each is consumed once. The component-retention model's lost material is an
uncharacterized export, not assumed CO2, methane, leachate, or a retained
intermediate. The reaction-package subset supplies separately balanced gas and
retained-intermediate quantities. Its unresolved species/pathways and leaching
remain explicit gaps even when some methane/CO2 quantities are computable.
`emissions_inventory_complete=False` and storage blockers cannot be removed
merely by marking a group complete in project assumptions. An explicit empty
emissions ledger with no blockers yields an explicit zero-activity row; absent
kinetics do not.

Biogenic CO2 is retained as a memorandum flow. There is no automatic uptake or
permanent-storage credit and no claim of a complete biogenic carbon cycle.
Ammonia and hydrogen sulfide remain visible inventory flows rather than invented
climate factors. Nutrient losses and subsequent N2O formation, eutrophication,
acidification, toxicity, land-use impacts, and water scarcity need relevant
inventory and supported characterization methods before those categories can
be calculated. This carbon-only implementation does not claim to cover them.

## Factors and provenance

`Greenhub/data/lca/climate_factors.json` contains the current default factor
registry. Direct factors use IPCC AR6 GWP100: fossil CO2 = 1 kg CO2e/kg, non-fossil
methane = 27 kg CO2e/kg, and N2O = 273 kg CO2e/kg **N2O**, not kg nitrogen.
The methane value follows the corrected table, not the older 27.2 draft value.
See [IPCC AR6 WGI Chapter 7, Table 7.15](https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/)
and [published errata](https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Errata.pdf).
These characterize supplied species masses; they do not validate those masses.

The logistics adapter receives fuel-combustion emissions already calculated by
`Greenhub/logistics.py`; it applies the registry's fossil-CO2 identity factor
to that characterized mass. Missing vehicle inputs or logistics limitations
still produce missing quantities and do not become zero.

Electricity and heat factors intentionally have `value=null` and
`source_status="missing"`. A supplier/year/location and boundary-matched factor
is required. Electricity generation-only emissions are not silently represented
as cradle-to-gate supply emissions. Heat factors must describe delivered heat
with explicit efficiency/upstream scope. Reagents, vehicles, materials,
equipment and waste require their own traceable factors and annual quantities.

Every factor record contains `value`, `quantity_unit`, `basis`, `geography`,
`reference_year`, `source_url`, `source_table_page`, `retrieval_date`,
`source_status`, `evidence_class`, `applicability`, `conversion_method`,
`uncertainty`, `method`, and `warning`. `unit` is derived as
`kg CO2e/{quantity_unit}`. Overrides require a complete metadata object, not a
bare number. Published metadata are not implicitly inherited when replacing a
factor value. Engineering assumptions remain possible, explicitly tagged and
unvalidated; they must not be described as measurements.

## Inventory contract and completeness

An additional annual inventory row has this shape:

```json
{
  "flow_id": "measured_storage_methane",
  "group": "storage_emissions",
  "quantity": null,
  "unit": "kg",
  "factor_id": "biogenic_methane",
  "accounting_key": "storage_methane_to_air",
  "direction": "burden",
  "compartment": "air",
  "source_status": "missing",
  "source_id": "site_storage_measurement_required",
  "warning": "Placeholder contract example; no measured value supplied."
}
```

Flow metadata additionally supports basis, geography/year, URL/table/retrieval
date, evidence class, applicability, conversion and uncertainty. Quantities must
be finite and nonnegative or null. Activity/factor units must match exactly;
unit conversions must be done explicitly upstream and described in provenance.
Duplicate `accounting_key` values are rejected, including duplicates between the
process adapter and `additional_inventory`. Do not supply both an aggregate
package footprint and its already-included subcomponents under different keys.

Each included group needs an explicit burden inventory and a declaration such
as `{"status":"complete","note":"Scope and completeness evidence"}` in
`inventory_completeness`. Such declarations do not fill missing quantities or
factors. A known zero quantity is allowed without a factor. An absent inventory
is not zero, and memorandum flows alone cannot assert a zero climate burden.
Every omitted group requires an exclusion rationale. A narrow direct-emissions
scope can be complete for that declared scope; it must not be called total
life-cycle climate or compared with different boundaries without harmonization.

Important output fields:

| Field | Meaning |
|---|---|
| `totals.climate_kg_co2e_per_year` | Attributional total, null until included burden inventory is complete |
| `totals.partial_climate_kg_co2e_per_year` | Sum of known contributions; null when none are known |
| `totals.substitution_credit_kg_co2e_per_year` | Separate complete credit scenario; null when disabled/incomplete |
| `totals.partial_substitution_credit_kg_co2e_per_year` | Known credits; never silently presented as a complete net |
| `totals.substitution_net_kg_co2e_per_year` | Net only when attributional and credit inventories are complete |
| `missing_inputs` | Burden/group gaps blocking the attributional objective |
| `substitution_missing_inputs` | Credit gaps; these do not erase an otherwise known attributional total |
| `inventory_gaps` | Missing memorandum quantities |
| `readiness.climate_objective_eligible` | Complete for the declared climate boundary; not validated LCA |
| `readiness.validated_lca_ready` | Always false |

Substitution is off by default. Credit rows require `counterfactual`,
`quality_verified=true`, and `available_quantity`; displaced activity cannot
exceed that eligible quantity. The caller must substantiate grade, purity,
moisture, nutrient availability, destination market and substitution service.
No candidate-product wet mass is treated as equivalent to a saleable fertilizer.

## Running and verification

```python
from Greenhub.application.lca_service import calculate_empirical_lca

# result is an existing, completed empirical or seasonal SimulationResult.
report = calculate_empirical_lca(
    result,
    project_basis={"operating_hours_per_year": 744},
).to_dict()
# Inspect report['missing_inputs']; defaults deliberately do not complete LCA.
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_lca_service.py tests/test_decision_support.py
```

Tests cover missing versus zero inventories, static energy units, seasonal
integration, nonmutation, gas fate, storage incompleteness, wet/dry functional
units, independent credit readiness, JSON-safe output and duplicate accounting.
Synthetic complete scoped fixtures test calculation logic; they provide no
evidence that real GreenHub environmental performance is validated.

Remaining evidence includes site utilities and supplier footprints, reagent and
transport quantities, full storage/process loss pathways, leakage/flare fate,
waste treatment, cultivation and equipment where in scope, and verified
coproduct substitution. No additional impact category is reported until an
appropriate method and characterization factors are provided.
