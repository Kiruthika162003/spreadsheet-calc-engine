"""Reshaping regions: take, drop, and pick rows or columns, landed by the spill.

The modern reshaping functions slice a region without a
formula per cell, and they share the array lab's honesty:
read the source, compute a smaller grid, and land it through
the spill manager so all-or-nothing landing and the named
blocker come for free. TAKE keeps the first or last n rows,
a negative count meaning from the end, the incumbent's
convention, and taking more rows than exist keeps them all
rather than erroring, because take-up-to-n is what a caller
asking for the top ten of a maybe-shorter list actually
wants. DROP is the complement, removing the first or last n,
and dropping everything leaves nothing, which is refused
rather than spilled as an empty rectangle that reads as a
mystery blank. CHOOSEROWS and CHOOSECOLS pick specific
one-based indices in the order given, so a caller can
reorder or repeat, and an index outside the region is refused
by name rather than clamped, because CHOOSEROWS(region, 9) on
a five-row region is an off-by-something the caller needs
told. Every function preserves the source's values exactly,
copying not computing, so a reshaped region is the same data
in a new arrangement and never a recomputation that could
drift from what the cells actually hold.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import Value

Grid = list[list[Value]]


def _read(sheet: Sheet, region: RangeRef) -> Grid:
    return [
        [
            sheet.value_of(CellRef(row=row, col=col))
            for col in range(region.left, region.right + 1)
        ]
        for row in range(region.top, region.bottom + 1)
    ]


@dataclass
class Reshaper:
    sheet: Sheet
    spill: SpillManager

    def _land(self, anchor, grid):
        if not grid or not grid[0]:
            raise Invalid(
                "the reshape left nothing to land"
            )
        return self.spill.spill_grid(anchor, grid)

    def take(
        self,
        region: RangeRef,
        rows: int,
        anchor: CellRef,
    ) -> Value | str:
        grid = _read(self.sheet, region)
        if rows == 0:
            raise Invalid("TAKE of zero rows keeps nothing")
        if rows > 0:
            kept = grid[:rows]
        else:
            kept = grid[rows:]
        return self._land(anchor, kept)

    def drop(
        self,
        region: RangeRef,
        rows: int,
        anchor: CellRef,
    ) -> Value | str:
        grid = _read(self.sheet, region)
        if rows >= 0:
            kept = grid[rows:]
        else:
            kept = grid[:rows]
        if not kept:
            raise Invalid(
                "DROP removed every row; nothing left to "
                "land, and an empty spill reads as a mystery "
                "blank"
            )
        return self._land(anchor, kept)

    def choose_rows(
        self,
        region: RangeRef,
        indices: list[int],
        anchor: CellRef,
    ) -> Value | str:
        grid = _read(self.sheet, region)
        chosen = []
        for index in indices:
            if not 1 <= index <= len(grid):
                raise Invalid(
                    f"row {index} is outside the "
                    f"{len(grid)}-row region; CHOOSEROWS "
                    "does not clamp"
                )
            chosen.append(list(grid[index - 1]))
        return self._land(anchor, chosen)

    def choose_cols(
        self,
        region: RangeRef,
        indices: list[int],
        anchor: CellRef,
    ) -> Value | str:
        grid = _read(self.sheet, region)
        width = len(grid[0]) if grid else 0
        for index in indices:
            if not 1 <= index <= width:
                raise Invalid(
                    f"column {index} is outside the "
                    f"{width}-column region; CHOOSECOLS "
                    "does not clamp"
                )
        chosen = [
            [row[index - 1] for index in indices]
            for row in grid
        ]
        return self._land(anchor, chosen)
