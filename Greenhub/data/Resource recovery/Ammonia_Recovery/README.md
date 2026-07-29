# GreenHub ammonia-recovery dataset suite

The package covers ammonia stripping and acid absorption from digestate and high-ammonia liquids.

`ammonia_stripping_experiments.csv` includes exact half-hour time-series values from 0.5–3 h
at 10, 20, 30 and 40 °C. These support empirical dynamic calibration but not a transferable kLa.

TAN removal is not automatically ammonia recovery. Close the mass balance across remaining TAN,
captured ammonium product and gaseous emissions.

The freshwater NH4+/NH3 relation is included symbolically. High-ionic-strength digestate may
require activity correction. Unsupported kLa/HTU/NTU values, packing dimensions, product
concentrations, equipment costs and scaling exponents remain blank.

Zero external energy in the full-scale case means CHP-supplied utilities, not zero process duty.
