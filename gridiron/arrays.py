"""Array operations: grids in, grids out, and every shape rule said aloud.

The array lab reads a region into a grid, transforms it, and
spills the result through the spill manager, which means
every operation here inherits the all-or-nothing landing and
the named blocker for free instead of reinventing them.
TRANSPOSE is the honest baseline, rows become columns and
nothing else changes, errors riding along verbatim because
an error is a value with the same right to a seat. UNIQUE
keeps first appearances in first-seen order rather than
sorting as a side effect, since deduplication that reorders
is two operations wearing one name. SORT sinks empties to
the bottom whichever direction the numbers go, matching the
sorting module's rule, and refuses mixed text-and-number
columns instead of inventing a cross-type order. FREQUENCY
returns one more bucket than it has edges, the incumbent's
convention, because values above the last edge still
happened and a histogram that silently drops its tail is a
lie about the data's range. MMULT demands numbers in every
seat and an inner dimension that agrees, and its refusal
quotes both shapes, because rows-of-A times columns-of-B is
the one fact every matrix bug report needs first.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
)

Grid = list[list[Value]]


def region_grid(sheet: Sheet, region: RangeRef) -> Grid:
    return [
        [
            sheet.value_of(CellRef(row=row, col=col))
            for col in range(region.left, region.right + 1)
        ]
        for row in range(region.top, region.bottom + 1)
    ]


def transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid, strict=True)]


def unique_column(grid: Grid) -> Grid:
    if any(len(row) != 1 for row in grid):
        raise Invalid(
            "UNIQUE here works on a single column; "
            "reshape wider data first"
        )
    seen = []
    for row in grid:
        value = row[0]
        if value is None:
            continue
        if value not in seen:
            seen.append(value)
    if not seen:
        raise Invalid("UNIQUE of an empty column has no rows")
    return [[value] for value in seen]


def sort_column(grid: Grid, descending: bool = False) -> Grid:
    if any(len(row) != 1 for row in grid):
        raise Invalid(
            "SORT here works on a single column; "
            "reshape wider data first"
        )
    filled = [row[0] for row in grid if row[0] is not None]
    for value in filled:
        if is_error(value):
            raise Invalid(
                "a column containing errors will not sort; "
                "fix the errors first"
            )
    kinds = {
        isinstance(value, str) for value in filled
    }
    if len(kinds) > 1:
        raise Invalid(
            "the column mixes text and numbers; there is "
            "no honest order across types"
        )
    ordered = sorted(filled, reverse=descending)
    blanks = len(grid) - len(filled)
    result: Grid = [[value] for value in ordered]
    result.extend([[None]] * blanks)
    return result


def frequency(grid: Grid, edges: list[float]) -> Grid:
    if sorted(edges) != edges:
        raise Invalid(
            "FREQUENCY edges must rise; a shuffled "
            "histogram is not a histogram"
        )
    if not edges:
        raise Invalid("FREQUENCY needs at least one edge")
    numbers = []
    for row in grid:
        for value in row:
            if is_error(value):
                raise Invalid(
                    "the data contains errors; a histogram "
                    "of wounds is not a histogram of values"
                )
            if isinstance(value, float) and not isinstance(
                value, bool
            ):
                numbers.append(value)
    counts = [0.0] * (len(edges) + 1)
    for number in numbers:
        placed = False
        for index, edge in enumerate(edges):
            if number <= edge:
                counts[index] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    return [[count] for count in counts]


def mmult(a: Grid, b: Grid) -> Grid:
    a_rows, a_cols = len(a), len(a[0])
    b_rows, b_cols = len(b), len(b[0])
    if a_cols != b_rows:
        raise Invalid(
            f"MMULT shapes disagree: {a_rows}x{a_cols} "
            f"times {b_rows}x{b_cols} needs the inner "
            "numbers to match"
        )
    for grid in (a, b):
        for row in grid:
            for value in row:
                if not isinstance(
                    value, float
                ) or isinstance(value, bool):
                    return [
                        [
                            ErrorValue(
                                code="#VALUE!",
                                note=(
                                    "MMULT demands numbers "
                                    "in every seat"
                                ),
                            )
                        ]
                    ]
    return [
        [
            sum(
                a[row][inner] * b[inner][col]
                for inner in range(a_cols)
            )
            for col in range(b_cols)
        ]
        for row in range(a_rows)
    ]


@dataclass
class ArrayLab:
    sheet: Sheet
    spill: SpillManager

    def _land(
        self, anchor: CellRef, grid: Grid
    ) -> Value | str:
        return self.spill.spill_grid(anchor, grid)

    def transpose_region(
        self, region: RangeRef, anchor: CellRef
    ) -> Value | str:
        return self._land(
            anchor, transpose(region_grid(self.sheet, region))
        )

    def unique_region(
        self, region: RangeRef, anchor: CellRef
    ) -> Value | str:
        return self._land(
            anchor,
            unique_column(region_grid(self.sheet, region)),
        )

    def sort_region(
        self,
        region: RangeRef,
        anchor: CellRef,
        descending: bool = False,
    ) -> Value | str:
        return self._land(
            anchor,
            sort_column(
                region_grid(self.sheet, region), descending
            ),
        )

    def frequency_region(
        self,
        region: RangeRef,
        edges: list[float],
        anchor: CellRef,
    ) -> Value | str:
        return self._land(
            anchor,
            frequency(region_grid(self.sheet, region), edges),
        )

    def mmult_regions(
        self,
        left: RangeRef,
        right: RangeRef,
        anchor: CellRef,
    ) -> Value | str:
        product = mmult(
            region_grid(self.sheet, left),
            region_grid(self.sheet, right),
        )
        return self._land(anchor, product)
