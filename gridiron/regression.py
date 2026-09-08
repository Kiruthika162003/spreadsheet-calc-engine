"""Regression: least squares once, and every statistic read off the same fit.

SLOPE, INTERCEPT, RSQ, CORREL, and FORECAST are five names
for one computation, the least-squares line through paired
points, and a family that recomputed the sums five times
would drift on the fifth when someone edited the fourth. So
the fit is computed once into a small record of sums and
every statistic reads from it, which also makes the shared
refusals shared by construction: fewer than two points is
refused because a line needs two, mismatched range lengths
are refused by their two numbers because pairing x with y
demands they pair, and a vertical scatter, every x
identical, is refused for slope because the denominator is
the variance of x and dividing the world by zero variance is
how a forecast becomes infinity. The correlation coefficient
is clamped into its mathematical range before it is returned,
not because the arithmetic should leave it, but because
floating-point rounding on a near-perfect fit can nudge it a
hair past one, and a correlation of 1.0000000002 reported to
a user is a bug report waiting to happen. FORECAST evaluates
the fitted line at a new x, which is the honest thing a
regression is for, extrapolation included and labeled as the
caller's responsibility rather than the function's refusal.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.ast import Range
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


@dataclass(frozen=True)
class Fit:
    n: int
    slope: float
    intercept: float
    r: float


def _pairs(
    x_arg, y_arg, lookup
) -> tuple[list[float], list[float]] | ErrorValue:
    if not isinstance(x_arg, Range) or not isinstance(
        y_arg, Range
    ):
        return ErrorValue(
            code="#VALUE!",
            note="regression takes two ranges, x and y",
        )
    xs = _numbers(x_arg, lookup)
    if is_error(xs):
        return xs
    ys = _numbers(y_arg, lookup)
    if is_error(ys):
        return ys
    if len(xs) != len(ys):
        return ErrorValue(
            code="#N/A",
            note=(
                f"x has {len(xs)} point(s) and y has "
                f"{len(ys)}; pairing demands they pair"
            ),
        )
    return xs, ys


def _numbers(arg: Range, lookup) -> list[float] | ErrorValue:
    values = []
    for cell in arg.ref.cells():
        value = lookup(cell)
        if is_error(value):
            return value
        if isinstance(value, float) and not isinstance(
            value, bool
        ):
            values.append(value)
    return values


def _fit(xs: list[float], ys: list[float]) -> Fit | ErrorValue:
    n = len(xs)
    if n < 2:
        return ErrorValue(
            code="#NUM!",
            note="a line needs at least two points",
        )
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    sxy = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(xs, ys, strict=True)
    )
    if sxx == 0:
        return ErrorValue(
            code="#DIV/0!",
            note=(
                "every x is identical; a vertical scatter "
                "has no slope and dividing by zero variance "
                "makes a forecast infinite"
            ),
        )
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    if syy == 0:
        r = 0.0
    else:
        r = sxy / (sxx**0.5 * syy**0.5)
        r = max(-1.0, min(1.0, r))
    return Fit(n=n, slope=slope, intercept=intercept, r=r)


def _fit_from(args, lookup, x_index, y_index):
    pairs = _pairs(args[x_index], args[y_index], lookup)
    if is_error(pairs):
        return pairs
    return _fit(*pairs)


def _slope(args, lookup, _functions, _names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!", note="SLOPE takes y and x ranges"
        )
    fit = _fit_from(args, lookup, 1, 0)
    return fit if is_error(fit) else fit.slope


def _intercept(args, lookup, _functions, _names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="INTERCEPT takes y and x ranges",
        )
    fit = _fit_from(args, lookup, 1, 0)
    return fit if is_error(fit) else fit.intercept


def _rsq(args, lookup, _functions, _names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!", note="RSQ takes y and x ranges"
        )
    fit = _fit_from(args, lookup, 1, 0)
    return fit if is_error(fit) else fit.r**2


def _correl(args, lookup, _functions, _names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="CORREL takes two ranges",
        )
    fit = _fit_from(args, lookup, 1, 0)
    return fit if is_error(fit) else fit.r


def _forecast(args, lookup, functions, names) -> Value:
    if len(args) != 3:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "FORECAST takes a new x, then the y and x "
                "ranges"
            ),
        )
    new_x = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(new_x):
        return new_x
    fit = _fit_from(args, lookup, 2, 1)
    if is_error(fit):
        return fit
    return fit.slope * new_x + fit.intercept


REGRESSION_FUNCTIONS = {
    "SLOPE": _slope,
    "INTERCEPT": _intercept,
    "RSQ": _rsq,
    "CORREL": _correl,
    "FORECAST": _forecast,
}
