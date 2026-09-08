from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.workdaysintl import networkdays, workday

# Serial 3 = 2000-01-03 (Monday); 7 = Friday.


class TestNetworkdays:
    def test_a_full_work_week(self):
        assert networkdays(3, 7) == 5

    def test_a_holiday_on_a_workday_subtracts(self):
        assert networkdays(3, 7, holidays=frozenset({5})) == 4

    def test_a_holiday_on_a_weekend_does_not(self):
        # Serial 1 is a Saturday, already outside the span
        # and the weekend; it must not reduce the count.
        assert networkdays(3, 7, holidays=frozenset({1})) == 5

    def test_a_reversed_span_is_negative(self):
        assert networkdays(7, 3) == -5

    def test_a_custom_weekend(self):
        # Friday/Saturday weekend over Mon..Sun (serials 3-9).
        assert (
            networkdays(3, 9, weekend=frozenset({5, 6}))
            == 5
        )


class TestWorkday:
    def test_five_working_days_forward(self):
        # From Monday, five working days lands next Monday.
        assert workday(3, 5) == 10

    def test_it_steps_over_a_holiday(self):
        # A holiday on serial 5 pushes the landing out a day.
        assert workday(3, 2) == 5
        assert workday(3, 2, holidays=frozenset({5})) == 6

    def test_a_backward_walk(self):
        assert workday(10, -5) == 3

    def test_zero_days_stays_put(self):
        assert workday(3, 0) == 3


class TestRefusals:
    def test_a_full_week_weekend_is_refused(self):
        with pytest.raises(Invalid) as caught:
            networkdays(3, 7, weekend=frozenset(range(1, 8)))
        assert "no workdays" in str(caught.value)

    def test_an_out_of_range_weekend_day(self):
        with pytest.raises(Invalid) as caught:
            workday(3, 1, weekend=frozenset({9}))
        assert "1 (Monday) to 7" in str(caught.value)
