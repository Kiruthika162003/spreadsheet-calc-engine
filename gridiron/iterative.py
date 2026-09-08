"""Iterative solve: circular references as a tool instead of a mistake.

Most circular references are typos, which is why the engine
quarantines them by default. But a minority are models:
interest compounding on a balance that includes the interest,
allocations that feed back one step, and the incumbent ships
an opt-in mode for exactly this. The solver runs the loop's
cells repeatedly from a zero start, and stops on the honest
condition, every cell in the loop moving less than epsilon
between rounds, or on the round budget, and the two stops are
reported differently because they mean different things:
convergence is an answer, budget exhaustion is a shrug with
the last delta named, and a model whose deltas grow instead
of shrink is diverging, called out as such, since running a
divergent loop to the budget and reporting the final numbers
would dress noise as a result.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.functions import builtin_table
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.values import Value, is_error, to_number


@dataclass
class IterativeSolver:
    sheet: Sheet
    max_rounds: int = 100
    epsilon: float = 1e-6

    def __post_init__(self) -> None:
        if self.max_rounds < 1:
            raise Invalid("the solver needs at least one round")
        if self.epsilon <= 0:
            raise Invalid("epsilon must be positive")

    def solve(self, loop_keys: set[tuple[int, int]]) -> str:
        if not loop_keys:
            raise Invalid("no loop to solve")
        for key in loop_keys:
            self.sheet.cells[key].computed = 0.0
        previous_delta: float | None = None
        for round_number in range(1, self.max_rounds + 1):
            largest_delta = 0.0
            for key in sorted(loop_keys):
                cell = self.sheet.cells[key]
                fresh = evaluate(
                    cell.tree,
                    self.sheet.value_of,
                    builtin_table,
                )
                if is_error(fresh):
                    ref = CellRef(row=key[0], col=key[1])
                    return (
                        f"halted: {ref.a1()} produced "
                        f"{fresh.code} inside the loop"
                    )
                old = to_number(cell.computed)
                new = to_number(fresh)
                largest_delta = max(
                    largest_delta, abs(new - old)
                )
                cell.computed = fresh
            if largest_delta < self.epsilon:
                return (
                    f"converged in {round_number} round(s); "
                    "convergence is an answer"
                )
            if (
                previous_delta is not None
                and largest_delta > previous_delta * 1.5
                and round_number > 3
            ):
                return (
                    f"DIVERGING after {round_number} round(s): "
                    f"the delta grew to {largest_delta:.4f}; "
                    "running this to the budget would dress "
                    "noise as a result"
                )
            previous_delta = largest_delta
        return (
            f"budget exhausted at {self.max_rounds} round(s) "
            f"with the last delta at {previous_delta:.6f}; "
            "exhaustion is a shrug, not an answer"
        )

    def read(self, key: tuple[int, int]) -> Value:
        return self.sheet.cells[key].computed
