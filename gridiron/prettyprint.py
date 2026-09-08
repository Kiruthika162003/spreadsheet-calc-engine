"""Formula pretty-printing: parentheses only where meaning needs them.

The paste module's unparse wraps every binary node in
parentheses, which is correct and unreadable: =(((A1*2)+B1))
computes right and reads like a bug report. This printer
renders the same tree with the fewest parentheses that
preserve meaning, the way a person would write it, by
carrying each operator's precedence and associativity and
parenthesizing a child only when the child binds looser than
its parent, or equally loose on the associativity-losing
side. The two famous traps are handled explicitly. A right
child of subtraction or division needs parentheses when it
is itself an addition or a like operation, because a-(b+c)
is not a-b+c, and the printer that forgets this ships the
sign error every hand-rolled formatter ships. Exponentiation
is the third member of that club and the first draft got it
exactly backwards: it called the caret right-associative and
wrapped the left power for the reader, but this grammar
climbs the caret left-associatively, so 2^3^2 already means
(2^3)^2 and wants no parentheses on the left, while 2^(3^2)
is the form that must keep them or change value. The
measurement corrected the docstring; the caret now guards
its right child at equal precedence beside minus and slash,
and the left power renders bare. Unary minus over anything that
binds looser gets parentheses, so -(A1+B1) keeps its meaning
and -A1 stays bare.
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
from gridiron.parser import parse_formula
from gridiron.values import render

_PRECEDENCE = {
    "=": 1,
    "<>": 1,
    "<": 1,
    "<=": 1,
    ">": 1,
    ">=": 1,
    "&": 2,
    "+": 3,
    "-": 3,
    "*": 4,
    "/": 4,
    "^": 5,
}
_UNARY = 6
_ATOM = 7


def _binding(node: Node) -> int:
    if isinstance(node, Binary):
        return _PRECEDENCE[node.op]
    if isinstance(node, Unary):
        return _UNARY
    return _ATOM


def _atom(node: Node) -> str:
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
    return ""


def _wrap(inner: str, needed: bool) -> str:
    return f"({inner})" if needed else inner


def _render(node: Node) -> str:
    if isinstance(node, Unary):
        operand = node.operand
        text = _render(operand)
        needs = _binding(operand) < _UNARY
        return "-" + _wrap(text, needs)
    if isinstance(node, Binary):
        parent = _PRECEDENCE[node.op]
        left = _render(node.left)
        right = _render(node.right)
        left_binds = _binding(node.left)
        right_binds = _binding(node.right)
        left_wrap = left_binds < parent
        right_wrap = right_binds < parent
        if (
            node.op in ("-", "/", "^")
            and right_binds == parent
        ):
            right_wrap = True
        return (
            f"{_wrap(left, left_wrap)}{node.op}"
            f"{_wrap(right, right_wrap)}"
        )
    if isinstance(node, Call):
        args = ", ".join(
            _render(arg) for arg in node.args
        )
        return f"{node.function}({args})"
    return _atom(node)


def pretty(node: Node) -> str:
    return "=" + _render(node)


def pretty_formula(text: str) -> str:
    return pretty(parse_formula(text))
