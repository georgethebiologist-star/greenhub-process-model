# GreenHub PEF and Ultrasound Pretreatment Dataset Suite

Path: `Greenhub/data/Pre-treatment/PEF_Ultrasound/`

## Scope
The package separates pulsed electric field (PEF) and ultrasound pretreatment. It prioritizes fresh alfalfa and fresh ryegrass–white-clover PEF experiments. The ultrasound condition matrix is based on a peer-reviewed pumpkin-leaf study using mechanically ground, lyophilized leaf powder resuspended in water; those rows are explicitly classified as a proxy rather than fresh wet grass data.

## Main files
- `pef_operating_parameters.csv`
- `pef_treatment_response.csv`
- `ultrasound_operating_parameters.csv`
- `ultrasound_treatment_response.csv`
- `pef_ultrasound_equation_registry.csv`
- `pef_ultrasound_scenario_controller.csv`

Supporting governance files:
- `dataset_manifest.csv`
- `source_register.csv`
- `assumption_and_missing_data_register.csv`
- `validation_report.csv`

## Observation policy
Every experimental treatment condition is a separate observation. The ultrasound source tested six amplitudes (20–70%) and ten durations (0–20 min), creating 60 retained condition rows. Where the numerical response existed only in a plotted figure, the response cell is blank, `data_status=missing`, and `response_availability=graph_only_not_digitized`.

## Critical scientific limitations
1. The PEF grass-clover pilot is directly transferable only near its tested feed mixture and equipment conditions.
2. The alfalfa PEF study does not report pulse width, pulse shape, conductivity, current waveform, delivered energy or temperature rise. Specific energy is therefore not calculated.
3. The ultrasound source reports homogenizer input power, but not calorimetrically delivered acoustic power or exact slurry loading. Power density and specific energy remain blank.
4. Pumpkin leaves were lyophilized before ultrasound extraction. These results must not be represented as validated fresh-grass response data.
5. The ultrasound kinetic equation is copied from the source, but no kinetic constant is populated because exact source-fitted values were not available in an accessible table.
6. Generator input power must not be treated as acoustic power without calorimetric calibration.

## Integration guardrails
The scenario controller blocks predictive calculations when required energy, conductivity, geometry, loading, or calibration data are absent. Missing values must remain blank and must never be silently replaced by zero or generic defaults.

## Encoding and format
All CSV files are comma-separated UTF-8 with BOM. Numeric cells contain one value only. Equations and citations are stored in dedicated text columns.
