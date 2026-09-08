from __future__ import annotations

import pytest

from gridiron.clipboard import Clipboard
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def sheet_with_model() -> Sheet:
    sheet = Sheet()
    sheet.set_literal(ref("A1"), 10.0)
    sheet.set_formula(ref("B1"), "=A1*2")
    sheet.set_formula(ref("C1"), "=B1+5")
    return sheet


class TestTheTwoTheories:
    def test_copy_rewrites_and_makes_strangers(self):
        sheet = sheet_with_model()
        verdict = Clipboard(sheet=sheet).copy_cell(
            ref("B1"), ref("B3")
        )
        assert "strangers now" in verdict
        assert sheet.cell(ref("B3")).formula_text == "=(A3*2)"
        assert sheet.cell(ref("B1")).formula_text == "=A1*2"

    def test_cut_moves_house_and_followers_follow(self):
        sheet = sheet_with_model()
        verdict = Clipboard(sheet=sheet).cut_cell(
            ref("B1"), ref("E5")
        )
        assert "1 formula(s) followed it" in verdict
        assert sheet.cell(ref("B1")) is None
        assert sheet.cell(ref("E5")).formula_text == "=A1*2"
        assert sheet.cell(ref("C1")).formula_text == "=(E5+5)"

    def test_copy_of_a_literal_is_just_a_value(self):
        sheet = sheet_with_model()
        Clipboard(sheet=sheet).copy_cell(
            ref("A1"), ref("A9")
        )
        assert sheet.value_of(ref("A9")) == 10.0


class TestRangeMoves:
    def test_the_block_travels_together(self):
        sheet = sheet_with_model()
        verdict = Clipboard(sheet=sheet).cut_range(
            RangeRef.parse("A1:C1"), ref("A5")
        )
        assert "3 cell(s) travelled" in verdict
        assert sheet.value_of(ref("A5")) == 10.0

    def test_the_self_overlapping_move_is_refused(self):
        sheet = sheet_with_model()
        with pytest.raises(Invalid) as caught:
            Clipboard(sheet=sheet).cut_range(
                RangeRef.parse("A1:C1"), ref("B1")
            )
        assert "a different wrong answer" in str(caught.value)

    def test_the_move_to_nowhere_is_refused(self):
        with pytest.raises(Invalid):
            Clipboard(sheet=sheet_with_model()).cut_range(
                RangeRef.parse("A1:C1"), ref("A1")
            )


class TestRefusals:
    def test_empty_sources_and_self_cuts_are_refused(self):
        clipboard = Clipboard(sheet=sheet_with_model())
        with pytest.raises(Invalid):
            clipboard.copy_cell(ref("Z9"), ref("A2"))
        with pytest.raises(Invalid):
            clipboard.cut_cell(ref("B1"), ref("B1"))
