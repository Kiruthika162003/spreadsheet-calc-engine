"""The formula tracer: precedents and dependents, drawn in text.

Auditing a workbook means asking two questions of a cell,
what feeds it and what it feeds, and the tracer answers both
from the same trees the engine computes with, so the trace
can never disagree with the calculation. Precedents come in
levels, direct first, then the precedents of precedents,
with ranges expanded only to the cells that actually hold
something, because listing a million empty members of A:A
would bury the three that matter. The dependent trace runs
the other way and includes range watchers, the classic blind
spot: B7 feeds SUM(B1:B100) even though no formula names B7,
and an auditor whose tracer misses that has audited the
labels. Cycles in the trace are marked and not followed,
since a trace that loops forever answers nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.engine import Engine
from gridiron.errors import Missing
from gridiron.refs import CellRef


@dataclass
class Tracer:
    engine: Engine

    def _direct_precedents(
        self, key: tuple[int, int]
    ) -> list[tuple[int, int]]:
        cell = self.engine.sheet.cells.get(key)
        if cell is None or not cell.is_formula():
            return []
        found: list[tuple[int, int]] = []
        for precedent in cell.tree.refs():
            if isinstance(precedent, CellRef):
                found.append(precedent.key())
            else:
                for member in precedent.cells():
                    if member.key() in self.engine.sheet.cells:
                        found.append(member.key())
        return found

    def precedents(self, ref: CellRef, depth: int = 3) -> str:
        if ref.key() not in self.engine.sheet.cells:
            raise Missing(f"{ref.a1()} is empty; nothing feeds it")
        lines = [f"what feeds {ref.a1()}:"]
        seen: set[tuple[int, int]] = {ref.key()}
        level = [ref.key()]
        for tier in range(1, depth + 1):
            next_level: list[tuple[int, int]] = []
            names: list[str] = []
            for key in level:
                for precedent in self._direct_precedents(key):
                    label = CellRef(
                        row=precedent[0], col=precedent[1]
                    ).a1()
                    if precedent in seen:
                        names.append(f"{label} (cycle, not followed)")
                        continue
                    seen.add(precedent)
                    next_level.append(precedent)
                    names.append(label)
            if not names:
                break
            lines.append(
                f"  level {tier}: {', '.join(sorted(set(names)))}"
            )
            level = next_level
        if len(lines) == 1:
            lines.append("  nothing; it is a source")
        return "\n".join(lines)

    def dependents(self, ref: CellRef) -> str:
        self.engine._reindex()
        direct = self.engine._dependents_of(ref.key())
        if not direct:
            return (
                f"{ref.a1()} feeds nothing; deleting it "
                "breaks no formula"
            )
        names = sorted(
            CellRef(row=key[0], col=key[1]).a1()
            for key in direct
        )
        watcher_note = ""
        watchers = [
            CellRef(row=key[0], col=key[1]).a1()
            for region, key in self.engine.range_watchers
            if region.contains(ref)
        ]
        if watchers:
            watcher_note = (
                f"; {', '.join(sorted(set(watchers)))} "
                "watch(es) through a range, the classic "
                "blind spot"
            )
        return (
            f"{ref.a1()} feeds {', '.join(names)}"
            + watcher_note
        )
