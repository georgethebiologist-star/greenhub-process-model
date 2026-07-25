from Greenhub.systems import create_phase4_scenario


def test_pr2_heat_coagulation_has_no_acid_dose():
    model = create_phase4_scenario("PR2").simulate()
    assert model.streams["acid_solution"].F_mass == 0.0
    assert model.streams["protein_precipitation_slurry"].imass["HeatCoagulatedProtein"] > 0.0
