"""Normalizing a column: three rescalings, each undefined somewhere and saying so.

Before values of different scales are compared or fed to a
model, they are rescaled, and the three common rescalings
each break on a degenerate column in a way worth naming.
Min-max scaling maps the minimum to zero and the maximum to
one, and it divides by the range, so a column where every
value is identical has a zero range and is refused rather
than returning zeros or nans, because a constant column
carries no information to scale and pretending it maps to
anything is a lie. Z-score standardizing subtracts the mean
and divides by the standard deviation, so a column with zero
variance is refused for the same reason: every value is the
mean and the distance over zero spread is undefined. Robust
scaling subtracts the median and divides by the interquartile
range, which is the choice when outliers would blow out the
mean and standard deviation, and it too refuses a zero IQR,
though a zero IQR with a nonzero range means most of the mass
sits on one value, a fact the refusal surfaces rather than
buries. Each returns a new list and never mutates the input,
so the same column normalizes the same way every time and a
pipeline is reproducible. The output of min-max lands exactly
on zero and one at the extremes rather than a rounding away,
because a scaled column whose maximum is 0.9999999 fails the
bounds check a downstream model asserts.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _quartiles(values: list[float]) -> tuple[float, float]:
    ordered = sorted(values)
    n = len(ordered)

    def at(fraction: float) -> float:
        position = fraction * (n - 1)
        low = int(position)
        frac = position - low
        if low + 1 < n:
            return (
                ordered[low]
                + frac * (ordered[low + 1] - ordered[low])
            )
        return ordered[low]

    return at(0.25), at(0.75)


def min_max(values: list[float]) -> list[float]:
    if not values:
        raise Invalid("no values to scale")
    low, high = min(values), max(values)
    if low == high:
        raise Invalid(
            "the column is constant; a zero range carries no "
            "information to scale"
        )
    span = high - low
    result = [(v - low) / span for v in values]
    # Pin the extremes exactly so a bounds check downstream
    # does not fail on a rounding.
    result[values.index(low)] = 0.0
    result[values.index(high)] = 1.0
    return result


def z_score(values: list[float]) -> list[float]:
    if len(values) < 2:
        raise Invalid(
            "standardizing needs at least two values"
        )
    mean = sum(values) / len(values)
    variance = sum(
        (v - mean) ** 2 for v in values
    ) / len(values)
    if variance == 0:
        raise Invalid(
            "the column has zero variance; every value is "
            "the mean and the distance over zero spread is "
            "undefined"
        )
    sd = variance**0.5
    return [(v - mean) / sd for v in values]


def robust(values: list[float]) -> list[float]:
    if len(values) < 4:
        raise Invalid(
            "robust scaling needs at least four values for "
            "quartiles worth trusting"
        )
    ordered = sorted(values)
    median = _median(ordered)
    q1, q3 = _quartiles(values)
    iqr = q3 - q1
    if iqr == 0:
        raise Invalid(
            "the interquartile range is zero; most of the "
            "mass sits on one value and there is no robust "
            "spread to scale by"
        )
    return [(v - median) / iqr for v in values]


def _median(ordered: list[float]) -> float:
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2
