"""T-tests: is this difference real, or the kind of wobble sampling produces.

A t-test asks whether an observed difference, a sample mean
against a claim, or two samples against each other, is larger
than sampling noise would casually produce, and it answers
with a p-value, the probability of seeing a difference this
big if there were really no difference at all. The honest
version reports the p-value rather than a bare reject or
accept, because the threshold for significance is the
caller's judgment and a function that baked in a 0.05 cutoff
would make a decision that is not its to make. The one-sample
test compares a sample mean to a hypothesized value; the
two-sample test compares two independent samples, and it uses
the Welch form, which does not assume the two groups share a
variance, because the equal-variance assumption of the older
Student form is exactly the thing most real comparisons
violate, and Welch is correct when it holds and safe when it
does not. Both are two-tailed by default, doubling the
one-tail probability, because most questions are is-there-a-
difference rather than is-it-larger, and reporting a one-tail
p for a two-tail question halves the number that decides
significance. A sample with fewer than two values has no
variance and is refused, because a t-statistic needs a spread
to divide by, and a group with zero variance in both samples
is refused rather than dividing by a zero standard error.
"""

from __future__ import annotations

from gridiron.confidence import _t_cdf
from gridiron.errors import Invalid


def _mean_var(values: list[float]) -> tuple[float, float]:
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (
        n - 1
    )
    return mean, variance


def _two_tailed_p(t: float, df: float) -> float:
    # _t_cdf takes integer-ish df; round for the tail area.
    upper = 1 - _t_cdf(abs(t), max(round(df), 1))
    return min(1.0, 2 * upper)


def one_sample(
    values: list[float], hypothesized_mean: float
) -> tuple[float, float]:
    if len(values) < 2:
        raise Invalid(
            "a one-sample t-test needs at least two values"
        )
    n = len(values)
    mean, variance = _mean_var(values)
    if variance == 0:
        raise Invalid(
            "the sample has zero variance; a t-statistic "
            "cannot divide by a zero standard error"
        )
    standard_error = (variance / n) ** 0.5
    t = (mean - hypothesized_mean) / standard_error
    return t, _two_tailed_p(t, n - 1)


def two_sample(
    a: list[float], b: list[float]
) -> tuple[float, float]:
    if len(a) < 2 or len(b) < 2:
        raise Invalid(
            "each sample needs at least two values"
        )
    mean_a, var_a = _mean_var(a)
    mean_b, var_b = _mean_var(b)
    na, nb = len(a), len(b)
    se_sq = var_a / na + var_b / nb
    if se_sq == 0:
        raise Invalid(
            "both samples have zero variance; there is no "
            "standard error to test against"
        )
    t = (mean_a - mean_b) / se_sq**0.5
    # Welch-Satterthwaite degrees of freedom.
    numerator = se_sq**2
    denominator = (var_a / na) ** 2 / (na - 1) + (
        var_b / nb
    ) ** 2 / (nb - 1)
    df = (
        numerator / denominator
        if denominator > 0
        else na + nb - 2
    )
    return t, _two_tailed_p(t, df)
