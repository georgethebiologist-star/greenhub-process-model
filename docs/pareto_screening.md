# Offline 2,000-scenario Pareto screening

Decision support evaluates and plots exactly 2,000 seeded, frontend-only screening
cases without requiring the Python API. This is a distinct lightweight proxy,
not 2,000 empirical BioSTEAM runs, a calibrated surrogate, or 2,000 validated
feasible plants. Existing scientific calculations, LCA readiness, backend
batch limits and strict ranking eligibility remain unchanged.

## Design and uncertainty

The default basis is 30,000 tonnes/year available, 5,160 operating hours/year,
3,000 kg/h maximum processing capacity, five nominal full-feed staff and a
minimum of two staff. A seeded stratified random sample covers valorization
fractions from 10% to 50%. Only this fraction is processed. Unprocessed biomass
is outside the plant boundary and earns no income or environmental credit.

Each case draws PEF on/off; protein bypass, acid, heat or combined recovery;
AD bypass, mesophilic or thermophilic digestion; gas product bypass with flaring,
water scrubbing, membrane or PSA; and nutrient bypass, separation, phosphorus,
ammonia or combined recovery. AD bypass forces gas and nutrient bypass in this
topology. No inactive fermentation, CO2-assisted protein or CHP pathway is
represented as supported scientific code.

Prices use low/high values in the existing Netherlands product-price register.
Tariff, wage and haulage sensitivities are explicit assumed envelopes around
cost-register rates. Yield, method response, utility shares, CAPEX uncertainty,
staffing, leakage, transport footprint, consumables and climate ranges are
engineering assumptions, not measured confidence intervals. All ranges, units,
source references and evidence statuses are visible and editable. Sampling is
independent uniform, with no inferred correlations. A different random seed
changes the study; the same seed reproduces all 2,000 points.

`paretoReference.json` stores the compact saved process/cost anchors and source
run ID. It includes raw methane mass, avoiding use of compressed physical gas
volume as Nm3. Gas sales convert recovered CH4 to dry ideal Nm3 at 273.15 K /
101325 Pa, then apply LHV 9.94 kWh/Nm3 to the EUR/MWh price. Saleability and
certificate eligibility remain conditional.

## Scaling and economic objective

Annual feed = available feed × valorization fraction.
Flow = annual feed × 1000 / operating hours.

For each active equipment item:

    cost = reference cost × uncertain cost multiplier
           × (0.15 + 0.85 × (flow / reference flow)^exponent)
    exponent = mean(register item exponent, sampled scale exponent)

The 15% fixed share is assumed. Bypassed equipment is removed. Alternate
method CAPEX/yield/utility responses are explicitly uncalibrated comparisons.
Missing installation, civil, replacement and other project costs remain
excluded, not verified zero. This is screening capital, not complete installed
plant CAPEX.

    staff = max(2, ceil(full-feed staff × fraction^staffing exponent
                       × route complexity))

Route complexity ranges 0.6–1.0, with the complete chain normalized to one.
Staff work 1,500 paid hours/person/year. Thus matched smaller plants have
nonincreasing staff and lower equipment cost; minimum staff remain two.
Costs include registered wage/haulage/energy prices, 2% capital maintenance and
an explicit uncertain reagent/media allowance. Market grade is unverified.

The x-axis maximizes annualized screening profit:

    operating profit = product revenue − included operating costs
    annualized profit = operating profit − capital × capital recovery factor
    CRF = r / (1 − (1+r)^(-years)); CRF = 1/years when r = 0

Default recovery is 20 years at 8%. There is no inferred tax, financing,
inflation, residual value or disposal fee. Negative-profit cases stay visible;
model feasibility does not imply profitability.

## Climate objective and scope

The y-axis maximizes net CO2 offset in tonnes CO2e/year:

    offset = (fossil-gas substitution credit − included burdens) / 1000
    gas credit = sold recovered methane Nm3 × sampled gas displacement factor

Burdens include purchased electricity, heat, transport and methane release.
Methane GWP100 is 27 (AR6). Gas-product bypass assumes 98% flare destruction
plus upstream leakage, not automatic gas revenue or energy credit. With
upgrading, unrecovered methane is conservatively treated as emitted. No
fertilizer/protein displacement, cultivation, embodied equipment, storage,
waste or complete reagent-production impacts are inferred. Fertilizer quality,
gas market counterfactuals and unmodeled emission pathways remain unresolved.
Positive offset means an avoided burden relative to the explicit substitution
counterfactual; negative offset means added emissions. This is not carbon
removal or a full comparative LCA.

## Feasibility, ranking and interaction

Checks reject incompatible downstream routes, flow above plant capacity,
products above the feed/dry-matter envelope and nonfinite calculations. These
are screening constraints, not mass/element conservation, hydraulic design,
product compliance or empirical scientific validation. All cases are plotted;
failed cases are grey and excluded from the frontier. Export includes reasons.

Both axes are maximized. The Pareto implementation retains nondominated cases,
including ties, among model-feasible samples. It is tested against a brute-force
dominance calculation. Because designs have different uncertainty draws,
favourable draws can enter the front: this is a sampled design/uncertainty
frontier, not a robust optimum or evidence to choose a commercial design.
Re-evaluate candidates with matched assumptions and full scientific models.

Hover reveals feed fraction/flow, annualized and operating profit, net offset,
credits/burdens, capital, staff, revenue/OPEX and route configuration. Clicking
or keyboard selection keeps metadata visible. Full sampled inputs and product
KPIs are available in details. Export downloads all 2,000 cases plus active
basis, bounds, seed, constraints and limitations. Invalid edits leave the last
valid study displayed with an error until corrected and regenerated.
