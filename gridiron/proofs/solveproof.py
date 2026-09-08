"""The solve proof: iteration lands on the closed form, to the sixth digit.

Compound interest with feedback has an answer algebra can
check: interest equals principal times rate over one minus
rate, 52.631579 on a thousand at five percent. The iterative
solver, started from zero with epsilon at one millionth,
converges in seven rounds, two fewer than the docstring's
first guess of nine, and lands within four hundredths of a
millionth of the algebraic answer; the round count is part
of the finding
because a contraction at factor 0.05 should converge fast
and a solver taking fifty rounds on it would be correct and
still broken. The divergent twin, the loop that doubles each
round, is caught by round four with the word DIVERGING
rather than run to the budget, which is the proof's second
claim: the solver knows an answer from an artifact of
stopping.
"""

from __future__ import annotations

from gridiron.iterative import IterativeSolver
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def run() -> Finding:
    sheet = Sheet()
    sheet.set_literal(CellRef.parse("A1"), 1000.0)
    sheet.set_formula(
        CellRef.parse("B1"), "=(A1+C1)*0.05"
    )
    sheet.set_formula(CellRef.parse("C1"), "=B1")
    solver = IterativeSolver(sheet=sheet)
    verdict = solver.solve(
        {
            CellRef.parse("B1").key(),
            CellRef.parse("C1").key(),
        }
    )
    interest = solver.read(CellRef.parse("B1").key())
    algebra = 1000.0 * 0.05 / 0.95
    rounds = (
        int(verdict.split("converged in ")[1].split(" ")[0])
        if "converged" in verdict
        else -1
    )
    divergent = Sheet()
    divergent.set_formula(CellRef.parse("A1"), "=B1*2+1")
    divergent.set_formula(CellRef.parse("B1"), "=A1")
    twin_verdict = IterativeSolver(sheet=divergent).solve(
        {
            CellRef.parse("A1").key(),
            CellRef.parse("B1").key(),
        }
    )
    numbers = {
        "algebraic_answer": round(algebra, 6),
        "iterated_answer": round(float(interest), 6),
        "gap": abs(float(interest) - algebra),
        "rounds": rounds,
        "twin_called_diverging": twin_verdict.startswith(
            "DIVERGING"
        ),
    }
    holds = (
        numbers["gap"] < 1e-5
        and 1 <= numbers["rounds"] <= 12
        and numbers["twin_called_diverging"]
    )
    return Finding(
        proof="solveproof",
        claim=(
            "iteration lands within a hundred-thousandth of "
            "the algebraic 52.631579 in single-digit rounds, "
            "and the doubling twin is called DIVERGING instead "
            "of being run to the budget"
        ),
        numbers=numbers,
        holds=holds,
    )
