"""The sleep proof: the economy half of incremental recalc, measured.

A pyramid of forty formulas sits on two input cells: twenty
first-tier cells read input A, nineteen second-tier cells
read pairs of the first tier, and one apex sums the second
tier. Editing input A must wake all forty; editing input B,
referenced by nobody, must wake zero; and editing one
first-tier formula must wake only its two watchers and the
apex. The first guess in this file said the single-formula
edit would wake three formulas plus itself, four evaluated,
and measurement agreed, but the guess about the full cone
was wrong once: the apex was counted twice in the draft
arithmetic, thirty-nine plus itself is forty, not
forty-one, and the wrong sum is kept here beside the
measured one because the whole point of the sleep count is
that arithmetic, not confidence, decides it. The apex value
was guessed wrong too: 78 was computed against the pre-edit
input, and the measured answer after A1 becomes 2 and B7
becomes A1*3 is 156, seventeen pairs at 8 plus two pairs at
10, which the proof now holds to.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef


def _build() -> Engine:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 1.0)
    engine.set_literal(CellRef.parse("A2"), 100.0)
    for row in range(1, 21):
        engine.set_formula(
            CellRef.parse(f"B{row}"), "=A1*2"
        )
    for row in range(1, 20):
        engine.set_formula(
            CellRef.parse(f"C{row}"),
            f"=B{row}+B{row + 1}",
        )
    engine.set_formula(
        CellRef.parse("D1"), "=SUM(C1:C19)"
    )
    return engine


def run() -> Finding:
    engine = _build()
    full_wake = engine.set_literal(CellRef.parse("A1"), 2.0)
    nobody = engine.set_literal(CellRef.parse("A2"), 5.0)
    one_tier = engine.set_formula(
        CellRef.parse("B7"), "=A1*3"
    )
    numbers = {
        "formulas_total": 40,
        "full_wake_evaluated": len(full_wake.evaluated),
        "full_wake_slept": full_wake.slept,
        "nobody_evaluated": len(nobody.evaluated),
        "nobody_slept": nobody.slept,
        "one_tier_evaluated": len(one_tier.evaluated),
        "one_tier_slept": one_tier.slept,
        "apex_after": engine.value(CellRef.parse("D1")),
    }
    holds = (
        numbers["full_wake_evaluated"] == 40
        and numbers["full_wake_slept"] == 0
        and numbers["nobody_evaluated"] == 0
        and numbers["nobody_slept"] == 40
        and numbers["one_tier_evaluated"] == 4
        and numbers["one_tier_slept"] == 36
        and numbers["apex_after"] == 156.0
    )
    return Finding(
        proof="sleepproof",
        claim=(
            "the input edit wakes all 40, the stranger edit "
            "wakes 0, and the one-formula edit wakes exactly "
            "its two watchers and the apex: 4 evaluated, 36 "
            "asleep"
        ),
        numbers=numbers,
        holds=holds,
    )
