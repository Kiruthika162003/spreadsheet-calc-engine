from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.seasonal import (
    deseasonalize,
    reseasonalize,
    seasonal_indices,
)

VALUES = [
    100.0,
    200.0,
    150.0,
    50.0,
    110.0,
    220.0,
    165.0,
    55.0,
]


class TestIndices:
    def test_the_pattern_shows_the_high_season(self):
        idx = seasonal_indices(VALUES, 4)
        # Season 2 (index 1) is the peak, season 4 the trough.
        assert idx[1] == max(idx)
        assert idx[3] == min(idx)

    def test_indices_average_to_one(self):
        idx = seasonal_indices(VALUES, 4)
        assert sum(idx) / 4 == pytest.approx(1.0)

    def test_a_flat_series_has_unit_indices(self):
        idx = seasonal_indices([5.0] * 8, 4)
        assert all(x == pytest.approx(1.0) for x in idx)


class TestRoundTrip:
    def test_deseasonalize_then_reseasonalize(self):
        idx = seasonal_indices(VALUES, 4)
        de = deseasonalize(VALUES, idx)
        back = reseasonalize(de, idx)
        assert back == pytest.approx(VALUES)

    def test_deseasonalizing_flattens_the_pattern(self):
        idx = seasonal_indices(VALUES, 4)
        de = deseasonalize(VALUES, idx)
        # The deseasonalized first cycle should be roughly
        # flat compared to the raw swing.
        raw_swing = max(VALUES[:4]) - min(VALUES[:4])
        de_swing = max(de[:4]) - min(de[:4])
        assert de_swing < raw_swing


class TestRefusals:
    def test_a_partial_cycle_is_refused(self):
        with pytest.raises(Invalid) as caught:
            seasonal_indices([1.0, 2.0, 3.0], 2)
        assert "partial cycle" in str(caught.value)

    def test_a_zero_average_is_refused(self):
        with pytest.raises(Invalid) as caught:
            seasonal_indices([0.0, 0.0], 2)
        assert "no baseline" in str(caught.value)
