from __future__ import annotations

import pytest

from gridiron.datatable import DataTable
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def mortgage() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 0.005)
    engine.set_literal(ref("A2"), 360.0)
    engine.set_formula(
        ref("C1"), "=ROUND(PMT(A1, A2, 300000), 2)"
    )
    return engine


class TestOneVariable:
    def test_the_sweep_tabulates_and_restores(self):
        engine = mortgage()
        rows = DataTable(engine=engine).one_variable(
            ref("A1"), [0.004, 0.005, 0.006], ref("C1")
        )
        assert rows[0] == (0.004, "-1574")
        assert rows[1] == (0.005, "-1798.65")
        assert engine.value(ref("A1")) == 0.005

    def test_a_swept_formula_is_refused(self):
        engine = mortgage()
        with pytest.raises(Invalid) as caught:
            DataTable(engine=engine).one_variable(
                ref("C1"), [1.0], ref("C1")
            )
        assert "sweep inputs, not the model" in str(
            caught.value
        )

    def test_an_empty_sweep_is_refused(self):
        with pytest.raises(Invalid):
            DataTable(engine=mortgage()).one_variable(
                ref("A1"), [], ref("C1")
            )


class TestTwoVariable:
    def test_the_rate_by_term_grid(self):
        engine = mortgage()
        grid = DataTable(engine=engine).two_variable(
            ref("A1"), [0.004, 0.005],
            ref("A2"), [180.0, 360.0],
            ref("C1"),
        )
        assert len(grid) == 2
        assert len(grid[0]) == 2
        assert grid[1][1] == "-1798.65"
        assert engine.value(ref("A2")) == 360.0


class TestTheBreakReport:
    def test_errors_are_recorded_not_aborted(self):
        engine = Engine()
        engine.set_literal(ref("A1"), 2.0)
        engine.set_formula(ref("C1"), "=100/A1")
        report = DataTable(engine=engine).break_report(
            ref("A1"), [2.0, 1.0, 0.0], ref("C1")
        )
        assert "breaks at 1 of 3 candidate(s)" in report
        assert "first at 0.0 with #DIV/0!" in report
        assert "the interesting part" in report

    def test_the_unbroken_model_says_so(self):
        engine = mortgage()
        report = DataTable(engine=engine).break_report(
            ref("A1"), [0.004, 0.005], ref("C1")
        )
        assert report == (
            "the model held across all 2 candidate(s)"
        )
