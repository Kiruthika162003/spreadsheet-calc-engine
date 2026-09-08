from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.sorting import Sorter


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def ledger() -> Sheet:
    sheet = Sheet()
    rows = [
        ("cheese", 8.0),
        ("apples", 40.0),
        ("bread", 15.0),
    ]
    for offset, (name, count) in enumerate(rows):
        sheet.set_literal(
            CellRef(row=offset, col=0), name
        )
        sheet.set_literal(
            CellRef(row=offset, col=1), count
        )
    return sheet


def column_a(sheet: Sheet) -> list:
    return [
        sheet.value_of(CellRef(row=row, col=0))
        for row in range(3)
    ]


class TestSorting:
    def test_rows_move_together(self):
        sheet = ledger()
        Sorter(sheet=sheet).sort_range(
            RangeRef.parse("A1:B3"), key_col=0
        )
        assert column_a(sheet) == [
            "apples", "bread", "cheese",
        ]
        assert sheet.value_of(ref("B1")) == 40.0

    def test_descending_reverses_the_keys(self):
        sheet = ledger()
        Sorter(sheet=sheet).sort_range(
            RangeRef.parse("A1:B3"), key_col=1,
            descending=True,
        )
        assert sheet.value_of(ref("B1")) == 40.0
        assert sheet.value_of(ref("B3")) == 8.0

    def test_empties_sink_regardless_of_direction(self):
        sheet = ledger()
        sheet.clear(ref("A2"))
        verdict = Sorter(sheet=sheet).sort_range(
            RangeRef.parse("A1:B3"), key_col=0,
            descending=True,
        )
        assert "1 blank row(s) sank to the bottom" in verdict
        assert column_a(sheet)[2] is None

    def test_ties_are_stable(self):
        sheet = Sheet()
        for offset, label in enumerate(("x", "y", "z")):
            sheet.set_literal(
                CellRef(row=offset, col=0), 5.0
            )
            sheet.set_literal(
                CellRef(row=offset, col=1), label
            )
        Sorter(sheet=sheet).sort_range(
            RangeRef.parse("A1:B3"), key_col=0
        )
        labels = [
            sheet.value_of(CellRef(row=row, col=1))
            for row in range(3)
        ]
        assert labels == ["x", "y", "z"]


class TestRefusals:
    def test_formulas_refuse_to_ride(self):
        sheet = ledger()
        sheet.set_formula(ref("B2"), "=B1*2")
        with pytest.raises(Invalid) as caught:
            Sorter(sheet=sheet).sort_range(
                RangeRef.parse("A1:B3"), key_col=0
            )
        assert "sort values or paste as values first" in str(
            caught.value
        )

    def test_the_key_must_live_inside_the_range(self):
        with pytest.raises(Invalid):
            Sorter(sheet=ledger()).sort_range(
                RangeRef.parse("A1:B3"), key_col=9
            )
