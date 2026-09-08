"""The IFS family: many criteria, all of which must hold, checked shape-first.

COUNTIF grew a plural because one condition is rarely the
question; the real one is how many rows are East and over
budget and this quarter, three criteria joined by and. This
family implements SUMIFS, COUNTIFS, AVERAGEIFS, MAXIFS, and
MINIFS with the incumbent's argument shape, which is the part
that trips everyone: SUMIFS leads with the sum range and then
takes criteria-range and criterion pairs, while COUNTIFS has
no value range and is all pairs, an inconsistency this module
mirrors rather than fixes because a formula that works in one
engine and not another over argument order is worse than an
ugly convention everyone already learned. Every criteria
range must match the sum range in length, and a mismatch is
refused with the two lengths rather than truncated, because
ranges that do not line up compare row three of one against
row four of another and the total is quietly wrong. The
criteria reuse the same micro-grammar COUNTIF speaks, parsed
by the criteria module, so a wildcard or a comparison means
the same thing here as there. A row counts only when every
criterion holds, empty cells never matching per the criteria
module's rule, and AVERAGEIFS over zero matching rows is a
#DIV/0! rather than a zero, because the average of nothing is
undefined and a zero would understate the real figure the
moment it is summed into something else.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.criteria import Criterion
from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.refs import CellRef
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    render,
)


def _cells(arg) -> list[CellRef] | None:
    if not isinstance(arg, Range):
        return None
    return arg.ref.cells()


def _criterion_of(arg, lookup, functions, names):
    value = evaluate(arg, lookup, functions, names)
    if is_error(value):
        return value
    source = (
        render(value)
        if isinstance(value, float)
        else value
    )
    if not isinstance(source, str):
        source = render(source)
    try:
        return Criterion.parse(source)
    except Invalid as refusal:
        return ErrorValue(
            code="#VALUE!", note=str(refusal)
        )


def _matching_rows(
    pairs, lookup, functions, names, length
):
    matches = [True] * length
    for range_arg, criterion_arg in pairs:
        cells = _cells(range_arg)
        if cells is None:
            return ErrorValue(
                code="#VALUE!",
                note="each criteria argument must be a range",
            )
        if len(cells) != length:
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"a criteria range has {len(cells)} "
                    f"cell(s) but the anchor has {length}; "
                    "mismatched ranges compare the wrong rows"
                ),
            )
        criterion = _criterion_of(
            criterion_arg, lookup, functions, names
        )
        if is_error(criterion):
            return criterion
        for index, cell in enumerate(cells):
            if matches[index] and not criterion.matches(
                lookup(cell)
            ):
                matches[index] = False
    return matches


def _sumifs(args, lookup, functions, names) -> Value:
    if len(args) < 3 or len(args) % 2 == 0:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "SUMIFS takes a sum range then "
                "criteria-range/criterion pairs"
            ),
        )
    sum_cells = _cells(args[0])
    if sum_cells is None:
        return ErrorValue(
            code="#VALUE!",
            note="the first argument is the sum range",
        )
    pairs = list(zip(args[1::2], args[2::2], strict=True))
    matches = _matching_rows(
        pairs, lookup, functions, names, len(sum_cells)
    )
    if is_error(matches):
        return matches
    total = 0.0
    for index, cell in enumerate(sum_cells):
        if not matches[index]:
            continue
        value = lookup(cell)
        if is_error(value):
            return value
        if isinstance(value, float) and not isinstance(
            value, bool
        ):
            total += value
    return total


def _countifs(args, lookup, functions, names) -> Value:
    if len(args) < 2 or len(args) % 2 == 1:
        return ErrorValue(
            code="#VALUE!",
            note="COUNTIFS takes criteria-range/criterion pairs",
        )
    first = _cells(args[0])
    if first is None:
        return ErrorValue(
            code="#VALUE!",
            note="each criteria argument must be a range",
        )
    pairs = list(zip(args[0::2], args[1::2], strict=True))
    matches = _matching_rows(
        pairs, lookup, functions, names, len(first)
    )
    if is_error(matches):
        return matches
    return float(sum(1 for m in matches if m))


def _conditional_values(
    args, lookup, functions, names
):
    value_cells = _cells(args[0])
    if value_cells is None:
        return ErrorValue(
            code="#VALUE!",
            note="the first argument is the value range",
        )
    pairs = list(zip(args[1::2], args[2::2], strict=True))
    matches = _matching_rows(
        pairs, lookup, functions, names, len(value_cells)
    )
    if is_error(matches):
        return matches
    collected = []
    for index, cell in enumerate(value_cells):
        if not matches[index]:
            continue
        value = lookup(cell)
        if is_error(value):
            return value
        if isinstance(value, float) and not isinstance(
            value, bool
        ):
            collected.append(value)
    return collected


def _averageifs(args, lookup, functions, names) -> Value:
    if len(args) < 3 or len(args) % 2 == 0:
        return ErrorValue(
            code="#VALUE!",
            note="AVERAGEIFS takes a value range then pairs",
        )
    values = _conditional_values(
        args, lookup, functions, names
    )
    if is_error(values):
        return values
    if not values:
        return ErrorValue(
            code="#DIV/0!",
            note=(
                "no rows matched every criterion; the "
                "average of nothing is undefined, not zero"
            ),
        )
    return sum(values) / len(values)


def _extreme(pick: str):
    def run(args, lookup, functions, names) -> Value:
        if len(args) < 3 or len(args) % 2 == 0:
            return ErrorValue(
                code="#VALUE!",
                note=f"{pick} takes a value range then pairs",
            )
        values = _conditional_values(
            args, lookup, functions, names
        )
        if is_error(values):
            return values
        if not values:
            return 0.0
        return max(values) if pick == "MAXIFS" else min(
            values
        )

    return run


MULTICRITERIA_FUNCTIONS = {
    "SUMIFS": _sumifs,
    "COUNTIFS": _countifs,
    "AVERAGEIFS": _averageifs,
    "MAXIFS": _extreme("MAXIFS"),
    "MINIFS": _extreme("MINIFS"),
}
