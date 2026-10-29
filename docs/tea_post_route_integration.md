# Post-route TEA integration

GreenHub's screening TEA is a read-only post-processing layer. The empirical or
dynamic process route is built and simulated first. Only then does TEA inspect
the selected scenario IDs, formed units, capacities, throughput, annual
utilities, products, and operating time. TEA does not select chemistry, alter
feed composition, create model overrides, or change mass and energy results.

## Runtime sources

- `Greenhub/data/GreenHub_TEA_Compact_Cost_Register (1).xlsx` is the reviewed
  source workbook.
- `Greenhub/data/tea/tea_cost_register.csv` is the normalized runtime register.
- `Greenhub/tea_costs.py` defines the typed cost record and workbook maintenance
  import. Runtime calculations read the CSV and do not require Excel.
- `Greenhub/application/tea_service.py` implements empirical and dynamic
  post-route calculation.

The normalized register preserves source title, URL, evidence status,
confidence, notes, scope boundaries, and workbook row. The compact generic
upgrader row is expanded into PSA, water-scrubbing, and membrane anchors using
the method-specific base values and capacities stated in the workbook. This is
a transparent normalization, not a new quote.

## Usage

```python
from Greenhub.application.tea_service import (
    TEAFinancialAssumptions,
    TEAProjectBasis,
    calculate_dynamic_tea,
    calculate_empirical_tea,
)

# Run the process first.
simulation_result = simulation_service.execute_run(run_id)

tea = calculate_empirical_tea(
    simulation_result,
    project_basis=TEAProjectBasis(
        operating_hours_per_year=4000,
        capacities={
            # Explicit values are needed where the process result has no
            # compatible design capacity.
            "TEA-011": {"value": 100, "unit": "kg water evaporated/h"},
        },
    ),
    financial_assumptions=TEAFinancialAssumptions(
        project_lifetime_years=20,
        discount_rate=0.08,
        tax_rate=0.0,
        depreciation_method="none",
        # Add product_prices only after a market source or project-approved
        # value exists; otherwise revenue intentionally remains incomplete.
    ),
)
payload = tea.to_dict()

# Dynamic reporting contracts or complete-proxy grid results are accepted.
dynamic_tea = calculate_dynamic_tea(dynamic_report)
```

`ResultService.get_tea(run_id, ...)` provides the same optional empirical
post-processing after a completed run. No TEA fields are added to
`SimulationResult`, so existing empirical outputs are unchanged when TEA is not
requested.

## Selection and anti-double-count rules

- Scenario IDs and formed method names select matching records.
- PSA, membrane, water scrubbing, and MEA are mutually exclusive unless the
  caller explicitly supplies a formed route containing more than one unit.
- Spray and freeze drying are alternatives.
- PEF, ultrasound, and thermal/enzymatic pretreatment are alternatives unless
  explicitly combined.
- CHP and biomethane upgrading remain different gas-product routes.
- Package/subcomponent groups cannot be summed together. The excluded line and
  selected package are reported.
- Rows marked `can_sum_by_default=false` require an explicit route tag or cost
  ID in `TEAProjectBasis`.

## Calculation rules

CAPEX uses only:

```text
scaled cost = reference cost
            * (project capacity / reference capacity) ** scaling exponent
```

All three numeric inputs and compatible units are required. Missing capacities,
reference anchors, scaling exponents, or installed factors remain explicit
missing inputs; no design capacity is invented. Installed CAPEX is `null` when
any selected direct line lacks an installed factor.

Utility and product quantities come from annual simulation outputs when they
exist. Steady-state rates are annualized only when operating hours are supplied.
Consumables require matching simulated quantities or explicit project-basis
quantities. Labor, maintenance, logistics, indirect, site, and disposal lines
require explicit project-basis quantities. Dynamic steps are summed as provided;
missing periods or quantities are not interpolated.

## Report and limitations

The JSON-safe report includes route summary, selected and excluded records,
CAPEX/OPEX/revenue lines, missing inputs, warnings, totals, confidence counts,
source traceability, explicit financial assumptions, replacement schedule,
annual cash flow, and screening financial KPIs. The KPI set includes gross
profit, EBITDA-like operating cash flow, NPV, IRR, simple and discounted
payback, operating cost per wet-feed tonne, cost per protein-product kilogram,
and cost per biomethane Nm3.

Investment returns are calculated only when installed CAPEX, annual OPEX,
required product revenue, project lifetime, and discount rate are complete.
Construction CAPEX is assigned through an explicit spend-fraction schedule.
Tax defaults to zero, depreciation to `none`, working capital to zero, and
residual value to zero, and all four remain visible in the report. Straight-line
depreciation is available only with an explicit depreciation period.
Replacement events use a cost-record lifetime when available or explicit years
from the financial assumptions; their basis is included in the replacement
schedule.

The compact register contains no product-price records. A price must therefore
be supplied as a traceable `TEAProductPrice`/mapping or revenue stays zero and
`revenue_status` remains `incomplete`. Dynamic quantities are summed only from
the reported periods, including biomethane volume; missing periods are never
interpolated. Product-specific costs are simple OPEX intensity indicators, not
multi-product allocations.

`Greenhub/tea_reporting.py` provides fixed-seed valid-scenario samplers and
writes the comparison artifacts in `Greenhub/results/tea_scenario_kpis.csv`,
`Greenhub/results/tea_scenario_kpis.json`, and
`docs/tea_screening_results.md`. Cases with missing inputs remain in these
tables with null investment KPIs.

This is not investment-grade TEA. Remaining work includes confirmed design
capacities, package boundaries, installed factors, vendor quotes, consumable
doses, staffing and logistics plans, site-specific tariffs and product
offtake prices, financing structure, tax/depreciation review, escalation and
currency-date normalization, commissioning/ramp-up, contingencies, and
probabilistic uncertainty analysis.
