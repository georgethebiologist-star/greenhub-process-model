from Greenhub.phase4_validation import PROTEIN_POOL_IDS


def test_true_protein_inventory_excludes_peptides_and_amino_acids(simulated_phase4_pr3):
    model = simulated_phase4_pr3
    feed = model.streams["clarified_protein_rich_liquid"]
    protein = sum(float(feed.imass[ID]) for ID in PROTEIN_POOL_IDS)
    assert "Peptides" not in PROTEIN_POOL_IDS
    assert "AminoAcids" not in PROTEIN_POOL_IDS
    assert protein == model.validation.protein_balance["protein_entering_kg_hr"]
