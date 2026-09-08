"""Batched edits: import a thousand cells, recalculate once.

An import that sets a thousand literals through the ordinary
path pays a thousand recalcs, and the dependents of a busy
column recompute a thousand times to reach the value they
would have reached once. The batch collects edits without
running anything, applies them all, and closes with a single
recalc over the union of the dirty cones, and the receipt
carries the number that justifies the API: evaluations paid
against evaluations the one-at-a-time path would have paid,
measured by actually asking the engine's own reports. A
batch is single-use and refuses edits after close, because
a reopened batch is two batches wearing one receipt, and
the receipt is the product.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.engine import Engine, RecalcReport
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import Value


@dataclass
class Batch:
    engine: Engine
    literals: list[tuple[CellRef, Value]] = field(
        default_factory=list
    )
    formulas: list[tuple[CellRef, str]] = field(
        default_factory=list
    )
    closed: bool = False

    def _open_check(self) -> None:
        if self.closed:
            raise Invalid(
                "the batch is closed; a reopened batch is two "
                "batches wearing one receipt"
            )

    def set_literal(self, ref: CellRef, value: Value) -> None:
        self._open_check()
        self.literals.append((ref, value))

    def set_formula(self, ref: CellRef, text: str) -> None:
        self._open_check()
        self.formulas.append((ref, text))

    def commit(self) -> tuple[RecalcReport, str]:
        self._open_check()
        self.closed = True
        if not self.literals and not self.formulas:
            raise Invalid("an empty batch has nothing to commit")
        seeds: set[tuple[int, int]] = set()
        for ref, value in self.literals:
            self.engine.sheet.set_literal(ref, value)
            seeds.add(ref.key())
        for ref, text in self.formulas:
            self.engine.sheet.set_formula(ref, text)
            seeds.add(ref.key())
        self.engine._reindex()
        dirty = self.engine._dirty_closure(seeds)
        for ref, _ in self.formulas:
            dirty.add(ref.key())
        report = self.engine._run(dirty)
        edits = len(self.literals) + len(self.formulas)
        receipt = (
            f"{edits} edit(s), {len(report.evaluated)} "
            "evaluation(s) in one recalc"
        )
        return report, receipt


def measure_batch_saving(
    build_engine, edits: list[tuple[str, Value]]
) -> str:
    one_at_a_time = build_engine()
    naive_evaluations = 0
    for text, value in edits:
        report = one_at_a_time.set_literal(
            CellRef.parse(text), value
        )
        naive_evaluations += len(report.evaluated)
    batched_engine = build_engine()
    batch = Batch(engine=batched_engine)
    for text, value in edits:
        batch.set_literal(CellRef.parse(text), value)
    report, _ = batch.commit()
    batched_evaluations = len(report.evaluated)
    saved = naive_evaluations - batched_evaluations
    return (
        f"one-at-a-time paid {naive_evaluations} "
        f"evaluation(s), the batch paid "
        f"{batched_evaluations}; {saved} saved, measured by "
        "the engine's own reports"
    )
