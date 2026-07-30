# Activated Reference Pathway

## Activation

`Protein recovery/Isoelectric/recovery.csv`, row `REC-001`, is activated only for scenario `PR1` in `literature_default` and `expert_override` modes. The reported value is 0.34 kg recovered N per kg incoming N for grass-clover cleared juice at approximately pH 4–4.5.

The local source register identifies la Cour et al. (2019), *Enhancing Protein Recovery in Green Biorefineries by Lignosulfonate-Assisted Precipitation*, DOI `10.3389/fsufs.2019.00112`, with the recovery discussed around Figure 4. The source dataset passed the Checkpoint 1 row audit and was previously D3 reference-only.

## Mapping

GreenHub applies the 0.34 fraction only to the lumped `SolubleProtein` pool. A recovery fraction transfers equivalently when the N fraction within that pool is treated as constant, but this is not a claim that total N equals protein. Non-protein nitrogen remains outside the protein pool and is not precipitated by this activation.

## Exclusions

The source does not provide a GreenHub titration curve, pH-response kinetics, mechanical separator sizing, power, or CAPEX. None was invented. Centrifuge records remain blocked because of duplicate identities, and `PR3` remains structural because the cited direct-precipitation evidence does not establish combined heat/wash performance.

Project grass-juice measurements must validate protein basis, feed applicability, pH, and recovered-product composition before design or economic use.
