from __future__ import annotations

from gridiron.crosssheet3d import (
    average3d,
    count3d,
    max3d,
    min3d,
    sum3d,
)
from gridiron.refs import CellRef
from gridiron.values import ErrorValue, is_error
from gridiron.workbook import Workbook


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def year() -> Workbook:
    book = Workbook()
    for month, value in (
        ("Jan", 100.0),
        ("Feb", 200.0),
        ("Mar", 300.0),
    ):
        sheet = book.add_sheet(month)
        sheet.set_literal(ref("B5"), value)
    return book


MONTHS = ["Jan", "Feb", "Mar"]


class TestAggregation:
    def test_sum_across_sheets(self):
        assert sum3d(year(), MONTHS, ref("B5")) == 600.0

    def test_average_and_count_share_a_gather(self):
        book = year()
        assert average3d(book, MONTHS, ref("B5")) == 200.0
        assert count3d(book, MONTHS, ref("B5")) == 3.0

    def test_max_and_min(self):
        book = year()
        assert max3d(book, MONTHS, ref("B5")) == 300.0
        assert min3d(book, MONTHS, ref("B5")) == 100.0


class TestErrorFlow:
    def test_a_wound_on_one_sheet_flows(self):
        book = year()
        book.sheet("Feb").set_literal(
            ref("B5"),
            ErrorValue(code="#DIV/0!", note="x"),
        )
        outcome = sum3d(book, MONTHS, ref("B5"))
        assert is_error(outcome)
        assert outcome.code == "#DIV/0!"

    def test_an_unknown_sheet_is_a_ref_wound(self):
        outcome = sum3d(
            year(), ["Jan", "Ghost", "Mar"], ref("B5")
        )
        assert is_error(outcome)
        assert outcome.code == "#REF!"


class TestSkippingAndEdges:
    def test_text_in_the_gathered_cell_is_skipped(self):
        book = year()
        book.sheet("Feb").set_literal(ref("B5"), "n/a")
        assert sum3d(book, MONTHS, ref("B5")) == 400.0
        assert count3d(book, MONTHS, ref("B5")) == 2.0

    def test_no_sheets_is_a_ref_wound(self):
        outcome = sum3d(year(), [], ref("B5"))
        assert outcome.code == "#REF!"

    def test_averaging_no_numbers_divides_by_zero(self):
        book = Workbook()
        book.add_sheet("Empty")
        outcome = average3d(book, ["Empty"], ref("B5"))
        assert outcome.code == "#DIV/0!"
