# Pareto figure methodology

This figure library is produced by `scripts/generate_rvo_pareto_pngs.py` from `Greenhub/results/pareto_rvo_2026/`. It uses the saved no-PEF BioSTEAM outputs, paired RVO-labelled financial overlays, and exact candidate metadata. See [`docs/RVO_PARETO_METHODOLOGY.md`](../../docs/RVO_PARETO_METHODOLOGY.md) for the full model boundary, assumptions, equations, scenario definitions and limitations.

## Front construction and candidate selection

Protein-enabled and protein-bypassed designs are optimized separately. The 2D fronts minimize net carbon while maximizing pre-tax screening NPV, or minimize present value of assumed public support while maximizing NPV. A third front minimizes net carbon and support PV while maximizing NPV. Fronts are nondominated sets within the saved sample; they do not establish a global optimum. The 11 displayed representative candidates are selected from the 3-objective set, ordered from rank 0 at its highest-NPV endpoint toward rank 10 at its lowest-net-carbon endpoint. Rank 0 is rose and rank 10 green. Labels use Protein–Biogas–N–P–K order, with `X` for bypass.

When the 3D front is projected to a 2D plot, selected candidates can be dominated in that projection. This is an expected consequence of preserving the joint three-objective candidate set, not evidence that the 2D front computation includes those dominated points. Separate 2D front points are also saved in the structured output.

## Figure inventory and units

Each figure is indexed in `rvo_pareto_figure_index.csv`. Product, energy, CAPEX, OPEX, NPV, support and carbon metrics use the units printed in the index and axes. Biomethane mass is converted to CH₄ normal volume with the documented pure-methane basis of 0.716 kg/Nm³ at 0 °C and 101.325 kPa; the resulting volume is not raw biogas volume. 3D plots are static projections of the stored third objective, with rank endpoints identified in the legend.

The existing GreenHub background, ink, rose, green, blue and gold palette is retained. PNGs are exported at approximately 2,250 px width and 300 DPI. The new Pareto and candidate panels are visually inspected for clipping, overlap, readability and scaling after generation.

## Interpretation limits

The subsidy assumptions are hypothetical screening cases and are not verified DEI+ rates, SDE++ tariffs, eligibility decisions or awarded amounts. Net carbon is a mixed operational climate and assumed product-carbon-retention screening metric in t C/year; it is not a complete LCA or durable-removal result. The electricity/heat/process climate inventory is gate-to-gate and excludes upstream equipment, feedstock, transport and downstream burdens. Stored-run hotspot charts display positive attributional burdens; credits and climate offsets are not shown. The model is steady-state for these candidates, so time-series kinetics and Monte Carlo confidence intervals are not generated without defensible data and distributions.
