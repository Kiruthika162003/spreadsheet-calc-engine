"""Snapshots: named moments of a sheet, diffed honestly, restored loudly.

A snapshot is the sheet's state given a name so a later
reader can ask the only two questions that matter: what
changed since, and can we go back. The stored state is the
authored truth, literals and formula text, not computed
values, because computed values are derivable and storing
them invites the classic drift where a restored sheet shows
numbers its own formulas no longer produce; restore instead
rebuilds cells from their text and tells the caller to
recalculate, one honest sentence instead of a stale display.
The diff speaks in three verbs and counts them separately,
cells added since the snapshot, cells removed, cells
changed, and a changed formula is reported as its text
change even when the computed value happens to match,
because =A1+1 and =B1+1 agreeing today is a coincidence, not
an identity. Snapshot names are unique by refusal, taking a
second snapshot under one name would make which-tuesday a
guessing game, and restoring a name that was never taken is
a Missing, not a silent no-op, since a rollback that did
nothing while claiming otherwise is the worst outcome
version control can produce.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.values import Value, render


def _shown(value: Value) -> str:
    if value is None:
        return "(empty)"
    if isinstance(value, str):
        return value
    return render(value)


@dataclass(frozen=True)
class FrozenCell:
    literal: Value
    formula_text: str | None

    def describe(self) -> str:
        if self.formula_text is not None:
            return self.formula_text
        return _shown(self.literal)


@dataclass
class DiffReport:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    untouched: int = 0

    def line(self) -> str:
        return (
            f"{len(self.added)} added, "
            f"{len(self.removed)} removed, "
            f"{len(self.changed)} changed, "
            f"{self.untouched} untouched"
        )

    def full(self) -> str:
        lines = []
        for label, entries in (
            ("added", self.added),
            ("removed", self.removed),
            ("changed", self.changed),
        ):
            lines.extend(
                f"{label}: {entry}" for entry in entries
            )
        lines.append(self.line())
        return "\n".join(lines)


@dataclass
class SnapshotVault:
    sheet: Sheet
    saved: dict[
        str, dict[tuple[int, int], FrozenCell]
    ] = field(default_factory=dict)

    def _freeze(self) -> dict[tuple[int, int], FrozenCell]:
        frozen = {}
        for key, cell in self.sheet.cells.items():
            frozen[key] = FrozenCell(
                literal=cell.literal,
                formula_text=cell.formula_text,
            )
        return frozen

    def take(self, name: str) -> str:
        title = name.strip()
        if not title:
            raise Invalid("a snapshot needs a name")
        if title in self.saved:
            raise Invalid(
                f"a snapshot named {title!r} exists; two "
                "moments under one name make which-tuesday "
                "a guessing game"
            )
        self.saved[title] = self._freeze()
        return (
            f"snapshot {title!r} holds "
            f"{len(self.saved[title])} cell(s)"
        )

    def _get(
        self, name: str
    ) -> dict[tuple[int, int], FrozenCell]:
        if name not in self.saved:
            known = ", ".join(sorted(self.saved)) or "none"
            raise Missing(
                f"no snapshot named {name!r}; taken: {known}"
            )
        return self.saved[name]

    def diff(self, name: str) -> DiffReport:
        then = self._get(name)
        now = self._freeze()
        report = DiffReport()
        for key in sorted(set(then) | set(now)):
            address = CellRef(row=key[0], col=key[1]).a1()
            if key not in then:
                report.added.append(
                    f"{address} = {now[key].describe()}"
                )
            elif key not in now:
                report.removed.append(
                    f"{address} was {then[key].describe()}"
                )
            elif then[key] != now[key]:
                report.changed.append(
                    f"{address}: {then[key].describe()} "
                    f"-> {now[key].describe()}"
                )
            else:
                report.untouched += 1
        return report

    def restore(self, name: str) -> str:
        then = self._get(name)
        for key in list(self.sheet.cells):
            del self.sheet.cells[key]
        for key, frozen in then.items():
            target = CellRef(row=key[0], col=key[1])
            if frozen.formula_text is not None:
                self.sheet.set_formula(
                    target, frozen.formula_text
                )
            else:
                self.sheet.set_literal(
                    target, frozen.literal
                )
        return (
            f"restored {name!r}: {len(then)} cell(s) "
            "rebuilt from their text; recalculate before "
            "trusting any computed value"
        )

    def drop(self, name: str) -> str:
        self._get(name)
        del self.saved[name]
        return f"snapshot {name!r} dropped"

    def catalog(self) -> str:
        if not self.saved:
            return "no snapshots taken"
        lines = [
            f"{name}: {len(cells)} cell(s)"
            for name, cells in sorted(self.saved.items())
        ]
        return "\n".join(lines)
