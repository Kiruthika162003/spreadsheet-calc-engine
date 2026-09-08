"""Manual calculation: deferral with a ledger, staleness with a name.

Automatic recalculation is the grid's default promise, and
manual mode is the deliberate breaking of it for workbooks
where one edit costs a minute of recompute. Breaking a
promise safely requires bookkeeping, so the controller keeps
a ledger: every deferred edit lands on the sheet immediately,
its value is what changed, but no formula runs, and the seeds
accumulate until calculate() runs the dirty closure of all of
them at once, exactly the cells an automatic engine would
have touched across the whole batch and not one more. The
danger of manual mode is not the deferral, it is the read in
between, a stale number wearing the confidence of a computed
one, so staleness is queryable by cell: is_stale answers
whether a cell sits in the pending closure, and the pending
report counts both edits deferred and formulas gone stale,
because sixteen edits might stale three formulas or three
hundred and the difference is the whole cost decision.
Switching back to automatic does not quietly discard the
ledger, it calculates first, since a mode switch that loses
pending work is the kind of bug users diagnose for a week.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.engine import Engine, RecalcReport
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import Value


@dataclass
class CalcController:
    engine: Engine
    manual: bool = False
    pending_seeds: set[tuple[int, int]] = field(
        default_factory=set
    )
    deferred_edits: int = 0

    def set_manual(self) -> str:
        if self.manual:
            return "already manual; the ledger continues"
        self.manual = True
        return (
            "manual mode: edits land, formulas wait, the "
            "ledger remembers"
        )

    def set_auto(self) -> str:
        if not self.manual:
            return "already automatic"
        report = self.calculate()
        self.manual = False
        return (
            "automatic again after settling the ledger: "
            f"{report.line()}"
        )

    def set_literal(
        self, ref: CellRef, value: Value
    ) -> RecalcReport | str:
        if not self.manual:
            return self.engine.set_literal(ref, value)
        self.engine.sheet.set_literal(ref, value)
        self.pending_seeds.add(ref.key())
        self.deferred_edits += 1
        return (
            f"{ref.a1()} changed; recalculation deferred "
            f"({self.deferred_edits} edit(s) on the ledger)"
        )

    def set_formula(
        self, ref: CellRef, text: str
    ) -> RecalcReport | str:
        if not self.manual:
            return self.engine.set_formula(ref, text)
        self.engine.sheet.set_formula(ref, text)
        self.pending_seeds.add(ref.key())
        self.deferred_edits += 1
        return (
            f"{ref.a1()} rewritten; it and its dependents "
            "wait for calculate()"
        )

    def _stale_keys(self) -> set[tuple[int, int]]:
        if not self.pending_seeds:
            return set()
        self.engine._reindex()
        closure = self.engine._dirty_closure(
            set(self.pending_seeds)
        )
        closure.update(
            key
            for key in self.pending_seeds
            if self.engine.sheet.cells.get(key) is not None
            and self.engine.sheet.cells[key].tree is not None
        )
        return closure

    def is_stale(self, ref: CellRef) -> bool:
        return ref.key() in self._stale_keys()

    def pending_report(self) -> str:
        stale = len(self._stale_keys())
        return (
            f"{self.deferred_edits} edit(s) deferred; "
            f"{stale} formula(s) stale"
        )

    def calculate(self) -> RecalcReport:
        if not self.manual:
            raise Invalid(
                "calculate() belongs to manual mode; "
                "automatic mode never owes a recalc"
            )
        dirty = self._stale_keys()
        report = self.engine._run(dirty)
        self.pending_seeds.clear()
        self.deferred_edits = 0
        return report

    def value(self, ref: CellRef) -> Value:
        return self.engine.value(ref)
