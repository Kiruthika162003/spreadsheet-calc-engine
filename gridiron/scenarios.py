"""Scenarios: named input sets, swapped whole, compared side by side.

A scenario is a saved set of input cells and their values,
best case, worst case, the board's case, and the manager's
whole job is atomicity: applying a scenario swaps every
input or none, restoring is exact, and the current state can
always be captured as a scenario itself before anything is
applied, which is the escape hatch users learn to want after
the first time. Applying refuses if any target cell holds a
formula, because a scenario that overwrites formulas is not
setting inputs, it is rewriting the model, and the two
deserve different verbs. The summary report runs every
scenario against a set of watched output cells and tabulates
the results, which is the entire point of keeping scenarios:
the comparison table nobody wants to rebuild by hand every
Friday.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.engine import Engine
from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef
from gridiron.values import Value, render


@dataclass
class ScenarioManager:
    engine: Engine
    scenarios: dict[str, dict[tuple[int, int], Value]] = field(
        default_factory=dict
    )

    def capture(
        self, name: str, inputs: tuple[CellRef, ...]
    ) -> str:
        if not name.strip():
            raise Invalid("a scenario needs a name")
        if name in self.scenarios:
            raise Invalid(
                f"{name} exists; scenarios are captured once "
                "and compared, not silently replaced"
            )
        if not inputs:
            raise Invalid("a scenario with no inputs sets nothing")
        held: dict[tuple[int, int], Value] = {}
        for ref in inputs:
            cell = self.engine.sheet.cell(ref)
            if cell is not None and cell.is_formula():
                raise Invalid(
                    f"{ref.a1()} holds a formula; a scenario "
                    "that overwrites formulas is rewriting "
                    "the model, and the two deserve "
                    "different verbs"
                )
            held[ref.key()] = (
                cell.literal if cell else None
            )
        self.scenarios[name] = held
        return (
            f"{name} captured with {len(held)} input(s)"
        )

    def apply(self, name: str) -> str:
        held = self.scenarios.get(name)
        if held is None:
            raise Missing(f"no scenario named {name}")
        for key, value in held.items():
            ref = CellRef(row=key[0], col=key[1])
            cell = self.engine.sheet.cell(ref)
            if cell is not None and cell.is_formula():
                raise Invalid(
                    f"{ref.a1()} grew a formula since "
                    f"{name} was captured; applying would "
                    "rewrite the model"
                )
        for key, value in held.items():
            ref = CellRef(row=key[0], col=key[1])
            if value is None:
                self.engine.sheet.cells.pop(key, None)
            else:
                self.engine.sheet.set_literal(ref, value)
        self.engine.full_recalc()
        return f"{name} applied, all inputs swapped together"

    def summary(
        self,
        watched: tuple[CellRef, ...],
        names: tuple[str, ...],
    ) -> str:
        if not watched or not names:
            raise Invalid(
                "a summary needs outputs to watch and "
                "scenarios to compare"
            )
        lines = ["the Friday table, built by machine:"]
        for name in names:
            self.apply(name)
            cells = ", ".join(
                f"{ref.a1()}={render(self.engine.value(ref))}"
                for ref in watched
            )
            lines.append(f"  {name}: {cells}")
        return "\n".join(lines)
