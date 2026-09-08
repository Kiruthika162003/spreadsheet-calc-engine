"""Inserting and deleting rows: every formula on the sheet is a bystander.

Inserting a row above the data moves cells down, and every
formula anywhere that pointed at the moved cells must follow
them, absolute references included, because the dollar sign
pins against copy and fill, not against the sheet itself
shifting underneath; a $A$5 that kept saying row five after
row three was inserted would point at a different number
wearing the same address. Deletion is the harsher case: a
formula that referenced a deleted cell gets #REF! baked into
its tree, not a shifted guess, because the incumbent decided
decades ago that a visible wound beats a silent misdirection
and every auditor since has agreed. Ranges shrink and grow
at their edges: deleting a row inside SUM(A1:A10) narrows
the sum, inserting inside it widens it, which is exactly
the behavior ledger keepers rely on when they add a row for
March and the yearly total absorbs it unasked.
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
    ref: CellRef, at_row: int, count: int
) -> CellRef | None:
    if count > 0:
        if ref.row >= at_row:
            return CellRef(
                row=ref.row + count,
                col=ref.col,
                row_absolute=ref.row_absolute,
                col_absolute=ref.col_absolute,
            )
        return ref
    removed = -count
    if at_row <= ref.row < at_row + removed:
        return None
    if ref.row >= at_row + removed:
        return CellRef(
            row=ref.row - removed,
            col=ref.col,
            row_absolute=ref.row_absolute,
            col_absolute=ref.col_absolute,
        )
    return ref


def _moved_range(
    region: RangeRef, at_row: int, count: int
) -> RangeRef | None:
    if count > 0:
        top = (
            region.top + count
            if region.top >= at_row
            else region.top
        )
        bottom = (
            region.bottom + count
            if region.bottom >= at_row
            else region.bottom
        )
        return RangeRef(
            top=top,
            left=region.left,
            bottom=bottom,
            right=region.right,
        )
    removed = -count
    if region.top >= at_row + removed:
        top = region.top - removed
    elif region.top >= at_row:
        top = at_row
    else:
        top = region.top
    if region.bottom >= at_row + removed:
        bottom = region.bottom - removed
    elif region.bottom >= at_row:
        bottom = at_row - 1
    else:
        bottom = region.bottom
    if bottom < top:
        return None
    return RangeRef(
        top=top,
        left=region.left,
        bottom=bottom,
        right=region.right,
    )


def rewrite(node: Node, at_row: int, count: int) -> Node:
    if isinstance(node, Ref):
        moved = _moved_ref(node.ref, at_row, count)
        if moved is None:
            return Name(name="#REF!")
        return Ref(ref=moved)
    if isinstance(node, Range):
        moved = _moved_range(node.ref, at_row, count)
        if moved is None:
            return Name(name="#REF!")
        return Range(ref=moved)
    if isinstance(node, Unary):
        return Unary(
            op=node.op,
            operand=rewrite(node.operand, at_row, count),
        )
    if isinstance(node, Binary):
        return Binary(
            op=node.op,
            left=rewrite(node.left, at_row, count),
            right=rewrite(node.right, at_row, count),
        )
    if isinstance(node, Call):
        return Call(
            function=node.function,
            args=tuple(
                rewrite(arg, at_row, count)
                for arg in node.args
            ),
        )
    return node


@dataclass
class RowEditor:
    sheet: Sheet

    def _rebuild_storage(
        self, at_row: int, count: int
    ) -> int:
        moved = 0
        fresh: dict[tuple[int, int], Cell] = {}
        for (row, col), cell in self.sheet.cells.items():
            if count < 0 and at_row <= row < at_row - count:
                continue
            new_row = row
            if (count > 0 and row >= at_row) or (count < 0 and row >= at_row - count):
                new_row = row + count
                moved += 1
            fresh[(new_row, col)] = cell
        self.sheet.cells = fresh
        return moved

    def _rewrite_formulas(
        self, at_row: int, count: int
    ) -> int:
        wounded = 0
        for _, cell in self.sheet.formula_cells():
            new_tree = rewrite(cell.tree, at_row, count)
            if new_tree is not cell.tree:
                cell.tree = new_tree
                cell.formula_text = "=" + unparse(new_tree)
                if "#REF!" in cell.formula_text:
                    wounded += 1
        return wounded

    def insert_rows(self, at_row: int, count: int = 1) -> str:
        if count < 1:
            raise Invalid("insert at least one row")
        moved = self._rebuild_storage(at_row, count)
        self._rewrite_formulas(at_row, count)
        return (
            f"{count} row(s) inserted at {at_row + 1}; "
            f"{moved} cell(s) moved and every formula "
            "followed them"
        )

    def delete_rows(self, at_row: int, count: int = 1) -> str:
        if count < 1:
            raise Invalid("delete at least one row")
        moved = self._rebuild_storage(at_row, -count)
        wounded = self._rewrite_formulas(at_row, -count)
        note = (
            f"; {wounded} formula(s) now carry #REF!, a "
            "visible wound beating a silent misdirection"
            if wounded
            else ""
        )
        return (
            f"{count} row(s) deleted at {at_row + 1}; "
            f"{moved} cell(s) moved{note}"
        )
