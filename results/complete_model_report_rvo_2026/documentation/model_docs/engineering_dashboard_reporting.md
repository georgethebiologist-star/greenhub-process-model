# Engineering dashboard reporting

The empirical and dynamic proxy dashboards remain separate calculation pathways, but now use a consistent decision-reporting structure.

## Included views

- Seasonal biomass availability, processed intake, unused biomass, utilization, and peak throughput.
- Separate charts for bulk streams, small products, biomethane, electricity in MWh, and heat in GJ.
- A staged, keyboard-focusable process story with inputs, outputs, active units, utilities, warnings, and evidence maturity.
- Annual engineering intensities including product per feed, biomethane per feed, electricity per feed, utilization, and unmodelled-utility counts.
- Baseline/current/browser-saved scenario comparison with absolute deltas.
- Frontend exports for scenario JSON, monthly CSV, annual-summary CSV, assumptions CSV, and Markdown.

## Trust boundary

Every report displays its source status. The bundled preview is a fixed known-good baseline and does not respond to changed controls. Dynamic outputs remain proxy/assumption enabled and not validated. Empirical outputs are only described as live scientific results after the Python run and its annual reporting bundle both return successfully.

Press cake remains an external output in the dynamic pathway and is not included in the in-project AD feed. Zero utility values are shown as **Not modelled** where the model does not provide a meaningful demand, rather than presented as proven zero consumption.

Browser-saved comparisons and exports stay on the user's device. They are decision aids, not a replacement for the Python provenance package, laboratory validation, TEA, LCA, or detailed equipment design.
