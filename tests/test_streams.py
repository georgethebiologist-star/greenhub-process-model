"""Tests for direct GreenHub stream creation."""

import pytest

from Greenhub.streams import BASELINE_FEED_FLOWS_KG_HR, create_liquid_fraction


def test_feed_total_mass_matches_component_sum():
    feed = create_liquid_fraction(ID="direct_test_feed")
    assert feed.F_mass == pytest.approx(sum(BASELINE_FEED_FLOWS_KG_HR.values()))


def test_negative_component_flow_raises():
    invalid = dict(BASELINE_FEED_FLOWS_KG_HR)
    invalid["Water"] = -1.0
    with pytest.raises(ValueError, match="negative"):
        create_liquid_fraction(invalid, ID="negative_feed")


def test_unknown_component_raises():
    invalid = dict(BASELINE_FEED_FLOWS_KG_HR)
    invalid["UnknownComponent"] = 1.0
    with pytest.raises(KeyError, match="Unknown component"):
        create_liquid_fraction(invalid, ID="unknown_feed")
