import pytest

from Greenhub.systems import create_phase3_scenario


def test_pef_conserves_mass_elements_protein_and_cod():
    for retired in ("F2", "F3"):
        with pytest.raises(ValueError, match="retired|disabled"):
            create_phase3_scenario(retired)

