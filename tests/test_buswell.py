import pytest

from Greenhub.reactions import buswell


def test_glucose_buswell_products_and_balance():
    result = buswell("C6H12O6")
    assert result.methane == pytest.approx(3.0)
    assert result.carbon_dioxide == pytest.approx(3.0)
    assert max(abs(i) for i in result.atom_residuals.values()) < 1e-12


def test_buswell_with_nitrogen_and_sulfur_balances():
    result = buswell("C5H7O2NS")
    assert result.ammonia == pytest.approx(1.0)
    assert result.hydrogen_sulfide == pytest.approx(1.0)
    assert max(abs(i) for i in result.atom_residuals.values()) < 1e-12
