"""The batch proof: the receipt's numbers come from the engine, not the brochure.

Ten literal edits into a column watched by a SUM and its
doubler cost twenty evaluations one at a time, because each
edit wakes both watchers, and two in a batch, because the
union of ten dirty cones is still just two formulas. The
proof measures both paths with the engine's own recalc
reports, checks the final values agree between the two
worlds, and holds the saving at exactly eighteen. The
agreement check matters as much as the saving: a batch that
saved evaluations by skipping one would show the same
receipt and a different total, which is the failure mode
receipts exist to catch.
"""

from __future__ import annotations

from gridiron.batch import Batch
from gridiron.engine import Engine
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef


def _build() -> Engine:
    engine = Engine()
    for row in range(1, 11):
        engine.set_literal(
            CellRef.parse(f"A{row}"), float(row)
        )
    engine.set_formula(
        CellRef.parse("C1"), "=SUM(A1:A10)"
    )
    engine.set_formula(CellRef.parse("C2"), "=C1*2")
    return engine


def run() -> Finding:
    edits = [
        (f"A{row}", float(row * 10))
        for row in range(1, 11)
    ]
    one_at_a_time = _build()
    naive_evaluations = 0
    for text, value in edits:
        report = one_at_a_time.set_literal(
            CellRef.parse(text), value
        )
        naive_evaluations += len(report.evaluated)
    batched = _build()
    batch = Batch(engine=batched)
    for text, value in edits:
        batch.set_literal(CellRef.parse(text), value)
    report, _receipt = batch.commit()
    worlds_agree = all(
        one_at_a_time.value(CellRef.parse(name))
        == batched.value(CellRef.parse(name))
        for name in ("C1", "C2")
    )
    numbers = {
        "edits": len(edits),
        "naive_evaluations": naive_evaluations,
        "batched_evaluations": len(report.evaluated),
        "saved": naive_evaluations - len(report.evaluated),
        "worlds_agree": worlds_agree,
        "final_sum": batched.value(CellRef.parse("C1")),
    }
    holds = (
        numbers["naive_evaluations"] == 20
        and numbers["batched_evaluations"] == 2
        and numbers["saved"] == 18
        and numbers["worlds_agree"]
        and numbers["final_sum"] == 550.0
    )
    return Finding(
        proof="batchproof",
        claim=(
            "ten edits cost twenty evaluations one at a time "
            "and two in a batch, eighteen saved, and both "
            "worlds agree on every watched value, because a "
            "batch that saved by skipping would show the same "
            "receipt and a different total"
        ),
        numbers=numbers,
        holds=holds,
    )
