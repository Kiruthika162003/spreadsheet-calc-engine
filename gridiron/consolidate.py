"""Consolidation: many label-and-value regions folded into one, by name.

Consolidating is what happens when four regional sheets each
list the same product categories in a different order and
finance needs one combined table. The operation folds a list
of two-column regions, a label column and a value column,
into a single map from label to combined value, matching by
label rather than by position, because position matching is
the bug that sums East's electronics into West's furniture
when someone inserts a row. The combining function is
explicit, sum or max or count, so the caller states whether
consolidating means totaling or picking the extreme, and a
label that appears in one region but not another contributes
where it appears rather than forcing a zero, because a
category absent from a region is missing data, not a measured
zero, and the two must not be confused. An error in any
value column poisons only that label's combined total, the
value model's promise carried through the fold, and a region
whose label column holds a number rather than text is refused
by name, since a consolidation keyed on numbers is a
consolidation waiting to merge account 100 with the quantity
100. The output preserves first-seen label order across the
regions, so the combined table reads in the order the data
first introduced its categories.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue, Value, is_error

_COMBINERS = ("SUM", "MAX", "MIN", "COUNT")


@dataclass(frozen=True)
class Region:
    sheet: Sheet
    area: RangeRef
    label_col: int
    value_col: int


def _pairs(region: Region) -> list[tuple[str, Value]]:
    pairs = []
    for row in range(region.area.top, region.area.bottom + 1):
        label = region.sheet.value_of(
            CellRef(row=row, col=region.label_col)
        )
        if label is None:
            continue
        if not isinstance(label, str):
            raise Invalid(
                f"a consolidation label must be text; row "
                f"{row + 1} holds a non-text label, and "
                "keying on numbers merges account 100 with "
                "the quantity 100"
            )
        value = region.sheet.value_of(
            CellRef(row=row, col=region.value_col)
        )
        pairs.append((label.strip(), value))
    return pairs


def _combine(
    combiner: str, values: list[Value]
) -> Value:
    for value in values:
        if is_error(value):
            return value
    numbers = [
        v
        for v in values
        if isinstance(v, float) and not isinstance(v, bool)
    ]
    if combiner == "COUNT":
        return float(len(numbers))
    if not numbers:
        return None
    if combiner == "SUM":
        return sum(numbers)
    if combiner == "MAX":
        return max(numbers)
    return min(numbers)


def consolidate(
    regions: list[Region], combiner: str = "SUM"
) -> dict[str, Value]:
    key = combiner.strip().upper()
    if key not in _COMBINERS:
        raise Invalid(
            f"unknown combiner {combiner!r}; pick one of "
            f"{', '.join(_COMBINERS)}"
        )
    order: list[str] = []
    gathered: dict[str, list[Value]] = {}
    for region in regions:
        for label, value in _pairs(region):
            if label not in gathered:
                gathered[label] = []
                order.append(label)
            gathered[label].append(value)
    return {
        label: _combine(key, gathered[label])
        for label in order
    }


def consolidate_error(
    label: str, note: str
) -> ErrorValue:
    return ErrorValue(code="#N/A", note=f"{label}: {note}")
