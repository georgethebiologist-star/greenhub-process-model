import pytest

from Greenhub.systems import create_phase4_scenario


def test_repeated_phase4_builds_are_fresh_and_deterministic():
    first = create_phase4_scenario("PR3").simulate()
    second = create_phase4_scenario("PR3").simulate()
    assert first.flowsheet is not second.flowsheet
    assert first.units["R401"] is not second.units["R401"]
    assert first.streams["dry_protein_product"].F_mass == pytest.approx(
        second.streams["dry_protein_product"].F_mass
    )
