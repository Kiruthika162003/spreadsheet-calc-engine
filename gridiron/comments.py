"""Cell comments: threads that follow their cell and orphan loudly when it dies.

A comment is attached to a conversation about a cell, not to
a pair of coordinates, so the anchor must move when rows
move: insert a row above the discussion and the thread rides
its cell downward, delete a row below and it rides up
untouched. The interesting case is deletion of the anchored
row itself, and the honest answer is neither silent removal,
which erases a conversation someone thought worth having,
nor silent survival at new coordinates, which pins the
discussion of one cell onto a stranger. Threads on deleted
rows become orphans: still readable, marked with the address
they used to watch, excluded from the per-cell lookup, and
counted in the census so a cleanup pass can find them.
Replies append to their thread in order with an author on
every entry, because an unattributed margin note in a shared
workbook is a rumor. Resolution is a state, not a deletion,
a resolved thread stays until someone purges it on purpose,
and purging reports how many conversations it destroyed,
resolved and orphaned counted separately, since those are
different kinds of goodbye.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef


@dataclass
class Entry:
    author: str
    text: str


@dataclass
class Thread:
    anchor_key: tuple[int, int] | None
    lost_address: str | None
    entries: list[Entry] = field(default_factory=list)
    resolved: bool = False

    def address(self) -> str:
        if self.anchor_key is None:
            return f"orphaned from {self.lost_address}"
        ref = CellRef(
            row=self.anchor_key[0], col=self.anchor_key[1]
        )
        return ref.a1()


@dataclass
class CommentBoard:
    threads: list[Thread] = field(default_factory=list)

    def start(
        self, ref: CellRef, author: str, text: str
    ) -> Thread:
        if not author.strip():
            raise Invalid(
                "a comment needs an author; an unattributed "
                "margin note in a shared workbook is a rumor"
            )
        if not text.strip():
            raise Invalid("an empty comment says nothing")
        existing = self.thread_at(ref)
        if existing is not None:
            raise Invalid(
                f"{ref.a1()} already carries a thread; "
                "reply to it instead of starting a rival"
            )
        thread = Thread(
            anchor_key=ref.key(), lost_address=None
        )
        thread.entries.append(
            Entry(author=author.strip(), text=text.strip())
        )
        self.threads.append(thread)
        return thread

    def thread_at(self, ref: CellRef) -> Thread | None:
        for thread in self.threads:
            if thread.anchor_key == ref.key():
                return thread
        return None

    def reply(
        self, ref: CellRef, author: str, text: str
    ) -> str:
        thread = self.thread_at(ref)
        if thread is None:
            raise Missing(
                f"{ref.a1()} carries no thread to reply to"
            )
        if not author.strip():
            raise Invalid(
                "a reply needs an author; an unattributed "
                "margin note in a shared workbook is a rumor"
            )
        thread.entries.append(
            Entry(author=author.strip(), text=text.strip())
        )
        return (
            f"{ref.a1()} now holds {len(thread.entries)} "
            "entr(ies)"
        )

    def resolve(self, ref: CellRef) -> str:
        thread = self.thread_at(ref)
        if thread is None:
            raise Missing(
                f"{ref.a1()} carries no thread to resolve"
            )
        if thread.resolved:
            return f"{ref.a1()} was already resolved"
        thread.resolved = True
        return (
            f"{ref.a1()} resolved after "
            f"{len(thread.entries)} entr(ies); the thread "
            "stays until purged on purpose"
        )

    def rows_inserted(self, at_row: int, count: int) -> int:
        moved = 0
        for thread in self.threads:
            if thread.anchor_key is None:
                continue
            row, col = thread.anchor_key
            if row >= at_row:
                thread.anchor_key = (row + count, col)
                moved += 1
        return moved

    def rows_deleted(self, at_row: int, count: int) -> int:
        touched = 0
        for thread in self.threads:
            if thread.anchor_key is None:
                continue
            row, col = thread.anchor_key
            if at_row <= row < at_row + count:
                thread.lost_address = CellRef(
                    row=row, col=col
                ).a1()
                thread.anchor_key = None
                touched += 1
            elif row >= at_row + count:
                thread.anchor_key = (row - count, col)
                touched += 1
        return touched

    def orphans(self) -> list[Thread]:
        return [
            thread
            for thread in self.threads
            if thread.anchor_key is None
        ]

    def census(self) -> str:
        open_count = sum(
            1
            for thread in self.threads
            if not thread.resolved
            and thread.anchor_key is not None
        )
        resolved = sum(
            1 for thread in self.threads if thread.resolved
        )
        orphaned = len(self.orphans())
        return (
            f"{len(self.threads)} thread(s): {open_count} "
            f"open, {resolved} resolved, {orphaned} "
            "orphaned"
        )

    def purge(self) -> str:
        resolved = [
            thread
            for thread in self.threads
            if thread.resolved
        ]
        orphaned = [
            thread
            for thread in self.threads
            if thread.anchor_key is None
            and not thread.resolved
        ]
        keep = [
            thread
            for thread in self.threads
            if not thread.resolved
            and thread.anchor_key is not None
        ]
        self.threads = keep
        return (
            f"purged {len(resolved)} resolved and "
            f"{len(orphaned)} orphaned thread(s); those "
            "are different kinds of goodbye"
        )
