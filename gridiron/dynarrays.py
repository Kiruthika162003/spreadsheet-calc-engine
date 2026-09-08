"""FILTER and SORTBY: query a region into a smaller region, landed by the spill.

These are the dynamic-array workhorses, and they share the
array lab's honesty: read a source region, compute a smaller
or reordered one, and land it through the spill manager so
the all-or-nothing rule and the named blocker come along for
free. FILTER keeps the rows whose parallel condition column
is truthy, and a condition column of a different length than
the source is refused by its two numbers rather than
truncated to the shorter, because a filter that silently
drops the tail of the longer input is answering a question
nobody asked. When nothing matches, FILTER does not spill an
empty region that reads as a mystery blank; it lands the
caller's stated fallback, and refuses with a named error
when no fallback was given, because zero rows is a real
answer that still needs somewhere to be shown. SORTBY orders
the source rows by a separate key column without moving the
key into the output, which is the whole point over a plain
sort: rank the report by a hidden score and show only the
report. Both treat an error anywhere in the region as
poison for the whole operation rather than sorting or
filtering around it, since a comparison against a wound has
no defined truth.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import Value, is_error

Grid = list[list[Value]]


def _column(sheet: Sheet, region: RangeRef) -> list[Value]:
    if region.left != region.right:
        raise Invalid(
            "a condition or key is a single column; got "
            f"{region.right - region.left + 1} wide"
        )
    return [
        sheet.value_of(CellRef(row=row, col=region.left))
        for row in range(region.top, region.bottom + 1)
    ]


def _rows(sheet: Sheet, region: RangeRef) -> Grid:
    return [
        [
            sheet.value_of(CellRef(row=row, col=col))
            for col in range(region.left, region.right + 1)
        ]
        for row in range(region.top, region.bottom + 1)
    ]


def _poison(grid: Grid) -> Value | None:
    for row in grid:
        for value in row:
            if is_error(value):
                return value
    return None


def _truthy(value: Value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value != 0.0
    if isinstance(value, str):
        return value != ""
    return False


@dataclass
class DynamicArrays:
    sheet: Sheet
    spill: SpillManager

    def filter(
        self,
        source: RangeRef,
        condition: RangeRef,
        anchor: CellRef,
        fallback: Value | None = None,
    ) -> Value | str:
        grid = _rows(self.sheet, source)
        flags = _column(self.sheet, condition)
        height = source.bottom - source.top + 1
        if len(flags) != height:
            raise Invalid(
                f"the condition has {len(flags)} row(s) "
                f"and the source {height}; a filter will "
                "not drop the tail of the longer one"
            )
        poison = _poison(grid) or _poison(
            [[flag] for flag in flags]
        )
        if poison is not None:
            return poison
        kept = [
            row
            for row, flag in zip(grid, flags, strict=True)
            if _truthy(flag)
        ]
        if not kept:
            if fallback is None:
                raise Invalid(
                    "nothing matched and no fallback was "
                    "given; zero rows is a real answer "
                    "that still needs somewhere to be shown"
                )
            return self.spill.spill_grid(
                anchor, [[fallback]]
            )
        return self.spill.spill_grid(anchor, kept)

    def sortby(
        self,
        source: RangeRef,
        key: RangeRef,
        anchor: CellRef,
        descending: bool = False,
    ) -> Value | str:
        grid = _rows(self.sheet, source)
        keys = _column(self.sheet, key)
        height = source.bottom - source.top + 1
        if len(keys) != height:
            raise Invalid(
                f"the key has {len(keys)} row(s) and the "
                f"source {height}; SORTBY needs one key per "
                "row"
            )
        poison = _poison(grid) or _poison(
            [[k] for k in keys]
        )
        if poison is not None:
            return poison
        decorated = sorted(
            zip(keys, grid, strict=True),
            key=lambda pair: _sort_key(pair[0]),
            reverse=descending,
        )
        ordered = [row for _, row in decorated]
        return self.spill.spill_grid(anchor, ordered)


_TYPE_RANK = {"number": 0, "text": 1, "bool": 2}


def _sort_key(value: Value):
    if isinstance(value, bool):
        return (_TYPE_RANK["bool"], value)
    if isinstance(value, float):
        return (_TYPE_RANK["number"], value)
    if isinstance(value, str):
        return (_TYPE_RANK["text"], value.upper())
    return (_TYPE_RANK["number"], 0.0)
