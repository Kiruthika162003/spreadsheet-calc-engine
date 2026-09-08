"""Binning: grouping numbers into buckets, and the boundary that belongs to one side.

Turning a column of numbers into a histogram is two honest
choices dressed as one. The first is the bucket boundaries:
equal-width bins split the range into k equal spans, and
quantile bins split it so each bucket holds roughly the same
count, and the two answer different questions, is the data
spread evenly across values, or where do the values cluster,
so the module offers both by name rather than picking one.
The second choice is the boundary rule, and it is the one
that silently double-counts or drops a value in careless
code: a value exactly on a boundary belongs to exactly one
bucket, here the upper one, half-open intervals closed on the
left, so the buckets tile the range with no gap and no
overlap and the counts sum to the number of values every
time. The maximum value is the exception, folded into the
last bucket rather than falling off the closed-left top,
because a value at the very top is data and a histogram that
drops its maximum is lying about its range. Bins are labeled
with their half-open span so the reader can see which side a
boundary went to, and equal-width binning of a single
repeated value is refused rather than dividing by a zero
range, because a histogram of one value is a count, not a
distribution.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Bucket:
    low: float
    high: float
    count: int
    last: bool = False

    def label(self) -> str:
        right = "]" if self.last else ")"
        return f"[{self.low:g}, {self.high:g}{right}"


def _place(
    numbers: list[float], edges: list[float]
) -> list[Bucket]:
    counts = [0] * (len(edges) - 1)
    top = edges[-1]
    for value in numbers:
        if value == top:
            counts[-1] += 1
            continue
        for index in range(len(edges) - 1):
            if edges[index] <= value < edges[index + 1]:
                counts[index] += 1
                break
    return [
        Bucket(
            low=edges[index],
            high=edges[index + 1],
            count=counts[index],
            last=index == len(counts) - 1,
        )
        for index in range(len(counts))
    ]


def equal_width(
    numbers: list[float], bins: int
) -> list[Bucket]:
    if bins < 1:
        raise Invalid("a histogram needs at least one bin")
    if not numbers:
        raise Invalid("no values to bin")
    low, high = min(numbers), max(numbers)
    if low == high:
        raise Invalid(
            "every value is identical; a histogram of one "
            "value is a count, not a distribution"
        )
    step = (high - low) / bins
    edges = [low + step * i for i in range(bins + 1)]
    edges[-1] = high
    return _place(numbers, edges)


def quantile_bins(
    numbers: list[float], bins: int
) -> list[Bucket]:
    if bins < 1:
        raise Invalid("a histogram needs at least one bin")
    if len(numbers) < bins:
        raise Invalid(
            f"cannot split {len(numbers)} value(s) into "
            f"{bins} quantile bin(s); each bin needs a home"
        )
    ordered = sorted(numbers)
    edges = [ordered[0]]
    for i in range(1, bins):
        position = i * len(ordered) // bins
        edges.append(ordered[position])
    edges.append(ordered[-1])
    # Quantile edges can repeat on clustered data; collapse
    # duplicates so the buckets stay strictly increasing.
    unique_edges = [edges[0]]
    for edge in edges[1:]:
        if edge > unique_edges[-1]:
            unique_edges.append(edge)
    if len(unique_edges) < 2:
        raise Invalid(
            "the data clusters on one value; quantile bins "
            "collapse to a single count"
        )
    return _place(numbers, unique_edges)


def total_count(buckets: list[Bucket]) -> int:
    return sum(b.count for b in buckets)
