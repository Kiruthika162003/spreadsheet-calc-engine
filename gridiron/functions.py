"""The function library: aggregates that know a reference from an argument.

The oldest trap in spreadsheet functions is that SUM treats
the text "12" differently depending on how it arrives: typed
directly as an argument it coerces and counts, sitting in a
referenced cell it is silently ignored. This library keeps
the incumbent's rule because a million workbooks lean on it,
but keeps it in exactly one documented place, the flatten
step, where every argument declares itself scalar or region.
Errors poison any aggregate that touches them. IF evaluates
only the branch it takes, which is not an optimization but a
semantic: the untaken branch is allowed to be broken, and
half the conditional formulas in the wild rely on exactly
that permission. AVERAGE ignores empty cells while SUM
counts them as nothing, the one inconsistency users expect.
"""

from __future__ import annotations

from gridiron.ast import Node, Range
from gridiron.errors import Invalid
from gridiron.evaluate import (
    CellLookup,
    FunctionTable,
    NameTable,
    evaluate,
)
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _flatten(
    args: tuple[Node, ...],
    lookup: CellLookup,
    functions: FunctionTable,
    names: NameTable,
) -> list[tuple[str, Value]] | ErrorValue:
    gathered: list[tuple[str, Value]] = []
    for arg in args:
        if isinstance(arg, Range):
            for cell in arg.ref.cells():
                value = lookup(cell)
                if is_error(value):
                    return value
                gathered.append(("region", value))
        else:
            value = evaluate(arg, lookup, functions, names)
            if is_error(value):
                return value
            gathered.append(("scalar", value))
    return gathered


def _numeric(
    gathered: list[tuple[str, Value]],
) -> list[float] | ErrorValue:
    numbers: list[float] = []
    for origin, value in gathered:
        if origin == "region":
            if isinstance(value, float) and not isinstance(
                value, bool
            ):
                numbers.append(value)
            continue
        coerced = to_number(value)
        if is_error(coerced):
            return coerced
        numbers.append(coerced)
    return numbers


def _aggregate(kind: str):
    def run(args, lookup, functions, names) -> Value:
        gathered = _flatten(args, lookup, functions, names)
        if is_error(gathered):
            return gathered
        numbers = _numeric(gathered)
        if is_error(numbers):
            return numbers
        if kind == "SUM":
            return float(sum(numbers))
        if kind == "COUNT":
            return float(len(numbers))
        if not numbers:
            return ErrorValue(
                code="#DIV/0!",
                note=f"{kind} of nothing has no answer",
            )
        if kind == "AVERAGE":
            return sum(numbers) / len(numbers)
        if kind == "MIN":
            return min(numbers)
        return max(numbers)

    return run


def _if(args, lookup, functions, names) -> Value:
    if len(args) not in (2, 3):
        return ErrorValue(
            code="#VALUE!",
            note="IF takes a condition and one or two branches",
        )
    condition = evaluate(args[0], lookup, functions, names)
    if is_error(condition):
        return condition
    truthy = bool(condition) and condition != 0.0
    if truthy:
        return evaluate(args[1], lookup, functions, names)
    if len(args) == 3:
        return evaluate(args[2], lookup, functions, names)
    return False


def _round(args, lookup, functions, names) -> Value:
    if len(args) not in (1, 2):
        return ErrorValue(
            code="#VALUE!", note="ROUND takes a value and digits"
        )
    value = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(value):
        return value
    digits = 0.0
    if len(args) == 2:
        digits = to_number(
            evaluate(args[1], lookup, functions, names)
        )
        if is_error(digits):
            return digits
    return float(round(value, int(digits)))


def _abs(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="ABS takes one value"
        )
    value = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(value):
        return value
    return abs(value)


BUILTINS = {
    "SUM": _aggregate("SUM"),
    "COUNT": _aggregate("COUNT"),
    "AVERAGE": _aggregate("AVERAGE"),
    "MIN": _aggregate("MIN"),
    "MAX": _aggregate("MAX"),
    "IF": _if,
    "ROUND": _round,
    "ABS": _abs,
}


def builtin_table(name: str):
    return BUILTINS.get(name)


def register(name: str, function) -> None:
    upper = name.upper()
    if upper in BUILTINS:
        raise Invalid(
            f"{upper} exists; shadowing a builtin changes "
            "workbooks that never heard of you"
        )
    BUILTINS[upper] = function
