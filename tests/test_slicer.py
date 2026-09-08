from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.slicer import Slicer


def sheet_with(values: list[object]) -> Sheet:
    sheet = Sheet()
    for row, value in enumerate(values):
        sheet.set_literal(CellRef(row=row, col=0), value)
    return sheet


def slicer_over(values: list[object]) -> Slicer:
    sheet = sheet_with(values)
    region = RangeRef(
        top=0, left=0, bottom=len(values) - 1, right=0
    )
    return Slicer(sheet=sheet, region=region, column=0)


class TestDefaults:
    def test_everything_selected_by_default(self):
        slicer = slicer_over(
            ["Region", "East", "West", "East"]
        )
        assert slicer.selected() == [
            "Region",
            "East",
            "West",
        ]
        assert slicer.switched_off() == []

    def test_the_state_reads_show_all(self):
        slicer = slicer_over(["a", "b"])
        assert "showing all 2 value(s)" in slicer.state()


class TestToggling:
    def test_switching_off_hides_its_rows(self):
        slicer = slicer_over(
            ["Region", "East", "West", "East"]
        )
        slicer.toggle_off("East")
        # Header row 0 always visible; West at row 2.
        assert slicer.visible_rows() == [0, 2]

    def test_switching_back_on_restores(self):
        slicer = slicer_over(["Hdr", "x", "y"])
        slicer.toggle_off("x")
        slicer.toggle_on("x")
        assert slicer.switched_off() == []

    def test_the_state_shows_what_is_hidden(self):
        slicer = slicer_over(["Hdr", "x", "y"])
        slicer.toggle_off("y")
        assert "hiding ['y']" in slicer.state()


class TestEdges:
    def test_selecting_nothing_differs_from_everything(self):
        slicer = slicer_over(["Hdr", "x", "y"])
        slicer.toggle_off("Hdr")
        slicer.toggle_off("x")
        slicer.toggle_off("y")
        assert slicer.selected() == []
        assert slicer.visible_rows() == [0]

    def test_a_phantom_selection_is_refused(self):
        slicer = slicer_over(["Hdr", "x"])
        with pytest.raises(Invalid) as caught:
            slicer.toggle_off("nonexistent")
        assert "phantom selection" in str(caught.value)

    def test_available_reflects_live_data(self):
        sheet = sheet_with(["Hdr", "x"])
        region = RangeRef(top=0, left=0, bottom=2, right=0)
        slicer = Slicer(
            sheet=sheet, region=region, column=0
        )
        sheet.set_literal(CellRef(row=2, col=0), "new")
        assert "new" in slicer.available()
