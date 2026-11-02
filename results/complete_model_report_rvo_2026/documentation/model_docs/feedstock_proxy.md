# Feedstock Proxy Layer

`Greenhub/feedstock_proxy.py` provides a read-only proxy inventory for roadside grass feedstock evidence. It does not activate parameters, change scenarios, or integrate with the seasonal controller.

The primary source is `Greenhub/data/Pre-treatment/Feedstock/roadside_grass_composition_scientific.csv`. Direct roadside rows with numeric SI values are preferred over older overlapping Czubaszek/Wrobel rows. Older rows are fallback-only when the new CSV has no usable direct value for the same canonical field.

Actual GreenHub measured data must override all proxy values. These proxies are only a traceable reference layer for future integration decisions.

Safe active proxy fields currently include moisture/as-received, volatile matter, ash, C, H, O, N, S, C:N ratio, bulk density, total protein, and extractive sugars. Total protein is treated only as total protein, not soluble protein. Extractive sugars are treated only as total/extractive sugars, not fermentation-ready sugar.

BMP rows are retained as reference-only unless explicitly requested. Indirect non-roadside rows and missing rows are not returned as active proxy values.

Protein and sugar proxy rows are not enough to activate protein precipitation. Soluble protein, insoluble protein, amino-acid profile, true protein, soluble sugar release, acid demand, titration behavior, and precipitation kinetics remain separate unresolved inputs.
