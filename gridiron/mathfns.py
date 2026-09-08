"""Math functions: CEILING climbs away from zero arguments, and says which way.

INT and the rounding family are where off-by-a-penny bugs
are born, so each function states its direction: INT floors
toward negative infinity, matching the incumbent, which
means INT of minus 2.1 is minus 3 and every teller who
assumed truncation learns it in production once. CEILING and
FLOOR here take a significance and snap to multiples of it,
refusing a zero significance rather than dividing by it, and
refusing mismatched signs because a positive number ceiling
to negative multiples is a question without a defensible
answer. SUMPRODUCT multiplies ranges elementwise and demands
equal shapes, the same discipline the conditional family
enforces, and SQRT of a negative is #NUM! with the value
shown, since the complex plane is not on the menu of any
ledger.
"""

from __future__ import annotations

import math

from gridiron.ast import Range
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _one_number(args, lookup, functions, names):
    return to_number(
        evaluate(args[0], lookup, functions, names)
    )


def _int(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="INT takes one value"
        )
    value = _one_number(args, lookup, functions, names)
    if is_error(value):
        return value
    return float(math.floor(value))


def _sqrt(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="SQRT takes one value"
        )
    value = _one_number(args, lookup, functions, names)
    if is_error(value):
        return value
    if value < 0:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"SQRT of {value}; the complex plane is not "
                "on the menu of any ledger"
            ),
        )
    return math.sqrt(value)


def _snap(kind: str):
    def run(args, lookup, functions, names) -> Value:
        if len(args) != 2:
            return ErrorValue(
                code="#VALUE!",
                note=f"{kind} takes a value and a significance",
            )
        value = _one_number(args, lookup, functions, names)
        if is_error(value):
            return value
        significance = to_number(
            evaluate(args[1], lookup, functions, names)
        )
        if is_error(significance):
            return significance
        if significance == 0:
            return ErrorValue(
                code="#DIV/0!",
                note=(
                    f"{kind} with zero significance is a "
                    "division wearing a costume"
                ),
            )
        if (value > 0) and (significance < 0):
            return ErrorValue(
                code="#NUM!",
                note=(
                    "a positive value against negative "
                    "multiples is a question without a "
                    "defensible answer"
                ),
            )
        quotient = value / significance
        snapped = (
            math.ceil(quotient)
            if kind == "CEILING"
            else math.floor(quotient)
        )
        return snapped * significance

    return run


def _product(args, lookup, functions, names) -> Value:
    total = 1.0
    counted = 0
    for arg in args:
        if isinstance(arg, Range):
            for cell in arg.ref.cells():
                value = lookup(cell)
                if is_error(value):
                    return value
                if isinstance(value, float) and not isinstance(
                    value, bool
                ):
                    total *= value
                    counted += 1
        else:
            value = to_number(
                evaluate(arg, lookup, functions, names)
            )
            if is_error(value):
                return value
            total *= value
            counted += 1
    if counted == 0:
        return ErrorValue(
            code="#VALUE!",
            note="PRODUCT of nothing multiplies nothing",
        )
    return total


def _sumproduct(args, lookup, _functions, _names) -> Value:
    if len(args) < 2 or not all(
        isinstance(arg, Range) for arg in args
    ):
        return ErrorValue(
            code="#VALUE!",
            note="SUMPRODUCT takes two or more ranges",
        )
    columns = []
    for arg in args:
        values = []
        for cell in arg.ref.cells():
            value = lookup(cell)
            if is_error(value):
                return value
            values.append(
                value
                if isinstance(value, float)
                and not isinstance(value, bool)
                else 0.0
            )
        columns.append(values)
    lengths = {len(column) for column in columns}
    if len(lengths) != 1:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"ranges of sizes {sorted(lengths)} cannot "
                "multiply elementwise; equal shapes are the "
                "same discipline the conditional family "
                "enforces"
            ),
        )
    total = 0.0
    for elements in zip(*columns, strict=True):
        term = 1.0
        for element in elements:
            term *= element
        total += term
    return total


MATH_FUNCTIONS = {
    "INT": _int,
    "SQRT": _sqrt,
    "CEILING": _snap("CEILING"),
    "FLOOR": _snap("FLOOR"),
    "PRODUCT": _product,
    "SUMPRODUCT": _sumproduct,
}
