"""Polynomial fitting: least squares of any degree, through the same elimination.

Fitting a straight line is the degree-one case of fitting a
polynomial, and this module does the general version by
building the normal equations and handing them to the matrix
solver already written, rather than a second hand-rolled
elimination that could disagree with the first about a
singular case. The degree is the caller's, and the one hard
constraint is stated and enforced: fitting a degree-d
polynomial needs at least d plus one distinct x-values,
because d plus one points determine the curve exactly and
fewer leave it underdetermined, a system with infinitely
many answers that the honest response is to refuse rather
than return one arbitrary member of. Distinct is the operative
word, since ten points all at the same x still fix only a
constant, so the module counts distinct x-values, not points,
and refuses when they are too few even if the rows are many.
The fit returns coefficients low-order first, constant term
at index zero, matching how the evaluator reads them, and a
perfect fit, data that actually lies on a polynomial of the
requested degree, reproduces every point to within float
dust, a law the tests check by evaluating the fitted curve
back at the sample x-values rather than trusting the
coefficients on faith.
"""

from __future__ import annotations

from gridiron.errors import Invalid
from gridiron.matrixmath import msolve


def poly_eval(coefficients: list[float], x: float) -> float:
    result = 0.0
    for coefficient in reversed(coefficients):
        result = result * x + coefficient
    return result


def poly_fit(
    xs: list[float], ys: list[float], degree: int
) -> list[float]:
    if len(xs) != len(ys):
        raise Invalid(
            f"{len(xs)} x-value(s) and {len(ys)} "
            "y-value(s); a fit needs them paired"
        )
    if degree < 0:
        raise Invalid("a polynomial degree cannot be negative")
    distinct = len(set(xs))
    if distinct < degree + 1:
        raise Invalid(
            f"a degree-{degree} fit needs {degree + 1} "
            f"distinct x-value(s), got {distinct}; fewer "
            "leaves the curve underdetermined"
        )
    terms = degree + 1
    # Build the normal-equation matrix of summed powers.
    power_sums = [
        sum(x ** p for x in xs)
        for p in range(2 * degree + 1)
    ]
    matrix = [
        [power_sums[row + col] for col in range(terms)]
        for row in range(terms)
    ]
    rhs = [
        sum(
            y * x**row
            for x, y in zip(xs, ys, strict=True)
        )
        for row in range(terms)
    ]
    return msolve(matrix, rhs)
