"""Volatile functions: the clock and the dice arrive injected, or not at all.

RAND and TODAY are where determinism goes to die in most
engines, and this one refuses the death: there is no ambient
clock and no global generator anywhere in the package. A
VolatileContext carries a seeded generator and a fixed today
serial, formulas evaluate against a context or the volatile
functions return #NAME? explaining what is missing, and two
evaluations under the same context produce byte-identical
sheets, which is the property every test in this repository
quietly relies on. The taint is the second half: any cell
whose formula touches a volatile function is marked, because
those cells are stale the moment the context advances, and a
recalculator that cannot list its volatile cells cannot
honestly claim the rest of the sheet is current.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.ast import Call, Node
from gridiron.errors import Invalid
from gridiron.values import ErrorValue, Value

VOLATILE_NAMES = ("RAND", "TODAY")


@dataclass
class VolatileContext:
    seed: int
    today_serial: int
    _state: int = 0

    def __post_init__(self) -> None:
        if self.today_serial < 1:
            raise Invalid("today must be on the calendar")
        self._state = self.seed % 2147483647 or 1

    def next_random(self) -> float:
        self._state = (self._state * 48271) % 2147483647
        return self._state / 2147483647

    def make_functions(self):
        def rand(args, _lookup, _functions, _names) -> Value:
            if args:
                return ErrorValue(
                    code="#VALUE!",
                    note="RAND takes no arguments",
                )
            return self.next_random()

        def today(args, _lookup, _functions, _names) -> Value:
            if args:
                return ErrorValue(
                    code="#VALUE!",
                    note="TODAY takes no arguments",
                )
            return float(self.today_serial)

        return {"RAND": rand, "TODAY": today}


def missing_context_functions():
    def refuse(name: str):
        def run(_args, _lookup, _functions, _names) -> Value:
            return ErrorValue(
                code="#NAME?",
                note=(
                    f"{name} needs a VolatileContext; there "
                    "is no ambient clock or global generator "
                    "anywhere in this package"
                ),
            )

        return run

    return {name: refuse(name) for name in VOLATILE_NAMES}


def is_volatile(tree: Node) -> bool:
    if isinstance(tree, Call):
        if tree.function in VOLATILE_NAMES:
            return True
        return any(is_volatile(arg) for arg in tree.args)
    for attribute in ("operand", "left", "right"):
        child = getattr(tree, attribute, None)
        if child is not None and is_volatile(child):
            return True
    return False


def volatile_census(formula_cells) -> str:
    tainted = [
        ref.a1()
        for ref, cell in formula_cells
        if is_volatile(cell.tree)
    ]
    if not tainted:
        return (
            "no volatile cells; the whole sheet is current "
            "until the next edit"
        )
    return (
        f"{len(tainted)} volatile cell(s) "
        f"({', '.join(tainted)}): stale the moment the "
        "context advances, and a recalculator that cannot "
        "list them cannot claim the rest is current"
    )
