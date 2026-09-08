from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.reshape import Reshaper
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def grid_sheet() -> Reshaper:
    sheet = Sheet()
    # A 4-row, 2-column block A1:B4 = row number in col A,
    # ten times it in col B.
    for r in range(4):
        sheet.set_literal(
            CellRef(row=r, col=0), float(r + 1)
        )
        sheet.set_literal(
            CellRef(row=r, col=1), float((r + 1) * 10)
        )
    return Reshaper(
        sheet=sheet, spill=SpillManager(sheet=sheet)
    )


REGION = RangeRef.parse("A1:B4")


class TestTake:
    def test_the_first_rows(self):
        lab = grid_sheet()
        lab.take(REGION, 2, ref("D1"))
        assert lab.sheet.value_of(ref("D1")) == 1.0
        assert lab.sheet.value_of(ref("D2")) == 2.0
        assert lab.sheet.value_of(ref("D3")) is None

    def test_the_last_rows_with_a_negative(self):
        lab = grid_sheet()
        lab.take(REGION, -1, ref("D1"))
        assert lab.sheet.value_of(ref("D1")) == 4.0
        assert lab.sheet.value_of(ref("E1")) == 40.0

    def test_taking_more_than_exists_keeps_all(self):
        lab = grid_sheet()
        verdict = lab.take(REGION, 99, ref("D1"))
        assert "4x2" in verdict


class TestDrop:
    def test_dropping_the_first_rows(self):
        lab = grid_sheet()
        lab.drop(REGION, 2, ref("D1"))
        assert lab.sheet.value_of(ref("D1")) == 3.0

    def test_dropping_everything_is_refused(self):
        lab = grid_sheet()
        with pytest.raises(Invalid) as caught:
            lab.drop(REGION, 4, ref("D1"))
        assert "mystery blank" in str(caught.value)


class TestChoose:
    def test_rows_in_the_order_given(self):
        lab = grid_sheet()
        lab.choose_rows(REGION, [3, 1], ref("D1"))
        assert lab.sheet.value_of(ref("D1")) == 3.0
        assert lab.sheet.value_of(ref("D2")) == 1.0

    def test_a_repeated_row(self):
        lab = grid_sheet()
        lab.choose_rows(REGION, [2, 2], ref("D1"))
        assert lab.sheet.value_of(ref("D1")) == 2.0
        assert lab.sheet.value_of(ref("D2")) == 2.0

    def test_columns_can_reorder(self):
        lab = grid_sheet()
        lab.choose_cols(REGION, [2, 1], ref("D1"))
        assert lab.sheet.value_of(ref("D1")) == 10.0
        assert lab.sheet.value_of(ref("E1")) == 1.0

    def test_an_index_outside_is_refused(self):
        lab = grid_sheet()
        with pytest.raises(Invalid) as caught:
            lab.choose_rows(REGION, [9], ref("D1"))
        assert "does not clamp" in str(caught.value)
