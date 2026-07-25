# Methodology and Limitations

# 1. Direct Isoelectric Recovery

Model:
- pH adjustment
- protein charge estimation
- solubility prediction
- precipitation kinetics
- coagulation
- solid-liquid separation

Dynamic variables:
pH
protein solubility
precipitated fraction
yield
purity

Limitations:
- grass-specific protein fractions approximated
- precipitation kinetics simplified
- equilibrium assumptions for some proteins
- ionic-strength effects simplified

Missing data:
grass protein pI distribution
protein-specific kinetic constants
activity coefficients

--------------------------------

# 2. Lactic Acid Recovery

Model:
- microbial growth
- sugar consumption
- lactic acid production
- pH evolution
- protein precipitation
- metabolite formation

Supported sub-scenarios:
L. plantarum
L. casei
L. acidophilus
L. delbrueckii
mixed culture

Limitations:
mixed metabolic products simplified
strain-specific kinetics incomplete
enzyme activity ignored

Missing data:
grass juice fermentation experiments
protein recovery validation
industrial productivity

--------------------------------

# 3. Membrane Filtration

Model:
- resistance-in-series
- pore blocking
- cake filtration
- concentration polarization
- rejection
- diafiltration
- cleaning
- energy

Supports:
green/white separation
protein concentration
post-fermentation polishing
post-isoelectric washing

Limitations:
grass slurry rheology incomplete
dynamic rejection empirical
cake compressibility estimated
cleaning recovery estimated

Missing data:
viscosity
TMP optimisation
real fouling coefficients
industrial membrane performance

--------------------------------

# 4. Drying

Spray drying:
atomization
droplet evaporation
heat transfer
mass transfer
water activity
denaturation
particle formation

Freeze drying:
freezing
nucleation
ice crystal growth
primary drying
secondary drying
protein stability

Limitations:
grass kinetics unavailable
collapse temperature estimated
protein sorption estimated
droplet distributions estimated

Missing data:
DSC
freeze microscopy
drying kinetics
protein stability
powder properties

--------------------------------

# Global assumptions

The framework intentionally separates:

Measured parameters

Engineering priors

Scenario assumptions

Future calibration parameters

Every assumption exists in an explicit assumption register.

No hidden constants are allowed.

# Future upgrades

Recommended future modules:

electrodialysis
electrocoagulation
enzyme-assisted recovery
PEF
vacuum drying
fluidised-bed drying
industrial CIP
real equipment sizing
pilot-scale validation
uncertainty propagation
Monte Carlo analysis

