"""Statistics functions: MEDIAN interpolates, STDEV picks a side and says so.

Every statistics library quietly answers two contested
questions and most users never learn which way. The first is
the even-count median: this family interpolates, the mean of
the two middle values, matching the incumbent. The second is
the variance denominator: STDEV here is the sample form,
dividing by n minus one, and STDEVP the population form,
dividing by n, because shipping one function called STDEV
and letting the reader guess the denominator is how papers
get retracted. LARGE and SMALL are one-based like everything
users type, MODE returns the smallest of tied modes so the
answer is deterministic rather than dictionary-ordered, and
every function refuses fewer values than its formula needs,
with the minimum named: a standard deviation of one number
is not zero, it is a question that does not parse.
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


def _numbers(
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


def _need(numbers, minimum: int, what: str):
    if len(numbers) < minimum:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"{what} needs at least {minimum} value(s), "
                f"got {len(numbers)}; the question does not "
                "parse with fewer"
            ),
        )
    return None


def _median(args, lookup, functions, names) -> Value:
    numbers = _numbers(args, lookup, functions, names)
    if is_error(numbers):
        return numbers
    refusal = _need(numbers, 1, "MEDIAN")
    if refusal:
        return refusal
    ordered = sorted(numbers)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _mode(args, lookup, functions, names) -> Value:
    numbers = _numbers(args, lookup, functions, names)
    if is_error(numbers):
        return numbers
    refusal = _need(numbers, 1, "MODE")
    if refusal:
        return refusal
    counts: dict[float, int] = {}
    for number in numbers:
        counts[number] = counts.get(number, 0) + 1
    best = max(counts.values())
    if best == 1:
        return ErrorValue(
            code="#N/A",
            note="every value appears once; there is no mode",
        )
    return min(
        value
        for value, count in counts.items()
        if count == best
    )


def _variance(numbers: list[float], sample: bool) -> float:
    mean = sum(numbers) / len(numbers)
    total = sum((n - mean) ** 2 for n in numbers)
    return total / (len(numbers) - (1 if sample else 0))


def _stdev(sample: bool, label: str):
    def run(args, lookup, functions, names) -> Value:
        numbers = _numbers(args, lookup, functions, names)
        if is_error(numbers):
            return numbers
        refusal = _need(numbers, 2 if sample else 1, label)
        if refusal:
            return refusal
        return _variance(numbers, sample) ** 0.5

    return run


def _ranked(kind: str):
    def run(args, lookup, functions, names) -> Value:
        if len(args) != 2:
            return ErrorValue(
                code="#VALUE!",
                note=f"{kind} takes a range and a rank",
            )
        numbers = _numbers(
            args[:1], lookup, functions, names
        )
        if is_error(numbers):
            return numbers
        rank_value = to_number(
            evaluate(args[1], lookup, functions, names)
        )
        if is_error(rank_value):
            return rank_value
        rank = int(rank_value)
        if not 1 <= rank <= len(numbers):
            return ErrorValue(
                code="#NUM!",
                note=(
                    f"rank {rank} against {len(numbers)} "
                    "value(s); ranks are one-based like "
                    "everything users type"
                ),
            )
        ordered = sorted(
            numbers, reverse=(kind == "LARGE")
        )
        return ordered[rank - 1]

    return run


STAT_FUNCTIONS = {
    "MEDIAN": _median,
    "MODE": _mode,
    "STDEV": _stdev(True, "STDEV"),
    "STDEVP": _stdev(False, "STDEVP"),
    "LARGE": _ranked("LARGE"),
    "SMALL": _ranked("SMALL"),
}
