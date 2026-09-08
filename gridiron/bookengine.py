"""The workbook engine: one recalc across every sheet, edges and all.

Cross-sheet references make the dependency graph span the
workbook, and the book engine owns that span: each sheet
keeps a local engine for its internal edges while the book
tracks the cross edges, an edit on Data recalculates Data's
cone locally and then the formulas on other sheets that
watch the changed cells through XRefs, in that order,
because a summary sheet reading a total must read the total
after it settled. The evaluation world injected into every
formula includes the sheet resolver, so Data!A1 reads
through the same door the workbook module built, wounds and
all: a reference to a dropped sheet computes as #REF!
mid-formula while the rest of the expression carries on
poisoned, exactly as the value model promises.
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
from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.refs import CellRef
from gridiron.values import Value
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
        self.engines[name.casefold()] = Engine(sheet=sheet)

    def _engine(self, sheet_name: str) -> Engine:
        folded = sheet_name.casefold()
        if folded not in self.engines:
            raise Invalid(f"no sheet named {sheet_name}")
        return self.engines[folded]

    def _resolver(self):
        def read(sheet_name: str, ref: CellRef) -> Value:
            return self.book.read(sheet_name, ref)

        return read

    def _recalc_watchers(self, changed_sheet: str) -> int:
        folded = changed_sheet.casefold()
        recalculated = 0
        for sheet_name, engine in self.engines.items():
            for _, cell in engine.sheet.formula_cells():
                crossings = find_xrefs(cell.tree)
                if not crossings:
                    continue
                if sheet_name != folded and not any(
                    xref.sheet.casefold() == folded
                    for xref in crossings
                ):
                    continue
                cell.computed = evaluate(
                    cell.tree,
                    engine.sheet.value_of,
                    full_table,
                    sheets=self._resolver(),
                )
                recalculated += 1
        return recalculated

    def set_literal(
        self, sheet_name: str, ref: CellRef, value: Value
    ) -> str:
        engine = self._engine(sheet_name)
        report = engine.set_literal(ref, value)
        crossers = self._recalc_watchers(sheet_name)
        return (
            f"{sheet_name}: {report.line()}; {crossers} "
            "cross-sheet formula(s) refreshed after the "
            "local cone settled"
        )

    def set_formula(
        self, sheet_name: str, ref: CellRef, text: str
    ) -> str:
        engine = self._engine(sheet_name)
        engine.set_formula(ref, text)
        cell = engine.sheet.cells[ref.key()]
        if find_xrefs(cell.tree):
            cell.computed = evaluate(
                cell.tree,
                engine.sheet.value_of,
                full_table,
                sheets=self._resolver(),
            )
        crossers = self._recalc_watchers(sheet_name)
        return (
            f"{sheet_name}!{ref.a1()} set; {crossers} "
            "cross-sheet formula(s) refreshed"
        )

    def value(
        self, sheet_name: str, ref: CellRef
    ) -> Value:
        return self._engine(sheet_name).value(ref)
