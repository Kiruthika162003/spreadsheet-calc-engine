"""The evaluator: one walk, every node kind, errors flowing instead of thrown.

Evaluation is a fold over the tree with two lookups injected,
one for cell values and one for functions, because the
evaluator owning storage would weld the calculator to the
grid and the whole point of the split is that a formula can
be evaluated against any world, the live sheet, a what-if
overlay, a test fixture. Semantics follow the value module's
oath: errors flow, first error wins, text refuses to become
a number silently. Comparisons order numbers before text
before booleans, matching the incumbent's sort order, and a
bare range in scalar position is a #VALUE! rather than a
guess about which of its nine cells the author meant, since
guessing is how a wrong quarter total survives review.
"""

from __future__ import annotations

from collections.abc import Callable

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
)
from gridiron.errors import Missing
from gridiron.refs import CellRef
from gridiron.values import (
    ErrorValue,
    Value,
    add,
    divide,
    first_error,
    multiply,
    render,
    to_number,
)

CellLookup = Callable[[CellRef], Value]
FunctionTable = Callable[[str], Callable | None]
NameTable = Callable[[str], Node | None]

_TYPE_RANK = {"number": 0, "text": 1, "bool": 2}


def _rank(value: Value) -> tuple[int, float | str | bool]:
    if isinstance(value, bool):
        return (_TYPE_RANK["bool"], value)
    if isinstance(value, float):
        return (_TYPE_RANK["number"], value)
    if isinstance(value, str):
        return (_TYPE_RANK["text"], value.upper())
    return (_TYPE_RANK["number"], 0.0)


def compare(op: str, left: Value, right: Value) -> Value:
    poisoned = first_error(left, right)
    if poisoned:
        return poisoned
    left_rank = _rank(left)
    right_rank = _rank(right)
    if op == "=":
        return left_rank == right_rank
    if op == "<>":
        return left_rank != right_rank
    if op == "<":
        return left_rank < right_rank
    if op == "<=":
        return left_rank <= right_rank
    if op == ">":
        return left_rank > right_rank
    return left_rank >= right_rank


def concat(left: Value, right: Value) -> Value:
    poisoned = first_error(left, right)
    if poisoned:
        return poisoned
    return render(left) + render(right)


def power(left: Value, right: Value) -> Value:
    poisoned = first_error(left, right)
    if poisoned:
        return poisoned
    base = to_number(left)
    exponent = to_number(right)
    poisoned = first_error(base, exponent)
    if poisoned:
        return poisoned
    try:
        result = float(base**exponent)
    except (OverflowError, ZeroDivisionError, ValueError):
        return ErrorValue(
            code="#NUM!",
            note="the power left the representable world",
        )
    if isinstance(result, complex):
        return ErrorValue(code="#NUM!", note="complex result")
    return result


def evaluate(
    node: Node,
    lookup: CellLookup,
    functions: FunctionTable,
    names: NameTable = lambda _name: None,
) -> Value:
    if isinstance(node, Number):
        return node.value
    if isinstance(node, Text):
        return node.value
    if isinstance(node, Bool):
        return node.value
    if isinstance(node, Ref):
        return lookup(node.ref)
    if isinstance(node, Range):
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"range {node.ref.a1()} in scalar position; "
                "guessing which cell the author meant is how "
                "a wrong quarter total survives review"
            ),
        )
    if isinstance(node, Name):
        if node.name == "#REF!":
            return ErrorValue(
                code="#REF!",
                note=(
                    "this formula carries a baked wound from "
                    "a deletion; the wound must compute as "
                    "itself"
                ),
            )
        bound = names(node.name)
        if bound is None:
            return ErrorValue(
                code="#NAME?",
                note=f"{node.name} is not a defined name",
            )
        return evaluate(bound, lookup, functions, names)
    if isinstance(node, Unary):
        inner = evaluate(node.operand, lookup, functions, names)
        return multiply(inner, -1.0)
    if isinstance(node, Binary):
        left = evaluate(node.left, lookup, functions, names)
        right = evaluate(node.right, lookup, functions, names)
        if node.op == "+":
            return add(left, right)
        if node.op == "-":
            return add(left, multiply(right, -1.0))
        if node.op == "*":
            return multiply(left, right)
        if node.op == "/":
            return divide(left, right)
        if node.op == "^":
            return power(left, right)
        if node.op == "&":
            return concat(left, right)
        return compare(node.op, left, right)
    if isinstance(node, Call):
        function = functions(node.function)
        if function is None:
            return ErrorValue(
                code="#NAME?",
                note=f"{node.function} is not a function here",
            )
        return function(node.args, lookup, functions, names)
    raise Missing(f"unknown node kind {type(node).__name__}")
