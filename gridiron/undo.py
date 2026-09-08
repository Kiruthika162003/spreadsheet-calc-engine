"""Undo: built from what the setters returned, never from spying.

The sheet's setters return the displaced cell, and this
module is why: every edit records what stood there before,
undo re-installs it, redo re-applies the edit, and the stack
never inspects storage internals, so the undo system cannot
drift out of sync with a sheet it does not reach into. The
redo stack clears on any fresh edit, the convention every
editor converged on, because a redo after new work would
graft an old future onto a new past and the result belongs
to neither timeline. Depth is bounded and the bound is
honest: when history overflows, the oldest entry falls off
and the report says so, since an unbounded undo stack is a
memory leak with sentimental value.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Cell
from gridiron.values import Value

HISTORY_LIMIT = 100


@dataclass
class Edit:
    ref: CellRef
    before: Cell | None
    after: Cell | None


@dataclass
class UndoStack:
    engine: Engine
    past: list[Edit] = field(default_factory=list)
    future: list[Edit] = field(default_factory=list)
    dropped: int = 0

    def _record(
        self, ref: CellRef, before: Cell | None
    ) -> None:
        after = self.engine.sheet.cell(ref)
        self.past.append(
            Edit(ref=ref, before=before, after=after)
        )
        self.future.clear()
        if len(self.past) > HISTORY_LIMIT:
            self.past.pop(0)
            self.dropped += 1

    def set_literal(self, ref: CellRef, value: Value) -> None:
        before = self.engine.sheet.cell(ref)
        self.engine.set_literal(ref, value)
        self._record(ref, before)

    def set_formula(self, ref: CellRef, text: str) -> None:
        before = self.engine.sheet.cell(ref)
        self.engine.set_formula(ref, text)
        self._record(ref, before)

    def _install(
        self, ref: CellRef, cell: Cell | None
    ) -> None:
        if cell is None:
            self.engine.sheet.cells.pop(ref.key(), None)
        else:
            self.engine.sheet.cells[ref.key()] = cell
        self.engine.full_recalc()

    def undo(self) -> str:
        if not self.past:
            raise Invalid(
                "nothing to undo; history began after this"
            )
        edit = self.past.pop()
        self._install(edit.ref, edit.before)
        self.future.append(edit)
        return f"undid the edit at {edit.ref.a1()}"

    def redo(self) -> str:
        if not self.future:
            raise Invalid(
                "nothing to redo; the future was overwritten "
                "or never happened"
            )
        edit = self.future.pop()
        self._install(edit.ref, edit.after)
        self.past.append(edit)
        return f"redid the edit at {edit.ref.a1()}"

    def report(self) -> str:
        line = (
            f"{len(self.past)} undoable, "
            f"{len(self.future)} redoable"
        )
        if self.dropped:
            line += (
                f"; {self.dropped} oldest edit(s) fell off "
                "the bounded history, said out loud because "
                "an unbounded stack is a memory leak with "
                "sentimental value"
            )
        return line
