"""Set operations on rows: union, intersection, difference, keyed and stable.

Comparing two lists, which customers are in both, which are
new this month, which dropped off, is a set operation dressed
as a spreadsheet chore, and doing it by eye is how a renewal
list misses three names. This module treats each region as a
set of rows keyed by a chosen column and computes the three
operations that answer those questions. Two decisions keep it
honest. Order is preserved from the inputs rather than sorted,
because a union that reorders makes the reviewer re-find every
row they already knew, so union lists the first region's rows
in order then appends the second region's new ones in order,
and intersection and difference keep the order of the region
they draw from. Identity is the engine's own equality on the
key cell, so the number 5 and the text five are different
keys the same way they are everywhere else, and a duplicate
key within one region is collapsed to its first occurrence
before the operation, because a set with duplicates is a
multiset and the operations named here are set operations,
with the collapse counted and reported rather than done in
silence. A row whose key cell is empty is excluded and
counted, not treated as a key of blank that would match every
other blank into a spurious intersection.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value


def _hashable(value: Value):
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, float):
        return ("number", value)
    return ("text", value)


@dataclass
class KeyedRegion:
    sheet: Sheet
    area: RangeRef
    key_col: int
    dropped_duplicates: int = field(default=0)
    dropped_blanks: int = field(default=0)

    def keys_in_order(self) -> list[tuple]:
        seen = set()
        order = []
        self.dropped_duplicates = 0
        self.dropped_blanks = 0
        for row in range(
            self.area.top, self.area.bottom + 1
        ):
            value = self.sheet.value_of(
                CellRef(row=row, col=self.key_col)
            )
            if value is None:
                self.dropped_blanks += 1
                continue
            key = _hashable(value)
            if key in seen:
                self.dropped_duplicates += 1
                continue
            seen.add(key)
            order.append(key)
        return order


def _label(key: tuple) -> Value:
    return key[1] if len(key) > 1 else None


@dataclass
class SetResult:
    keys: list[tuple]
    note: str

    def labels(self) -> list[Value]:
        return [_label(key) for key in self.keys]


def union(
    left: KeyedRegion, right: KeyedRegion
) -> SetResult:
    left_keys = left.keys_in_order()
    right_keys = right.keys_in_order()
    seen = set(left_keys)
    result = list(left_keys)
    for key in right_keys:
        if key not in seen:
            seen.add(key)
            result.append(key)
    return SetResult(
        keys=result,
        note=(
            f"{len(result)} in the union of "
            f"{len(left_keys)} and {len(right_keys)}"
        ),
    )


def intersection(
    left: KeyedRegion, right: KeyedRegion
) -> SetResult:
    left_keys = left.keys_in_order()
    right_set = set(right.keys_in_order())
    result = [k for k in left_keys if k in right_set]
    return SetResult(
        keys=result,
        note=f"{len(result)} in both regions",
    )


def difference(
    left: KeyedRegion, right: KeyedRegion
) -> SetResult:
    left_keys = left.keys_in_order()
    right_set = set(right.keys_in_order())
    result = [
        k for k in left_keys if k not in right_set
    ]
    return SetResult(
        keys=result,
        note=(
            f"{len(result)} in the first region but not "
            "the second"
        ),
    )
