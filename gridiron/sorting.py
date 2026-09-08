"""Sorting: rows move together, empties sink, and formulas refuse to ride.

A sort is a permutation of whole rows, never of cells, and
this module holds the incumbent's one universally loved
quirk: empty cells sink to the bottom regardless of
direction, because nobody sorting invoices ascending wants
four hundred blanks before the first invoice. Type ordering
matches the comparison operators, numbers before text before
booleans, ties are stable so equal keys keep their arrival
order, and the hard boundary is formulas: a range containing
formula cells refuses to sort, since moving a formula
rewrites what its relative references mean, and an engine
that silently re-pointed them would be sorting the labels
while scrambling the arithmetic. Sort values, or paste as
values first; the refusal says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Cell, Sheet
from gridiron.values import Value

_TYPE_ORDER = {"number": 0, "text": 1, "bool": 2}


def _sort_key(value: Value):
    if isinstance(value, bool):
        return (_TYPE_ORDER["bool"], value)
    if isinstance(value, float):
        return (_TYPE_ORDER["number"], value)
    if isinstance(value, str):
        return (_TYPE_ORDER["text"], value.upper())
    raise Invalid("empties are handled before keying")


@dataclass
class Sorter:
    sheet: Sheet

    def sort_range(
        self,
        region: RangeRef,
        key_col: int,
        descending: bool = False,
    ) -> str:
        if not region.left <= key_col <= region.right:
            raise Invalid(
                f"key column {key_col} is outside the range "
                f"{region.a1()}"
            )
        for cell_ref in region.cells():
            held = self.sheet.cell(cell_ref)
            if held is not None and held.is_formula():
                raise Invalid(
                    f"{cell_ref.a1()} is a formula; moving it "
                    "rewrites what its references mean, so "
                    "sort values or paste as values first"
                )
        rows: list[list[Cell | None]] = []
        for row in range(region.top, region.bottom + 1):
            rows.append(
                [
                    self.sheet.cell(
                        CellRef(row=row, col=col)
                    )
                    for col in range(
                        region.left, region.right + 1
                    )
                ]
            )
        key_offset = key_col - region.left

        occupied = [
            row
            for row in rows
            if row[key_offset] is not None
            and row[key_offset].literal is not None
        ]
        blanks = [row for row in rows if row not in occupied]
        occupied.sort(
            key=lambda row: _sort_key(
                row[key_offset].literal
            ),
            reverse=descending,
        )
        ordered = occupied + blanks
        moved = 0
        for offset, row_cells in enumerate(ordered):
            for col_offset, cell in enumerate(row_cells):
                target = CellRef(
                    row=region.top + offset,
                    col=region.left + col_offset,
                )
                if cell is None:
                    if (
                        self.sheet.cells.pop(
                            target.key(), None
                        )
                        is not None
                    ):
                        moved += 1
                else:
                    if (
                        self.sheet.cells.get(target.key())
                        is not cell
                    ):
                        moved += 1
                    self.sheet.cells[target.key()] = cell
        direction = "descending" if descending else "ascending"
        return (
            f"{region.a1()} sorted {direction} on column "
            f"{key_col - region.left + 1}; {len(blanks)} "
            f"blank row(s) sank to the bottom, {moved} "
            "cell(s) moved"
        )
