"""Defined names: TAXRATE beats F$17 in every formula a human will read.

A defined name binds a word to a formula fragment, usually a
reference, occasionally a constant, and the payoff is
entirely for the reader: =REVENUE*TAXRATE survives a code
review that =B7*$F$17 does not. The registry enforces the
grammar the parser already assumes, letters and underscores,
no valid cell address allowed as a name, because a name
spelled B12 would shadow twelve billion cells of address
space and the parser would have to guess which the author
meant, and guessing is banned in this codebase. Names
resolve at evaluation through the same hook the evaluator
already carries, deletion of a name leaves dependents
saying #NAME? rather than freezing their last value, and
the census lists every name with what it binds, since a
workbook's names are its API and an API deserves a page.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from gridiron.ast import Node
from gridiron.errors import Invalid, Missing
from gridiron.parser import parse_formula
from gridiron.paste import unparse
from gridiron.refs import CellRef

_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


@dataclass
class NameRegistry:
    bindings: dict[str, Node] = field(default_factory=dict)

    def define(self, name: str, fragment: str) -> str:
        upper = name.upper()
        if not _NAME_PATTERN.match(upper):
            raise Invalid(
                f"{name!r} is not a legal name; letters, "
                "digits, underscores, starting with a letter"
            )
        try:
            CellRef.parse(upper)
        except Invalid:
            pass
        else:
            raise Invalid(
                f"{upper} is a cell address; a name spelled "
                "like one would make the parser guess, and "
                "guessing is banned in this codebase"
            )
        if upper in self.bindings:
            raise Invalid(
                f"{upper} is already defined; redefine "
                "explicitly through replace"
            )
        tree = parse_formula(fragment)
        self.bindings[upper] = tree
        return f"{upper} = {unparse(tree)}"

    def replace(self, name: str, fragment: str) -> str:
        upper = name.upper()
        if upper not in self.bindings:
            raise Missing(f"{upper} is not defined")
        self.bindings[upper] = parse_formula(fragment)
        return f"{upper} now = {unparse(self.bindings[upper])}"

    def forget(self, name: str) -> str:
        upper = name.upper()
        if self.bindings.pop(upper, None) is None:
            raise Missing(f"{upper} is not defined")
        return (
            f"{upper} forgotten; dependents will say #NAME? "
            "instead of freezing their last value"
        )

    def lookup(self, name: str) -> Node | None:
        return self.bindings.get(name.upper())

    def census(self) -> str:
        if not self.bindings:
            return "no names defined; every formula is addresses"
        lines = [
            f"{len(self.bindings)} name(s), the workbook's API:"
        ]
        for name in sorted(self.bindings):
            lines.append(
                f"  {name} = {unparse(self.bindings[name])}"
            )
        return "\n".join(lines)
