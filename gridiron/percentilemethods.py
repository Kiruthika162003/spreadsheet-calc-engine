"""Percentile methods: three definitions that give three answers, each named.

There is no single percentile; there is a family of
definitions that agree in the middle of a large dataset and
disagree at the edges and on small samples, and a function
that computed the percentile without saying which one it used
would hand two analysts different numbers from the same data
and no way to reconcile them. This module offers the three
that matter. The inclusive method, the one the base engine's
PERCENTILE already uses, places the p-th percentile at rank p
times n minus one and interpolates, so it always returns a
value between the minimum and maximum and reaches both at the
ends. The exclusive method places it at rank p times n plus
one minus one, which pulls the extremes off the ends and
refuses percentiles too close to zero or one to have a rank
inside the data, because on ten points the exclusive fifth
percentile falls below the first point and there is nothing
there to interpolate, an honest refusal rather than a clamp
to the minimum. The nearest-rank method does not interpolate
at all; it returns an actual data point, the one at the
ceiling of p times n, which is what a caller wants when the
percentile must be a value that really occurred rather than a
blend of two that did. Naming the three lets a report state
its method, and the tests pin a small sample where all three
disagree, which is the whole reason to keep them distinct.
"""

from __future__ import annotations

import math

from gridiron.errors import Invalid


def _check(values: list[float], p: float) -> list[float]:
    if not values:
        raise Invalid("no values for a percentile")
    if not 0.0 <= p <= 1.0:
        raise Invalid(
            f"percentile {p} must sit in [0, 1]"
        )
    return sorted(values)


def inclusive(values: list[float], p: float) -> float:
    ordered = _check(values, p)
    position = p * (len(ordered) - 1)
    low = int(position)
    frac = position - low
    if frac == 0:
        return ordered[low]
    return ordered[low] + frac * (
        ordered[low + 1] - ordered[low]
    )


def exclusive(values: list[float], p: float) -> float:
    ordered = _check(values, p)
    n = len(ordered)
    position = p * (n + 1) - 1
    if position < 0 or position > n - 1:
        raise Invalid(
            f"the exclusive {p:.0%} percentile falls outside "
            f"the {n} data points; there is no rank inside "
            "the data to interpolate, so it is refused rather "
            "than clamped to an extreme"
        )
    low = int(position)
    frac = position - low
    if frac == 0:
        return ordered[low]
    return ordered[low] + frac * (
        ordered[low + 1] - ordered[low]
    )


def nearest_rank(values: list[float], p: float) -> float:
    ordered = _check(values, p)
    if p == 0:
        return ordered[0]
    rank = math.ceil(p * len(ordered))
    return ordered[rank - 1]
