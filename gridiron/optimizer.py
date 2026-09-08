"""Optimize: find the input that minimizes or maximizes a cell, honestly bracketed.

Where goal seek finds the input that hits a target value,
the optimizer finds the input that makes a target as small
or as large as possible over a range, and it uses golden-
section search because that method needs no derivative and
converges without assuming the model is anything but
continuous and unimodal over the bracket. The unimodal
assumption is the honest catch, and it is stated rather than
hidden: golden-section finds a local optimum, and if the
model has two valleys in the bracket it finds one of them,
so the result is labeled a local optimum and the caller who
needs the global one is told to bracket more tightly around
the region of interest. Maximizing is minimizing the
negated output, done by flipping a sign in one place rather
than duplicating the search, because two copies of a search
loop drift apart on the day someone fixes a bug in one. The
input cell is left holding the optimizing value, the same
contract goal seek honors, so the sheet after optimizing is
a sheet at its optimum, not a report about one. A model that
errors at a probe point halts the search with that error
rather than treating a #NUM! as a very large number, because
optimizing toward a wound is optimizing toward nonsense.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import Value, is_error

_INV_PHI = (5**0.5 - 1) / 2
_INV_PHI2 = (3 - 5**0.5) / 2


@dataclass
class OptimizeResult:
    input_value: float
    output_value: float
    iterations: int
    kind: str

    def line(self) -> str:
        return (
            f"local {self.kind} at input "
            f"{self.input_value:.6g}, output "
            f"{self.output_value:.6g} "
            f"({self.iterations} probe(s)); a local optimum, "
            "bracket tighter for a global one"
        )


@dataclass
class Optimizer:
    engine: Engine
    tolerance: float = 1e-6
    max_probes: int = 200

    def _probe(
        self,
        input_ref: CellRef,
        target_ref: CellRef,
        value: float,
    ) -> Value:
        self.engine.set_literal(input_ref, value)
        return self.engine.value(target_ref)

    def _search(
        self,
        input_ref: CellRef,
        target_ref: CellRef,
        low: float,
        high: float,
        sign: float,
        kind: str,
    ) -> OptimizeResult:
        if low >= high:
            raise Invalid("the bracket needs low < high")
        a, b = low, high
        c = a + _INV_PHI2 * (b - a)
        d = a + _INV_PHI * (b - a)
        fc = self._scaled(input_ref, target_ref, c, sign)
        fd = self._scaled(input_ref, target_ref, d, sign)
        probes = 2
        while (b - a) > self.tolerance and (
            probes < self.max_probes
        ):
            if fc < fd:
                b, d, fd = d, c, fc
                c = a + _INV_PHI2 * (b - a)
                fc = self._scaled(
                    input_ref, target_ref, c, sign
                )
            else:
                a, c, fc = c, d, fd
                d = a + _INV_PHI * (b - a)
                fd = self._scaled(
                    input_ref, target_ref, d, sign
                )
            probes += 1
        best = (a + b) / 2
        output = self._probe(input_ref, target_ref, best)
        if is_error(output):
            raise Invalid(
                f"the model errors at the optimum ({output.code}); "
                "optimizing toward a wound is nonsense"
            )
        return OptimizeResult(
            input_value=best,
            output_value=output,
            iterations=probes,
            kind=kind,
        )

    def _scaled(
        self,
        input_ref: CellRef,
        target_ref: CellRef,
        value: float,
        sign: float,
    ) -> float:
        output = self._probe(input_ref, target_ref, value)
        if is_error(output):
            raise Invalid(
                f"the model errors at input {value:.6g} "
                f"({output.code}); optimizing toward a wound "
                "is nonsense"
            )
        if not isinstance(output, float) or isinstance(
            output, bool
        ):
            raise Invalid(
                "the target is not a number at this input; "
                "there is nothing to optimize"
            )
        return sign * output

    def minimize(
        self,
        target_ref: CellRef,
        input_ref: CellRef,
        low: float,
        high: float,
    ) -> OptimizeResult:
        return self._search(
            input_ref, target_ref, low, high, 1.0, "minimum"
        )

    def maximize(
        self,
        target_ref: CellRef,
        input_ref: CellRef,
        low: float,
        high: float,
    ) -> OptimizeResult:
        return self._search(
            input_ref, target_ref, low, high, -1.0, "maximum"
        )
