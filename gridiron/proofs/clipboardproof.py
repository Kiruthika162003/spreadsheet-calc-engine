"""The clipboard proof: copy makes strangers, cut makes followers.

The two paste theories differ in exactly one measurable way,
and this drill measures it. Copy a formula that references a
neighbor and the copy's reference shifts with the
displacement, so the original and the copy compute from
different cells and a later edit to the original's precedent
leaves the copy untouched: strangers. Cut the same formula
and it lands unchanged, but every other formula that pointed
at its old address is rewritten to follow it, so a summary
cell that referenced the moved cell still references it at
its new home: followers. The drill builds a small model,
copies once and cuts once, and reads the resulting formula
text and computed values to prove each theory held: the
copied formula's text differs from the original by the
shift, while the cut leaves a dependent still pointing at the
moved value. The number worth watching is the follower count
the cut reports, because that count going to zero would mean
the magic half of cut-paste silently failed and left
dangling references behind, the exact corruption the feature
exists to prevent.
"""

from __future__ import annotations

from gridiron.clipboard import Clipboard
from gridiron.engine import Engine
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef


def run() -> Finding:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 10.0)
    engine.set_literal(CellRef.parse("A2"), 20.0)
    engine.set_formula(CellRef.parse("B1"), "=A1*2")
    clip = Clipboard(sheet=engine.sheet)

    # Copy B1 down to B2: the relative reference shifts to A2.
    clip.copy_cell(
        CellRef.parse("B1"), CellRef.parse("B2")
    )
    engine.full_recalc()
    copied_text = engine.sheet.cell(
        CellRef.parse("B2")
    ).formula_text
    copied_value = engine.value(CellRef.parse("B2"))

    # A summary references B1; then B1 is cut to D1.
    engine.set_formula(CellRef.parse("C1"), "=B1+1")
    engine.full_recalc()
    verdict = clip.cut_cell(
        CellRef.parse("B1"), CellRef.parse("D1")
    )
    engine.full_recalc()
    follower_text = engine.sheet.cell(
        CellRef.parse("C1")
    ).formula_text
    summary_value = engine.value(CellRef.parse("C1"))
    moved_here = (
        engine.sheet.cell(CellRef.parse("D1")) is not None
    )
    origin_empty = (
        engine.sheet.cell(CellRef.parse("B1")) is None
    )

    numbers = {
        "copied_text": copied_text,
        "copied_value": copied_value,
        "copy_shifted_reference": copied_text == "=(A2*2)",
        "follower_text": follower_text,
        "cut_rewrote_the_follower": follower_text
        == "=(D1+1)",
        "summary_value": summary_value,
        "cut_verdict": verdict,
        "moved_and_vacated": moved_here and origin_empty,
    }
    holds = (
        copied_text == "=(A2*2)"
        and copied_value == 40.0
        and follower_text == "=(D1+1)"
        and summary_value == 21.0
        and moved_here
        and origin_empty
        and "1 formula(s) followed" in verdict
    )
    return Finding(
        proof="clipboardproof",
        claim=(
            "copy shifts the reference so B2 becomes =(A2*2), "
            "cut leaves the formula but rewrites the "
            "dependent to =(D1+1) and follows the move, so "
            "the summary still reads 21 from the new home"
        ),
        numbers=numbers,
        holds=holds,
    )
