"""Three-dimensional aggregation: the same cell, gathered across a stack of sheets.

The classic three-dimensional reference sums B5 across
January through December, twelve sheets laid out identically,
and this module computes that gather over an explicit,
ordered list of sheet names rather than a from-here-to-there
range, because a range across sheets breaks the moment
someone reorders the tabs and a named list survives it. The
aggregation reuses the value model's error discipline
literally: a wound on any gathered sheet flows into the
result rather than being skipped, because a year-to-date
total that silently drops the month with a #DIV/0! is a
smaller, wrong number that reconciles against nothing. A
sheet named in the list that does not exist in the workbook
is itself a #REF!, the same wound a deleted sheet leaves
behind a cross-sheet formula, so a typo in the sheet list
surfaces as an error in the total instead of a silently
omitted term. Non-numeric cells are skipped rather than
coerced, matching how SUM already treats stray text, so a
label accidentally sitting in the gathered cell on one sheet
does not become a zero that drags the average. COUNT reports
how many of the gathered cells were numbers, which is the
denominator the average divides by, and the two are computed
from the same gather so they cannot disagree.
"""

from __future__ import annotations

from gridiron.refs import CellRef
from gridiron.values import (
    ErrorValue,
    Value,
    first_error,
    is_error,
)
from gridiron.workbook import Workbook


def _gather(
    book: Workbook, sheets: list[str], ref: CellRef
) -> list[Value]:
    return [book.read(name, ref) for name in sheets]


def _numbers(values: list[Value]) -> list[float]:
    return [
        v
        for v in values
        if isinstance(v, float) and not isinstance(v, bool)
    ]


def _first_wound(values: list[Value]) -> Value | None:
    errors = [v for v in values if is_error(v)]
    if errors:
        return first_error(*errors)
    return None


def sum3d(
    book: Workbook, sheets: list[str], ref: CellRef
) -> Value:
    if not sheets:
        return ErrorValue(
            code="#REF!",
            note="a 3D sum needs at least one sheet",
        )
    values = _gather(book, sheets, ref)
    wound = _first_wound(values)
    if wound is not None:
        return wound
    return sum(_numbers(values))


def count3d(
    book: Workbook, sheets: list[str], ref: CellRef
) -> Value:
    values = _gather(book, sheets, ref)
    wound = _first_wound(values)
    if wound is not None:
        return wound
    return float(len(_numbers(values)))


def average3d(
    book: Workbook, sheets: list[str], ref: CellRef
) -> Value:
    values = _gather(book, sheets, ref)
    wound = _first_wound(values)
    if wound is not None:
        return wound
    numbers = _numbers(values)
    if not numbers:
        return ErrorValue(
            code="#DIV/0!",
            note="no numeric cells across the sheets to average",
        )
    return sum(numbers) / len(numbers)


def max3d(
    book: Workbook, sheets: list[str], ref: CellRef
) -> Value:
    values = _gather(book, sheets, ref)
    wound = _first_wound(values)
    if wound is not None:
        return wound
    numbers = _numbers(values)
    if not numbers:
        return ErrorValue(
            code="#NUM!",
            note="no numeric cells across the sheets",
        )
    return max(numbers)


def min3d(
    book: Workbook, sheets: list[str], ref: CellRef
) -> Value:
    values = _gather(book, sheets, ref)
    wound = _first_wound(values)
    if wound is not None:
        return wound
    numbers = _numbers(values)
    if not numbers:
        return ErrorValue(
            code="#NUM!",
            note="no numeric cells across the sheets",
        )
    return min(numbers)
