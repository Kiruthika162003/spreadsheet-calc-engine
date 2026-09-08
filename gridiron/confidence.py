"""Confidence intervals: the margin around a mean, and when to stop trusting the normal.

A confidence interval says the true mean is within a margin
of the sample mean with a stated probability, and the margin
is where two honest choices live. The first is the critical
value: for a known population standard deviation the normal
distribution's quantile is right, but for an estimated one
from a small sample the normal understates the margin and the
t-distribution is correct, wider in the tails to account for
the extra uncertainty of estimating the spread. This module
offers both and names which it used, because a margin
computed from the normal on a sample of eight is too tight
and the interval it draws will miss the true mean more often
than its label claims. The confidence level must sit strictly
inside zero and one, refused otherwise, because a hundred
percent confidence needs an infinite margin and zero percent
is a point, neither an interval. The margin scales with the
standard error, the standard deviation over the square root
of the sample size, so quadrupling the sample halves the
margin, the square-root law every power calculation rests on.
The t critical value is computed by inverting a t-distribution
built from its own series rather than borrowed from a table
truncated at thirty degrees of freedom, so the interval is
exact at every sample size rather than snapping to the normal
the moment a lookup table runs out.
"""

from __future__ import annotations

import math

from gridiron.distributions import normal_inv
from gridiron.errors import Invalid


def _z_critical(confidence: float) -> float:
    tail = (1 - confidence) / 2
    return normal_inv(1 - tail)


def _t_cdf(t: float, df: int) -> float:
    # Regularized incomplete beta gives the t CDF; use the
    # relationship to the incomplete beta via a continued
    # fraction through math functions.
    x = df / (df + t * t)
    ib = _reg_incomplete_beta(df / 2.0, 0.5, x)
    tail = 0.5 * ib
    return 1 - tail if t > 0 else tail


def _reg_incomplete_beta(
    a: float, b: float, x: float
) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = (
        math.lgamma(a)
        + math.lgamma(b)
        - math.lgamma(a + b)
    )
    front = math.exp(
        a * math.log(x)
        + b * math.log(1 - x)
        - lbeta
    ) / a
    # Lentz's continued fraction.
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 200):
        m = i // 2
        if i == 0:
            numerator = 1.0
        elif i % 2 == 0:
            numerator = (
                m * (b - m) * x
                / ((a + 2 * m - 1) * (a + 2 * m))
            )
        else:
            numerator = (
                -(a + m) * (a + b + m) * x
                / ((a + 2 * m) * (a + 2 * m + 1))
            )
        d = 1.0 + numerator * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = 1.0 + numerator / c
        if abs(c) < 1e-30:
            c = 1e-30
        f *= d * c
        if abs(1.0 - d * c) < 1e-12:
            break
    return front * (f - 1.0)


def _t_critical(confidence: float, df: int) -> float:
    target = 1 - (1 - confidence) / 2
    low, high = 0.0, 1000.0
    for _ in range(200):
        mid = (low + high) / 2
        if _t_cdf(mid, df) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def _validate(confidence: float) -> None:
    if not 0.0 < confidence < 1.0:
        raise Invalid(
            f"confidence {confidence} must sit inside (0, 1); "
            "a hundred percent needs an infinite margin and "
            "zero percent is a point"
        )


def margin_normal(
    confidence: float, sd: float, n: int
) -> float:
    _validate(confidence)
    if n < 1:
        raise Invalid("a sample needs at least one point")
    if sd < 0:
        raise Invalid("a standard deviation is not negative")
    return _z_critical(confidence) * sd / math.sqrt(n)


def margin_t(
    confidence: float, sample_sd: float, n: int
) -> float:
    _validate(confidence)
    if n < 2:
        raise Invalid(
            "the t interval needs at least two points for a "
            "sample standard deviation"
        )
    return (
        _t_critical(confidence, n - 1)
        * sample_sd
        / math.sqrt(n)
    )


def mean_interval(
    values: list[float], confidence: float
) -> tuple[float, float]:
    if len(values) < 2:
        raise Invalid(
            "a confidence interval needs at least two values"
        )
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    margin = margin_t(confidence, variance**0.5, n)
    return (mean - margin, mean + margin)
