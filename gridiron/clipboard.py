"""Cut and copy: the same gesture, opposite theories of identity.

Copy says "make me another one like it": the pasted formula
rewrites relative references against the displacement, the
original stays, and the two are strangers afterward. Cut
says "this cell is moving house": the formula lands
unchanged because it is the same formula, and, the half
everyone forgets, every OTHER formula that pointed at the
old address must be rewritten to follow it to the new one,
which is why cut-paste feels like magic and copy-paste
feels like arithmetic. This module implements both theories
and refuses the hybrid: cutting a range while pasting it
partially atop itself is rejected, because a move that
overlaps its own origin has no coherent order of operations
and every engine that allows it documents a different
wrong answer. The follower count is a measured number and
must stay honest, which cost a bug fix once: the retargeting
walk rebuilt every operator node whether or not a reference
underneath it actually moved, so the identity check that
decides "did this formula follow" reported yes for every
formula with any structure, inflating the count. The walk
now returns the very same node object when nothing beneath
it changed, so a formula counts as a follower only when a
reference in it truly retargeted.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.ast import (
    Binary,
    Call,
    Node,
    Range,
    Ref,
    Unary,
)
from gridiron.errors import Invalid
from gridiron.paste import shift_node, unparse
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def _retarget(
    node: Node, old: tuple[int, int], new: tuple[int, int]
) -> Node:
    if isinstance(node, Ref):
        if node.ref.key() == old:
            return Ref(
                ref=CellRef(
                    row=new[0],
                    col=new[1],
                    row_absolute=node.ref.row_absolute,
                    col_absolute=node.ref.col_absolute,
                )
            )
        return node
    if isinstance(node, Range):
        return node
    if isinstance(node, Unary):
        operand = _retarget(node.operand, old, new)
        if operand is node.operand:
            return node
        return Unary(op=node.op, operand=operand)
    if isinstance(node, Binary):
        left = _retarget(node.left, old, new)
        right = _retarget(node.right, old, new)
        if left is node.left and right is node.right:
            return node
        return Binary(op=node.op, left=left, right=right)
    if isinstance(node, Call):
        args = tuple(
            _retarget(arg, old, new) for arg in node.args
        )
        if all(
            new_arg is old_arg
            for new_arg, old_arg in zip(
                args, node.args, strict=True
            )
        ):
            return node
        return Call(function=node.function, args=args)
    return node


@dataclass
class Clipboard:
    sheet: Sheet

    def copy_cell(
        self, source: CellRef, target: CellRef
    ) -> str:
        held = self.sheet.cell(source)
        if held is None:
            raise Invalid(f"{source.a1()} is empty")
        if not held.is_formula():
            self.sheet.set_literal(target, held.literal)
            return f"{source.a1()} copied to {target.a1()}"
        moved = shift_node(
            held.tree,
            target.row - source.row,
            target.col - source.col,
        )
        self.sheet.set_formula(
            target, "=" + unparse(moved)
        )
        return (
            f"{source.a1()} copied to {target.a1()}; the "
            "two are strangers now"
        )

    def cut_cell(
        self, source: CellRef, target: CellRef
    ) -> str:
        if source.key() == target.key():
            raise Invalid(
                "cutting a cell onto itself has no coherent "
                "order of operations"
            )
        held = self.sheet.cell(source)
        if held is None:
            raise Invalid(f"{source.a1()} is empty")
        followers = 0
        for _, cell in self.sheet.formula_cells():
            if cell is held:
                continue
            new_tree = _retarget(
                cell.tree, source.key(), target.key()
            )
            if new_tree is not cell.tree:
                cell.tree = new_tree
                cell.formula_text = "=" + unparse(new_tree)
                followers += 1
        self.sheet.cells.pop(source.key())
        self.sheet.cells[target.key()] = held
        return (
            f"{source.a1()} moved house to {target.a1()}; "
            f"{followers} formula(s) followed it, which is "
            "why cut feels like magic and copy feels like "
            "arithmetic"
        )

    def cut_range(
        self, region: RangeRef, target_top_left: CellRef
    ) -> str:
        rows = target_top_left.row - region.top
        cols = target_top_left.col - region.left
        landing = RangeRef(
            top=region.top + rows,
            left=region.left + cols,
            bottom=region.bottom + rows,
            right=region.right + cols,
        )
        overlaps = not (
            landing.bottom < region.top
            or landing.top > region.bottom
            or landing.right < region.left
            or landing.left > region.right
        )
        if overlaps and (rows, cols) != (0, 0):
            raise Invalid(
                f"moving {region.a1()} onto {landing.a1()} "
                "overlaps its own origin; every engine that "
                "allows it documents a different wrong answer"
            )
        if (rows, cols) == (0, 0):
            raise Invalid("a move to nowhere moves nothing")
        moved = 0
        for cell_ref in region.cells():
            held = self.sheet.cells.pop(
                cell_ref.key(), None
            )
            if held is not None:
                self.sheet.cells[
                    (cell_ref.row + rows, cell_ref.col + cols)
                ] = held
                moved += 1
        return (
            f"{region.a1()} moved to {landing.a1()}; "
            f"{moved} cell(s) travelled"
        )
