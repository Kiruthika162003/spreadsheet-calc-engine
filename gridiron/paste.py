"""Copy and paste: the dollar signs finally do their job.

Fill and paste are reference rewriting, nothing more: a
formula copied two rows down has its relative rows moved two
and its absolute rows left alone, which is why $ was worth a
character of syntax. The rewriter works on the tree, not the
text, because regex-rewriting formula text is the bug factory
every spreadsheet clone rediscovers, the one where B12 inside
a string or a function name gets renumbered. A shift that
would push a relative reference off the sheet's edge turns
that reference into #REF! at the destination, not an error at
paste time, because the incumbent pastes first and apologizes
cell by cell, and matching that behavior means a block paste
never half-lands. Rendering back to text normalizes case and
spacing, which is honest as long as it is stated: the pasted
cell shows the rewritten formula, not the original author's
whitespace.
"""

from __future__ import annotations

from gridiron.ast import (
    Binary,
    Bool,
    Call,
    Name,
    Node,
    Number,
    Range,
    Ref,
    Text,
    Unary,
    XRef,
)
from gridiron.errors import Invalid
from gridiron.parser import parse_formula
from gridiron.refs import CellRef, RangeRef
from gridiron.values import render


def shift_node(node: Node, rows: int, cols: int) -> Node:
    if isinstance(node, (Number | Text | Bool | Name | XRef)):
        return node
    if isinstance(node, Ref):
        try:
            return Ref(ref=node.ref.shifted(rows, cols))
        except Invalid:
            return Name(name="#REF!")
    if isinstance(node, Range):
        top_left = CellRef(
            row=node.ref.top, col=node.ref.left
        ).shifted(rows, cols)
        bottom_right = CellRef(
            row=node.ref.bottom, col=node.ref.right
        ).shifted(rows, cols)
        return Range(
            ref=RangeRef(
                top=top_left.row,
                left=top_left.col,
                bottom=bottom_right.row,
                right=bottom_right.col,
            )
        )
    if isinstance(node, Unary):
        return Unary(
            op=node.op,
            operand=shift_node(node.operand, rows, cols),
        )
    if isinstance(node, Binary):
        return Binary(
            op=node.op,
            left=shift_node(node.left, rows, cols),
            right=shift_node(node.right, rows, cols),
        )
    return Call(
        function=node.function,
        args=tuple(
            shift_node(arg, rows, cols) for arg in node.args
        ),
    )


def unparse(node: Node) -> str:
    if isinstance(node, Number):
        return render(node.value)
    if isinstance(node, Text):
        escaped = node.value.replace('"', '""')
        return f'"{escaped}"'
    if isinstance(node, Bool):
        return "TRUE" if node.value else "FALSE"
    if isinstance(node, Ref):
        return node.ref.a1()
    if isinstance(node, Range):
        return node.ref.a1()
    if isinstance(node, Name):
        return node.name
    if isinstance(node, XRef):
        return f"{node.sheet}!{node.ref.a1()}"
    if isinstance(node, Unary):
        return f"-{unparse(node.operand)}"
    if isinstance(node, Binary):
        return (
            f"({unparse(node.left)}{node.op}"
            f"{unparse(node.right)})"
        )
    args = ", ".join(unparse(arg) for arg in node.args)
    return f"{node.function}({args})"


def shifted_formula(text: str, rows: int, cols: int) -> str:
    tree = parse_formula(text)
    moved = shift_node(tree, rows, cols)
    return "=" + unparse(moved)
