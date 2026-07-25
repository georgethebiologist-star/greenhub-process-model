
from dataclasses import replace

import biosteam as bst

from Greenhub.phase4_units import NeutralizationMixer


def test_baseline_neutralization_consumes_residual_hcl(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["M403"]
    assert unit.base_demand.pure_base_kg_hr > 0.0
    assert unit.neutralized_acid_kg_hr > 0.0
    assert unit.outs[0].imass["HydrochloricAcid"] < 1e-9


def test_calcium_hydroxide_neutralization_forms_calcium_chloride(simulated_phase4_pr3):
    parameters = replace(
        simulated_phase4_pr3.parameters["neutralization"],
        base_type="CalciumHydroxide",
    )
    liquid = bst.Stream(
        "calcium_base_liquid",
        Water=100.0,
        HydrochloricAcid=1.0,
        units="kg/hr",
    )
    base = bst.Stream("calcium_base_solution")
    unit = NeutralizationMixer(
        "M499",
        ins=(liquid, base),
        outs="calcium_conditioned_liquid",
        parameters=parameters,
    )
    unit.simulate()
    assert unit.outs[0].imass["CalciumChloride"] > 0.0
    assert unit.outs[0].imass["HydrochloricAcid"] < 1e-9
