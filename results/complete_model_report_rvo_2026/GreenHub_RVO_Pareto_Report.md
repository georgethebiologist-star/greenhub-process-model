# GreenHub RVO Pareto analysis

Current no-PEF BioSTEAM screening launch. Data assembled 2026-11-02T18:24:18Z UTC; seed 20261102; 128 sampled designs per protein group.

## Scope and decision objectives

Separate protein-enabled and protein-bypassed process routes were optimized. The analysis contains three sampled Pareto views: net carbon minimized with NPV maximized; assumed support present value minimized with NPV maximized; and a three-objective front combining all three. The sample is bounded by the specified design space, not a proof of global optimum.

All physical cases use F1 feed preparation (PEF disabled). The four support what-if cases are paired onto each simulated process design, so financial support changes do not alter process outputs. Support amounts are user-supplied screening assumptions, not confirmed awards or official tariff determinations.

## Support cases

| Case | Named authority and programme | CAPEX grant | Operating support | Duration |
|---|---|---:|---:|---:|
| A | A · RVO DEI+ 30% + RVO SDE++ €20/t feed proxy | 30% | €20/t wet grass/year | 15 years |
| B | B · RVO DEI+ 45% + RVO SDE++ €40/t feed proxy | 45% | €40/t wet grass/year | 15 years |
| C | C · RVO DEI+ 60% + RVO SDE++ €60/t feed proxy | 60% | €60/t wet grass/year | 15 years |
| D | D · RVO SDE++ €50/t feed proxy (OPEX only) | 0% | €50/t wet grass/year | 15 years |

## Front sizes

| Protein route | Net carbon vs NPV | Support PV vs NPV | Carbon, NPV, support |
|---|---:|---:|---:|
| Protein enabled | 3 | 19 | 129 |
| Protein bypassed | 4 | 26 | 106 |

## Selected candidates

Ranks are sampled from the three-objective front. Rank 0 has the highest NPV; rank 10 is the lowest-net-carbon endpoint among the selected candidates. Product-route switch labels use Protein-Biogas-N-P-K; 1 means present and 0 means bypassed.

### Protein enabled

| Rank | P-B-N-P-K | Route | Case | Feed (t/y) | Net carbon (t C/y) | NPV (€) | Support PV (€) |
|---:|---|---|:---:|---:|---:|---:|---:|
| 0 | P1-B1-N1-P1-K1 | PR3/BG4/NR7 | C | 24,204 | -3,208.0 | 18,039,491 | 13,798,787 |
| 1 | P1-B1-N1-P1-K1 | PR2/BG4/NR7 | C | 22,224 | -2,946.8 | 16,181,913 | 12,675,052 |
| 2 | P1-B1-N1-P1-K1 | PR3/BG4/NR7 | D | 24,204 | -3,208.0 | 14,599,369 | 10,358,665 |
| 3 | P1-B0-N0-P0-K0 | PR1/BG0/NR0 | C | 26,896 | -3,772.0 | 9,242,464 | 14,152,223 |
| 4 | P1-B1-N0-P1-K0 | PR1/BG3/NR2 | C | 27,114 | -3,786.6 | 9,296,779 | 15,027,774 |
| 5 | P1-B1-N1-P0-K0 | PR2/BG3/NR3 | C | 29,783 | -4,150.8 | 10,491,516 | 16,558,923 |
| 6 | P1-B1-N0-P0-K0 | PR1/BG3/NR0 | C | 27,345 | -3,818.2 | 8,934,227 | 14,992,753 |
| 7 | P1-B0-N0-P0-K0 | PR1/BG0/NR0 | C | 25,672 | -3,600.4 | 8,959,951 | 13,519,177 |
| 8 | P1-B0-N0-P0-K0 | PR3/BG0/NR0 | C | 25,039 | -3,500.2 | 8,396,748 | 13,191,755 |
| 9 | P1-B0-N0-P0-K0 | PR3/BG0/NR0 | D | 29,975 | -4,190.2 | 7,026,312 | 12,828,571 |
| 10 | P1-B0-N0-P0-K0 | PR3/BG0/NR0 | C | 29,975 | -4,190.2 | 9,942,938 | 15,745,197 |

### Protein bypassed

| Rank | P-B-N-P-K | Route | Case | Feed (t/y) | Net carbon (t C/y) | NPV (€) | Support PV (€) |
|---:|---|---|:---:|---:|---:|---:|---:|
| 0 | P0-B1-N1-P1-K1 | PR0/BG2/NR7 | C | 29,075 | -3,879.8 | 20,883,904 | 16,279,667 |
| 1 | P0-B1-N1-P1-K1 | PR0/BG2/NR7 | D | 29,075 | -3,879.8 | 17,047,456 | 12,443,219 |
| 2 | P0-B1-N1-P1-K1 | PR0/BG2/NR7 | B | 29,075 | -3,879.8 | 15,569,666 | 10,965,428 |
| 3 | P0-B0-N0-P0-K0 | PR0/BG0/NR0 | C | 27,648 | -3,887.9 | 8,712,470 | 14,460,167 |
| 4 | P0-B1-N0-P0-K0 | PR0/BG2/NR1 | C | 27,824 | -3,894.3 | 7,479,761 | 15,269,912 |
| 5 | P0-B0-N0-P0-K0 | PR0/BG0/NR0 | D | 27,648 | -3,887.9 | 6,084,795 | 11,832,492 |
| 6 | P0-B1-N0-P0-K0 | PR0/BG2/NR1 | D | 27,824 | -3,894.3 | 4,117,756 | 11,907,907 |
| 7 | P0-B1-N0-P1-K0 | PR0/BG3/NR2 | D | 28,376 | -3,972.2 | 3,643,226 | 12,144,318 |
| 8 | P0-B0-N0-P0-K0 | PR0/BG0/NR0 | B | 27,648 | -3,887.9 | 3,914,179 | 9,661,876 |
| 9 | P0-B1-N0-P1-K0 | PR0/BG3/NR2 | B | 28,376 | -3,972.2 | 2,037,927 | 10,539,019 |
| 10 | P0-B1-N0-P1-K0 | PR0/BG3/NR2 | C | 28,376 | -3,972.2 | 7,170,175 | 15,671,267 |

## Interpretation limits

NPV is a pre-tax 20-year screening calculation at 8%, using high direct uninstalled equipment CAPEX, current partial operating margin, and the assumed support schedule. It excludes financing, escalation, replacement, working capital, residual value, installation costs, and taxes. It is not investment-grade NPV.

Net carbon is operational gate-to-gate climate load converted to carbon equivalent, less assumed carbon retained in press-cake furniture and nutrient-rich solids. It is not full life-cycle climate impact or a verified durable-removal result. Scope and assumptions are documented in `documentation/RVO_PARETO_METHODOLOGY.md`.

Negative and dominated results are retained in the evidence batches. Candidate ranks and visual projections are not probability statements. Model warnings and evidence limitations remain in the batch records rather than printed over the figures.

## Figure library

The exact source PNGs are copied under `figures/`; 98 figure records are listed in `rvo_pareto_figure_index.csv`. The PDF includes the indexed figure sequence as an atlas.
