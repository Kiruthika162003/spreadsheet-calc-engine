from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.importers import (
    FixedColumn,
    import_fixed,
    import_tsv,
)
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


class TestTsv:
    def test_tabs_are_walls_newlines_are_floors(self):
        sheet = Sheet()
        report = import_tsv(
            sheet, "Item\tQty\nWidget\t3\nGadget\t5"
        )
        assert sheet.value_of(ref("A1")) == "Item"
        assert sheet.value_of(ref("B2")) == 3.0
        assert sheet.value_of(ref("A3")) == "Gadget"
        assert report.numbers == 2
        assert report.texts == 4

    def test_the_inference_ladder_is_shared(self):
        sheet = Sheet()
        report = import_tsv(
            sheet, "TRUE\t007\t1.5\t\thello"
        )
        assert sheet.value_of(ref("A1")) is True
        assert sheet.value_of(ref("B1")) == "007"
        assert sheet.value_of(ref("C1")) == 1.5
        assert sheet.value_of(ref("D1")) is None
        assert report.zeros_protected == 1
        assert report.empties == 1

    def test_placement_lands_at_the_offset(self):
        sheet = Sheet()
        import_tsv(sheet, "9", top=4, left=2)
        assert sheet.value_of(ref("C5")) == 9.0


class TestFixedWidth:
    SPEC = (
        FixedColumn(name="Item", start=0, width=8),
        FixedColumn(name="Qty", start=8, width=4),
        FixedColumn(name="Code", start=12, width=5),
    )

    ROW_ONE = "Widget  " + "   3" + "00042"
    ROW_TWO = "Gadget  " + "  12" + "00007"

    def test_columns_slice_by_position(self):
        sheet = Sheet()
        text = self.ROW_ONE + "\n" + self.ROW_TWO
        report = import_fixed(sheet, text, self.SPEC)
        assert sheet.value_of(ref("A1")) == "Widget"
        assert sheet.value_of(ref("B1")) == 3.0
        assert sheet.value_of(ref("C1")) == "00042"
        assert sheet.value_of(ref("B2")) == 12.0
        assert report.zeros_protected == 2

    def test_a_short_line_is_a_ragged_edge(self):
        sheet = Sheet()
        report = import_fixed(sheet, "Widget", self.SPEC)
        assert sheet.value_of(ref("A1")) == "Widget"
        assert sheet.value_of(ref("B1")) is None
        assert report.empties == 2

    def test_a_long_line_is_refused_with_its_number(self):
        sheet = Sheet()
        text = (
            self.ROW_ONE + "\n" + self.ROW_TWO + " EXTRA"
        )
        with pytest.raises(Invalid) as caught:
            import_fixed(sheet, text, self.SPEC)
        assert "line 2 runs past" in str(caught.value)


class TestSpecValidation:
    def test_overlapping_columns_are_refused(self):
        spec = (
            FixedColumn(name="A", start=0, width=5),
            FixedColumn(name="B", start=3, width=5),
        )
        with pytest.raises(Invalid) as caught:
            import_fixed(Sheet(), "x", spec)
        assert "overlap" in str(caught.value)

    def test_repeated_names_have_one_cause(self):
        spec = (
            FixedColumn(name="A", start=0, width=2),
            FixedColumn(name="A", start=2, width=2),
        )
        with pytest.raises(Invalid) as caught:
            import_fixed(Sheet(), "x", spec)
        assert "one cause" in str(caught.value)

    def test_a_zero_width_column_reads_nothing_forever(self):
        spec = (
            FixedColumn(name="A", start=0, width=0),
        )
        with pytest.raises(Invalid) as caught:
            import_fixed(Sheet(), "x", spec)
        assert "nothing forever" in str(caught.value)

    def test_an_empty_spec_is_refused(self):
        with pytest.raises(Invalid):
            import_fixed(Sheet(), "x", ())
