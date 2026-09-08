from __future__ import annotations

import pytest

from gridiron.dates import (
    CalendarDate,
    from_serial,
    is_leap,
    render_date,
    to_serial,
    weekday,
)
from gridiron.errors import Invalid


class TestTheCalendarRules:
    def test_the_gregorian_leap_rules_exactly(self):
        assert is_leap(2000)
        assert is_leap(2024)
        assert not is_leap(2100)
        assert not is_leap(2023)

    def test_the_impossible_dates_are_refused(self):
        with pytest.raises(Invalid):
            CalendarDate(year=2023, month=2, day=29)
        with pytest.raises(Invalid):
            CalendarDate(year=2024, month=13, day=1)

    def test_the_famous_lie_is_refused_by_epoch_choice(self):
        with pytest.raises(Invalid) as caught:
            CalendarDate(year=1900, month=2, day=28)
        assert "predates the epoch" in str(caught.value)


class TestSerials:
    def test_day_one_is_the_documented_epoch(self):
        assert to_serial(
            CalendarDate(year=2000, month=1, day=1)
        ) == 1
        assert render_date(1) == "2000-01-01"

    def test_serials_and_dates_round_trip(self):
        for triple in (
            (2000, 3, 1),
            (2024, 2, 29),
            (2100, 12, 31),
        ):
            date = CalendarDate(*triple)
            assert from_serial(to_serial(date)) == date

    def test_leap_day_2000_lands_on_serial_60(self):
        assert to_serial(
            CalendarDate(year=2000, month=2, day=29)
        ) == 60
        assert render_date(61) == "2000-03-01"

    def test_date_arithmetic_is_float_arithmetic(self):
        deadline = to_serial(CalendarDate(2024, 3, 15))
        today = to_serial(CalendarDate(2024, 3, 1))
        assert deadline - today == 14

    def test_the_negative_serial_is_a_modeling_question(self):
        with pytest.raises(Invalid) as caught:
            from_serial(0)
        assert "documented decision, not accident" in str(
            caught.value
        )


class TestWeekdays:
    def test_the_epoch_was_a_saturday(self):
        assert weekday(1) == 6

    def test_the_week_wraps_in_seven(self):
        assert weekday(2) == 7
        assert weekday(3) == 1
        assert weekday(8) == 6
