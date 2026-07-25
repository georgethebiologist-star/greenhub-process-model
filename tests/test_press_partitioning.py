from Greenhub.systems import create_phase3_scenario


def test_press_retains_structural_solids_and_extracts_solubles():
    model = create_phase3_scenario("F2").simulate()
    cake = model.streams["fibre_cake"]
    juice = model.streams["raw_liquid_fraction"]
    assert cake.imass["Cellulose"] > juice.imass["Cellulose"]
    assert juice.imass["SolubleProtein"] > cake.imass["SolubleProtein"]
    assert juice.imass["PotassiumIon"] > cake.imass["PotassiumIon"]

