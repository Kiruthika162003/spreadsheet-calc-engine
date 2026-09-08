"""The iterative proof: convergence is an answer, divergence is a refusal.

Circular references are usually errors, but some are
deliberate fixed-point problems, and the iterative solver
exists to tell the two apart honestly. The drill sets up the
convergent recurrence A1 = (10 + A1)/2, whose fixed point is
ten, seeds it, and confirms the solver reports convergence
and leaves the cell holding ten to within epsilon, because a
solver that converged but left the cell on a wrong value
would be a calculator lying about having solved. Then it sets
up the divergent recurrence A1 = 2*A1 + 1, whose iterates run
away to infinity, and confirms the solver names it DIVERGING
and refuses rather than running to the round budget and
dressing the last enormous number as a result. The measured
lesson the proof carries is that the two outcomes are
categorically different: convergence names its round count as
an answer, divergence names the growing delta as a refusal,
and a solver that returned a number in both cases would make
the dangerous divergent case indistinguishable from the safe
convergent one at the call site.
"""

from __future__ import annotations

from gridiron.iterative import IterativeSolver
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def run() -> Finding:
    convergent = Sheet()
    convergent.set_formula(
        CellRef.parse("A1"), "=(10+A1)/2"
    )
    solver = IterativeSolver(sheet=convergent)
    converge_verdict = solver.solve(
        {CellRef.parse("A1").key()}
    )
    settled = solver.read(CellRef.parse("A1").key())

    divergent = Sheet()
    divergent.set_formula(
        CellRef.parse("A1"), "=2*A1+1"
    )
    diverge_verdict = IterativeSolver(
        sheet=divergent
    ).solve({CellRef.parse("A1").key()})

    numbers = {
        "converge_verdict": converge_verdict,
        "fixed_point": settled,
        "landed_on_ten": abs(settled - 10.0) < 1e-4,
        "diverge_verdict": diverge_verdict,
        "named_diverging": diverge_verdict.startswith(
            "DIVERGING"
        ),
    }
    holds = (
        converge_verdict.startswith("converged")
        and numbers["landed_on_ten"]
        and numbers["named_diverging"]
    )
    return Finding(
        proof="iterativeproof",
        claim=(
            "the recurrence to ten converges and leaves the "
            "cell on ten, while the runaway recurrence is "
            "named DIVERGING and refused rather than run to "
            "the budget as a dressed-up result"
        ),
        numbers=numbers,
        holds=holds,
    )
