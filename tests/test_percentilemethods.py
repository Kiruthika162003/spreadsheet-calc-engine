from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.percentilemethods import (
    exclusive,
    inclusive,
    nearest_rank,
)

DATA = [15.0, 20.0, 35.0, 40.0, 50.0]


class TestTheyDisagree:
    def test_three_methods_three_answers(self):
        assert inclusive(DATA, 0.4) == pytest.approx(29.0)
        assert exclusive(DATA, 0.4) == pytest.approx(26.0)
        assert nearest_rank(DATA, 0.4) == 20.0


class TestInclusive:
    def test_it_reaches_the_extremes(self):
        assert inclusive(DATA, 0.0) == 15.0
        assert inclusive(DATA, 1.0) == 50.0

    def test_the_median(self):
        assert inclusive(DATA, 0.5) == 35.0


class TestExclusive:
    def test_it_pulls_off_the_ends(self):
        # The exclusive median matches, but low percentiles
        # sit below the minimum's rank and are refused.
        assert exclusive(DATA, 0.5) == 35.0

    def test_a_percentile_off_the_data_is_refused(self):
        with pytest.raises(Invalid) as caught:
            exclusive(DATA, 0.05)
        assert "refused rather than clamped" in str(
            caught.value
        )


class TestNearestRank:
    def test_it_returns_a_real_data_point(self):
        for p in (0.1, 0.3, 0.5, 0.9, 1.0):
            assert nearest_rank(DATA, p) in DATA

    def test_the_top_is_the_maximum(self):
        assert nearest_rank(DATA, 1.0) == 50.0


class TestRefusals:
    def test_no_values_is_refused(self):
        with pytest.raises(Invalid):
            inclusive([], 0.5)

    def test_a_percentile_out_of_range(self):
        with pytest.raises(Invalid):
            inclusive(DATA, 1.5)
