from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula


def run(formula: str):
    return evaluate(
        parse_formula(formula), lambda _r: None, full_table
    )


class TestWeekday:
    def test_the_epoch_was_a_saturday(self):
        # DATE(2000,1,1) is serial 1, a Saturday.
        assert run("=WEEKDAY(DATE(2000,1,1), 1)") == 7.0
        assert run("=WEEKDAY(DATE(2000,1,1), 2)") == 6.0
        assert run("=WEEKDAY(DATE(2000,1,1), 3)") == 5.0

    def test_a_monday_reads_one_in_the_iso_type(self):
        assert run("=WEEKDAY(DATE(2000,1,3), 2)") == 1.0

    def test_the_default_type_is_sunday_first(self):
        assert run("=WEEKDAY(DATE(2000,1,2))") == 1.0

    def test_an_unknown_type_is_refused(self):
        outcome = run("=WEEKDAY(DATE(2000,1,1), 9)")
        assert outcome.code == "#NUM!"
        assert "1, 2, and 3" in outcome.note


class TestWeeknumAndWorkday:
    def test_the_first_week_is_one(self):
        assert run("=WEEKNUM(DATE(2000,1,1))") == 1.0
        assert run("=WEEKNUM(DATE(2000,1,8))") == 2.0

    def test_workday_steps_over_the_weekend(self):
        # From Saturday, one working day lands on Monday.
        assert (
            run("=WORKDAY(DATE(2000,1,1), 1)")
            == run("=DATE(2000,1,3)")
        )

    def test_workday_counts_many(self):
        assert (
            run("=WORKDAY(DATE(2000,1,3), 5)")
            == run("=DATE(2000,1,10)")
        )

    def test_a_negative_workday_walks_backward(self):
        assert (
            run("=WORKDAY(DATE(2000,1,10), -5)")
            == run("=DATE(2000,1,3)")
        )


class TestEomonthAndDays:
    def test_eomonth_finds_the_last_day(self):
        assert (
            run("=EOMONTH(DATE(2000,1,15), 0)")
            == run("=DATE(2000,1,31)")
        )

    def test_eomonth_crosses_into_a_leap_february(self):
        assert (
            run("=EOMONTH(DATE(2000,1,15), 1)")
            == run("=DATE(2000,2,29)")
        )

    def test_days_is_plain_subtraction(self):
        assert (
            run("=DAYS(DATE(2000,1,31), DATE(2000,1,1))")
            == 30.0
        )


class TestYearfracAndDatedif:
    def test_a_full_leap_year_is_slightly_over_one(self):
        # 2000 has 366 days on the actual/365 basis.
        assert (
            run("=YEARFRAC(DATE(2000,1,1), DATE(2000,12,31))")
            == 365.0 / 365.0
        )

    def test_datedif_counts_whole_months(self):
        assert (
            run(
                '=DATEDIF(DATE(2000,1,15), '
                'DATE(2000,4,15), "M")'
            )
            == 3.0
        )

    def test_datedif_counts_whole_years(self):
        assert (
            run(
                '=DATEDIF(DATE(2000,6,1), '
                'DATE(2003,3,1), "Y")'
            )
            == 2.0
        )

    def test_datedif_days_is_the_difference(self):
        assert (
            run(
                '=DATEDIF(DATE(2000,1,1), '
                'DATE(2000,1,31), "D")'
            )
            == 30.0
        )

    def test_an_unknown_unit_is_refused(self):
        outcome = run(
            '=DATEDIF(DATE(2000,1,1), '
            'DATE(2000,2,1), "Q")'
        )
        assert outcome.code == "#NUM!"
        assert "silent zero" in outcome.note
