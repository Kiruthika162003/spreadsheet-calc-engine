"""Charts as text: scaled honestly, ticked on the 1-2-5 ladder, refusing wounds.

A chart is a claim about proportions, and a text chart makes
the claim auditable because the reader can count characters.
The scaling rules here are the ones every plotting library
half-hides. Bars scale to the axis maximum, not the data
maximum, so two charts drawn against the same axis are
comparable, and the axis is built on the 1-2-5 ladder, the
tick step is always one of 1, 2, or 5 times a power of ten,
because humans read 0 20 40 60 at a glance and 0 23 46 69
only with a calculator. The first draft snapped steps upward
to the ladder and the measurement refuted it: asked for five
ticks over 0 to 97, the ceiling ladder pushed 24.25 up to 50
and delivered three, so the step now rounds at the classic
midpoints, below 1.5 stays 1, below 3 becomes 2, below 7
becomes 5, and 24.25 lands on 20 where the glance lives. A bar for a negative number is drawn
leftward from the zero column when the axis spans zero,
since clamping negatives to zero-length bars is how a bad
quarter hides in the deck. Series are read from single
columns with their name taken from the header cell, a series
containing an error refuses to chart at all and names the
wounded cell, because averaging around a #DIV/0! draws a
picture of data that does not exist, and an empty series is
refused rather than drawn as an empty axis pretending to be
information. The sparkline compresses a series into one row
of ASCII depth marks, minimum to maximum, and states its own
scale beside it, a chart that fits in a cell comment without
lying about what it dropped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import is_error, render

_SPARK_RAMP = " .:-=+*#"


def nice_step(raw_step: float) -> float:
    if raw_step <= 0:
        raise Invalid("a step must be positive")
    magnitude = 10 ** math.floor(math.log10(raw_step))
    residual = raw_step / magnitude
    if residual < 1.5:
        factor = 1
    elif residual < 3:
        factor = 2
    elif residual < 7:
        factor = 5
    else:
        factor = 10
    return factor * magnitude


def nice_ticks(
    low: float, high: float, target: int = 5
) -> list[float]:
    if high < low:
        raise Invalid(
            f"the axis is upside down: {low} to {high}"
        )
    if high == low:
        high = low + 1.0
    if target < 2:
        raise Invalid("an axis needs at least two ticks")
    step = nice_step((high - low) / (target - 1))
    start = math.floor(low / step) * step
    ticks = [start]
    while ticks[-1] < high - 1e-9:
        ticks.append(round(ticks[-1] + step, 10))
    return ticks


@dataclass(frozen=True)
class Series:
    name: str
    values: tuple[float, ...]

    @classmethod
    def from_column(
        cls, sheet: Sheet, region: RangeRef
    ) -> Series:
        if region.left != region.right:
            raise Invalid(
                "a series reads one column; got "
                f"{region.right - region.left + 1}"
            )
        header = sheet.value_of(
            CellRef(row=region.top, col=region.left)
        )
        if not isinstance(header, str) or not header.strip():
            raise Invalid(
                "the first cell of a series names it; "
                "found no text there"
            )
        values = []
        for row in range(region.top + 1, region.bottom + 1):
            cell = CellRef(row=row, col=region.left)
            value = sheet.value_of(cell)
            if is_error(value):
                raise Invalid(
                    f"{cell.a1()} holds {value.code}; a "
                    "chart of wounded data draws a picture "
                    "of data that does not exist"
                )
            if isinstance(value, float) and not isinstance(
                value, bool
            ):
                values.append(value)
        if not values:
            raise Invalid(
                f"the series {header!r} has no numbers; an "
                "empty axis pretending to be information "
                "is refused"
            )
        return cls(name=header.strip(), values=tuple(values))


@dataclass
class BarChart:
    series: Series
    width: int = 40

    def axis(self) -> list[float]:
        low = min(0.0, *self.series.values)
        high = max(0.0, *self.series.values)
        return nice_ticks(low, high)

    def render(self) -> str:
        ticks = self.axis()
        low, high = ticks[0], ticks[-1]
        span = high - low
        zero_col = round((0.0 - low) / span * self.width)
        label_width = max(
            len(render(value)) for value in self.series.values
        )
        lines = [f"{self.series.name} ({render(low)} to {render(high)})"]
        for value in self.series.values:
            col = round((value - low) / span * self.width)
            if value >= 0:
                left = " " * zero_col
                bar = "#" * max(col - zero_col, 0)
            else:
                length = max(zero_col - col, 0)
                left = " " * (zero_col - length)
                bar = "-" * length
            label = render(value).rjust(label_width)
            lines.append(f"{label} |{left}{bar}")
        return "\n".join(lines)


def sparkline(series: Series) -> str:
    low = min(series.values)
    high = max(series.values)
    if high == low:
        marks = _SPARK_RAMP[-1] * len(series.values)
        return (
            f"{series.name}: [{marks}] flat at {render(low)}"
        )
    depth = len(_SPARK_RAMP) - 1
    marks = "".join(
        _SPARK_RAMP[
            round((value - low) / (high - low) * depth)
        ]
        for value in series.values
    )
    return (
        f"{series.name}: [{marks}] "
        f"{render(low)} to {render(high)}"
    )
