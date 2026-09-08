from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.goalseek import GoalSeeker
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def profit_model() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 10.0)
    engine.set_literal(ref("A2"), 500.0)
    engine.set_formula(ref("B1"), "=A1*80-A2")
    return engine


class TestSolving:
    def test_break_even_lands_on_the_algebraic_answer(self):
        engine = profit_model()
        verdict = GoalSeeker(engine=engine).seek(
            target_ref=ref("B1"),
            goal=0.0,
            input_ref=ref("A1"),
            low=0.0,
            high=100.0,
        )
        assert verdict.startswith("solved: A1 = 6.25")
        assert engine.value(ref("A1")) == 6.25
        assert engine.value(ref("B1")) == 0.0

    def test_the_answer_reports_residual_and_iterations(self):
        verdict = GoalSeeker(engine=profit_model()).seek(
            ref("B1"), 300.0, ref("A1"), 0.0, 100.0
        )
        assert "residual" in verdict
        assert "bisection(s)" in verdict
        assert "the input cell holds the solution" in verdict


class TestTheDiagnosedRefusals:
    def test_no_straddle_says_which_bound_to_widen(self):
        verdict = GoalSeeker(engine=profit_model()).seek(
            ref("B1"), 100000.0, ref("A1"), 0.0, 100.0
        )
        assert verdict.startswith("no straddle")
        assert "widen the high bound" in verdict

    def test_the_error_region_halts_with_the_input_named(self):
        engine = Engine()
        engine.set_literal(ref("A1"), 1.0)
        engine.set_formula(ref("B1"), "=100/A1")
        verdict = GoalSeeker(engine=engine).seek(
            ref("B1"), 5.0, ref("A1"), 0.0, 50.0
        )
        assert verdict.startswith("halted:")
        assert "#DIV/0!" in verdict
        assert "bracket a lie" in verdict

    def test_a_text_target_is_not_a_goal(self):
        engine = Engine()
        engine.set_literal(ref("A1"), 1.0)
        engine.set_formula(ref("B1"), '=A1&"x"')
        verdict = GoalSeeker(engine=engine).seek(
            ref("B1"), 5.0, ref("A1"), 0.0, 10.0
        )
        assert "goals are numeric" in verdict

    def test_the_backwards_bracket_is_refused(self):
        with pytest.raises(Invalid):
            GoalSeeker(engine=profit_model()).seek(
                ref("B1"), 0.0, ref("A1"), 9.0, 1.0
            )
