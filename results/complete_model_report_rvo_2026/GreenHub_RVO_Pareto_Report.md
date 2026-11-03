# GreenHub RVO Pareto analysis

Current no-PEF BioSTEAM screening launch. Data assembled 2026-11-03T12:21:09Z UTC; seed 20261102; 128 sampled designs per protein group.

## Scope and decision objectives

Separate protein-enabled and protein-bypassed process routes were optimized. The analysis contains three sampled Pareto views: net carbon minimized with NPV maximized; assumed support present value minimized with NPV maximized; and a three-objective front combining all three. The sample is bounded by the specified design space, not a proof of global optimum.

All physical cases use F1 feed preparation (PEF disabled). The four support what-if cases are paired onto each simulated process design, so financial support changes do not alter process outputs. Original modeled sales and partial OPEX are used unchanged: no assumed cost savings or yield/revenue uplifts are applied. Support amounts are user-supplied screening assumptions, not confirmed awards or official tariff determinations.

## Support cases

| Case | Named authority and programme | CAPEX grant | Operating support | Duration |
|---|---|---:|---:|---:|
| C30 | C30 · RVO DEI+ CAPEX grant 30%; dynamic SDE++ value €1.87/Nm³ biomethane | 30% | €1.87/Nm³ biomethane (dynamic by candidate output) | 15 years |
| C45 | C45 · RVO DEI+ CAPEX grant 45%; dynamic SDE++ value €1.87/Nm³ biomethane | 45% | €1.87/Nm³ biomethane (dynamic by candidate output) | 15 years |
| C60 | C60 · RVO DEI+ CAPEX grant 60%; dynamic SDE++ value €1.87/Nm³ biomethane | 60% | €1.87/Nm³ biomethane (dynamic by candidate output) | 15 years |
| C0 | C0 · no CAPEX grant; dynamic SDE++ value €1.87/Nm³ biomethane | 0% | €1.87/Nm³ biomethane (dynamic by candidate output) | 15 years |

## Front sizes

| Protein route | Net carbon vs NPV | Support PV vs NPV | Carbon, NPV, support |
|---|---:|---:|---:|
| Protein enabled | 9 | 10 | 78 |
| Protein bypassed | 2 | 12 | 120 |

## Selected candidates

Ranks are sampled from the three-objective front. Rank 0 has the highest NPV; rank 10 is the lowest-net-carbon endpoint among the selected candidates. Product-route switch labels use Protein-Biogas-N-P-K; 1 means present and 0 means bypassed.

### Protein enabled

| Rank | P-B-N-P-K | Route | Case | Feed (t/y) | Net carbon (t C/y) | NPV (€) | Support PV (€) |
|---:|---|---|:---:|---:|---:|---:|---:|
| 0 | P1-B1-N1-P1-K1 | PR3/BG4/NR7 | C60 | 24,204 | -3,208.0 | 3,216,023 | 1,626,824 |
| 1 | P1-B1-N1-P1-K1 | PR3/BG4/NR7 | C45 | 24,204 | -3,208.0 | 2,873,926 | 1,284,727 |
| 2 | P1-B1-N1-P1-K1 | PR3/BG4/NR7 | C30 | 24,204 | -3,208.0 | 2,531,829 | 942,629 |
| 3 | P1-B1-N1-P1-K1 | PR3/BG4/NR7 | C0 | 24,204 | -3,208.0 | 1,847,634 | 258,435 |
| 4 | P1-B1-N0-P0-K0 | PR1/BG3/NR0 | C45 | 27,345 | -3,818.2 | -5,829,115 | 1,351,015 |
| 5 | P1-B1-N0-P0-K0 | PR1/BG3/NR0 | C60 | 27,345 | -3,818.2 | -5,591,803 | 1,588,327 |
| 6 | P1-B0-N0-P0-K0 | PR1/BG0/NR0 | C60 | 25,672 | -3,600.4 | -5,429,473 | 334,864 |
| 7 | P1-B0-N0-P0-K0 | PR1/BG0/NR0 | C60 | 26,896 | -3,772.0 | -5,508,895 | 339,508 |
| 8 | P1-B0-N0-P0-K0 | PR1/BG0/NR0 | C60 | 24,314 | -3,409.9 | -5,341,248 | 329,628 |
| 9 | P1-B0-N0-P0-K0 | PR1/BG0/NR0 | C45 | 26,896 | -3,772.0 | -5,593,772 | 254,631 |
| 10 | P1-B0-N0-P0-K0 | PR3/BG0/NR0 | C60 | 29,975 | -4,190.2 | -5,972,643 | 350,912 |

### Protein bypassed

| Rank | P-B-N-P-K | Route | Case | Feed (t/y) | Net carbon (t C/y) | NPV (€) | Support PV (€) |
|---:|---|---|:---:|---:|---:|---:|---:|
| 0 | P0-B1-N1-P1-K1 | PR0/BG2/NR7 | C60 | 29,075 | -3,879.8 | 3,940,186 | 2,048,684 |
| 1 | P0-B1-N1-P1-K1 | PR0/BG2/NR7 | C45 | 29,075 | -3,879.8 | 3,603,235 | 1,711,733 |
| 2 | P0-B1-N1-P1-K1 | PR0/BG2/NR7 | C30 | 29,075 | -3,879.8 | 3,266,284 | 1,374,782 |
| 3 | P0-B1-N1-P1-K1 | PR0/BG2/NR7 | C0 | 29,075 | -3,879.8 | 2,592,382 | 700,880 |
| 4 | P0-B1-N0-P1-K0 | PR0/BG3/NR2 | C45 | 28,376 | -3,972.2 | -6,531,026 | 2,346,739 |
| 5 | P0-B1-N0-P1-K0 | PR0/BG3/NR2 | C30 | 28,376 | -3,972.2 | -6,805,547 | 2,072,217 |
| 6 | P0-B1-N0-P0-K0 | PR0/BG2/NR1 | C60 | 27,824 | -3,894.3 | -7,105,818 | 1,651,151 |
| 7 | P0-B1-N0-P1-K0 | PR0/BG3/NR2 | C0 | 28,376 | -3,972.2 | -7,354,590 | 1,523,174 |
| 8 | P0-B1-N0-P0-K0 | PR0/BG2/NR1 | C45 | 27,824 | -3,894.3 | -7,350,924 | 1,406,045 |
| 9 | P0-B1-N0-P0-K0 | PR0/BG2/NR1 | C30 | 27,824 | -3,894.3 | -7,596,030 | 1,160,939 |
| 10 | P0-B1-N0-P1-K0 | PR0/BG3/NR2 | C60 | 28,376 | -3,972.2 | -6,256,505 | 2,621,260 |

## Interpretation limits

NPV is a pre-tax 20-year screening calculation at 8%, using high direct uninstalled equipment CAPEX, current partial operating margin, and the assumed support schedule. It excludes financing, escalation, replacement, working capital, residual value, installation costs, and taxes. It is not investment-grade NPV.

Net carbon is operational gate-to-gate climate load converted to carbon equivalent, less assumed carbon retained in press-cake furniture and nutrient-rich solids. It is not full life-cycle climate impact or a verified durable-removal result. Scope and assumptions are documented in `documentation/RVO_PARETO_METHODOLOGY.md`.

Negative and dominated results are retained in the evidence batches. Candidate ranks and visual projections are not probability statements. Model warnings and evidence limitations remain in the batch records rather than printed over the figures.

## Figure library

The exact source PNGs are copied under `figures/`; 98 figure records are listed in `rvo_pareto_figure_index.csv`. The PDF includes the indexed figure sequence as an atlas.
