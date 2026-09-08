"""Freeze panes: the header rows that stay while the body scrolls.

Freezing is a view concern with no effect on values, and its
whole job is to answer one question for a renderer: given a
scroll position, which rows and columns are actually on
screen. The frozen band is the top rows and left columns
that never scroll; the body is everything below and to the
right, and it scrolls under them. The model computes the
visible set as the frozen band plus a window into the body
starting at the scroll offset, and the arithmetic that trips
every naive implementation is handled explicitly: the scroll
offset counts body rows, not sheet rows, so scrolling one
row past two frozen rows shows sheet row four at the top of
the body, not row two again. A freeze that claims more rows
than the viewport can hold is refused, because a frozen band
taller than the screen leaves no room for the body and a
window into nothing is not a view. The frozen count of zero
is legal and means no freeze, the honest identity, and a
scroll offset past the end of the body clamps to the last
possible window rather than scrolling into blank space,
because a spreadsheet that lets you scroll past the data is
showing you a void and calling it navigation.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass
class FreezeView:
    total_rows: int
    total_cols: int
    frozen_rows: int = 0
    frozen_cols: int = 0
    viewport_rows: int = 10
    viewport_cols: int = 5

    def __post_init__(self) -> None:
        if self.frozen_rows < 0 or self.frozen_cols < 0:
            raise Invalid(
                "a frozen band cannot be negative"
            )
        if self.frozen_rows >= self.viewport_rows:
            raise Invalid(
                f"{self.frozen_rows} frozen row(s) in a "
                f"{self.viewport_rows}-row viewport leaves "
                "no room for the body; a window into "
                "nothing is not a view"
            )
        if self.frozen_cols >= self.viewport_cols:
            raise Invalid(
                f"{self.frozen_cols} frozen column(s) in a "
                f"{self.viewport_cols}-column viewport "
                "leaves no room for the body"
            )

    def _body_window(
        self, offset: int, frozen: int, viewport: int, total: int
    ) -> list[int]:
        body_start = frozen
        body_length = total - frozen
        window = viewport - frozen
        max_offset = max(body_length - window, 0)
        clamped = max(0, min(offset, max_offset))
        first = body_start + clamped
        last = min(first + window, total)
        return list(range(first, last))

    def visible_rows(self, row_offset: int) -> list[int]:
        frozen = list(range(self.frozen_rows))
        body = self._body_window(
            row_offset,
            self.frozen_rows,
            self.viewport_rows,
            self.total_rows,
        )
        return frozen + body

    def visible_cols(self, col_offset: int) -> list[int]:
        frozen = list(range(self.frozen_cols))
        body = self._body_window(
            col_offset,
            self.frozen_cols,
            self.viewport_cols,
            self.total_cols,
        )
        return frozen + body

    def describe(
        self, row_offset: int, col_offset: int
    ) -> str:
        rows = self.visible_rows(row_offset)
        cols = self.visible_cols(col_offset)
        return (
            f"{self.frozen_rows}x{self.frozen_cols} frozen; "
            f"rows {[r + 1 for r in rows]}, "
            f"cols {[c + 1 for c in cols]}"
        )
