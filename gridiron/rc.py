"""R1C1 notation: the spelling in which copying is the identity.

A1 notation is what users type and R1C1 is what the formula
actually means: RC[-1] says the cell one to my left no
matter where I stand, which is why a column of copied
formulas that differ in A1 all collapse to one R1C1 string.
That collapse is the point of this module and the law its
tests enforce: render a formula in R1C1 from its home cell,
shift it with the paste rewriter to any other cell, render
again from there, and the string does not change, because
relative meaning was the thing being copied all along. The
grammar is the incumbent's: brackets mean offsets, R[2] two
rows down and C[-1] one column left, bare R and C mean my
own row or column, and a bracketless number is absolute and
one-based, R5C3 pinning exactly what $C$5 pins. Absolute
halves survive conversion in both directions, since a dollar
is a promise about meaning and changing notation must not
quietly break promises. Single references parse back from
R1C1 as well, so a tool can speak either dialect at the
reference level, and a malformed R1C1 string is refused with
its position rather than guessed at.
"""

from __future__ import annotations

import re

from gridiron.ast import (
    Binary,
    Bool,
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
from gridiron.refs import CellRef
from gridiron.values import render

_R1C1_PATTERN = re.compile(
    r"^R(?:\[(?P<row_off>-?\d+)\]|(?P<row_abs>\d+))?"
    r"C(?:\[(?P<col_off>-?\d+)\]|(?P<col_abs>\d+))?$"
)


def ref_to_r1c1(ref: CellRef, origin: CellRef) -> str:
    if ref.row_absolute:
        row_part = f"R{ref.row + 1}"
    else:
        offset = ref.row - origin.row
        row_part = f"R[{offset}]" if offset else "R"
    if ref.col_absolute:
        col_part = f"C{ref.col + 1}"
    else:
        offset = ref.col - origin.col
        col_part = f"C[{offset}]" if offset else "C"
    return row_part + col_part


def ref_from_r1c1(text: str, origin: CellRef) -> CellRef:
    matched = _R1C1_PATTERN.match(text.strip().upper())
    if not matched:
        raise Invalid(
            f"{text!r} is not R1C1; the grammar is R and C, "
            "each bare, bracketed with an offset, or "
            "numbered absolute"
        )
    row_abs = matched.group("row_abs")
    row_off = matched.group("row_off")
    col_abs = matched.group("col_abs")
    col_off = matched.group("col_off")
    if row_abs is not None:
        row = int(row_abs) - 1
        row_absolute = True
    else:
        row = origin.row + int(row_off or 0)
        row_absolute = False
    if col_abs is not None:
        col = int(col_abs) - 1
        col_absolute = True
    else:
        col = origin.col + int(col_off or 0)
        col_absolute = False
    if row < 0 or col < 0:
        raise Invalid(
            f"{text!r} walks off the sheet's edge from "
            f"{origin.a1()}"
        )
    return CellRef(
        row=row,
        col=col,
        row_absolute=row_absolute,
        col_absolute=col_absolute,
    )


def _range_to_r1c1(node: Range, origin: CellRef) -> str:
    top_left = CellRef(
        row=node.ref.top, col=node.ref.left
    )
    bottom_right = CellRef(
        row=node.ref.bottom, col=node.ref.right
    )
    return (
        f"{ref_to_r1c1(top_left, origin)}:"
        f"{ref_to_r1c1(bottom_right, origin)}"
    )


def _node_to_r1c1(node: Node, origin: CellRef) -> str:
    if isinstance(node, Number):
        return render(node.value)
    if isinstance(node, Text):
        escaped = node.value.replace('"', '""')
        return f'"{escaped}"'
    if isinstance(node, Bool):
        return "TRUE" if node.value else "FALSE"
    if isinstance(node, Ref):
        return ref_to_r1c1(node.ref, origin)
    if isinstance(node, Range):
        return _range_to_r1c1(node, origin)
    if isinstance(node, Name):
        return node.name
    if isinstance(node, XRef):
        return (
            f"{node.sheet}!"
            f"{ref_to_r1c1(node.ref, origin)}"
        )
    if isinstance(node, Unary):
        return f"-{_node_to_r1c1(node.operand, origin)}"
    if isinstance(node, Binary):
        return (
            f"({_node_to_r1c1(node.left, origin)}"
            f"{node.op}"
            f"{_node_to_r1c1(node.right, origin)})"
        )
    args = ", ".join(
        _node_to_r1c1(arg, origin) for arg in node.args
    )
    return f"{node.function}({args})"


def formula_to_r1c1(text: str, origin: CellRef) -> str:
    tree = parse_formula(text)
    return "=" + _node_to_r1c1(tree, origin)
