"""Still more math: rounding that means what it says, and the inverse trig.

The rounding family is where spreadsheet users get quietly
burned, because ROUND, ROUNDUP, ROUNDDOWN, and TRUNC are four
different operations and the difference matters at the penny.
ROUNDUP rounds away from zero, ROUNDDOWN toward zero, and
TRUNC is ROUNDDOWN's honest twin that also drops to an
integer by default, so this family keeps them distinct
rather than collapsing them into one helpful guess. MROUND
rounds to the nearest multiple and refuses a multiple whose
sign disagrees with the number, matching the incumbent,
because rounding 5 to the nearest -2 is a question with no
sensible answer and inventing one hides a sign error
upstream. The inverse trig functions carry their real
domains: ASIN and ACOS refuse an argument outside minus one
to one by name, because the arcsine of two is not a large
angle, it is undefined, and returning a complex number or a
clamp would both be lies. ATAN2 takes its arguments in the
incumbent's x-then-y order deliberately, stated here because
half the world's atan2 takes y-then-x and a silent
disagreement flips every angle into the wrong quadrant. PI
is a function taking no arguments rather than a constant,
matching how a sheet references it, and SIGN returns the
three-valued sign with zero mapping to zero, not to one.
"""

from __future__ import annotations

import math

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _args(args, lookup, functions, names, count, label):
    if len(args) != count:
        return ErrorValue(
            code="#VALUE!",
            note=f"{label} takes {count} argument(s)",
        )
    gathered = []
    for arg in args:
        value = to_number(
            evaluate(arg, lookup, functions, names)
        )
        if is_error(value):
            return value
        gathered.append(value)
    return gathered


def _unary(label, run):
    def wrapped(args, lookup, functions, names) -> Value:
        parsed = _args(
            args, lookup, functions, names, 1, label
        )
        if is_error(parsed):
            return parsed
        return run(parsed[0])

    return wrapped


def _sign(number: float) -> Value:
    if number > 0:
        return 1.0
    if number < 0:
        return -1.0
    return 0.0


def _arcsin(number: float) -> Value:
    if not -1.0 <= number <= 1.0:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"ASIN of {number}; the arcsine is defined "
                "only on [-1, 1]"
            ),
        )
    return math.asin(number)


def _arccos(number: float) -> Value:
    if not -1.0 <= number <= 1.0:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"ACOS of {number}; the arccosine is "
                "defined only on [-1, 1]"
            ),
        )
    return math.acos(number)


def _rounding(mode: str):
    def run(args, lookup, functions, names) -> Value:
        parsed = _args(
            args, lookup, functions, names, 2, mode
        )
        if is_error(parsed):
            return parsed
        number, digits = parsed
        factor = 10 ** int(digits)
        scaled = number * factor
        if mode == "ROUNDUP":
            rounded = math.ceil(abs(scaled)) * (
                1 if scaled >= 0 else -1
            )
        else:
            rounded = math.floor(abs(scaled)) * (
                1 if scaled >= 0 else -1
            )
        return rounded / factor

    return run


def _trunc(args, lookup, functions, names) -> Value:
    if len(args) not in (1, 2):
        return ErrorValue(
            code="#VALUE!",
            note="TRUNC takes a number and optional digits",
        )
    number = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(number):
        return number
    digits = 0
    if len(args) == 2:
        d = to_number(
            evaluate(args[1], lookup, functions, names)
        )
        if is_error(d):
            return d
        digits = int(d)
    factor = 10**digits
    return math.trunc(number * factor) / factor


def _mround(args, lookup, functions, names) -> Value:
    parsed = _args(
        args, lookup, functions, names, 2, "MROUND"
    )
    if is_error(parsed):
        return parsed
    number, multiple = parsed
    if multiple == 0:
        return 0.0
    if (number > 0) != (multiple > 0):
        return ErrorValue(
            code="#NUM!",
            note=(
                "MROUND refuses a multiple whose sign "
                "disagrees with the number; there is no "
                "sensible nearest multiple across zero"
            ),
        )
    return round(number / multiple) * multiple


def _power(args, lookup, functions, names) -> Value:
    parsed = _args(
        args, lookup, functions, names, 2, "POWER"
    )
    if is_error(parsed):
        return parsed
    base, exponent = parsed
    try:
        result = base**exponent
    except (OverflowError, ValueError):
        return ErrorValue(
            code="#NUM!",
            note="POWER left the representable world",
        )
    if isinstance(result, complex):
        return ErrorValue(
            code="#NUM!",
            note=(
                "a fractional power of a negative base is "
                "complex; not on any ledger"
            ),
        )
    return float(result)


def _atan2(args, lookup, functions, names) -> Value:
    parsed = _args(
        args, lookup, functions, names, 2, "ATAN2"
    )
    if is_error(parsed):
        return parsed
    x, y = parsed
    if x == 0 and y == 0:
        return ErrorValue(
            code="#DIV/0!",
            note="ATAN2 of the origin has no defined angle",
        )
    return math.atan2(y, x)


MATH_MORE_FUNCTIONS = {
    "SIGN": _unary("SIGN", _sign),
    "TRUNC": _trunc,
    "ROUNDUP": _rounding("ROUNDUP"),
    "ROUNDDOWN": _rounding("ROUNDDOWN"),
    "MROUND": _mround,
    "POWER": _power,
    "ASIN": _unary("ASIN", _arcsin),
    "ACOS": _unary("ACOS", _arccos),
    "ATAN": _unary("ATAN", math.atan),
    "ATAN2": _atan2,
    "SINH": _unary("SINH", math.sinh),
    "COSH": _unary("COSH", math.cosh),
    "TANH": _unary("TANH", math.tanh),
    "PI": lambda args, _l, _f, _n: (
        math.pi
        if not args
        else ErrorValue(
            code="#VALUE!", note="PI takes no arguments"
        )
    ),
}
