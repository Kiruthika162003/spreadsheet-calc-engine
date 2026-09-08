"""The watch window: a fixed set of cells, and what changed since last look.

Debugging a large model means watching a handful of cells
while editing far away, and the watch window is that handful
made explicit. It holds a set of watched cells and a snapshot
of their last-seen values, and each poll returns which of
them changed, from what to what, since the previous poll,
because the useful question during debugging is never the
whole sheet, it is did the number I care about move when I
touched something over there. The snapshot is taken at add
time so a freshly watched cell reads as unchanged on its
first poll rather than reporting a phantom change from
nothing to its value, which would be noise on every add. A
watched cell that becomes an error is a change like any
other and reports as one, because a cell going from a number
to a #REF! is exactly the transition a debugger is hunting,
and hiding it because it is not a number would hide the bug.
Removing a watch forgets its history, and re-adding it takes
a fresh snapshot rather than resurrecting the old one, so the
window never reports a change across a gap when it was not
looking, which would be a claim it cannot honestly make.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import Value, is_error, render


def _shown(value: Value) -> str:
    if value is None:
        return "(empty)"
    if is_error(value):
        return value.code
    if isinstance(value, str):
        return repr(value)
    return render(value)


@dataclass
class WatchWindow:
    engine: Engine
    watched: dict[tuple[int, int], Value] = field(
        default_factory=dict
    )

    def add(self, ref: CellRef) -> str:
        if ref.key() in self.watched:
            raise Invalid(f"{ref.a1()} is already watched")
        self.watched[ref.key()] = self.engine.value(ref)
        return f"watching {ref.a1()}"

    def remove(self, ref: CellRef) -> str:
        if ref.key() not in self.watched:
            raise Invalid(f"{ref.a1()} was not watched")
        del self.watched[ref.key()]
        return f"stopped watching {ref.a1()}"

    def poll(self) -> list[str]:
        changes = []
        for key in sorted(self.watched):
            ref = CellRef(row=key[0], col=key[1])
            current = self.engine.value(ref)
            previous = self.watched[key]
            if current != previous:
                changes.append(
                    f"{ref.a1()}: {_shown(previous)} -> "
                    f"{_shown(current)}"
                )
                self.watched[key] = current
        return changes

    def report(self) -> str:
        changes = self.poll()
        if not changes:
            return (
                f"{len(self.watched)} watched, none changed"
            )
        return "\n".join(changes)
