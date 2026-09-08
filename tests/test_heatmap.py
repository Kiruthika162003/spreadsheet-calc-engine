from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.heatmap import three_color_scale, two_color_scale
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


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


class TestTwoColor:
    def test_position_is_rank_not_magnitude(self):
        sheet = column([0.0, 25.0, 50.0, 75.0, 100.0])
        report = two_color_scale(
            sheet, region(5), bands=4
        )
        assert report.bucket_at(ref("A1")) == 0
        assert report.bucket_at(ref("A5")) == 3
        assert report.low == 0.0
        assert report.high == 100.0

    def test_an_outlier_does_not_shift_the_scale(self):
        low = column([1.0, 2.0, 3.0, 1000.0])
        report = two_color_scale(low, region(4), bands=4)
        # The three small values all sit in the bottom band.
        assert report.bucket_at(ref("A1")) == 0
        assert report.bucket_at(ref("A2")) == 0
        assert report.bucket_at(ref("A4")) == 3

    def test_a_flat_region_paints_the_middle(self):
        flat = column([5.0, 5.0, 5.0])
        report = two_color_scale(flat, region(3), bands=4)
        assert report.bucket_at(ref("A1")) == 2

    def test_an_empty_region_is_refused(self):
        with pytest.raises(Invalid) as caught:
            two_color_scale(column([]), region(1))
        assert "pretending to be data" in str(caught.value)


class TestThreeColor:
    def test_the_median_anchors_the_middle(self):
        sheet = column([0.0, 10.0, 20.0, 30.0, 100.0])
        report = three_color_scale(
            sheet, region(5), bands=3
        )
        # Median is 20; values at or below land in the low
        # half (bucket < 3), above land in the high half.
        assert report.bucket_at(ref("A3")) < 3
        assert report.bucket_at(ref("A5")) >= 3

    def test_the_mean_would_have_misled(self):
        # Mean is 28, median is 20; the value 25 sits above
        # the median (high half) but below the mean.
        sheet = column([0.0, 10.0, 20.0, 25.0, 85.0])
        report = three_color_scale(
            sheet, region(5), bands=3
        )
        assert report.bucket_at(ref("A4")) >= 3

    def test_an_explicit_midpoint_overrides(self):
        sheet = column([0.0, 50.0, 100.0])
        report = three_color_scale(
            sheet, region(3), bands=3, midpoint=90.0
        )
        assert report.bucket_at(ref("A2")) < 3


class TestWounds:
    def test_errors_are_reported_not_colored(self):
        sheet = column([10.0, 20.0, 30.0])
        sheet.set_literal(
            ref("A2"),
            ErrorValue(code="#DIV/0!", note="x"),
        )
        report = two_color_scale(sheet, region(3), bands=4)
        assert "A2" in report.wounds
        assert report.bucket_at(ref("A2")) is None
        assert report.bucket_at(ref("A1")) == 0
