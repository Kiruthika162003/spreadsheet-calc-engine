"""What-if data tables: sweep an input, tabulate an output, restore the world.

A data table is a disciplined loop: take an input cell, a
list of candidate values, and an output cell, run the model
once per candidate, record the outputs, and put the original
input back exactly, because a what-if that leaves the world
changed is a what-now. The two-variable form sweeps a grid,
rows for one input and columns for the other, the classic
mortgage-rate-by-term table, and both forms report through
the same contract: candidates paired with outcomes, errors
recorded as their codes rather than aborting the sweep,
since the whole point of a sensitivity table is seeing where
the model breaks, and a table that stops at the first break
shows everything except the interesting part.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import Value, render


@dataclass
class DataTable:
    engine: Engine

    def _restore(
        self, ref: CellRef, original: Value
    ) -> None:
        if original is None:
            self.engine.sheet.cells.pop(ref.key(), None)
            self.engine.full_recalc()
        else:
            self.engine.set_literal(ref, original)

    def one_variable(
        self,
        input_ref: CellRef,
        candidates: list[float],
        output_ref: CellRef,
    ) -> list[tuple[float, str]]:
        if not candidates:
            raise Invalid("a sweep needs candidates")
        held = self.engine.sheet.cell(input_ref)
        if held is not None and held.is_formula():
            raise Invalid(
                f"{input_ref.a1()} holds a formula; sweep "
                "inputs, not the model"
            )
        original = held.literal if held else None
        rows: list[tuple[float, str]] = []
        for candidate in candidates:
            self.engine.set_literal(input_ref, candidate)
            outcome = self.engine.value(output_ref)
            rows.append((candidate, render(outcome)))
        self._restore(input_ref, original)
        return rows

    def two_variable(
        self,
        row_input: CellRef,
        row_values: list[float],
        col_input: CellRef,
        col_values: list[float],
        output_ref: CellRef,
    ) -> list[list[str]]:
        if not row_values or not col_values:
            raise Invalid("both axes need candidates")
        row_cell = self.engine.sheet.cell(row_input)
        col_cell = self.engine.sheet.cell(col_input)
        for name, cell in (
            (row_input, row_cell),
            (col_input, col_cell),
        ):
            if cell is not None and cell.is_formula():
                raise Invalid(
                    f"{name.a1()} holds a formula; sweep "
                    "inputs, not the model"
                )
        row_original = row_cell.literal if row_cell else None
        col_original = col_cell.literal if col_cell else None
        grid: list[list[str]] = []
        for row_value in row_values:
            self.engine.set_literal(row_input, row_value)
            line: list[str] = []
            for col_value in col_values:
                self.engine.set_literal(
                    col_input, col_value
                )
                line.append(
                    render(self.engine.value(output_ref))
                )
            grid.append(line)
        self._restore(row_input, row_original)
        self._restore(col_input, col_original)
        return grid

    def break_report(
        self,
        input_ref: CellRef,
        candidates: list[float],
        output_ref: CellRef,
    ) -> str:
        rows = self.one_variable(
            input_ref, candidates, output_ref
        )
        breaks = [
            (candidate, outcome)
            for candidate, outcome in rows
            if outcome.startswith("#")
        ]
        if not breaks:
            return (
                f"the model held across all "
                f"{len(candidates)} candidate(s)"
            )
        first = breaks[0]
        return (
            f"the model breaks at {len(breaks)} of "
            f"{len(candidates)} candidate(s), first at "
            f"{first[0]} with {first[1]}; a table that "
            "stopped there would show everything except the "
            "interesting part"
        )
