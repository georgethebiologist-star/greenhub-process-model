
def test_phase4_system_contains_complete_combined_train(simulated_phase4_pr3):
    IDs = {unit.ID for unit in simulated_phase4_pr3.system.units}
    assert {"M401", "H401", "R401", "C401", "W401", "D401", "DR401", "M402", "M403"} <= IDs
    assert simulated_phase4_pr3.streams["dry_protein_product"].F_mass > 0.0
