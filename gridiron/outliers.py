"""Outliers: two detectors that disagree on purpose, each saying which it flags.

Flagging outliers is not one operation but a choice between
detectors that answer different questions, so this module
offers both and never hides which one spoke. The IQR fence
method marks a value an outlier when it falls more than a
multiple, conventionally one and a half, of the interquartile
range below the first quartile or above the third; it makes
no assumption about the shape of the data and is the robust
choice for skewed distributions, because it leans on
quartiles rather than the mean an outlier itself would drag.
The z-score method marks a value whose distance from the mean
exceeds a multiple of the standard deviation; it assumes the
data is roughly normal and is the wrong tool for skewed data,
where a long tail is not an anomaly, and that assumption is
stated rather than buried. The two will disagree on the same
data, and that disagreement is information, so a caller can
run both and see which values are robustly extreme versus
merely far from a mean the tail pulled. A dataset too small
to have a spread, fewer than the method needs, is refused
rather than flagging everything or nothing, and a z-score
method on data with zero variance refuses too, because every
value is the mean and dividing the distance by zero spread is
undefined, not a verdict that nothing is an outlier.
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


def iqr_outliers(
    values: list[float], multiplier: float = 1.5
) -> list[int]:
    if len(values) < 4:
        raise Invalid(
            "the IQR method needs at least four values to "
            "have quartiles worth trusting"
        )
    q1, q3 = _quartiles(values)
    iqr = q3 - q1
    low = q1 - multiplier * iqr
    high = q3 + multiplier * iqr
    return [
        index
        for index, value in enumerate(values)
        if value < low or value > high
    ]


def zscore_outliers(
    values: list[float], threshold: float = 3.0
) -> list[int]:
    if len(values) < 2:
        raise Invalid(
            "the z-score method needs at least two values "
            "for a standard deviation"
        )
    mean = sum(values) / len(values)
    variance = sum(
        (v - mean) ** 2 for v in values
    ) / len(values)
    if variance == 0:
        raise Invalid(
            "the data has zero spread; every value is the "
            "mean and a distance over zero deviation is "
            "undefined, not a verdict"
        )
    sd = variance**0.5
    return [
        index
        for index, value in enumerate(values)
        if abs(value - mean) / sd > threshold
    ]


def zscore_of(
    value: float, values: list[float]
) -> float:
    mean = sum(values) / len(values)
    variance = sum(
        (v - mean) ** 2 for v in values
    ) / len(values)
    if variance == 0:
        raise Invalid("zero spread has no z-score")
    return (value - mean) / variance**0.5
