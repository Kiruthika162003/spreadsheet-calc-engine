"""Waterfall bridges: deltas turned into floating bars that must land on the total.

A waterfall chart shows how a starting value becomes an
ending value through a sequence of increases and decreases,
each drawn as a bar floating between the running total before
and after it. The arithmetic that makes it honest is that the
bars must reconcile: the top of the last delta bar equals the
declared ending total, and if it does not, the chart is
lying about the components adding up, so this module computes
the ending total from the deltas and refuses to pretend a
mismatched declared total is correct. Each bar carries its
base and top so a renderer draws the floating rectangle
without recomputing the running sum and risking a different
answer, and the direction, up or down, travels with the bar
because a decrease drawn in the increase color is the single
most common waterfall mistake. Total markers, the anchored
full-height bars for the start and end, are distinguished
from the floating delta bars, because a total that floats
like a delta invites the reader to add it into the sequence a
second time. A delta of exactly zero is kept, not dropped,
drawn as a flat marker at the running level, because a step
that happened and changed nothing is information a reader may
be looking for, and silently removing it makes the chart
disagree with the ledger it summarizes.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Bar:
    label: str
    base: float
    top: float
    kind: str

    def height(self) -> float:
        return abs(self.top - self.base)

    def direction(self) -> str:
        if self.kind == "total":
            return "total"
        return "up" if self.top >= self.base else "down"


def build_waterfall(
    start: float,
    deltas: list[tuple[str, float]],
    declared_end: float | None = None,
) -> list[Bar]:
    bars = [
        Bar(
            label="start",
            base=0.0,
            top=start,
            kind="total",
        )
    ]
    running = start
    for label, delta in deltas:
        base = running
        running += delta
        bars.append(
            Bar(
                label=label,
                base=base,
                top=running,
                kind="delta",
            )
        )
    if declared_end is not None and (
        abs(declared_end - running) > 1e-9
    ):
        raise Invalid(
            f"the deltas sum to {running} but the declared "
            f"end is {declared_end}; a waterfall whose bars "
            "do not reconcile is lying about the components "
            "adding up"
        )
    bars.append(
        Bar(
            label="end",
            base=0.0,
            top=running,
            kind="total",
        )
    )
    return bars


def ending_total(bars: list[Bar]) -> float:
    return bars[-1].top
