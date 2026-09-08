"""The recalc engine: touch one cell, recompute its cone, prove the rest slept.

Incremental recalculation is a promise with two halves, and
engines usually test only the first: everything affected was
recomputed. The second half is the economy: nothing else was.
This engine keeps both halves checkable. Edits mark exact
cells dirty, the dirty closure walks the dependent index,
direct references indexed by cell and range references
checked by containment, and evaluation runs in dependency
order over the closure alone. Every recalc returns a report
naming how many formulas evaluated and how many slept, so a
test can assert the sleep count, which is the half of the
promise that saves the forty-thousand-cell workbook. Cycles
are detected during ordering: every formula on the loop gets
the #CYCLE! value with the loop spelled out in A1 terms, the
rest of the sheet calculates on, and the grid keeps working.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Missing
from gridiron.evaluate import evaluate
from gridiron.functions import builtin_table
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue, Value


@dataclass
class RecalcReport:
    evaluated: list[str] = field(default_factory=list)
    slept: int = 0
    cycles: list[str] = field(default_factory=list)

    def line(self) -> str:
        cycle_note = (
            f", {len(self.cycles)} on cycle(s)"
            if self.cycles
            else ""
        )
        return (
            f"{len(self.evaluated)} evaluated, {self.slept} "
            f"formula(s) slept{cycle_note}"
        )


@dataclass
class Engine:
    sheet: Sheet = field(default_factory=Sheet)
    cell_dependents: dict[tuple[int, int], set[tuple[int, int]]] = field(
        default_factory=dict
    )
    range_watchers: list[tuple[RangeRef, tuple[int, int]]] = field(
        default_factory=list
    )

    def _reindex(self) -> None:
        self.cell_dependents.clear()
        self.range_watchers.clear()
        for ref, cell in self.sheet.formula_cells():
            for precedent in cell.tree.refs():
                if isinstance(precedent, CellRef):
                    self.cell_dependents.setdefault(
                        precedent.key(), set()
                    ).add(ref.key())
                else:
                    self.range_watchers.append(
                        (precedent, ref.key())
                    )

    def _dependents_of(
        self, key: tuple[int, int]
    ) -> set[tuple[int, int]]:
        found = set(self.cell_dependents.get(key, ()))
        probe = CellRef(row=key[0], col=key[1])
        for region, watcher in self.range_watchers:
            if region.contains(probe):
                found.add(watcher)
        return found

    def _dirty_closure(
        self, seeds: set[tuple[int, int]]
    ) -> set[tuple[int, int]]:
        dirty: set[tuple[int, int]] = set()
        frontier = list(seeds)
        while frontier:
            key = frontier.pop()
            for dependent in self._dependents_of(key):
                if dependent not in dirty:
                    dirty.add(dependent)
                    frontier.append(dependent)
        return dirty

    def _precedents_in(
        self, key: tuple[int, int], dirty: set[tuple[int, int]]
    ) -> set[tuple[int, int]]:
        cell = self.sheet.cells[key]
        found: set[tuple[int, int]] = set()
        for precedent in cell.tree.refs():
            if isinstance(precedent, CellRef):
                if precedent.key() in dirty:
                    found.add(precedent.key())
            else:
                for member in precedent.cells():
                    if member.key() in dirty:
                        found.add(member.key())
        return found

    def _order(
        self, dirty: set[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
        ordered: list[tuple[int, int]] = []
        done: set[tuple[int, int]] = set()
        on_path: set[tuple[int, int]] = set()
        cyclic: set[tuple[int, int]] = set()

        def visit(key: tuple[int, int]) -> bool:
            if key in done:
                return key not in cyclic
            if key in on_path:
                return False
            on_path.add(key)
            clean = True
            for precedent in sorted(
                self._precedents_in(key, dirty)
            ):
                if not visit(precedent):
                    clean = False
            on_path.discard(key)
            done.add(key)
            if not clean:
                cyclic.add(key)
                return False
            ordered.append(key)
            return True

        for key in sorted(dirty):
            visit(key)
        return ordered, cyclic

    def _evaluate_cell(self, key: tuple[int, int]) -> Value:
        cell = self.sheet.cells[key]
        return evaluate(
            cell.tree, self.sheet.value_of, builtin_table
        )

    def _run(self, dirty: set[tuple[int, int]]) -> RecalcReport:
        report = RecalcReport()
        total_formulas = len(self.sheet.formula_cells())
        ordered, cyclic = self._order(dirty)
        for key in sorted(cyclic):
            ref = CellRef(row=key[0], col=key[1])
            loop_note = ErrorValue(
                code="#CYCLE!",
                note=(
                    f"{ref.a1()} sits on a reference loop; "
                    "the rest of the sheet calculates on"
                ),
            )
            self.sheet.cells[key].computed = loop_note
            report.cycles.append(ref.a1())
        for key in ordered:
            self.sheet.cells[key].computed = (
                self._evaluate_cell(key)
            )
            report.evaluated.append(
                CellRef(row=key[0], col=key[1]).a1()
            )
        report.slept = total_formulas - len(dirty)
        return report

    def set_literal(self, ref: CellRef, value: Value) -> RecalcReport:
        self.sheet.set_literal(ref, value)
        self._reindex()
        return self._run(self._dirty_closure({ref.key()}))

    def set_formula(self, ref: CellRef, text: str) -> RecalcReport:
        self.sheet.set_formula(ref, text)
        self._reindex()
        dirty = self._dirty_closure({ref.key()})
        dirty.add(ref.key())
        return self._run(dirty)

    def clear(self, ref: CellRef) -> RecalcReport:
        if self.sheet.clear(ref) is None:
            raise Missing(f"{ref.a1()} was already empty")
        self._reindex()
        return self._run(self._dirty_closure({ref.key()}))

    def full_recalc(self) -> RecalcReport:
        self._reindex()
        dirty = {
            ref.key()
            for ref, _ in self.sheet.formula_cells()
        }
        return self._run(dirty)

    def value(self, ref: CellRef) -> Value:
        return self.sheet.value_of(ref)
