"""Distributions: the normal curve, its integral, and its inverse, all real-valued.

The normal distribution functions are where a spreadsheet
does actual calculus, and the honest implementation leans on
the standard library's erf rather than a hand-rolled series
that is accurate in the middle and wrong in the tails, which
is exactly where risk calculations live. NORMDIST returns
the density at a point or the cumulative probability up to
it, selectable, because the two are different questions and a
function that guessed which one the caller meant would be
wrong half the time. The cumulative form is erf-based and so
is correct to the tails. NORMINV is the inverse cumulative,
the quantile, computed by bisection on the monotonic CDF
because there is no elementary closed form, and it refuses a
probability outside the open interval zero to one by name,
since the quantile at probability zero is negative infinity
and at one is positive infinity, values a cell cannot hold
and a bisection cannot bracket. The standard deviation must
be positive, a distribution with zero spread being a spike
that the density cannot represent as a finite number, and a
negative one being a data-entry slip. The standard normal
shortcuts, mean zero and deviation one, are provided as their
own functions rather than asking every caller to pass the two
constants, because the standard normal is the one everyone
actually reaches for.
"""

from __future__ import annotations

import math

from gridiron.errors import Invalid

_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)


def normal_pdf(
    x: float, mean: float = 0.0, sd: float = 1.0
) -> float:
    if sd <= 0:
        raise Invalid(
            "the standard deviation must be positive; a "
            "spike has no finite density"
        )
    z = (x - mean) / sd
    return math.exp(-0.5 * z * z) / (sd * _SQRT2PI)


def normal_cdf(
    x: float, mean: float = 0.0, sd: float = 1.0
) -> float:
    if sd <= 0:
        raise Invalid(
            "the standard deviation must be positive"
        )
    z = (x - mean) / (sd * _SQRT2)
    return 0.5 * (1.0 + math.erf(z))


def normal_inv(
    p: float, mean: float = 0.0, sd: float = 1.0
) -> float:
    if sd <= 0:
        raise Invalid(
            "the standard deviation must be positive"
        )
    if not 0.0 < p < 1.0:
        raise Invalid(
            f"probability {p} is outside the open interval "
            "(0, 1); the quantile at the ends is infinite "
            "and a cell cannot hold it"
        )
    low, high = -40.0, 40.0
    for _ in range(200):
        mid = (low + high) / 2
        if normal_cdf(mid) < p:
            low = mid
        else:
            high = mid
    z = (low + high) / 2
    return mean + z * sd


def standard_cdf(x: float) -> float:
    return normal_cdf(x, 0.0, 1.0)


def standard_inv(p: float) -> float:
    return normal_inv(p, 0.0, 1.0)
