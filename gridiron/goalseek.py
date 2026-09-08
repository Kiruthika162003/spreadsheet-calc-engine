"""Goal seek: invert the model by honest bisection, or say why not.

The question "what price makes profit zero" runs the model
backwards, and the solver refuses to pretend it can do
calculus on a spreadsheet: it bisects. Given a target cell, a
goal value, and one input cell to vary, it brackets the goal
between two input bounds where the model's outputs straddle
it, then halves the interval until the output lands within
tolerance. The refusals carry the diagnosis: no straddle
between the bounds means the goal is not reachable in that
interval, and the report says which direction both endpoints
missed on, because "widen the high bound" is actionable and
"no solution found" is a shrug. A non-numeric or erroring
model output halts immediately with the input value that
caused it, since a solver that skips over an error region
can bracket a lie. The answer reports its residual and its
iteration count, and the input cell is left holding the
solution, which is the entire point of asking.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import is_error

MAX_BISECTIONS = 80


@dataclass
class GoalSeeker:
    engine: Engine
    tolerance: float = 1e-7

    def _model_output(
        self, input_ref: CellRef, target_ref: CellRef, x: float
    ) -> float | str:
        self.engine.set_literal(input_ref, x)
        value = self.engine.value(target_ref)
        if is_error(value):
            return (
                f"the model errored ({value.code}) at input "
                f"{x}; a solver that skips an error region can "
                "bracket a lie"
            )
        if not isinstance(value, float):
            return (
                f"the target produced {value!r} at input {x}; "
                "goals are numeric"
            )
        return value

    def seek(
        self,
        target_ref: CellRef,
        goal: float,
        input_ref: CellRef,
        low: float,
        high: float,
    ) -> str:
        if low >= high:
            raise Invalid("the bracket needs low < high")
        low_out = self._model_output(input_ref, target_ref, low)
        if isinstance(low_out, str):
            return f"halted: {low_out}"
        high_out = self._model_output(
            input_ref, target_ref, high
        )
        if isinstance(high_out, str):
            return f"halted: {high_out}"
        low_miss = low_out - goal
        high_miss = high_out - goal
        if low_miss * high_miss > 0:
            side = "below" if low_miss < 0 else "above"
            return (
                f"no straddle: both endpoints land {side} the "
                f"goal ({low_out} and {high_out} against "
                f"{goal}); widen the "
                f"{'high' if side == 'below' else 'low'} bound"
            )
        for iteration in range(1, MAX_BISECTIONS + 1):
            middle = (low + high) / 2
            middle_out = self._model_output(
                input_ref, target_ref, middle
            )
            if isinstance(middle_out, str):
                return f"halted: {middle_out}"
            residual = middle_out - goal
            if abs(residual) <= self.tolerance:
                return (
                    f"solved: {input_ref.a1()} = {middle} "
                    f"makes {target_ref.a1()} = {middle_out} "
                    f"(residual {residual:.2e}, "
                    f"{iteration} bisection(s)); the input "
                    "cell holds the solution"
                )
            if (residual < 0) == (low_miss < 0):
                low = middle
                low_miss = residual
            else:
                high = middle
        return (
            f"bracket exhausted after {MAX_BISECTIONS} "
            "bisections; the model may step discontinuously "
            "across the goal"
        )
