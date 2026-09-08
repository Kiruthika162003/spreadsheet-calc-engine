from __future__ import annotations

import pytest

from gridiron.calendarfns import (
    day_name,
    days_in,
    is_leap_year,
    iso_week,
    month_name,
    quarter,
)
from gridiron.dates import CalendarDate, to_serial
from gridiron.errors import Invalid


def s(year: int, month: int, day: int) -> int:
    return to_serial(
        CalendarDate(year=year, month=month, day=day)
    )


class TestQuarterAndNames:
    def test_quarter_maps_months(self):
        assert quarter(s(2001, 3, 15)) == 1
        assert quarter(s(2001, 4, 1)) == 2
        assert quarter(s(2001, 11, 1)) == 4

    def test_month_name(self):
        assert month_name(7) == "July"

    def test_a_bad_month_is_refused(self):
        with pytest.raises(Invalid) as caught:
            month_name(13)
        assert "caller bug" in str(caught.value)

    def test_day_name_of_the_epoch(self):
        # 2000-01-01 (serial 1) was a Saturday.
        assert day_name(1) == "Saturday"


class TestDaysAndLeap:
    def test_february_in_a_leap_year(self):
        assert days_in(2000, 2) == 29
        assert days_in(2001, 2) == 28

    def test_the_leap_rule_is_honored(self):
        assert is_leap_year(2000) is True
        assert is_leap_year(2001) is False
        assert is_leap_year(2004) is True

    def test_a_bad_month_for_days(self):
        with pytest.raises(Invalid):
            days_in(2000, 13)


class TestIsoWeek:
    def test_a_monday_first_of_year_is_week_one(self):
        assert iso_week(s(2001, 1, 1)) == 1

    def test_late_december_can_belong_to_next_year(self):
        # 2001-12-31 is a Monday whose Thursday falls in
        # 2002, so it is ISO week 1.
        assert iso_week(s(2001, 12, 31)) == 1

    def test_a_midyear_week(self):
        assert iso_week(s(2001, 7, 2)) == 27
