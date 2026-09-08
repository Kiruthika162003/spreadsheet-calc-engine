"""Color scales: a value's position between the extremes, not its raw size.

A heatmap answers one question honestly or misleads
completely: is this cell high or low relative to its
neighbors. The honesty lives in the scaling. A two-color
scale maps the minimum of the region to one end and the
maximum to the other and every value to its linear position
between them, so the color says rank, not magnitude, which
is what a reader's eye reads anyway. A three-color scale
pins the midpoint to a chosen anchor, the median by default
rather than the arithmetic mean, because one outlier drags
the mean and paints an entire healthy column the alarm
color, and the median is the value that actually splits the
region in half. A region where every value is equal has no
high or low, so it paints the neutral midpoint rather than
dividing by a zero range and coloring by accident. Errors in
the region are not colored on the scale at all; they are
reported separately, because assigning a temperature to a
#DIV/0! is pretending a wound is a measurement. The output
is intensity buckets, integers zero through the band count,
so the scale is testable as numbers rather than as colors
nobody can assert on.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import is_error


@dataclass
class ScaleReport:
    buckets: dict[tuple[int, int], int]
    wounds: list[str]
    low: float
    high: float

    def bucket_at(self, ref: CellRef) -> int | None:
        return self.buckets.get(ref.key())


def _numbers_in(
    sheet: Sheet, region: RangeRef
) -> tuple[list[tuple[tuple[int, int], float]], list[str]]:
    values = []
    wounds = []
    for cell in region.cells():
        held = sheet.value_of(cell)
        if is_error(held):
            wounds.append(cell.a1())
        elif isinstance(held, float) and not isinstance(
            held, bool
        ):
            values.append((cell.key(), held))
    return values, wounds


def _median(numbers: list[float]) -> float:
    ordered = sorted(numbers)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def two_color_scale(
    sheet: Sheet, region: RangeRef, bands: int = 4
) -> ScaleReport:
    if bands < 1:
        raise Invalid("a scale needs at least one band")
    points, wounds = _numbers_in(sheet, region)
    if not points:
        raise Invalid(
            "the region has no numbers to scale; a heatmap "
            "of nothing is a blank pretending to be data"
        )
    values = [value for _, value in points]
    low, high = min(values), max(values)
    buckets: dict[tuple[int, int], int] = {}
    span = high - low
    for key, value in points:
        if span == 0:
            buckets[key] = bands // 2
        else:
            position = (value - low) / span
            buckets[key] = min(
                int(position * bands), bands - 1
            )
    return ScaleReport(
        buckets=buckets, wounds=wounds, low=low, high=high
    )


def three_color_scale(
    sheet: Sheet,
    region: RangeRef,
    bands: int = 4,
    midpoint: float | None = None,
) -> ScaleReport:
    if bands < 2:
        raise Invalid(
            "a three-color scale needs at least two bands "
            "per half"
        )
    points, wounds = _numbers_in(sheet, region)
    if not points:
        raise Invalid(
            "the region has no numbers to scale; a heatmap "
            "of nothing is a blank pretending to be data"
        )
    values = [value for _, value in points]
    low, high = min(values), max(values)
    anchor = (
        _median(values) if midpoint is None else midpoint
    )
    buckets: dict[tuple[int, int], int] = {}
    for key, value in points:
        if value <= anchor:
            span = anchor - low
            fraction = 0.0 if span == 0 else (
                (value - low) / span
            )
            buckets[key] = min(
                int(fraction * bands), bands - 1
            )
        else:
            span = high - anchor
            fraction = 0.0 if span == 0 else (
                (value - anchor) / span
            )
            buckets[key] = bands + min(
                int(fraction * bands), bands - 1
            )
    return ScaleReport(
        buckets=buckets, wounds=wounds, low=low, high=high
    )
