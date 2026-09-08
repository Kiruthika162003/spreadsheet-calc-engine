"""The workbook engine: one recalc across every sheet, edges and all.

Cross-sheet references make the dependency graph span the
workbook, and the book engine owns that span: each sheet
keeps a local engine for its internal edges, every local
engine carries the sheet resolver so Data!A1 evaluates
through the workbook door even during an ordinary local run,
and after an edit's local cone settles the book refreshes
the cross-sheet formulas in rounds until a whole round
changes nothing. Rounds matter because chains cross more
than one boundary: an edit on Costs moves a total that
Summary reads, and a Report cell reading Summary must see
the moved value, which a single sweep keyed to the edited
sheet would miss. The first design keyed the sweep exactly
that way and also refreshed the watcher cell directly,
leaving the watcher's own local dependents stale, so both
lessons are baked into the current shape: refreshes go
through the local engine so the dependent cone rides along,
and the sweep repeats until settled. A workbook cycle,
Sheet1 reading Sheet2 reading Sheet1, never settles, so the
rounds are capped at one per sheet plus one, and formulas
still changing at the cap are stamped #CYCLE! with a note
naming the boundary the loop crosses. Wounds behave as the
value model promises: a reference to a dropped sheet
computes as #REF! mid-formula while the rest of the
expression carries on poisoned.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.ast import (
    Binary,
    Call,
    Node,
    Unary,
    XRef,
)
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import ErrorValue, Value
from gridiron.workbook import Workbook


def find_xrefs(tree: Node) -> list[XRef]:
    if isinstance(tree, XRef):
        return [tree]
    found: list[XRef] = []
    if isinstance(tree, Unary):
        found.extend(find_xrefs(tree.operand))
    elif isinstance(tree, Binary):
        found.extend(find_xrefs(tree.left))
        found.extend(find_xrefs(tree.right))
    elif isinstance(tree, Call):
        for arg in tree.args:
            found.extend(find_xrefs(arg))
    return found


@dataclass
class BookEngine:
    book: Workbook = field(default_factory=Workbook)
    engines: dict[str, Engine] = field(default_factory=dict)

    def add_sheet(self, name: str) -> None:
        sheet = self.book.add_sheet(name)
        engine = Engine(sheet=sheet)
        engine.sheets = self._resolver()
        self.engines[name.casefold()] = engine

    def _engine(self, sheet_name: str) -> Engine:
        folded = sheet_name.casefold()
        if folded not in self.engines:
            raise Invalid(f"no sheet named {sheet_name}")
        return self.engines[folded]

    def _resolver(self):
        def read(sheet_name: str, ref: CellRef) -> Value:
            return self.book.read(sheet_name, ref)

        return read

    def _cross_cells(self):
        for sheet_name, engine in self.engines.items():
            for ref, cell in engine.sheet.formula_cells():
                if find_xrefs(cell.tree):
                    yield sheet_name, engine, ref, cell

    def _refresh_round(self) -> list[str]:
        changed = []
        for sheet_name, engine, ref, cell in self._cross_cells():
            before = cell.computed
            engine.recalc_cell(ref)
            if cell.computed != before:
                changed.append(f"{sheet_name}!{ref.a1()}")
        return changed

    def _settle_watchers(self) -> tuple[int, int]:
        cap = len(self.engines) + 1
        refreshed: set[str] = set()
        rounds = 0
        still_changing: list[str] = []
        while rounds < cap:
            still_changing = self._refresh_round()
            rounds += 1
            if not still_changing:
                break
            refreshed.update(still_changing)
        if still_changing:
            for label in still_changing:
                sheet_name, _, cell_text = label.partition("!")
                cell = self.engines[
                    sheet_name
                ].sheet.cells[CellRef.parse(cell_text).key()]
                cell.computed = ErrorValue(
                    code="#CYCLE!",
                    note=(
                        f"{label} sits on a loop that crosses "
                        "sheet boundaries; the refresh rounds "
                        "never settled"
                    ),
                )
        return len(refreshed), rounds

    def set_literal(
        self, sheet_name: str, ref: CellRef, value: Value
    ) -> str:
        engine = self._engine(sheet_name)
        report = engine.set_literal(ref, value)
        crossers, rounds = self._settle_watchers()
        return (
            f"{sheet_name}: {report.line()}; {crossers} "
            "cross-sheet formula(s) refreshed in "
            f"{rounds} round(s) after the local cone settled"
        )

    def set_formula(
        self, sheet_name: str, ref: CellRef, text: str
    ) -> str:
        engine = self._engine(sheet_name)
        engine.set_formula(ref, text)
        crossers, rounds = self._settle_watchers()
        return (
            f"{sheet_name}!{ref.a1()} set; {crossers} "
            "cross-sheet formula(s) refreshed in "
            f"{rounds} round(s)"
        )

    def value(
        self, sheet_name: str, ref: CellRef
    ) -> Value:
        return self._engine(sheet_name).value(ref)
