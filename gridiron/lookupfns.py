"""Lookup functions: the fourth argument everyone forgets, defaulted safely.

VLOOKUP's approximate mode is the most expensive default in
office software: it assumes the first column is sorted,
silently returns the wrong row when it is not, and the
workbook looks fine until the one lookup that lands between
misordered keys. This engine inverts the default: exact
match unless approximate is requested, and approximate mode
validates the whole key column before it takes a single
stair, refusing with the two offending rows named. The first
draft checked order during the scan and was caught by its
own test: a probe below the first stair breaks out of the
scan immediately, so disorder past the break went unseen,
which is precisely the incumbent's failure mode this module
exists to refuse. A lookup that finds nothing is #N/A with
the key rendered, because "which key missed" is the first
question every broken lookup formula gets asked.
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
            f"lookup key {render(key)!r} not found; which key "
            "missed is the first question every broken lookup "
            "gets asked"
        ),
    )


def _grid(
    arg, lookup
) -> list[list[Value]] | ErrorValue:
    if not isinstance(arg, Range):
        return ErrorValue(
            code="#VALUE!",
            note="the table argument must be a range",
        )
    region = arg.ref
    rows: list[list[Value]] = []
    for row in range(region.top, region.bottom + 1):
        line: list[Value] = []
        for col in range(region.left, region.right + 1):
            value = lookup(CellRef(row=row, col=col))
            if is_error(value):
                return value
            line.append(value)
        rows.append(line)
    return rows


def _same_kind(left: Value, right: Value) -> bool:
    return isinstance(left, type(right)) or isinstance(
        right, type(left)
    )


def _vlookup(args, lookup, functions, names) -> Value:
    if len(args) not in (3, 4):
        return ErrorValue(
            code="#VALUE!",
            note=(
                "VLOOKUP takes key, table, column, and an "
                "optional approximate flag"
            ),
        )
    key = evaluate(args[0], lookup, functions, names)
    if is_error(key):
        return key
    grid = _grid(args[1], lookup)
    if is_error(grid):
        return grid
    column = evaluate(args[2], lookup, functions, names)
    if is_error(column):
        return column
    if (
        not isinstance(column, float)
        or int(column) < 1
        or int(column) > len(grid[0])
    ):
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"column {render(column)} is outside the "
                f"table's {len(grid[0])} column(s)"
            ),
        )
    approximate = False
    if len(args) == 4:
        flag = evaluate(args[3], lookup, functions, names)
        if is_error(flag):
            return flag
        approximate = bool(flag)
    col_index = int(column) - 1
    if not approximate:
        for row in grid:
            if row[0] == key:
                return row[col_index]
        return _na(key)
    for number in range(1, len(grid)):
        earlier = grid[number - 1][0]
        later = grid[number][0]
        if _same_kind(earlier, later) and later < earlier:
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"approximate mode needs sorted keys; rows "
                    f"{number} and {number + 1} of the table "
                    "disagree, and a plausible wrong answer "
                    "would be worse"
                ),
            )
    best: list[Value] | None = None
    for row in grid:
        first = row[0]
        if _same_kind(first, key) and first <= key:
            best = row
        if _same_kind(first, key) and first > key:
            break
    if best is None:
        return _na(key)
    return best[col_index]


def _match(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="MATCH here takes a key and a range, exact only",
        )
    key = evaluate(args[0], lookup, functions, names)
    if is_error(key):
        return key
    grid = _grid(args[1], lookup)
    if is_error(grid):
        return grid
    flat = [value for row in grid for value in row]
    for position, value in enumerate(flat, start=1):
        if value == key:
            return float(position)
    return _na(key)


def _index(args, lookup, functions, names) -> Value:
    if len(args) != 3:
        return ErrorValue(
            code="#VALUE!",
            note="INDEX takes a range, a row, and a column",
        )
    grid = _grid(args[0], lookup)
    if is_error(grid):
        return grid
    row = evaluate(args[1], lookup, functions, names)
    col = evaluate(args[2], lookup, functions, names)
    poisoned = next(
        (v for v in (row, col) if is_error(v)), None
    )
    if poisoned:
        return poisoned
    try:
        row_index = int(row)
        col_index = int(col)
    except (TypeError, ValueError):
        return ErrorValue(
            code="#VALUE!", note="INDEX positions are numbers"
        )
    if not (
        1 <= row_index <= len(grid)
        and 1 <= col_index <= len(grid[0])
    ):
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"position ({row_index}, {col_index}) is "
                f"outside the {len(grid)}x{len(grid[0])} table"
            ),
        )
    return grid[row_index - 1][col_index - 1]


LOOKUP_FUNCTIONS = {
    "VLOOKUP": _vlookup,
    "MATCH": _match,
    "INDEX": _index,
}
