"""More statistics: the second and third moments, sample versus population stated.

Variance carries the same contested denominator its square
root does, so this family names the choice the way the STDEV
pair already does: VAR divides by n minus one for the sample,
VARP by n for the population, and shipping one function
called VAR that guessed the denominator is how a result
becomes irreproducible across two analysts. DEVSQ is the sum
of squared deviations, the numerator both variances share,
exposed on its own because it is the building block a custom
weighting needs and recomputing it inside three functions is
three chances to diverge. AVEDEV is the mean absolute
deviation, a different and more robust spread than the
standard deviation, kept distinct rather than presented as an
approximation of it. COVAR measures how two series move
together and requires them to be the same length, refused by
their two numbers otherwise, because a covariance of
mismatched series pairs the wrong points and means nothing.
SKEW is the third standardized moment and needs at least
three points and a nonzero spread, refused by name when the
data is a flat line whose skew is a zero-over-zero rather
than a real zero. Every function refuses fewer values than
its formula needs with the minimum named, because a variance
of one number is not zero, it is a question that does not
parse, the same oath the STDEV family swore.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _numbers(args, lookup, functions, names):
    gathered: list[float] = []
    for arg in args:
        if isinstance(arg, Range):
            for cell in arg.ref.cells():
                value = lookup(cell)
                if is_error(value):
                    return value
                if isinstance(value, float) and not isinstance(
                    value, bool
                ):
                    gathered.append(value)
        else:
            value = evaluate(arg, lookup, functions, names)
            if is_error(value):
                return value
            coerced = to_number(value)
            if is_error(coerced):
                return coerced
            gathered.append(coerced)
    return gathered


def _need(numbers, minimum, what):
    if len(numbers) < minimum:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"{what} needs at least {minimum} value(s), "
                f"got {len(numbers)}; a spread of fewer does "
                "not parse"
            ),
        )
    return None


def _devsq_of(numbers):
    mean = sum(numbers) / len(numbers)
    return sum((n - mean) ** 2 for n in numbers)


def _variance(sample: bool, label: str):
    def run(args, lookup, functions, names) -> Value:
        numbers = _numbers(args, lookup, functions, names)
        if is_error(numbers):
            return numbers
        refusal = _need(
            numbers, 2 if sample else 1, label
        )
        if refusal:
            return refusal
        divisor = len(numbers) - (1 if sample else 0)
        return _devsq_of(numbers) / divisor

    return run


def _devsq(args, lookup, functions, names) -> Value:
    numbers = _numbers(args, lookup, functions, names)
    if is_error(numbers):
        return numbers
    refusal = _need(numbers, 1, "DEVSQ")
    if refusal:
        return refusal
    return _devsq_of(numbers)


def _avedev(args, lookup, functions, names) -> Value:
    numbers = _numbers(args, lookup, functions, names)
    if is_error(numbers):
        return numbers
    refusal = _need(numbers, 1, "AVEDEV")
    if refusal:
        return refusal
    mean = sum(numbers) / len(numbers)
    return sum(abs(n - mean) for n in numbers) / len(
        numbers
    )


def _covar(args, lookup, functions, names) -> Value:
    if len(args) != 2 or not all(
        isinstance(a, Range) for a in args
    ):
        return ErrorValue(
            code="#VALUE!",
            note="COVAR takes two ranges",
        )
    left = _numbers(args[:1], lookup, functions, names)
    if is_error(left):
        return left
    right = _numbers(args[1:], lookup, functions, names)
    if is_error(right):
        return right
    if len(left) != len(right):
        return ErrorValue(
            code="#N/A",
            note=(
                f"the series have {len(left)} and "
                f"{len(right)} values; covariance of "
                "mismatched series pairs the wrong points"
            ),
        )
    if not left:
        return ErrorValue(
            code="#NUM!",
            note="COVAR of empty series does not parse",
        )
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    return sum(
        (a - mean_left) * (b - mean_right)
        for a, b in zip(left, right, strict=True)
    ) / len(left)


def _skew(args, lookup, functions, names) -> Value:
    numbers = _numbers(args, lookup, functions, names)
    if is_error(numbers):
        return numbers
    refusal = _need(numbers, 3, "SKEW")
    if refusal:
        return refusal
    n = len(numbers)
    mean = sum(numbers) / n
    variance = _devsq_of(numbers) / (n - 1)
    if variance == 0:
        return ErrorValue(
            code="#DIV/0!",
            note=(
                "the data is a flat line; its skew is "
                "zero over zero, not a real zero"
            ),
        )
    sd = variance**0.5
    factor = n / ((n - 1) * (n - 2))
    return factor * sum(
        ((x - mean) / sd) ** 3 for x in numbers
    )


STATS_MORE_FUNCTIONS = {
    "VAR": _variance(True, "VAR"),
    "VARP": _variance(False, "VARP"),
    "DEVSQ": _devsq,
    "AVEDEV": _avedev,
    "COVAR": _covar,
    "SKEW": _skew,
}
