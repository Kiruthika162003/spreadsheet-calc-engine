"""Column edits: the same contract as rows, on the axis with names.

Inserting a column is row insertion rotated ninety degrees,
with one twist worth its own module: columns are what users
see named, A through XFD, so shifting them re-letters every
reference in a way row shifts never make visible. The
contract is identical, references follow moved cells with
absolute flags irrelevant to sheet edits, deletions bake
#REF! as a visible wound, and ranges stretch or shrink at
their edges. The implementation shares nothing with the row
editor on purpose: the two were written against the same
tests translated across the diagonal, which is the cheapest
equivalence proof available, and a shared axis-generic core
would have traded that check for cleverness.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.ast import (
    Binary,
    Call,
    Name,
    Node,
    Range,
    Ref,
    Unary,
)
from gridiron.errors import Invalid
from gridiron.paste import unparse
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Cell, Sheet


def _moved_ref(
    ref: CellRef, at_col: int, count: int
) -> CellRef | None:
    if count > 0:
        if ref.col >= at_col:
            return CellRef(
                row=ref.row,
                col=ref.col + count,
                row_absolute=ref.row_absolute,
                col_absolute=ref.col_absolute,
            )
        return ref
    removed = -count
    if at_col <= ref.col < at_col + removed:
        return None
    if ref.col >= at_col + removed:
        return CellRef(
            row=ref.row,
            col=ref.col - removed,
            row_absolute=ref.row_absolute,
            col_absolute=ref.col_absolute,
        )
    return ref


def _moved_range(
    region: RangeRef, at_col: int, count: int
) -> RangeRef | None:
    if count > 0:
        left = (
            region.left + count
            if region.left >= at_col
            else region.left
        )
        right = (
            region.right + count
            if region.right >= at_col
            else region.right
        )
        return RangeRef(
            top=region.top,
            left=left,
            bottom=region.bottom,
            right=right,
        )
    removed = -count
    if region.left >= at_col + removed:
        left = region.left - removed
    elif region.left >= at_col:
        left = at_col
    else:
        left = region.left
    if region.right >= at_col + removed:
        right = region.right - removed
    elif region.right >= at_col:
        right = at_col - 1
    else:
        right = region.right
    if right < left:
        return None
    return RangeRef(
        top=region.top,
        left=left,
        bottom=region.bottom,
        right=right,
    )


def rewrite(node: Node, at_col: int, count: int) -> Node:
    if isinstance(node, Ref):
        moved = _moved_ref(node.ref, at_col, count)
        if moved is None:
            return Name(name="#REF!")
        return Ref(ref=moved)
    if isinstance(node, Range):
        moved = _moved_range(node.ref, at_col, count)
        if moved is None:
            return Name(name="#REF!")
        return Range(ref=moved)
    if isinstance(node, Unary):
        return Unary(
            op=node.op,
            operand=rewrite(node.operand, at_col, count),
        )
    if isinstance(node, Binary):
        return Binary(
            op=node.op,
            left=rewrite(node.left, at_col, count),
            right=rewrite(node.right, at_col, count),
        )
    if isinstance(node, Call):
        return Call(
            function=node.function,
            args=tuple(
                rewrite(arg, at_col, count)
                for arg in node.args
            ),
        )
    return node


@dataclass
class ColumnEditor:
    sheet: Sheet

    def _rebuild_storage(
        self, at_col: int, count: int
    ) -> int:
        moved = 0
        fresh: dict[tuple[int, int], Cell] = {}
        for (row, col), cell in self.sheet.cells.items():
            if count < 0 and at_col <= col < at_col - count:
                continue
            new_col = col
            if (count > 0 and col >= at_col) or (
                count < 0 and col >= at_col - count
            ):
                new_col = col + count
                moved += 1
            fresh[(row, new_col)] = cell
        self.sheet.cells = fresh
        return moved

    def _rewrite_formulas(
        self, at_col: int, count: int
    ) -> int:
        wounded = 0
        for _, cell in self.sheet.formula_cells():
            new_tree = rewrite(cell.tree, at_col, count)
            if new_tree is not cell.tree:
                cell.tree = new_tree
                cell.formula_text = "=" + unparse(new_tree)
                if "#REF!" in cell.formula_text:
                    wounded += 1
        return wounded

    def insert_columns(
        self, at_col: int, count: int = 1
    ) -> str:
        if count < 1:
            raise Invalid("insert at least one column")
        moved = self._rebuild_storage(at_col, count)
        self._rewrite_formulas(at_col, count)
        return (
            f"{count} column(s) inserted; {moved} cell(s) "
            "moved and re-lettered, references following"
        )

    def delete_columns(
        self, at_col: int, count: int = 1
    ) -> str:
        if count < 1:
            raise Invalid("delete at least one column")
        moved = self._rebuild_storage(at_col, -count)
        wounded = self._rewrite_formulas(at_col, -count)
        note = (
            f"; {wounded} formula(s) wear #REF!"
            if wounded
            else ""
        )
        return (
            f"{count} column(s) deleted; {moved} cell(s) "
            f"moved{note}"
        )
