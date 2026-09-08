"""Discrete distributions: binomial and Poisson, computed to survive large counts.

The binomial gives the chance of exactly k successes in n
independent trials each with probability p, and the Poisson
approximates it when n is large and p small, the chance of k
events in an interval given an average rate. Both have a
naive form that overflows: the binomial coefficient of a
large n is an astronomically large integer and the Poisson
needs the factorial of k, and multiplying those before
dividing produces numbers no float holds even when the final
probability is a modest decimal. This module computes in log
space where it must, exponentiating only the final sum, so
the probability of a hundred successes in a thousand trials
comes back as a clean small number rather than an overflow.
The CDFs sum the PMF from zero up to k, and they sum upward
from the small terms rather than downward, because adding the
tiny tail into the large body last preserves more precision
than the reverse. The parameters are guarded: a probability
outside zero to one is refused, a negative count of trials or
successes is refused, and asking for more successes than
trials in a binomial returns zero, a true probability rather
than an error, because it genuinely cannot happen and zero is
the honest chance of the impossible. The Poisson rate must be
non-negative, a rate of zero meaning no events ever, whose
distribution is all mass at zero.
"""

from __future__ import annotations

import math

from gridiron.errors import Invalid


def binomial_pmf(k: int, n: int, p: float) -> float:
    if not 0.0 <= p <= 1.0:
        raise Invalid(
            f"probability {p} must sit in [0, 1]"
        )
    if n < 0 or k < 0:
        raise Invalid("counts cannot be negative")
    if k > n:
        return 0.0
    if p == 0.0:
        return 1.0 if k == 0 else 0.0
    if p == 1.0:
        return 1.0 if k == n else 0.0
    log_coeff = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    )
    log_p = log_coeff + k * math.log(p) + (
        n - k
    ) * math.log(1 - p)
    return math.exp(log_p)


def binomial_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    upper = min(k, n)
    return sum(
        binomial_pmf(i, n, p) for i in range(upper + 1)
    )


def poisson_pmf(k: int, rate: float) -> float:
    if rate < 0:
        raise Invalid("a Poisson rate is not negative")
    if k < 0:
        raise Invalid("a count cannot be negative")
    if rate == 0.0:
        return 1.0 if k == 0 else 0.0
    log_p = (
        k * math.log(rate)
        - rate
        - math.lgamma(k + 1)
    )
    return math.exp(log_p)


def poisson_cdf(k: int, rate: float) -> float:
    if k < 0:
        return 0.0
    return sum(
        poisson_pmf(i, rate) for i in range(k + 1)
    )
