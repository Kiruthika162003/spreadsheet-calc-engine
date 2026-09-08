"""Information measures: how mixed a distribution is, in bits and in impurity.

Shannon entropy and Gini impurity both answer how uniform a
set of counts is, zero when everything is one category and
maximal when the categories are evenly split, and they show
up wherever a spreadsheet touches classification or
diversity. Entropy is measured in bits, the sum of minus p
times log-base-two p over the categories, and the one detail
that trips implementations is the zero-probability term: a
category with zero count contributes zero to the entropy, not
the negative infinity that zero times log zero naively
suggests, because a category that never occurs adds no
surprise, and the limit is a clean zero. This module takes
counts rather than probabilities and normalizes them itself,
so a caller passing raw category counts does not have to
divide first and risk a rounding that makes the probabilities
not quite sum to one. A total count of zero is refused,
because a distribution over nothing has no entropy to
measure, and a negative count is refused as the data error it
is, since a category cannot occur a negative number of times.
Gini impurity is one minus the sum of squared probabilities,
the chance that two draws land in different categories, and
it is offered beside entropy because decision trees use it
and the two rank splits almost identically while disagreeing
at the third decimal, a difference worth being able to show
rather than argue about.
"""

from __future__ import annotations

import math

from gridiron.errors import Invalid


def _probabilities(counts: list[float]) -> list[float]:
    if any(c < 0 for c in counts):
        raise Invalid(
            "a category cannot occur a negative number of "
            "times"
        )
    total = sum(counts)
    if total == 0:
        raise Invalid(
            "a distribution over nothing has no entropy to "
            "measure"
        )
    return [c / total for c in counts]


def entropy(counts: list[float]) -> float:
    probabilities = _probabilities(counts)
    return -sum(
        p * math.log2(p) for p in probabilities if p > 0
    )


def gini(counts: list[float]) -> float:
    probabilities = _probabilities(counts)
    return 1.0 - sum(p * p for p in probabilities)


def normalized_entropy(counts: list[float]) -> float:
    """Entropy scaled to [0, 1] by the maximum for the category count."""
    probabilities = _probabilities(counts)
    active = sum(1 for p in probabilities if p > 0)
    if active <= 1:
        return 0.0
    return entropy(counts) / math.log2(active)
