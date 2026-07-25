from Greenhub.reactions import EMPIRICAL_TRANSFORMATIONS, REACTION_DEFINITIONS, build_reaction_library


def test_molecular_reactions_are_balanced():
    library = build_reaction_library()
    assert set(library) == {definition.name for definition in REACTION_DEFINITIONS}
    for reaction in library.values():
        # Charged formulas include electron-mass differences in ThermoSTEAM.
        assert abs(float(reaction.mass_balance_error())) < 1e-5
        atom_errors = reaction.atomic_balance_error().values()
        assert max((abs(float(i)) for i in atom_errors), default=0.0) < 1e-9


def test_empirical_transformations_are_labeled_and_mass_consistent():
    for transformation in EMPIRICAL_TRANSFORMATIONS:
        transformation.validate()
        assert "protein" in transformation.name
