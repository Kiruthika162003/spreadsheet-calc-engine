"""Seasonal indices: separating the pattern that repeats from the trend that does not.

A monthly sales series carries two things tangled together, a
trend that moves over time and a seasonal pattern that
repeats every cycle, and separating them is what lets a
forecast say next December will be high because every
December is, not because the line happens to point up. This
module computes seasonal indices by the ratio-to-average
method: average each season's values across all cycles,
divide by the grand average, and the result is how much each
season runs above or below normal, an index that centers on
one. The indices are normalized so they average exactly one
across the cycle, because indices that did not would quietly
inflate or deflate every deseasonalized figure, and a
forecast built on them would drift by that bias every year.
The series length must be a whole number of cycles, refused
otherwise, because a partial final cycle weights its seasons
unequally and tilts the pattern toward whatever the year was
cut off before finishing. Deseasonalizing divides a value by
its season's index to reveal the trend, and reseasonalizing
multiplies a trend figure back by the index to project the
actual, and the two are exact inverses, a round trip the
tests pin, because an index you cannot invert is a
description, not a model.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def seasonal_indices(
    values: list[float], period: int
) -> list[float]:
    if period < 1:
        raise Invalid("a season needs at least one period")
    if len(values) % period != 0:
        raise Invalid(
            f"{len(values)} values is not a whole number of "
            f"{period}-period cycles; a partial cycle tilts "
            "the pattern"
        )
    if not values:
        raise Invalid("no values to analyze")
    grand = sum(values) / len(values)
    if grand == 0:
        raise Invalid(
            "the grand average is zero; there is no baseline "
            "to index against"
        )
    indices = []
    for season in range(period):
        members = values[season::period]
        season_average = sum(members) / len(members)
        indices.append(season_average / grand)
    # Normalize so the indices average exactly one.
    scale = period / sum(indices)
    return [index * scale for index in indices]


def deseasonalize(
    values: list[float], indices: list[float]
) -> list[float]:
    period = len(indices)
    return [
        value / indices[i % period]
        for i, value in enumerate(values)
    ]


def reseasonalize(
    trend: list[float], indices: list[float]
) -> list[float]:
    period = len(indices)
    return [
        value * indices[i % period]
        for i, value in enumerate(trend)
    ]
