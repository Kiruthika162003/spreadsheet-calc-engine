"""LET: names inside a formula, evaluated once, visible to what follows.

LET is the incumbent's answer to the formula that computes
the same subexpression four times because there was nowhere
to put the intermediate result, and it is worth building
carefully because its whole value is a promise about
evaluation order. The arguments alternate name and value and
end with one calculation: LET(x, A1*2, y, x+1, y*y). Each
value is evaluated once against the names bound before it, so
a later binding can build on an earlier one, and the final
calculation sees them all. Evaluated once is the load-bearing
phrase, because a LET that re-evaluated x every time y
mentioned it would defeat its own reason to exist and make a
volatile function inside x fire twice. The name must be a
bare identifier, so LET(A1, 5, A1) is refused with the note
that A1 is a cell reference wearing a variable's clothes,
the one mistake the syntax invites. A value that evaluates to
an error binds the error and the final calculation carries
it, because a name is not a firewall; if x is a #DIV/0! then
anything built on x is too, exactly as the value model
promises everywhere else.
"""

from __future__ import annotations

from gridiron.ast import (
    Bool,
    Name,
    Node,
    Number,
    Range,
    Text,
)
from gridiron.evaluate import evaluate
from gridiron.values import ErrorValue, Value, is_error


def _as_node(value: Value) -> Node:
    if isinstance(value, bool):
        return Bool(value=value)
    if isinstance(value, float):
        return Number(value=value)
    if isinstance(value, str):
        return Text(value=value)
    return Text(value="")


def _let(args, lookup, functions, names) -> Value:
    if len(args) < 3 or len(args) % 2 == 0:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "LET takes name and value pairs then one "
                "final calculation, an odd count of at "
                "least three"
            ),
        )
    bound: dict[str, Node] = {}

    def scope(name: str) -> Node | None:
        if name in bound:
            return bound[name]
        return names(name)

    pairs = args[:-1]
    for index in range(0, len(pairs), 2):
        name_node = pairs[index]
        value_node = pairs[index + 1]
        if not isinstance(name_node, Name):
            label = getattr(
                name_node, "ref", name_node
            )
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"LET names must be bare identifiers; "
                    f"{label} is a cell reference wearing a "
                    "variable's clothes"
                ),
            )
        if isinstance(value_node, Range):
            bound[name_node.name] = value_node
            continue
        computed = evaluate(
            value_node, lookup, functions, scope
        )
        if is_error(computed):
            bound[name_node.name] = value_node
            continue
        bound[name_node.name] = _as_node(computed)
    return evaluate(args[-1], lookup, functions, scope)


LET_FUNCTIONS = {
    "LET": _let,
}
