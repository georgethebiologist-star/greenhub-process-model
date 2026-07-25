
import biosteam as bst

from Greenhub.phase4_units import ProteinPrecipitation, precipitation_parameters_from_mapping


def test_combined_precipitation_creates_both_recovered_pools(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["R401"]
    assert unit.transfers_kg_hr["SolubleProtein_to_PrecipitatedProtein"] > 0.0
    assert unit.transfers_kg_hr["SolubleProtein_to_HeatCoagulatedProtein"] > 0.0


def test_zero_protein_feed_creates_no_protein(phase4_values):
    feed = bst.Stream("zero_protein_feed", Water=100.0, units="kg/hr")
    unit = ProteinPrecipitation(
        "R499",
        ins=feed,
        outs="zero_protein_slurry",
        parameters=precipitation_parameters_from_mapping(
            phase4_values,
            acid_enabled=True,
            heat_enabled=True,
        ),
    )
    unit.simulate()
    assert sum(unit.transfers_kg_hr.values()) == 0.0
    assert unit.outs[0].imass["PrecipitatedProtein"] == 0.0
