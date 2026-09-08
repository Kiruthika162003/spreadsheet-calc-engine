from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.smoothing import (
    double_forecast,
    single,
    single_forecast,
)


class TestSingle:
    def test_a_flat_series_stays_flat(self):
        assert single([10.0, 10.0, 10.0], 0.5) == [
            10.0,
            10.0,
            10.0,
        ]

    def test_alpha_one_tracks_the_data(self):
        assert single([1.0, 5.0, 3.0], 1.0) == [
            1.0,
            5.0,
            3.0,
        ]

    def test_alpha_zero_never_moves(self):
        assert single([1.0, 99.0, 50.0], 0.0) == [
            1.0,
            1.0,
            1.0,
        ]

    def test_the_forecast_is_the_last_level(self):
        assert single_forecast(
            [10.0, 12.0, 11.0], 0.5
        ) == pytest.approx(single([10.0, 12.0, 11.0], 0.5)[-1])


class TestDouble:
    def test_it_projects_a_trend(self):
        # A clean +1 per period continues to 6.
        assert double_forecast(
            [1.0, 2.0, 3.0, 4.0, 5.0], 0.5, 0.5
        ) == pytest.approx(6.0)

    def test_it_projects_further_ahead(self):
        assert double_forecast(
            [1.0, 2.0, 3.0, 4.0, 5.0], 0.8, 0.8, ahead=3
        ) == pytest.approx(8.0)

    def test_single_would_flatline_where_double_climbs(self):
        trend = [1.0, 2.0, 3.0, 4.0, 5.0]
        flat = single_forecast(trend, 0.5)
        climbing = double_forecast(trend, 0.5, 0.5)
        assert climbing > flat


class TestRefusals:
    def test_an_alpha_out_of_range(self):
        with pytest.raises(Invalid) as caught:
            single([1.0, 2.0], 1.5)
        assert "not a blend" in str(caught.value)

    def test_double_needs_two_points(self):
        with pytest.raises(Invalid):
            double_forecast([5.0], 0.5, 0.5)

    def test_a_zero_ahead_forecast(self):
        with pytest.raises(Invalid):
            double_forecast([1.0, 2.0], 0.5, 0.5, ahead=0)
