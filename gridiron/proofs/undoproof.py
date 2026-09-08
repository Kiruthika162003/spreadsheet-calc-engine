"""The undo proof: three edits walked back and forward, and the future erased.

The drill makes three edits on a chain, walks the whole
stack back to the beginning verifying the computed value at
every station, redoes one step, and then makes a fresh edit
while a redo future still stands to confirm the future is
erased rather than grafted on. The numbers worth watching
are the recomputed values at each undo station, because undo
that restores the literal but forgets to recalculate leaves
a formula showing a number its inputs no longer justify, and
that is the exact failure a stack built from setter returns
is supposed to make impossible. The last check is the erased
future: after a fresh edit the redo stack must be empty,
because a redo after new work would graft an old future onto
a new past and the result belongs to neither timeline.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.undo import UndoStack


def run() -> Finding:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 10.0)
    engine.set_formula(CellRef.parse("B1"), "=A1*2")
    stack = UndoStack(engine=engine)
    stack.set_literal(CellRef.parse("A1"), 20.0)
    stack.set_literal(CellRef.parse("A1"), 30.0)
    stack.set_literal(CellRef.parse("A1"), 40.0)

    def b1() -> float:
        return engine.value(CellRef.parse("B1"))

    top = b1()
    stack.undo()
    after_one = b1()
    stack.undo()
    after_two = b1()
    stack.undo()
    after_three = b1()
    stack.redo()
    after_redo = b1()

    stack.set_literal(CellRef.parse("A1"), 99.0)
    future_erased = False
    try:
        stack.redo()
    except Invalid:
        future_erased = True

    numbers = {
        "top": top,
        "after_one_undo": after_one,
        "after_two_undos": after_two,
        "after_three_undos": after_three,
        "after_one_redo": after_redo,
        "recompute_followed_every_undo": (
            after_one == 60.0
            and after_two == 40.0
            and after_three == 20.0
        ),
        "fresh_edit_recomputed": b1(),
        "future_erased_by_new_work": future_erased,
    }
    holds = (
        top == 80.0
        and numbers["recompute_followed_every_undo"]
        and after_redo == 40.0
        and numbers["fresh_edit_recomputed"] == 198.0
        and future_erased
    )
    return Finding(
        proof="undoproof",
        claim=(
            "undo and redo recompute the dependent at every "
            "station of the walk, and a fresh edit erases "
            "the redo future rather than grafting it onto a "
            "new past"
        ),
        numbers=numbers,
        holds=holds,
    )
