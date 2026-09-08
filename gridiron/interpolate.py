"""TREND and GROWTH: project a series forward, and refuse the impossible fit.

Forecasting a series is fitting a curve and reading it past
the data, and the two curves users reach for are the line
and the exponential. TREND fits a least-squares line to the
known y-values against their positions and extends it, which
is honest for anything that grows by a constant amount.
GROWTH fits the same line to the logarithms of the values
and exponentiates back, which is honest for anything that
grows by a constant factor, and its one hard precondition is
stated and enforced: every known value must be strictly
positive, because the logarithm of zero or a negative has no
real value and an exponential model of a series that touches
zero is a category error, not a hard case. A single known
point cannot fix a slope, so both refuse fewer than two
points rather than inventing a flat line through one, and a
zero-variance set of positions, every x identical, is refused
for the same reason the regression module refuses it: there
is no line through a vertical stack. The projection returns
the fitted values at the requested future positions, and the
fit statistics travel with them so a caller can see how well
the model matched before trusting where it points, because a
forecast without its fit quality is a guess wearing a lab
coat.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Projection:
    values: tuple[float, ...]
    slope: float
    intercept: float
    r_squared: float


def _least_squares(
    xs: list[float], ys: list[float]
) -> tuple[float, float, float]:
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        raise Invalid(
            "every position is identical; there is no line "
            "through a vertical stack"
        )
    syy = sum((y - mean_y) ** 2 for y in ys)
    sxy = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(xs, ys, strict=True)
    )
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    r_squared = (
        0.0 if syy == 0 else (sxy**2) / (sxx * syy)
    )
    return slope, intercept, r_squared


def _positions(
    known: list[float], xs: list[float] | None
) -> list[float]:
    if xs is None:
        return [float(i + 1) for i in range(len(known))]
    if len(xs) != len(known):
        raise Invalid(
            f"{len(xs)} position(s) for {len(known)} "
            "value(s); they must pair"
        )
    return xs


def trend(
    known: list[float],
    future: list[float],
    known_x: list[float] | None = None,
) -> Projection:
    if len(known) < 2:
        raise Invalid(
            "TREND needs at least two points; one point "
            "fixes no slope"
        )
    xs = _positions(known, known_x)
    slope, intercept, r_squared = _least_squares(xs, known)
    projected = tuple(
        slope * x + intercept for x in future
    )
    return Projection(
        values=projected,
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
    )


def growth(
    known: list[float],
    future: list[float],
    known_x: list[float] | None = None,
) -> Projection:
    if len(known) < 2:
        raise Invalid(
            "GROWTH needs at least two points; one point "
            "fixes no rate"
        )
    for value in known:
        if value <= 0:
            raise Invalid(
                f"GROWTH met {value}; an exponential model "
                "of a series that touches zero or goes "
                "negative is a category error, not a hard "
                "case"
            )
    xs = _positions(known, known_x)
    logs = [math.log(value) for value in known]
    slope, intercept, r_squared = _least_squares(xs, logs)
    projected = tuple(
        math.exp(slope * x + intercept) for x in future
    )
    return Projection(
        values=projected,
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
    )
