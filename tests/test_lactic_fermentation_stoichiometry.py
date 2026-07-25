from Greenhub.reactions import REACTION_LIBRARY


def test_glucose_to_lactic_acid_reaction_is_atom_and_mass_balanced():
    reaction = REACTION_LIBRARY["lactic_fermentation"]
    assert abs(float(reaction.mass_balance_error())) < 1e-9
    assert max(
        (abs(float(i)) for i in reaction.atomic_balance_error().values()),
        default=0.0,
    ) < 1e-9
