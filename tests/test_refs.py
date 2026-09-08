from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.refs import (
    CellRef,
    RangeRef,
    column_to_index,
    index_to_column,
)


class TestColumns:
    def test_the_alphabet_wraps_like_an_odometer(self):
        assert column_to_index("A") == 0
        assert column_to_index("Z") == 25
        assert column_to_index("AA") == 26
        assert column_to_index("AZ") == 51
        assert column_to_index("BA") == 52

    def test_letters_and_indices_round_trip(self):
        for index in (0, 25, 26, 700, 16_383):
            assert column_to_index(index_to_column(index)) == index

    def test_the_sheet_has_an_edge(self):
        with pytest.raises(Invalid):
            column_to_index("XFE")
        with pytest.raises(Invalid):
            index_to_column(16_384)


class TestCellRefs:
    def test_the_four_flavors_parse_and_print(self):
        for text in ("B7", "$B7", "B$7", "$B$7"):
            assert CellRef.parse(text).a1() == text

    def test_the_lenient_parser_horror_stories_are_refused(self):
        for text in ("B", "7", "B0", "b7", "B 7", "B7X", ""):
            with pytest.raises(Invalid):
                CellRef.parse(text)

    def test_relative_parts_shift_and_absolute_parts_pin(self):
        moved = CellRef.parse("$B7").shifted(rows=2, cols=5)
        assert moved.a1() == "$B9"
        pinned = CellRef.parse("$B$7").shifted(rows=2, cols=5)
        assert pinned.a1() == "$B$7"

    def test_shifting_off_the_sheet_is_refused(self):
        with pytest.raises(Invalid):
            CellRef.parse("A1").shifted(rows=-1, cols=0)


class TestRanges:
    def test_the_typed_order_is_not_a_specification(self):
        assert RangeRef.parse("C3:A1").a1() == "A1:C3"

    def test_cells_enumerate_row_major(self):
        cells = RangeRef.parse("A1:B2").cells()
        assert [cell.a1() for cell in cells] == [
            "A1", "B1", "A2", "B2",
        ]

    def test_size_and_containment(self):
        box = RangeRef.parse("B2:D4")
        assert box.size() == 9
        assert box.contains(CellRef.parse("C3"))
        assert not box.contains(CellRef.parse("A1"))

    def test_a_rangeless_text_is_refused(self):
        with pytest.raises(Invalid):
            RangeRef.parse("B7")
