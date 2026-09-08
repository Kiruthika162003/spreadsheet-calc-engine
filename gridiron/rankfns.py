"""Percentiles and ranks: the interpolation is named, the ties are settled.

A percentile is another of those functions where every
library quietly picks an answer to a contested question and
ships it unlabeled. This family picks the incumbent's
inclusive interpolation: the k-th percentile sits at
position k times n minus one in the sorted values, and a
fractional position interpolates linearly between its
neighbors, so PERCENTILE of 1 through 4 at 0.5 is 2.5, not
2 and not 3. QUARTILE is sugar over the same rule with
quarters instead of arbitrary k. RANK settles ties the way
league tables do: equal values share the best rank and the
following ranks are skipped, so two silver medals mean
nobody gets bronze, and a value that is not in the list at
all is #N/A rather than a nearest-neighbor guess.
PERCENTRANK inverts the interpolation exactly and does not
copy the incumbent's silent rounding to three decimals; that
divergence is deliberate and stated here, because a function
that rounds without saying so is how two workbooks disagree
about the same data. TRIMMEAN drops the same count from each
end, the floor of the fraction times n halved, and the
geometric and harmonic means refuse non-positive inputs by
name, since a geometric mean crossing zero is not a number,
it is a wrong question. The first draft of TRIMMEAN guarded
against the trim eating every value; measurement at a
fraction of 0.99 on four values refuted the fear, one value
left each side and the middle two stayed, because the floor
of n times f over two is strictly below n over two for any
fraction under one. The guard was dead code and is gone,
and this sentence is its tombstone.
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


def _gather(
    args, lookup, functions, names
) -> list[float] | ErrorValue:
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


def _scalar(arg, lookup, functions, names) -> Value:
    value = evaluate(arg, lookup, functions, names)
    if is_error(value):
        return value
    return to_number(value)


def _interpolated(ordered: list[float], k: float) -> float:
    position = k * (len(ordered) - 1)
    lower = int(position)
    fraction = position - lower
    if fraction == 0:
        return ordered[lower]
    return ordered[lower] + fraction * (
        ordered[lower + 1] - ordered[lower]
    )


def _percentile(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="PERCENTILE takes a range and a k in [0, 1]",
        )
    numbers = _gather(args[:1], lookup, functions, names)
    if is_error(numbers):
        return numbers
    if not numbers:
        return ErrorValue(
            code="#NUM!",
            note="PERCENTILE of no values does not parse",
        )
    k = _scalar(args[1], lookup, functions, names)
    if is_error(k):
        return k
    if not 0.0 <= k <= 1.0:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"k must sit in [0, 1], got {k}; percent "
                "means a fraction of the way through"
            ),
        )
    return _interpolated(sorted(numbers), k)


def _quartile(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="QUARTILE takes a range and a quarter 0 to 4",
        )
    quarter = _scalar(args[1], lookup, functions, names)
    if is_error(quarter):
        return quarter
    whole = int(quarter)
    if not 0 <= whole <= 4:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"quarter {whole} does not exist; the range "
                "runs 0 (minimum) to 4 (maximum)"
            ),
        )
    numbers = _gather(args[:1], lookup, functions, names)
    if is_error(numbers):
        return numbers
    if not numbers:
        return ErrorValue(
            code="#NUM!",
            note="QUARTILE of no values does not parse",
        )
    return _interpolated(sorted(numbers), whole / 4)


def _rank(args, lookup, functions, names) -> Value:
    if len(args) not in (2, 3):
        return ErrorValue(
            code="#VALUE!",
            note=(
                "RANK takes a value, a range, and an "
                "optional order flag"
            ),
        )
    target = _scalar(args[0], lookup, functions, names)
    if is_error(target):
        return target
    numbers = _gather(args[1:2], lookup, functions, names)
    if is_error(numbers):
        return numbers
    ascending = False
    if len(args) == 3:
        flag = _scalar(args[2], lookup, functions, names)
        if is_error(flag):
            return flag
        ascending = flag != 0.0
    if target not in numbers:
        return ErrorValue(
            code="#N/A",
            note=(
                f"{target} is not among the {len(numbers)} "
                "value(s); rank does not guess a nearest "
                "neighbor"
            ),
        )
    if ascending:
        beaten = sum(1 for n in numbers if n < target)
    else:
        beaten = sum(1 for n in numbers if n > target)
    return float(beaten + 1)


def _percentrank(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="PERCENTRANK takes a range and a value",
        )
    numbers = _gather(args[:1], lookup, functions, names)
    if is_error(numbers):
        return numbers
    if len(numbers) < 2:
        return ErrorValue(
            code="#NUM!",
            note=(
                "PERCENTRANK needs at least 2 values; a "
                "fraction of the way through one value is "
                "not a question"
            ),
        )
    target = _scalar(args[1], lookup, functions, names)
    if is_error(target):
        return target
    ordered = sorted(numbers)
    if not ordered[0] <= target <= ordered[-1]:
        return ErrorValue(
            code="#N/A",
            note=(
                f"{target} sits outside "
                f"[{ordered[0]}, {ordered[-1]}]; there is no "
                "rank off the ends"
            ),
        )
    span = len(ordered) - 1
    for index in range(span):
        low, high = ordered[index], ordered[index + 1]
        if low <= target <= high:
            if high == low:
                return index / span
            fraction = (target - low) / (high - low)
            return (index + fraction) / span
    return 1.0


def _trimmean(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="TRIMMEAN takes a range and a fraction",
        )
    numbers = _gather(args[:1], lookup, functions, names)
    if is_error(numbers):
        return numbers
    fraction = _scalar(args[1], lookup, functions, names)
    if is_error(fraction):
        return fraction
    if not 0.0 <= fraction < 1.0:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"a trim fraction of {fraction} does not "
                "parse; it must sit in [0, 1)"
            ),
        )
    if not numbers:
        return ErrorValue(
            code="#NUM!",
            note="TRIMMEAN of no values does not parse",
        )
    per_side = int(len(numbers) * fraction / 2)
    kept = sorted(numbers)[
        per_side : len(numbers) - per_side
    ]
    return sum(kept) / len(kept)


def _geomean(args, lookup, functions, names) -> Value:
    numbers = _gather(args, lookup, functions, names)
    if is_error(numbers):
        return numbers
    if not numbers:
        return ErrorValue(
            code="#NUM!",
            note="GEOMEAN of no values does not parse",
        )
    for number in numbers:
        if number <= 0:
            return ErrorValue(
                code="#NUM!",
                note=(
                    f"GEOMEAN met {number}; a geometric mean "
                    "crossing zero is a wrong question"
                ),
            )
    product = 1.0
    for number in numbers:
        product *= number
    return product ** (1 / len(numbers))


def _harmean(args, lookup, functions, names) -> Value:
    numbers = _gather(args, lookup, functions, names)
    if is_error(numbers):
        return numbers
    if not numbers:
        return ErrorValue(
            code="#NUM!",
            note="HARMEAN of no values does not parse",
        )
    for number in numbers:
        if number <= 0:
            return ErrorValue(
                code="#NUM!",
                note=(
                    f"HARMEAN met {number}; the harmonic "
                    "mean needs positive values"
                ),
            )
    return len(numbers) / sum(1 / n for n in numbers)


RANK_FUNCTIONS = {
    "PERCENTILE": _percentile,
    "QUARTILE": _quartile,
    "RANK": _rank,
    "PERCENTRANK": _percentrank,
    "TRIMMEAN": _trimmean,
    "GEOMEAN": _geomean,
    "HARMEAN": _harmean,
}
