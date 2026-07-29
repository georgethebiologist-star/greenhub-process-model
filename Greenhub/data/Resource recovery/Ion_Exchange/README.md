# GreenHub ion-exchange dataset suite

## Scope
Ammonium, potassium and other nutrient-cation exchange from digestate and agricultural wastewater
using clinoptilolite, modified zeolites, mordenite, ion-exchange resins and other validated media.

## Mandatory capacity distinction
The package uses separate `capacity_type` values:

- `theoretical_CEC`: structural or manufacturer exchange capacity;
- `theoretical_isotherm_capacity`: fitted Langmuir/Sips maximum;
- `measured batch uptake` or `equilibrium capacity`;
- `breakthrough_based_operating_capacity`;
- `working_cycle_capacity` or regenerated capacity.

Only breakthrough or demonstrated working-cycle capacity should normally size a continuous column.
A Langmuir qmax or theoretical CEC must never be substituted for operating capacity.

## Dynamic calibration
The breakthrough file includes explicit breakthrough bed volumes and hydraulic conditions where
directly reported. Full C/C0 time or bed-volume profiles remain required for mechanistic dynamic
calibration and are registered as missing.

## Real-matrix limitations
Most quantitative studies use synthetic ammonium solutions or municipal wastewater. Digestate
contains competing K, Na, Ca, Mg, dissolved organic matter and suspended solids. Single-solute
capacity must therefore be derated only through a cited competitive model or real-matrix test,
not through an invented factor.

## Regeneration
Media-capacity restoration, ammonium desorption and recovered-product yield are separate metrics.
The suite includes five-cycle zeolite data and hybrid NaOH regeneration evidence, while chemical
consumption and product composition remain blank where not directly reported.

## Costs
A reported annual regeneration scenario is retained with its original USD currency and plant scale.
It is OPEX, not equipment CAPEX. Unsupported equipment costs, duties, energy use and scaling
exponents remain blank.

## Integration
Use `parameter_id` as immutable provenance and `python_variable` as the GreenHub model key.
Always filter by target ion, media, capacity type, particle size, matrix and operating conditions.
