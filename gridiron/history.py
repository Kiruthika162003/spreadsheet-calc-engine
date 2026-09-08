"""Cell history: who changed B7, when in edit-time, and from what to what.

The question that ends spreadsheet arguments is not what B7
holds but what it held, and the ledger answers with entries
recorded at edit time: author, sequence number instead of a
wall clock because this package owns no clock, the value or
formula displaced, and the one that replaced it. Blame is
the read side, the latest author per cell, and the diff
between two sequence points reconstructs what a reviewer
would have seen, which turns "someone changed the tax rate"
into "edit 41, taxrate, 0.19 to 0.21", a sentence with a
defendant. The ledger is append-only by construction, and
an empty history for a cell is itself an answer: nobody
ever touched it, which for some numbers is the most
reassuring sentence an audit can produce.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.values import Value, render


@dataclass(frozen=True)
class Entry:
    sequence: int
    author: str
    ref_a1: str
    before: str
    after: str


@dataclass
class HistoryLedger:
    sheet: Sheet
    entries: list[Entry] = field(default_factory=list)

    def _describe(self, ref: CellRef) -> str:
        cell = self.sheet.cell(ref)
        if cell is None:
            return "(empty)"
        if cell.is_formula():
            return cell.formula_text
        return render(cell.literal)

    def record_literal(
        self, author: str, ref: CellRef, value: Value
    ) -> None:
        if not author.strip():
            raise Invalid("edits carry an author or they wait")
        before = self._describe(ref)
        self.sheet.set_literal(ref, value)
        self.entries.append(
            Entry(
                sequence=len(self.entries) + 1,
                author=author,
                ref_a1=ref.a1(),
                before=before,
                after=self._describe(ref),
            )
        )

    def record_formula(
        self, author: str, ref: CellRef, text: str
    ) -> None:
        if not author.strip():
            raise Invalid("edits carry an author or they wait")
        before = self._describe(ref)
        self.sheet.set_formula(ref, text)
        self.entries.append(
            Entry(
                sequence=len(self.entries) + 1,
                author=author,
                ref_a1=ref.a1(),
                before=before,
                after=self._describe(ref),
            )
        )

    def blame(self, ref: CellRef) -> str:
        target = ref.a1()
        for entry in reversed(self.entries):
            if entry.ref_a1 == target:
                return (
                    f"{target}: last touched by "
                    f"{entry.author} at edit "
                    f"{entry.sequence}, {entry.before} to "
                    f"{entry.after}; a sentence with a "
                    "defendant"
                )
        return (
            f"{target}: nobody ever touched it, which for "
            "some numbers is the most reassuring sentence an "
            "audit can produce"
        )

    def diff_since(self, sequence: int) -> str:
        recent = [
            entry
            for entry in self.entries
            if entry.sequence > sequence
        ]
        if not recent:
            return f"nothing changed since edit {sequence}"
        lines = [
            f"{len(recent)} edit(s) since {sequence}:"
        ]
        for entry in recent:
            lines.append(
                f"  {entry.sequence}. {entry.author}: "
                f"{entry.ref_a1} {entry.before} to "
                f"{entry.after}"
            )
        return "\n".join(lines)
