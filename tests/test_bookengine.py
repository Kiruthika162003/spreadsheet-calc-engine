from __future__ import annotations

import pytest

from gridiron.bookengine import BookEngine
from gridiron.errors import Unparseable
from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def book() -> BookEngine:
    engine = BookEngine()
    engine.add_sheet("Data")
    engine.add_sheet("Summary")
    engine.set_literal("Data", ref("A1"), 40.0)
    engine.set_literal("Data", ref("A2"), 2.0)
    engine.set_formula("Data", ref("B1"), "=A1*A2")
    engine.set_formula(
        "Summary", ref("C1"), "=Data!B1+10"
    )
    return engine


class TestCrossSheetReads:
    def test_the_summary_reads_through_the_door(self):
        engine = book()
        assert engine.value("Summary", ref("C1")) == 90.0

    def test_an_edit_refreshes_the_watchers_after_the_cone(self):
        engine = book()
        verdict = engine.set_literal(
            "Data", ref("A1"), 100.0
        )
        assert "cross-sheet formula(s) refreshed" in verdict
        assert engine.value("Data", ref("B1")) == 200.0
        assert engine.value("Summary", ref("C1")) == 210.0

    def test_the_watchers_local_dependents_ride_along(self):
        engine = book()
        engine.set_formula("Summary", ref("C2"), "=C1*2")
        engine.set_literal("Data", ref("A1"), 100.0)
        assert engine.value("Summary", ref("C1")) == 210.0
        assert engine.value("Summary", ref("C2")) == 420.0

    def test_a_chain_across_three_sheets_settles(self):
        engine = book()
        engine.add_sheet("Report")
        engine.set_formula(
            "Report", ref("A1"), "=Summary!C1*10"
        )
        verdict = engine.set_literal(
            "Data", ref("A1"), 100.0
        )
        assert engine.value("Report", ref("A1")) == 2100.0
        assert "round(s)" in verdict

    def test_a_workbook_loop_is_stamped_at_the_cap(self):
        engine = BookEngine()
        engine.add_sheet("Alpha")
        engine.add_sheet("Beta")
        engine.set_formula("Alpha", ref("A1"), "=Beta!A1+1")
        engine.set_formula("Beta", ref("A1"), "=Alpha!A1+1")
        value = engine.value("Alpha", ref("A1"))
        assert is_error(value)
        assert value.code == "#CYCLE!"
        assert "crosses sheet boundaries" in value.note

    def test_the_dropped_sheet_wounds_mid_formula(self):
        engine = book()
        engine.book.drop_sheet("Data")
        engine.set_literal("Summary", ref("D1"), 1.0)
        value = engine.value("Summary", ref("C1"))
        assert is_error(value)
        assert value.code == "#REF!"


class TestTheGrammarBoundary:
    def test_sheetless_evaluation_names_its_world(self):
        outcome = evaluate(
            parse_formula("=Data!A1"),
            lambda _ref: None,
            full_table,
        )
        assert outcome.code == "#REF!"
        assert "only one sheet's world" in outcome.note

    def test_cross_sheet_ranges_point_at_the_workaround(self):
        with pytest.raises(Unparseable) as caught:
            parse_formula("=SUM(Data!A1:A9)")
        assert "pull the range onto one sheet" in str(
            caught.value
        )

    def test_half_a_sheet_reference_is_named(self):
        with pytest.raises(Unparseable):
            parse_formula("=Data!")

    def test_the_call_boundary_is_stated_not_hidden(self):
        engine = book()
        engine.set_formula(
            "Summary", ref("E1"), "=ABS(Data!B1)"
        )
        value = engine.value("Summary", ref("E1"))
        assert is_error(value)
        assert value.code == "#REF!"
        assert "only one sheet's world" in value.note
