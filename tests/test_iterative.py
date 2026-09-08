from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.iterative import IterativeSolver
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def compounding_sheet() -> Sheet:
    sheet = Sheet()
    sheet.set_literal(ref("A1"), 1000.0)
    sheet.set_formula(ref("B1"), "=(A1+C1)*0.05")
    sheet.set_formula(ref("C1"), "=B1")
    return sheet


class TestConvergence:
    def test_the_compounding_model_converges(self):
        sheet = compounding_sheet()
        solver = IterativeSolver(sheet=sheet)
        verdict = solver.solve(
            {ref("B1").key(), ref("C1").key()}
        )
        assert "convergence is an answer" in verdict
        interest = solver.read(ref("B1").key())
        assert interest == pytest.approx(
            1000.0 * 0.05 / 0.95, abs=1e-3
        )

    def test_convergence_reports_its_round_count(self):
        sheet = compounding_sheet()
        verdict = IterativeSolver(sheet=sheet).solve(
            {ref("B1").key(), ref("C1").key()}
        )
        assert "converged in" in verdict


class TestTheTwoBadEndings:
    def test_the_divergent_loop_is_called_noise(self):
        sheet = Sheet()
        sheet.set_formula(ref("A1"), "=B1*2+1")
        sheet.set_formula(ref("B1"), "=A1")
        verdict = IterativeSolver(sheet=sheet).solve(
            {ref("A1").key(), ref("B1").key()}
        )
        assert verdict.startswith("DIVERGING")
        assert "dress noise as a result" in verdict

    def test_budget_exhaustion_is_a_shrug_with_the_delta(self):
        sheet = Sheet()
        sheet.set_formula(ref("A1"), "=B1+1")
        sheet.set_formula(ref("B1"), "=A1")
        verdict = IterativeSolver(
            sheet=sheet, max_rounds=10
        ).solve({ref("A1").key(), ref("B1").key()})
        assert "exhaustion is a shrug, not an answer" in verdict

    def test_an_error_inside_the_loop_halts_it(self):
        sheet = Sheet()
        sheet.set_formula(ref("A1"), "=B1/0")
        sheet.set_formula(ref("B1"), "=A1")
        verdict = IterativeSolver(sheet=sheet).solve(
            {ref("A1").key(), ref("B1").key()}
        )
        assert verdict.startswith("halted: A1 produced #DIV/0!")


class TestRefusals:
    def test_the_solver_needs_a_loop_and_a_budget(self):
        with pytest.raises(Invalid):
            IterativeSolver(sheet=Sheet()).solve(set())
        with pytest.raises(Invalid):
            IterativeSolver(sheet=Sheet(), max_rounds=0)
        with pytest.raises(Invalid):
            IterativeSolver(sheet=Sheet(), epsilon=0.0)
