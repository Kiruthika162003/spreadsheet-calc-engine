"""Weighted statistics: when the points do not count equally, and the weights say so.

Averaging survey responses by region, or grades by credit
hours, or prices by volume, all need the weighted versions of
the ordinary statistics, and the weighted mean is only the
easy one. The weighted mean divides the sum of value times
weight by the sum of weights, which is why a weighted mean
with weights that sum to zero is undefined and refused rather
than dividing by zero, and why negative weights are refused:
a negative weight is not a light vote, it is a sign error
that can produce a mean outside the range of the data, a
result that reads as a bug to anyone who checks. The weighted
median is the subtler one: it is the value where the
cumulative weight first reaches half the total, walking the
sorted values and accumulating their weights, which is not
the same as the median of the values repeated by their
weights rounded to integers, a shortcut that quietly biases
the answer. The weighted standard deviation uses the reliability
weights form, dividing by the sum of weights rather than a
count, because the weights are how much each point is trusted,
not how many times it was observed, and using the frequency
form would understate the spread. Values and weights must
pair, refused otherwise, because a value without its weight
has no say in the average, and a weight without its value has
nothing to weigh.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _validate(
    values: list[float], weights: list[float]
) -> None:
    if len(values) != len(weights):
        raise Invalid(
            f"{len(values)} value(s) and {len(weights)} "
            "weight(s) do not pair"
        )
    if not values:
        raise Invalid("no data to weight")
    if any(w < 0 for w in weights):
        raise Invalid(
            "a negative weight is a sign error, not a light "
            "vote; it can push the mean outside the data"
        )
    if sum(weights) == 0:
        raise Invalid(
            "the weights sum to zero; a weighted mean over "
            "no weight is undefined"
        )


def weighted_mean(
    values: list[float], weights: list[float]
) -> float:
    _validate(values, weights)
    total = sum(weights)
    return (
        sum(v * w for v, w in zip(values, weights, strict=True))
        / total
    )


def weighted_median(
    values: list[float], weights: list[float]
) -> float:
    _validate(values, weights)
    pairs = sorted(
        zip(values, weights, strict=True),
        key=lambda pair: pair[0],
    )
    half = sum(weights) / 2
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= half:
            return value
    return pairs[-1][0]


def weighted_std(
    values: list[float], weights: list[float]
) -> float:
    _validate(values, weights)
    mean = weighted_mean(values, weights)
    total = sum(weights)
    variance = (
        sum(
            w * (v - mean) ** 2
            for v, w in zip(values, weights, strict=True)
        )
        / total
    )
    return variance**0.5
