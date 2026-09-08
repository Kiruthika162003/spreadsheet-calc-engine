from __future__ import annotations

import pytest

from gridiron.dates import CalendarDate, to_serial
from gridiron.daycount import days360, year_fraction
from gridiron.errors import Invalid


def s(year: int, month: int, day: int) -> int:
    return to_serial(
        CalendarDate(year=year, month=month, day=day)
    )


class TestDays360:
    def test_a_full_year_is_360(self):
        assert days360(s(2001, 1, 1), s(2002, 1, 1)) == 360

    def test_a_single_30day_month(self):
        assert days360(s(2001, 1, 1), s(2001, 2, 1)) == 30

    def test_the_end_of_month_adjustment_us(self):
        assert (
            days360(s(2001, 1, 30), s(2001, 3, 31)) == 60
        )

    def test_us_and_european_differ_at_month_end(self):
        # Feb 28 to Mar 31: US keeps 31, European caps to 30.
        us = days360(s(2001, 2, 28), s(2001, 3, 31))
        eu = days360(
            s(2001, 2, 28), s(2001, 3, 31), european=True
        )
        assert us != eu

    def test_a_reversed_pair_is_negative(self):
        assert days360(s(2002, 1, 1), s(2001, 1, 1)) == -360


class TestYearFraction:
    def test_actual_365(self):
        assert year_fraction(
            s(2001, 1, 1), s(2002, 1, 1), "actual/365"
        ) == pytest.approx(1.0)

    def test_actual_360_runs_longer(self):
        assert year_fraction(
            s(2001, 1, 1), s(2002, 1, 1), "actual/360"
        ) == pytest.approx(365.0 / 360.0)

    def test_thirty_360(self):
        assert year_fraction(
            s(2001, 1, 1), s(2002, 1, 1), "30/360"
        ) == pytest.approx(1.0)

    def test_an_unknown_basis_is_refused(self):
        with pytest.raises(Invalid) as caught:
            year_fraction(
                s(2001, 1, 1), s(2002, 1, 1), "act/act"
            )
        assert "reproducible" in str(caught.value)
