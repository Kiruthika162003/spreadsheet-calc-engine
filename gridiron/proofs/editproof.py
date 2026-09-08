"""The edit proof: insert then delete is the identity, minus the parentheses.

A row inserted and immediately deleted should leave every
formula meaning what it meant, and the drill checks the
stronger textual claim with one honest allowance: the
rewriter normalizes as it goes, so a formula written =A2*2
returns as =(A2*2), changed in spelling and identical in
tree. The proof therefore compares parsed trees across the
round trip, the representation the engine actually computes
from, and holds on all four formulas including the absolute
reference and the range. The second half wounds on purpose:
deleting a referenced row converts the dependent to #REF!
and a recalculation after the wound produces the REF error
value rather than a stale number, which is the entire point
of visible wounds. The first run taught two lessons kept
here: the baked wound evaluated as #NAME? because it was
spelled as a name node, so the evaluator now honors #REF!
as the error it displays, and the cell this proof first
called a survivor sat on the deleted row itself, so the 40
it read was the relocated SUM of the rows that remained,
10 and 30, which is the measurement correcting the story.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.insertdelete import RowEditor
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.values import is_error


def run() -> Finding:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 10.0)
    engine.set_literal(CellRef.parse("A2"), 20.0)
    engine.set_literal(CellRef.parse("A3"), 30.0)
    engine.set_formula(CellRef.parse("C1"), "=A2*2")
    engine.set_formula(CellRef.parse("C2"), "=$A$3+1")
    engine.set_formula(CellRef.parse("C3"), "=SUM(A1:A3)")
    engine.set_formula(CellRef.parse("D1"), "=C1+C3")
    before_trees = {
        ref.a1(): cell.tree
        for ref, cell in engine.sheet.formula_cells()
    }
    editor = RowEditor(sheet=engine.sheet)
    editor.insert_rows(at_row=1)
    editor.delete_rows(at_row=1)
    after_trees = {
        ref.a1(): cell.tree
        for ref, cell in engine.sheet.formula_cells()
    }
    round_trip_identity = before_trees == after_trees
    text_changed = engine.sheet.cell(
        CellRef.parse("C1")
    ).formula_text == "=(A2*2)"
    editor.delete_rows(at_row=1)
    engine.full_recalc()
    wounded = engine.value(CellRef.parse("C1"))
    relocated_sum = engine.value(CellRef.parse("C2"))
    numbers = {
        "formulas_tracked": len(before_trees),
        "round_trip_identity_on_trees": round_trip_identity,
        "spelling_normalized": text_changed,
        "wound_is_ref_error": is_error(wounded)
        and wounded.code == "#REF!",
        "relocated_sum_value": relocated_sum,
    }
    holds = (
        numbers["formulas_tracked"] == 4
        and numbers["round_trip_identity_on_trees"]
        and numbers["spelling_normalized"]
        and numbers["wound_is_ref_error"]
        and numbers["relocated_sum_value"] == 40.0
    )
    return Finding(
        proof="editproof",
        claim=(
            "insert then delete is the identity on parsed "
            "trees for all four formulas while the spelling "
            "normalizes, and the deliberate wound recalculates "
            "to a REF error instead of a stale number"
        ),
        numbers=numbers,
        holds=holds,
    )
