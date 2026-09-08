from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.insertdelete import RowEditor
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def ledger_sheet() -> Sheet:
    sheet = Sheet()
    sheet.set_literal(ref("A1"), 10.0)
    sheet.set_literal(ref("A2"), 20.0)
    sheet.set_literal(ref("A3"), 30.0)
    sheet.set_formula(ref("C1"), "=A2*2")
    sheet.set_formula(ref("C2"), "=$A$3+1")
    sheet.set_formula(ref("D1"), "=SUM(A1:A3)")
    return sheet


class TestInsertion:
    def test_cells_move_and_every_formula_follows(self):
        sheet = ledger_sheet()
        verdict = RowEditor(sheet=sheet).insert_rows(at_row=1)
        assert "every formula followed them" in verdict
        assert sheet.cell(ref("C1")).formula_text == "=(A3*2)"
        assert sheet.value_of(ref("A3")) == 20.0

    def test_the_dollar_pins_against_copy_not_the_sheet(self):
        sheet = ledger_sheet()
        RowEditor(sheet=sheet).insert_rows(at_row=0)
        assert sheet.cell(ref("C3")).formula_text == "=($A$4+1)"

    def test_a_range_widens_when_a_row_lands_inside_it(self):
        sheet = ledger_sheet()
        RowEditor(sheet=sheet).insert_rows(at_row=1)
        assert sheet.cell(ref("D1")).formula_text == (
            "=SUM(A1:A4)"
        )

    def test_the_observer_moves_with_the_sheet_it_observes(self):
        sheet = Sheet()
        sheet.set_formula(ref("F1"), "=SUM(A5:A8)")
        RowEditor(sheet=sheet).insert_rows(at_row=0, count=2)
        assert sheet.cell(ref("F1")) is None
        assert sheet.cell(ref("F3")).formula_text == (
            "=SUM(A7:A10)"
        )


class TestDeletion:
    def test_the_deleted_reference_is_a_visible_wound(self):
        sheet = ledger_sheet()
        verdict = RowEditor(sheet=sheet).delete_rows(at_row=1)
        assert "visible wound" in verdict
        assert sheet.cell(ref("C1")).formula_text == "=(#REF!*2)"

    def test_the_range_narrows_and_the_total_recovers(self):
        sheet = ledger_sheet()
        RowEditor(sheet=sheet).delete_rows(at_row=1)
        assert sheet.cell(ref("D1")).formula_text == (
            "=SUM(A1:A2)"
        )

    def test_deleting_the_whole_range_is_a_wound_too(self):
        sheet = Sheet()
        sheet.set_formula(ref("F1"), "=SUM(A2:A3)")
        RowEditor(sheet=sheet).delete_rows(at_row=1, count=2)
        assert sheet.cell(ref("F1")).formula_text == "=SUM(#REF!)"

    def test_references_above_the_deletion_are_bystanders(self):
        sheet = ledger_sheet()
        RowEditor(sheet=sheet).delete_rows(at_row=2)
        assert sheet.cell(ref("C1")).formula_text == "=(A2*2)"


class TestRefusals:
    def test_zero_counts_are_refused(self):
        with pytest.raises(Invalid):
            RowEditor(sheet=Sheet()).insert_rows(at_row=0, count=0)
        with pytest.raises(Invalid):
            RowEditor(sheet=Sheet()).delete_rows(at_row=0, count=0)
