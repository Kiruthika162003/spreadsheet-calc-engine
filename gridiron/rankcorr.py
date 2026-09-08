"""Rank correlations: agreement in order, not in value, and the ties that complicate it.

Pearson correlation measures whether two variables move
together linearly, but sometimes the question is only whether
they move together at all, monotonically, regardless of the
shape, and for that the rank correlations answer better.
Spearman's rho is Pearson applied to the ranks rather than
the values, so it sees a perfect one when one variable always
rises with the other even along a curve that Pearson would
score below one. Kendall's tau counts concordant and
discordant pairs directly, the fraction of pairs that agree
on direction minus the fraction that disagree, a more
intuitive definition that a caller can check by hand on a
small set. Both live on minus-one to one and both are
clamped there before return, because rounding on a
near-perfect ranking can nudge the value a hair past one and
a correlation outside its range fails the assertion the next
step makes. The two series must be the same length, refused
otherwise, because a rank correlation pairs observations and
unpaired ones have no rank to compare. Ties are the honest
complication: this module uses average ranks for ties in the
Spearman computation, the standard treatment, and states that
Kendall's tau here is the tau-a form that does not correct
for ties, so a caller with heavily tied data knows to read
the tau with that caveat rather than assuming a tie
correction that is not there.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while (
            j + 1 < len(order)
            and values[order[j + 1]] == values[order[i]]
        ):
            j += 1
        average = sum(range(i + 1, j + 2)) / (j - i + 1)
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    return ranks


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    sab = sum(
        (x - mean_a) * (y - mean_b)
        for x, y in zip(a, b, strict=True)
    )
    saa = sum((x - mean_a) ** 2 for x in a)
    sbb = sum((y - mean_b) ** 2 for y in b)
    if saa == 0 or sbb == 0:
        raise Invalid(
            "a series with no variance has no correlation; "
            "every value tied leaves nothing to rank against"
        )
    value = sab / (saa**0.5 * sbb**0.5)
    return max(-1.0, min(1.0, value))


def spearman(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise Invalid(
            f"series of length {len(a)} and {len(b)} cannot "
            "be rank-correlated; observations must pair"
        )
    if len(a) < 2:
        raise Invalid("need at least two observations")
    return _pearson(_average_ranks(a), _average_ranks(b))


def kendall_tau(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise Invalid(
            "series must be the same length to correlate"
        )
    n = len(a)
    if n < 2:
        raise Invalid("need at least two observations")
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            da = a[i] - a[j]
            db = b[i] - b[j]
            product = da * db
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    pairs = n * (n - 1) / 2
    value = (concordant - discordant) / pairs
    return max(-1.0, min(1.0, value))
