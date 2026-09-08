from __future__ import annotations

import pytest

from gridiron.dates import CalendarDate, render_date, to_serial
from gridiron.dateseries import daily, monthly, weekly
from gridiron.errors import Invalid


def s(year: int, month: int, day: int) -> int:
    return to_serial(
        CalendarDate(year=year, month=month, day=day)
    )


def shown(serials: list[int]) -> list[str]:
    return [render_date(x) for x in serials]


class TestDaily:
    def test_inclusive_of_the_end(self):
        assert shown(daily(s(2001, 1, 1), s(2001, 1, 3))) == [
            "2001-01-01",
            "2001-01-02",
            "2001-01-03",
        ]

    def test_a_step(self):
        assert shown(
            daily(s(2001, 1, 1), s(2001, 1, 10), 3)
        ) == [
            "2001-01-01",
            "2001-01-04",
            "2001-01-07",
            "2001-01-10",
        ]

    def test_a_zero_step_is_refused(self):
        with pytest.raises(Invalid):
            daily(s(2001, 1, 1), s(2001, 1, 5), 0)


class TestWeekly:
    def test_seven_days_apart(self):
        assert shown(
            weekly(s(2001, 1, 1), s(2001, 1, 31))
        ) == [
            "2001-01-01",
            "2001-01-08",
            "2001-01-15",
            "2001-01-22",
            "2001-01-29",
        ]


class TestMonthly:
    def test_the_month_end_clamp_does_not_stick(self):
        # From Jan 31: Feb clamps to 28, but March returns
        # to 31 because the series remembers the anchor day.
        assert shown(
            monthly(s(2001, 1, 31), s(2001, 4, 30))
        ) == [
            "2001-01-31",
            "2001-02-28",
            "2001-03-31",
            "2001-04-30",
        ]

    def test_a_plain_first_of_month(self):
        assert shown(
            monthly(s(2001, 1, 1), s(2001, 3, 1))
        ) == [
            "2001-01-01",
            "2001-02-01",
            "2001-03-01",
        ]


class TestEdges:
    def test_a_reversed_range_is_empty(self):
        assert daily(s(2001, 2, 1), s(2001, 1, 1)) == []

    def test_a_zero_month_step_is_refused(self):
        with pytest.raises(Invalid):
            monthly(s(2001, 1, 1), s(2001, 6, 1), 0)
