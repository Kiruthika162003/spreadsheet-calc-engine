from __future__ import annotations

import pytest

from gridiron.coledit import ColumnEditor
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def ledger_sheet() -> Sheet:
    sheet = Sheet()
    sheet.set_literal(ref("A1"), 10.0)
    sheet.set_literal(ref("B1"), 20.0)
    sheet.set_literal(ref("C1"), 30.0)
    sheet.set_formula(ref("E1"), "=B1*2")
    sheet.set_formula(ref("E2"), "=$C$1+1")
    sheet.set_formula(ref("F1"), "=SUM(A1:C1)")
    return sheet


class TestInsertion:
    def test_references_re_letter_when_columns_move(self):
        sheet = ledger_sheet()
        verdict = ColumnEditor(sheet=sheet).insert_columns(
            at_col=1
        )
        assert "re-lettered" in verdict
        assert sheet.cell(ref("F1")).formula_text == "=(C1*2)"

    def test_the_absolute_flag_is_irrelevant_to_sheet_edits(self):
        sheet = ledger_sheet()
        ColumnEditor(sheet=sheet).insert_columns(at_col=0)
        assert sheet.cell(ref("F2")).formula_text == "=($D$1+1)"

    def test_a_range_widens_when_a_column_lands_inside(self):
        sheet = ledger_sheet()
        ColumnEditor(sheet=sheet).insert_columns(at_col=1)
        assert sheet.cell(ref("G1")).formula_text == (
            "=SUM(A1:D1)"
        )


class TestDeletion:
    def test_the_deleted_column_is_a_visible_wound(self):
        sheet = ledger_sheet()
        verdict = ColumnEditor(sheet=sheet).delete_columns(
            at_col=1
        )
        assert "wear #REF!" in verdict
        assert sheet.cell(ref("D1")).formula_text == (
            "=(#REF!*2)"
        )

    def test_the_range_narrows_at_its_edge(self):
        sheet = ledger_sheet()
        ColumnEditor(sheet=sheet).delete_columns(at_col=1)
        assert sheet.cell(ref("E1")).formula_text == (
            "=SUM(A1:B1)"
        )

    def test_deleting_the_whole_range_wounds_the_sum(self):
        sheet = Sheet()
        sheet.set_formula(ref("F1"), "=SUM(B1:C3)")
        ColumnEditor(sheet=sheet).delete_columns(
            at_col=1, count=2
        )
        assert sheet.cell(ref("D1")).formula_text == (
            "=SUM(#REF!)"
        )


class TestRefusals:
    def test_zero_counts_are_refused(self):
        with pytest.raises(Invalid):
            ColumnEditor(sheet=Sheet()).insert_columns(
                at_col=0, count=0
            )
        with pytest.raises(Invalid):
            ColumnEditor(sheet=Sheet()).delete_columns(
                at_col=0, count=0
            )
