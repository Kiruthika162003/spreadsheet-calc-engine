"""Cell references: A1 is an address, and addresses parse exactly or not at all.

The A1 notation carries four flavors in two characters of
syntax: A1 moves with a copy, $A$1 does not, and $A1 and A$1
pin one axis each, which is the entire mechanism behind fill
and paste behaving sensibly. The parser here is strict on
purpose: column letters then digits, an optional dollar before
each part, nothing else, because every spreadsheet bug story
that starts with a lenient reference parser ends with a
formula silently pointing somewhere the author can see is
wrong only after the quarter closes. Ranges are ordered
rectangles regardless of how they were typed, C3:A1
normalizes to A1:C3, since iteration order is the engine's
business and the author's typing order is not a specification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from gridiron.errors import Invalid

_REF_PATTERN = re.compile(
    r"^(\$?)([A-Z]{1,3})(\$?)([1-9][0-9]{0,6})$"
)

MAX_COLUMNS = 16_384
MAX_ROWS = 1_048_576


def column_to_index(letters: str) -> int:
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    if index > MAX_COLUMNS:
        raise Invalid(
            f"column {letters} is past the {MAX_COLUMNS}-column "
            "edge of the sheet"
        )
    return index - 1


def index_to_column(index: int) -> str:
    if index < 0 or index >= MAX_COLUMNS:
        raise Invalid(f"column index {index} is off the sheet")
    letters = ""
    remaining = index + 1
    while remaining:
        remaining, digit = divmod(remaining - 1, 26)
        letters = chr(ord("A") + digit) + letters
    return letters


@dataclass(frozen=True, order=True)
class CellRef:
    row: int
    col: int
    row_absolute: bool = False
    col_absolute: bool = False

    def __post_init__(self) -> None:
        if not (0 <= self.row < MAX_ROWS):
            raise Invalid(f"row {self.row} is off the sheet")
        if not (0 <= self.col < MAX_COLUMNS):
            raise Invalid(f"column {self.col} is off the sheet")

    @classmethod
    def parse(cls, text: str) -> CellRef:
        match = _REF_PATTERN.match(text)
        if match is None:
            raise Invalid(
                f"{text!r} is not a cell reference; the "
                "grammar is dollars, letters, dollars, digits, "
                "and leniency here is how formulas point "
                "somewhere wrong quietly"
            )
        col_dollar, letters, row_dollar, digits = match.groups()
        return cls(
            row=int(digits) - 1,
            col=column_to_index(letters),
            row_absolute=bool(row_dollar),
            col_absolute=bool(col_dollar),
        )

    def a1(self) -> str:
        return (
            ("$" if self.col_absolute else "")
            + index_to_column(self.col)
            + ("$" if self.row_absolute else "")
            + str(self.row + 1)
        )

    def key(self) -> tuple[int, int]:
        return (self.row, self.col)

    def shifted(self, rows: int, cols: int) -> CellRef:
        return CellRef(
            row=self.row if self.row_absolute else self.row + rows,
            col=self.col if self.col_absolute else self.col + cols,
            row_absolute=self.row_absolute,
            col_absolute=self.col_absolute,
        )


@dataclass(frozen=True)
class RangeRef:
    top: int
    left: int
    bottom: int
    right: int

    @classmethod
    def parse(cls, text: str) -> RangeRef:
        if ":" not in text:
            raise Invalid(f"{text!r} is not a range")
        first_text, second_text = text.split(":", 1)
        first = CellRef.parse(first_text)
        second = CellRef.parse(second_text)
        return cls(
            top=min(first.row, second.row),
            left=min(first.col, second.col),
            bottom=max(first.row, second.row),
            right=max(first.col, second.col),
        )

    def cells(self) -> list[CellRef]:
        return [
            CellRef(row=row, col=col)
            for row in range(self.top, self.bottom + 1)
            for col in range(self.left, self.right + 1)
        ]

    def a1(self) -> str:
        start = CellRef(row=self.top, col=self.left)
        end = CellRef(row=self.bottom, col=self.right)
        return f"{start.a1()}:{end.a1()}"

    def size(self) -> int:
        return (self.bottom - self.top + 1) * (
            self.right - self.left + 1
        )

    def contains(self, ref: CellRef) -> bool:
        return (
            self.top <= ref.row <= self.bottom
            and self.left <= ref.col <= self.right
        )
