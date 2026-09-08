from __future__ import annotations

import pytest

from gridiron.columnprofile import profile_column
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue


def column(values: list[object]) -> Sheet:
    sheet = Sheet()
    for row, value in enumerate(values):
        if value is not None:
            sheet.set_literal(
                CellRef(row=row, col=0), value
            )
    return sheet


def region(rows: int) -> RangeRef:
    return RangeRef(top=0, left=0, bottom=rows - 1, right=0)


class TestCounts:
    def test_the_kinds_are_counted_separately(self):
        sheet = column([1.0, "two", True, None, 4.0])
        profile = profile_column(sheet, region(5))
        assert profile.numbers == 2
        assert profile.texts == 1
        assert profile.booleans == 1
        assert profile.empty == 1
        assert profile.filled == 4

    def test_text_in_a_numeric_column_is_not_hidden(self):
        sheet = column([10.0, "n/a", 20.0, "n/a", "n/a"])
        profile = profile_column(sheet, region(5))
        assert profile.numbers == 2
        assert profile.texts == 3
        assert profile.mean == pytest.approx(15.0)


class TestErrorsAreTheirOwnKind:
    def test_errors_stay_out_of_the_numeric_summary(self):
        sheet = column([10.0, 20.0])
        sheet.set_literal(
            CellRef(row=1, col=0),
            ErrorValue(code="#DIV/0!", note="x"),
        )
        profile = profile_column(sheet, region(2))
        assert profile.errors == 1
        assert profile.numbers == 1
        assert profile.mean == pytest.approx(10.0)


class TestDistinct:
    def test_number_and_text_five_are_distinct(self):
        sheet = column([5.0, "5", 5.0])
        profile = profile_column(sheet, region(3))
        assert profile.distinct == 2

    def test_repeated_values_count_once(self):
        sheet = column([1.0, 1.0, 1.0])
        profile = profile_column(sheet, region(3))
        assert profile.distinct == 1


class TestEdges:
    def test_an_empty_column_profiles_as_empty(self):
        sheet = column([None, None])
        profile = profile_column(sheet, region(2))
        assert profile.filled == 0
        assert profile.empty == 2
        assert profile.mean is None

    def test_the_line_reads_without_a_numeric_summary(self):
        sheet = column(["a", "b"])
        line = profile_column(sheet, region(2)).line()
        assert "no numeric summary" in line

    def test_the_line_includes_the_numeric_summary(self):
        sheet = column([2.0, 4.0, 6.0])
        line = profile_column(sheet, region(3)).line()
        assert "mean 4" in line
        assert "min 2.0" in line
