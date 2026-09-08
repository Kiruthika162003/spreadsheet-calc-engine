from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.movingstats import (
    cumulative,
    moving_average,
    moving_sum,
    period_change,
)


class TestMovingAverage:
    def test_the_front_has_no_full_window(self):
        result = moving_average([1.0, 2.0, 3.0, 4.0], 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == pytest.approx(2.0)
        assert result[3] == pytest.approx(3.0)

    def test_it_lines_up_cell_for_cell(self):
        source = [10.0, 20.0, 30.0]
        assert len(moving_average(source, 2)) == len(source)

    def test_a_gap_poisons_only_its_windows(self):
        result = moving_average([1.0, None, 3.0, 4.0], 2)
        assert result[1] is None
        assert result[2] is None
        assert result[3] == pytest.approx(3.5)

    def test_a_zero_window_is_refused(self):
        with pytest.raises(Invalid):
            moving_average([1.0], 0)


class TestMovingSumAndCumulative:
    def test_moving_sum_windows(self):
        result = moving_sum([1.0, 2.0, 3.0, 4.0], 2)
        assert result == [None, 3.0, 5.0, 7.0]

    def test_cumulative_carries_forward(self):
        result = cumulative([1.0, 2.0, 3.0])
        assert result == [1.0, 3.0, 6.0]

    def test_cumulative_skips_gaps_without_breaking(self):
        result = cumulative([1.0, None, 3.0])
        assert result == [1.0, None, 4.0]


class TestPeriodChange:
    def test_absolute_and_relative_change(self):
        result = period_change([100.0, 120.0, 90.0])
        assert result[0] == (None, None)
        assert result[1][0] == pytest.approx(20.0)
        assert result[1][1] == pytest.approx(0.2)
        assert result[2][0] == pytest.approx(-30.0)
        assert result[2][1] == pytest.approx(-0.25)

    def test_change_off_zero_has_no_percentage(self):
        result = period_change([0.0, 50.0])
        absolute, relative = result[1]
        assert absolute == pytest.approx(50.0)
        assert relative is None

    def test_a_gap_breaks_the_pairing(self):
        result = period_change([10.0, None, 30.0])
        assert result[1] == (None, None)
        assert result[2] == (None, None)
