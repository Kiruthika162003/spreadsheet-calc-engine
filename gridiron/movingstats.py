"""Windowed series: moving averages, running totals, and honest period change.

Time-series columns invite three transforms, and each has a
boundary decision that separates the honest implementation
from the one that quietly fabricates data. A moving average
of window k has no answer for the first k-1 points, because
the window hangs off the front of the data, and this module
returns them as absent rather than averaging a short window
and pretending it is the same statistic, since a three-month
average computed from one month is a one-month number wearing
a three-month label. The running total is unambiguous and
carries no such gap. Period-over-period change is the one
that hides a division: the change from a previous value of
zero is undefined as a percentage, not infinity and not a
hundred percent, and the module reports it as absent with the
absolute change still available, because a percentage change
off zero is a quantity that does not exist and printing any
number for it is a lie with a decimal point. Every transform
skips nothing and reorders nothing: position i out maps to
position i in, so a result column lines up cell for cell with
its source, which is the property that lets it sit in the
next column over without the rows sliding out from under the
labels.
"""

from __future__ import annotations

from gridiron.errors import Invalid

Number = float | None


def moving_average(
    values: list[Number], window: int
) -> list[Number]:
    if window < 1:
        raise Invalid("a window needs at least one point")
    result: list[Number] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        chunk = values[index - window + 1 : index + 1]
        if any(v is None for v in chunk):
            result.append(None)
        else:
            result.append(sum(chunk) / window)
    return result


def moving_sum(
    values: list[Number], window: int
) -> list[Number]:
    if window < 1:
        raise Invalid("a window needs at least one point")
    result: list[Number] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        chunk = values[index - window + 1 : index + 1]
        if any(v is None for v in chunk):
            result.append(None)
        else:
            result.append(sum(chunk))
    return result


def cumulative(values: list[Number]) -> list[Number]:
    result: list[Number] = []
    running = 0.0
    for value in values:
        if value is None:
            result.append(None)
            continue
        running += value
        result.append(running)
    return result


def period_change(
    values: list[Number],
) -> list[tuple[Number, Number]]:
    result: list[tuple[Number, Number]] = []
    for index, value in enumerate(values):
        if index == 0 or value is None:
            result.append((None, None))
            continue
        previous = values[index - 1]
        if previous is None:
            result.append((None, None))
            continue
        absolute = value - previous
        if previous == 0:
            result.append((absolute, None))
        else:
            result.append(
                (absolute, absolute / previous)
            )
    return result
