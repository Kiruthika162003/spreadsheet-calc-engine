"""XLOOKUP and HLOOKUP: the lookup rebuilt with its regrets designed out.

XLOOKUP is the incumbent's public apology for VLOOKUP, and
this implementation keeps the three fixes that constitute
the apology. The key column and the result column are
separate ranges of equal length, so inserting a column
between them breaks nothing and the counting-to-the-result
bug dies at the type level, with unequal lengths refused by
their two numbers. The not-found case is an argument, not a
sentinel: pass a fallback and it is returned, pass none and
the #N/A names the key, which keeps the fallback where the
formula's author can see it instead of buried in a wrapping
IFERROR. Search direction is explicit, first match from the
top or from the bottom, because last-match-wins is a real
question ledgers ask, who touched this account most
recently, and reversing a range by helper column to fake it
is the workaround this argument retires. HLOOKUP is
VLOOKUP's transpose with the same exact-by-default
discipline the vertical family already enforces, indexing
rows instead of columns, included because tables laid
sideways exist and rotating a worksheet to satisfy a
function is the tail wagging the dog.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.evaluate import evaluate
from gridiron.refs import CellRef
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    render,
)


def _na(key: Value) -> ErrorValue:
    return ErrorValue(
        code="#N/A",
        note=(
            f"lookup key {render(key)!r} not found; which "
            "key missed is the first question every broken "
            "lookup gets asked"
        ),
    )


def _column_values(
    arg, lookup
) -> list[Value] | ErrorValue:
    if not isinstance(arg, Range):
        return ErrorValue(
            code="#VALUE!",
            note="XLOOKUP takes ranges for its columns",
        )
    region = arg.ref
    if region.left != region.right:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "XLOOKUP columns are single columns; got "
                f"{region.right - region.left + 1} wide"
            ),
        )
    values: list[Value] = []
    for row in range(region.top, region.bottom + 1):
        value = lookup(CellRef(row=row, col=region.left))
        if is_error(value):
            return value
        values.append(value)
    return values


def _matches(candidate: Value, key: Value) -> bool:
    if isinstance(candidate, str) and isinstance(key, str):
        return candidate.upper() == key.upper()
    return candidate == key


def _xlookup(args, lookup, functions, names) -> Value:
    if len(args) not in (3, 4, 5):
        return ErrorValue(
            code="#VALUE!",
            note=(
                "XLOOKUP takes a key, a key column, a "
                "result column, an optional fallback, and "
                "an optional direction"
            ),
        )
    key = evaluate(args[0], lookup, functions, names)
    if is_error(key):
        return key
    keys = _column_values(args[1], lookup)
    if is_error(keys):
        return keys
    results = _column_values(args[2], lookup)
    if is_error(results):
        return results
    if len(keys) != len(results):
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"the key column has {len(keys)} row(s) "
                f"and the result column {len(results)}; "
                "unequal lengths are the counting bug "
                "reborn"
            ),
        )
    from_last = False
    if len(args) == 5:
        direction = evaluate(
            args[4], lookup, functions, names
        )
        if is_error(direction):
            return direction
        if not isinstance(direction, str) or (
            direction.upper() not in ("FIRST", "LAST")
        ):
            return ErrorValue(
                code="#VALUE!",
                note=(
                    "the direction is the text FIRST or "
                    "LAST, stated"
                ),
            )
        from_last = direction.upper() == "LAST"
    order = (
        range(len(keys) - 1, -1, -1)
        if from_last
        else range(len(keys))
    )
    for index in order:
        if _matches(keys[index], key):
            return results[index]
    if len(args) >= 4:
        return evaluate(args[3], lookup, functions, names)
    return _na(key)


def _hlookup(args, lookup, functions, names) -> Value:
    if len(args) != 3:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "HLOOKUP takes a key, a table, and a row "
                "number"
            ),
        )
    key = evaluate(args[0], lookup, functions, names)
    if is_error(key):
        return key
    if not isinstance(args[1], Range):
        return ErrorValue(
            code="#VALUE!",
            note="the table argument must be a range",
        )
    region = args[1].ref
    row_value = evaluate(
        args[2], lookup, functions, names
    )
    if is_error(row_value):
        return row_value
    if not isinstance(row_value, float) or isinstance(
        row_value, bool
    ):
        return ErrorValue(
            code="#VALUE!",
            note="the row number must be a number",
        )
    row_index = int(row_value)
    height = region.bottom - region.top + 1
    if not 1 <= row_index <= height:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"row {row_index} is outside the table's "
                f"{height} row(s)"
            ),
        )
    for col in range(region.left, region.right + 1):
        candidate = lookup(
            CellRef(row=region.top, col=col)
        )
        if is_error(candidate):
            return candidate
        if _matches(candidate, key):
            answer = lookup(
                CellRef(
                    row=region.top + row_index - 1,
                    col=col,
                )
            )
            if is_error(answer):
                return answer
            return answer
    return _na(key)


LOOKUP_EXTRA_FUNCTIONS = {
    "XLOOKUP": _xlookup,
    "HLOOKUP": _hlookup,
}
