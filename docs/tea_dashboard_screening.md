# Dashboard TEA screening

Decision support now defaults to a visible screening toggle and five people at
1,500 paid hours/person/year. At the register's EUR47.90/paid hour, annual labour
is EUR359,250. Headcount is editable; process operating hours are independent.

The strict TEA calculation remains available by disabling the screening toggle.
Screening is a post-process estimate; it does not change flows, chemistry or LCA
readiness. Explicit cost IDs, exclusions, quantities and capacities take priority.

Screening includes labour, feedstock haulage, registered delivered heat, and
routine maintenance at the register's 2% of calculated capital. Mechanical wear
is excluded to avoid overlap with top-down maintenance. Haulage uses processed
wet tonnes as an assumption, not measured deliveries.

Capacity hierarchy is explicit project inputs, compatible process conversions,
and labelled screening assumptions: liquid density 1000 kg/m3, whole-feed
hydraulic envelope, one-hour vessels. Gas volume is calculated from component
moles at 273.15 K/101325 Pa on a dry basis for Nm3. Representative gas streams do
not establish seasonal peak design. The per-kWe AD reference is multiplied by
an energy-equivalent comparator using methane LHV 9.94 kWh/Nm3 and assumed 35%
electric efficiency. This does not activate CHP or create electricity credits.
Missing reference capacities permit unscaled prices only for per-package,
per-unit or per-system references, with a warning. Capacities are not invented
from unrelated dimensions.

Missing installation factors no longer suppress the screening capital estimate:
direct equipment cost is retained and installation exclusions are warned per
line. The result is called screening capital; complete installed CAPEX stays
unavailable. Product benchmarks are activated visibly and remain conditional on
product grade and marketability. Physical biomethane m3 are derived at reported
stream state; they are not silently relabelled Nm3.

The dashboard displays the known-cost operating balance even when completeness
gates remain unresolved. Missing reagents/adsorbent consumption, civil/indirect
scope, installation and price-year harmonization remain visible; this balance
is not complete profit. NPV/IRR still require complete scope and explicit
financial assumptions. Complete LCA still needs utility factors, materials,
transport, waste, storage/process emission inventories and fate, and scope
completeness. The historical dynamic proxy remains a separate illustrative model.

## Frontend baseline and visual previews

The Decision support page bundles `frontend/src/data/decisionBaseline.json`, a
compact snapshot from run `37134f6d6b1c4866ac75e1538e12a9f7` using commit
`be1c03b3`. It is a saved screening case, not a fresh simulation. The frontend
can show it without a reachable Python backend. A successful live evaluation
replaces the snapshot; offline errors never manufacture a new process result.
An entry on Overview opens the TEA/LCA dashboard.

Cost and revenue charts include only known values; tables retain missing lines.
The financial preview assumes an initial screening-capital outlay and constant
annual known-line operating balance, a 20-year life and 8% discount rate by
default. Life, discount rate and hypothetical annual cash flow are editable.
No taxes, replacements, escalation, missing installation or residual value are
inferred. IRR is solved from the discounted cash-flow root; when cash flows
never change sign, it is reported as no IRR. Payback is not reached when
cumulative cash flow does not recover capital within the selected horizon.
These local previews never change strict backend financial completeness,
scientific outputs, objective eligibility or Pareto ranking.

Climate previews separately use the existing 0.20 electricity proxy, an explicitly
illustrative 0.202 kg CO2e/kWh delivered-heat coefficient, and an editable assumed
emitted fraction of tracked methane (100% by default, not established actual
fate), characterized at AR6 GWP100 27. These are partial scenario contributions,
not a complete LCA. Missing transport, storage, material, waste and other gas
pathways remain listed; no coproduct substitution credit is inferred. Wet/dry
intensities divide only this preview subtotal by the corresponding feed basis.

Deploying the frontend bundle publishes the baseline preview even before the
Python backend is connected. Git push alone does not prove Render deployment;
Render's service must deploy the commit, through automatic or manual deployment.
