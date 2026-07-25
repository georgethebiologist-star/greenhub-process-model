from Greenhub.reactions import REACTION_LIBRARY


def test_calcium_phosphate_reaction_is_balanced_but_disabled_in_baseline(simulated_phase4_pr3):
    reaction = REACTION_LIBRARY["calcium_phosphate_precipitation"]
    assert abs(float(reaction.mass_balance_error())) < 1e-9
    assert simulated_phase4_pr3.streams["conditioned_protein_depleted_liquid"].imass["CalciumPhosphate"] == 0.0
