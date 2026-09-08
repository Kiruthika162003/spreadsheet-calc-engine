"""Logic functions: AND is not lazy, IFERROR is, and the difference is policy.

AND and OR evaluate every argument even after the answer is
settled, matching the incumbent, because formulas grow side
effects in extensions and an engine that short-circuits
where the reference does not will disagree with it somewhere
subtle. IFERROR is the deliberate opposite: it exists to
catch, so the fallback is evaluated only when the first
argument actually errs, and a fallback that itself errs is
allowed to, since masking the mask would leave nothing
trustworthy on the page. The empty AND() is refused rather
than defaulting to TRUE, because vacuous truth is a logic
course's joke and a spreadsheet's incident.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _truthiness(value: Value) -> bool | ErrorValue:
    if is_error(value):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value != 0.0
    if value is None:
        return False
    return ErrorValue(
        code="#VALUE!",
        note=f"text {value!r} is not a truth value",
    )


def _gather_truths(args, lookup, functions, names):
    truths = []
    poisoned = None
    for arg in args:
        value = evaluate(arg, lookup, functions, names)
        truth = _truthiness(value)
        if is_error(truth) and poisoned is None:
            poisoned = truth
        elif not is_error(truth):
            truths.append(truth)
    return truths, poisoned


def _and(args, lookup, functions, names) -> Value:
    if not args:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "AND of nothing is a logic course's joke and "
                "a spreadsheet's incident"
            ),
        )
    truths, poisoned = _gather_truths(
        args, lookup, functions, names
    )
    if poisoned:
        return poisoned
    return all(truths)


def _or(args, lookup, functions, names) -> Value:
    if not args:
        return ErrorValue(
            code="#VALUE!", note="OR of nothing decides nothing"
        )
    truths, poisoned = _gather_truths(
        args, lookup, functions, names
    )
    if poisoned:
        return poisoned
    return any(truths)


def _not(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="NOT takes one argument"
        )
    truth = _truthiness(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(truth):
        return truth
    return not truth


def _xor(args, lookup, functions, names) -> Value:
    if not args:
        return ErrorValue(
            code="#VALUE!", note="XOR of nothing decides nothing"
        )
    truths, poisoned = _gather_truths(
        args, lookup, functions, names
    )
    if poisoned:
        return poisoned
    return sum(1 for truth in truths if truth) % 2 == 1


def _iferror(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="IFERROR takes a try and a fallback",
        )
    attempt = evaluate(args[0], lookup, functions, names)
    if not is_error(attempt):
        return attempt
    return evaluate(args[1], lookup, functions, names)


def _mod(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!", note="MOD takes a value and a divisor"
        )
    value = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(value):
        return value
    divisor = to_number(
        evaluate(args[1], lookup, functions, names)
    )
    if is_error(divisor):
        return divisor
    if divisor == 0.0:
        return ErrorValue(
            code="#DIV/0!", note="MOD by zero"
        )
    return value - divisor * (value // divisor)


LOGIC_FUNCTIONS = {
    "AND": _and,
    "OR": _or,
    "NOT": _not,
    "XOR": _xor,
    "IFERROR": _iferror,
    "MOD": _mod,
}
