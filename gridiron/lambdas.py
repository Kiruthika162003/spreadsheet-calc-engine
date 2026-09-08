"""LAMBDA: user-defined functions, bound by name, checked at the call.

A named LAMBDA is the reusable cousin of LET: where LET names
a value for one formula, LAMBDA names a computation for many,
DISCOUNT defined once as a function of price and rate, then
called wherever a discount is needed. The registry stores the
parameter names and the parsed body, and wraps the function
table so a call to a registered name binds its arguments to
the parameters and evaluates the body, which means user
functions and built-ins share one calling convention and the
evaluator never learns they are different. The argument count
is checked at the call and refused by its two numbers, too
few or too many, because a function silently ignoring an
extra argument or defaulting a missing one is how a wrong
column sails through a review. Parameters are bare
identifiers for the same reason LET's names are, so a
parameter that looks like a cell reference is refused at
definition time rather than shadowing A1 at call time. A body
that references a name that is neither a parameter nor a
defined name resolves through the outer scope unchanged, so a
LAMBDA can close over workbook names, and recursion is
refused by not binding the function's own name inside its
body, because unbounded self-reference in a recalculation
engine is a hang, not a feature, and the honest answer is to
say so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.ast import Bool, Node, Number, Text
from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import ErrorValue, Value, is_error


@dataclass(frozen=True)
class LambdaDef:
    params: tuple[str, ...]
    body: Node


def _as_node(value: Value) -> Node:
    if isinstance(value, bool):
        return Bool(value=value)
    if isinstance(value, float):
        return Number(value=value)
    if isinstance(value, str):
        return Text(value=value)
    return Text(value="")


@dataclass
class LambdaRegistry:
    defs: dict[str, LambdaDef] = field(default_factory=dict)

    def define(
        self, name: str, params: list[str], body: str
    ) -> str:
        key = name.strip().upper()
        seen = set()
        for param in params:
            upper = param.strip().upper()
            try:
                CellRef.parse(upper)
            except Invalid:
                pass
            else:
                raise Invalid(
                    f"parameter {param!r} looks like a cell "
                    "reference; it would shadow the grid at "
                    "call time"
                )
            if upper in seen:
                raise Invalid(
                    f"parameter {param!r} is repeated; a "
                    "function cannot bind one name twice"
                )
            seen.add(upper)
        self.defs[key] = LambdaDef(
            params=tuple(p.strip().upper() for p in params),
            body=parse_formula(body),
        )
        return (
            f"{key} defined over "
            f"{len(params)} parameter(s)"
        )

    def _caller(self, definition: LambdaDef):
        def run(args, lookup, functions, names) -> Value:
            if len(args) != len(definition.params):
                return ErrorValue(
                    code="#VALUE!",
                    note=(
                        f"this function takes "
                        f"{len(definition.params)} "
                        f"argument(s), got {len(args)}"
                    ),
                )
            bound: dict[str, Node] = {}
            for param, arg in zip(
                definition.params, args, strict=True
            ):
                value = evaluate(
                    arg, lookup, functions, names
                )
                if is_error(value):
                    return value
                bound[param] = _as_node(value)

            def scope(name: str) -> Node | None:
                if name in bound:
                    return bound[name]
                return names(name)

            return evaluate(
                definition.body, lookup, functions, scope
            )

        return run

    def table(self, base):
        def resolved(name: str):
            key = name.upper()
            if key in self.defs:
                return self._caller(self.defs[key])
            return base(name)

        return resolved
