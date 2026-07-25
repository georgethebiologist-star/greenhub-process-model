import pytest

from Greenhub.phase4_specifications import pH_response_recovery


def test_pH_response_peaks_at_effective_isoelectric_point():
    peak = pH_response_recovery(pH=4.5, isoelectric_pH=4.5, width=0.6, maximum_recovery=0.8)
    away = pH_response_recovery(pH=6.5, isoelectric_pH=4.5, width=0.6, maximum_recovery=0.8)
    assert peak == pytest.approx(0.8)
    assert 0.0 <= away < peak
