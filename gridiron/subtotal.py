"""SUBTOTAL: the aggregate that respects the view and ignores itself.

Plain SUM is honest about the sheet and blind to the screen:
it sums hidden rows too, which is the classic silent error
the filters module already reports. SUBTOTAL is the other
contract, an aggregate scoped to what the user can see, and
this module builds it as an overlay: a scope holds the set
of hidden rows, adopted from a filter view or hidden by
hand, and wraps any function table so SUBTOTAL exists inside
it while every other name passes through untouched. Two of
the incumbent's rules are kept because both prevent real
double counting. Hidden rows do not participate, that is the
point of the function. And cells that are themselves
SUBTOTAL formulas do not participate either, detected by
looking at the cell's parsed tree rather than its text, so a
grand subtotal over a column of section subtotals counts
each section once instead of twice. The detection is the
top-level shape: a subtotal wrapped in arithmetic like
SUBTOTAL(9, ...)+0 is a computation that happens to mention
one, counts as a plain value, and the incumbent's deeper
scan is deliberately not copied, because a rule you can
state in one sentence beats a rule that needs a walker. The code menu is the
useful subset, 1 average, 2 count, 4 max, 5 min, 9 sum, and
an unknown code is refused with the menu quoted, because a
numeric first argument is already one indirection too many
to leave unexplained when it fails.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.ast import Call, Range
from gridiron.errors import Invalid
from gridiron.evaluate import FunctionTable, evaluate
from gridiron.filters import FilterView
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)

_CODES = {
    1: "AVERAGE",
    2: "COUNT",
    4: "MAX",
    5: "MIN",
    9: "SUM",
}


@dataclass
class SubtotalScope:
    sheet: Sheet
    hidden_rows: set[int] = field(default_factory=set)

    def hide_rows(self, rows: list[int]) -> str:
        self.hidden_rows.update(rows)
        return (
            f"{len(rows)} row(s) hidden by hand; "
            f"{len(self.hidden_rows)} hidden in all"
        )

    def unhide_all(self) -> str:
        count = len(self.hidden_rows)
        self.hidden_rows.clear()
        return f"{count} row(s) returned to view"

    def adopt_filter(self, view: FilterView) -> str:
        visible = set(view.visible_rows())
        adopted = [
            row
            for row in range(
                view.region.top, view.region.bottom + 1
            )
            if row not in visible
        ]
        self.hidden_rows.update(adopted)
        return (
            f"{len(adopted)} filtered row(s) adopted into "
            "the hidden set"
        )

    def _is_subtotal_cell(self, ref: CellRef) -> bool:
        cell = self.sheet.cell(ref)
        return (
            cell is not None
            and cell.tree is not None
            and isinstance(cell.tree, Call)
            and cell.tree.function == "SUBTOTAL"
        )

    def _subtotal(self, args, lookup, functions, names) -> Value:
        if len(args) != 2 or not isinstance(args[1], Range):
            return ErrorValue(
                code="#VALUE!",
                note="SUBTOTAL takes a code and a range",
            )
        code_value = evaluate(
            args[0], lookup, functions, names
        )
        if is_error(code_value):
            return code_value
        code_number = to_number(code_value)
        if is_error(code_number):
            return code_number
        code = int(code_number)
        if code not in _CODES:
            menu = ", ".join(
                f"{number} {name}"
                for number, name in sorted(_CODES.items())
            )
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"code {code} is not on the menu: {menu}"
                ),
            )
        numbers: list[float] = []
        for cell_ref in args[1].ref.cells():
            if cell_ref.row in self.hidden_rows:
                continue
            if self._is_subtotal_cell(cell_ref):
                continue
            value = lookup(cell_ref)
            if is_error(value):
                return value
            if isinstance(value, float) and not isinstance(
                value, bool
            ):
                numbers.append(value)
        name = _CODES[code]
        if name == "COUNT":
            return float(len(numbers))
        if not numbers:
            if name == "AVERAGE":
                return ErrorValue(
                    code="#DIV/0!",
                    note=(
                        "every row in view was hidden or a "
                        "subtotal; there is nothing to "
                        "average"
                    ),
                )
            return None
        if name == "AVERAGE":
            return sum(numbers) / len(numbers)
        if name == "SUM":
            return sum(numbers)
        if name == "MAX":
            return max(numbers)
        return min(numbers)

    def table(self, base: FunctionTable) -> FunctionTable:
        def scoped(name: str):
            if name == "SUBTOTAL":
                return self._subtotal
            return base(name)

        return scoped


def install(engine, scope: SubtotalScope) -> str:
    if engine.sheet is not scope.sheet:
        raise Invalid(
            "the scope watches a different sheet than the "
            "engine computes; installing it would scope "
            "the wrong rows"
        )
    engine.functions = scope.table(engine.functions)
    return (
        "SUBTOTAL installed; aggregates now respect the "
        "hidden set"
    )
