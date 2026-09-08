"""The goal-seek proof: bisection converges, and the input cell holds the answer.

Goal seek is inverse evaluation, and the property worth
pinning is that when it succeeds it actually writes the
solution into the input cell, not merely reports a number:
after seeking, reading the input back and recomputing the
target must reproduce the goal, because a solver that
returned the right answer but left the sheet on a wrong one
would be a calculator lying about having solved. The drill
seeks the square-root of eighty-one by inverting the model
B1 = A1*A1, confirms the verdict says solved, and then reads
A1 and B1 straight from the engine to prove they landed on 9
and 81 within tolerance. The second half pins the honest
refusal: asked to reach a goal both bracket endpoints fall
short of, the seeker does not bisect toward a boundary and
call it close; it reports no straddle and names which bound
to widen, because bisection with no sign change between the
ends has nothing to converge to and pretending otherwise is
how a root-finder returns an endpoint dressed as a solution.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.goalseek import GoalSeeker
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef


def run() -> Finding:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 5.0)
    engine.set_formula(CellRef.parse("B1"), "=A1*A1")
    verdict = GoalSeeker(engine=engine).seek(
        target_ref=CellRef.parse("B1"),
        goal=81.0,
        input_ref=CellRef.parse("A1"),
        low=0.0,
        high=20.0,
    )
    solved = verdict.startswith("solved:")
    input_value = engine.value(CellRef.parse("A1"))
    target_value = engine.value(CellRef.parse("B1"))
    landed = (
        abs(input_value - 9.0) < 1e-4
        and abs(target_value - 81.0) < 1e-4
    )

    stuck = Engine()
    stuck.set_literal(CellRef.parse("A1"), 1.0)
    stuck.set_formula(CellRef.parse("B1"), "=A1*A1")
    refusal = GoalSeeker(engine=stuck).seek(
        target_ref=CellRef.parse("B1"),
        goal=81.0,
        input_ref=CellRef.parse("A1"),
        low=0.0,
        high=5.0,
    )
    refused_cleanly = (
        "no straddle" in refusal
        and "widen the high bound" in refusal
    )

    numbers = {
        "verdict_solved": solved,
        "input_landed": input_value,
        "target_landed": target_value,
        "solution_in_the_cell": landed,
        "no_straddle_refused": refused_cleanly,
    }
    holds = (
        solved
        and landed
        and refused_cleanly
    )
    return Finding(
        proof="goalseekproof",
        claim=(
            "seeking B1=81 through B1=A1*A1 writes A1=9 into "
            "the cell so a recompute reproduces the goal, "
            "and a goal outside the bracket is refused with "
            "no straddle rather than bisected to a boundary"
        ),
        numbers=numbers,
        holds=holds,
    )
