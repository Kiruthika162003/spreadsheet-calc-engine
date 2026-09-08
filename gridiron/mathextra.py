"""Trig, logs, and combinatorics: the domain errors named, not swallowed.

These are the functions with real mathematical domains, and
a spreadsheet that returns a number where the mathematics has
none is lying with a straight face. SQRT of a negative was
already refused by the math module this family extends, and
building it here surfaced the collision at once: the family
chain checks the base module first, so this module keeps the
functions that were genuinely missing and does not shadow the
one that was not. LOG refuses
zero and negatives and refuses a base of one, because log
base one is division by the logarithm of one, which is zero,
and the engine says so rather than raising ZeroDivisionError
from inside a helper. Trig works in radians, the mathematical
default, with DEGREES and RADIANS as the explicit bridges,
because the incumbent's silent-degrees convention in some
functions and silent-radians in others is the source of half
the wrong-angle bugs in engineering sheets; here the unit is
never a guess. GCD and LCM take whole numbers and say so when
handed a fraction, since the greatest common divisor of 2.5
is a question that does not parse, and LCM guards against the
overflow of multiplying before dividing by computing through
the GCD. FACT and COMBIN refuse negatives and non-integers,
and COMBIN refuses choosing more than the set holds rather
than returning zero, because zero ways is a true fact about
a different, valid question and silence about the invalid one
is how an off-by-one in the arguments survives.
"""

from __future__ import annotations

import math
from math import comb, factorial, gcd

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _one_number(args, lookup, functions, names, label):
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!",
            note=f"{label} takes one number",
        )
    value = evaluate(args[0], lookup, functions, names)
    if is_error(value):
        return value
    return to_number(value)


def _unary(label, run):
    def wrapped(args, lookup, functions, names) -> Value:
        number = _one_number(
            args, lookup, functions, names, label
        )
        if is_error(number):
            return number
        return run(number)

    return wrapped


def _ln(number: float) -> Value:
    if number <= 0:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"LN of {number}; the logarithm is defined "
                "only for positive numbers"
            ),
        )
    return math.log(number)


def _exp(number: float) -> Value:
    try:
        return math.exp(number)
    except OverflowError:
        return ErrorValue(
            code="#NUM!",
            note="EXP overflowed the representable world",
        )


def _log(args, lookup, functions, names) -> Value:
    if len(args) not in (1, 2):
        return ErrorValue(
            code="#VALUE!",
            note="LOG takes a number and an optional base",
        )
    number = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(number):
        return number
    base = 10.0
    if len(args) == 2:
        base = to_number(
            evaluate(args[1], lookup, functions, names)
        )
        if is_error(base):
            return base
    if number <= 0:
        return ErrorValue(
            code="#NUM!",
            note=f"LOG of {number}; the argument must be positive",
        )
    if base <= 0 or base == 1:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"base {base} does not define a logarithm; "
                "base one is division by zero wearing a "
                "disguise"
            ),
        )
    return math.log(number, base)


def _whole(number: float, label: str):
    if number != int(number):
        return ErrorValue(
            code="#NUM!",
            note=(
                f"{label} needs whole numbers; {number} is "
                "a question that does not parse"
            ),
        )
    return int(number)


def _collect_ints(args, lookup, functions, names, label):
    values = []
    for arg in args:
        number = to_number(
            evaluate(arg, lookup, functions, names)
        )
        if is_error(number):
            return number
        whole = _whole(number, label)
        if is_error(whole):
            return whole
        values.append(whole)
    return values


def _gcd(args, lookup, functions, names) -> Value:
    if not args:
        return ErrorValue(
            code="#VALUE!", note="GCD needs numbers"
        )
    values = _collect_ints(
        args, lookup, functions, names, "GCD"
    )
    if is_error(values):
        return values
    result = 0
    for value in values:
        result = gcd(result, abs(value))
    return float(result)


def _lcm(args, lookup, functions, names) -> Value:
    if not args:
        return ErrorValue(
            code="#VALUE!", note="LCM needs numbers"
        )
    values = _collect_ints(
        args, lookup, functions, names, "LCM"
    )
    if is_error(values):
        return values
    result = 1
    for value in values:
        if value == 0:
            return 0.0
        result = result // gcd(result, abs(value)) * abs(value)
    return float(result)


def _fact(args, lookup, functions, names) -> Value:
    number = _one_number(
        args, lookup, functions, names, "FACT"
    )
    if is_error(number):
        return number
    whole = _whole(number, "FACT")
    if is_error(whole):
        return whole
    if whole < 0:
        return ErrorValue(
            code="#NUM!",
            note="FACT of a negative is undefined",
        )
    return float(factorial(whole))


def _combin(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="COMBIN takes a set size and a choice",
        )
    values = _collect_ints(
        args, lookup, functions, names, "COMBIN"
    )
    if is_error(values):
        return values
    total, chosen = values
    if total < 0 or chosen < 0:
        return ErrorValue(
            code="#NUM!",
            note="COMBIN counts of a negative set do not exist",
        )
    if chosen > total:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"choosing {chosen} from {total} is not a "
                "smaller question with answer zero; it is an "
                "invalid one"
            ),
        )
    return float(comb(total, chosen))


MATH_EXTRA_FUNCTIONS = {
    "LN": _unary("LN", _ln),
    "EXP": _unary("EXP", _exp),
    "SIN": _unary("SIN", math.sin),
    "COS": _unary("COS", math.cos),
    "TAN": _unary("TAN", math.tan),
    "DEGREES": _unary("DEGREES", math.degrees),
    "RADIANS": _unary("RADIANS", math.radians),
    "LOG": _log,
    "GCD": _gcd,
    "LCM": _lcm,
    "FACT": _fact,
    "COMBIN": _combin,
}
