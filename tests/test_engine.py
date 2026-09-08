from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Missing
from gridiron.refs import CellRef
from gridiron.values import is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def ledger() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 10.0)
    engine.set_literal(ref("A2"), 20.0)
    engine.set_formula(ref("B1"), "=A1*2")
    engine.set_formula(ref("B2"), "=A2*2")
    engine.set_formula(ref("C1"), "=B1+B2")
    engine.set_formula(ref("D1"), "=SUM(A1:A2)")
    return engine


class TestBothHalvesOfThePromise:
    def test_the_cone_recomputes_in_dependency_order(self):
        engine = ledger()
        report = engine.set_literal(ref("A1"), 100.0)
        assert sorted(report.evaluated) == ["B1", "C1", "D1"]
        assert report.evaluated.index(
            "B1"
        ) < report.evaluated.index("C1")
        assert engine.value(ref("C1")) == 240.0
        assert engine.value(ref("D1")) == 120.0

    def test_the_rest_of_the_sheet_slept(self):
        engine = ledger()
        report = engine.set_literal(ref("A2"), 30.0)
        assert "B1" not in report.evaluated
        assert report.slept == 1

    def test_an_untouched_edit_wakes_nobody(self):
        engine = ledger()
        report = engine.set_literal(ref("Z99"), 1.0)
        assert report.line() == (
            "0 evaluated, 4 formula(s) slept"
        )

    def test_range_watchers_wake_on_membership(self):
        engine = ledger()
        report = engine.set_literal(ref("A2"), 5.0)
        assert "D1" in report.evaluated
        assert engine.value(ref("D1")) == 15.0


class TestEditing:
    def test_a_new_formula_computes_itself_immediately(self):
        engine = ledger()
        engine.set_formula(ref("E1"), "=C1+1")
        assert engine.value(ref("E1")) == 61.0

    def test_clearing_a_precedent_reruns_the_cone(self):
        engine = ledger()
        engine.clear(ref("A1"))
        assert engine.value(ref("B1")) == 0.0
        assert engine.value(ref("D1")) == 20.0

    def test_clearing_the_empty_cell_is_missing(self):
        with pytest.raises(Missing):
            ledger().clear(ref("K9"))


class TestCycles:
    def test_the_loop_is_named_and_the_sheet_calculates_on(self):
        engine = ledger()
        engine.set_formula(ref("F1"), "=G1+1")
        report = engine.set_formula(ref("G1"), "=F1+1")
        assert sorted(report.cycles) == ["F1", "G1"]
        assert is_error(engine.value(ref("F1")))
        assert engine.value(ref("F1")).code == "#CYCLE!"
        assert engine.value(ref("C1")) == 60.0

    def test_a_self_loop_is_the_smallest_cycle(self):
        engine = Engine()
        report = engine.set_formula(ref("A1"), "=A1+1")
        assert report.cycles == ["A1"]

    def test_breaking_the_loop_heals_the_cells(self):
        engine = ledger()
        engine.set_formula(ref("F1"), "=G1+1")
        engine.set_formula(ref("G1"), "=F1+1")
        engine.set_formula(ref("G1"), "=1")
        assert engine.value(ref("G1")) == 1.0
        assert engine.value(ref("F1")) == 2.0


class TestFullRecalc:
    def test_the_cold_start_computes_everything_once(self):
        engine = ledger()
        report = engine.full_recalc()
        assert len(report.evaluated) == 4
        assert report.slept == 0
