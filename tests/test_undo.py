from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.undo import UndoStack


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def stack() -> UndoStack:
    chosen = UndoStack(engine=Engine())
    chosen.set_literal(ref("A1"), 10.0)
    chosen.set_formula(ref("B1"), "=A1*2")
    return chosen


class TestUndoRedo:
    def test_undo_reinstalls_the_displaced_cell(self):
        chosen = stack()
        chosen.set_literal(ref("A1"), 99.0)
        assert chosen.engine.value(ref("B1")) == 198.0
        chosen.undo()
        assert chosen.engine.value(ref("A1")) == 10.0
        assert chosen.engine.value(ref("B1")) == 20.0

    def test_undoing_a_fresh_cell_leaves_absence(self):
        chosen = stack()
        chosen.undo()
        assert chosen.engine.sheet.cell(ref("B1")) is None

    def test_redo_reapplies_the_edit(self):
        chosen = stack()
        chosen.set_literal(ref("A1"), 99.0)
        chosen.undo()
        chosen.redo()
        assert chosen.engine.value(ref("A1")) == 99.0
        assert chosen.engine.value(ref("B1")) == 198.0

    def test_a_fresh_edit_burns_the_future(self):
        chosen = stack()
        chosen.set_literal(ref("A1"), 99.0)
        chosen.undo()
        chosen.set_literal(ref("A1"), 55.0)
        with pytest.raises(Invalid) as caught:
            chosen.redo()
        assert "overwritten or never happened" in str(
            caught.value
        )

    def test_the_empty_past_says_when_history_began(self):
        with pytest.raises(Invalid):
            UndoStack(engine=Engine()).undo()


class TestTheBound:
    def test_overflow_is_said_out_loud(self):
        chosen = UndoStack(engine=Engine())
        for number in range(105):
            chosen.set_literal(
                ref("A1"), float(number)
            )
        report = chosen.report()
        assert "100 undoable" in report
        assert "5 oldest edit(s) fell off" in report
        assert "sentimental value" in report
