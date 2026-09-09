from __future__ import annotations

import pytest

from gridiron.comments import CommentBoard
from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def board_with_thread() -> CommentBoard:
    board = CommentBoard()
    board.start(
        ref("B3"), "Kiruthika", "why is this negative?"
    )
    return board


class TestThreads:
    def test_a_thread_starts_with_its_first_entry(self):
        board = board_with_thread()
        thread = board.thread_at(ref("B3"))
        assert thread is not None
        assert thread.entries[0].author == "Kiruthika"
        assert thread.address() == "B3"

    def test_replies_append_in_order(self):
        board = board_with_thread()
        verdict = board.reply(
            ref("B3"), "Priya", "sign convention from PMT"
        )
        assert "2 entr(ies)" in verdict
        thread = board.thread_at(ref("B3"))
        assert [e.author for e in thread.entries] == [
            "Kiruthika",
            "Priya",
        ]

    def test_a_rival_thread_is_refused(self):
        board = board_with_thread()
        with pytest.raises(Invalid) as caught:
            board.start(ref("B3"), "Priya", "also...")
        assert "rival" in str(caught.value)

    def test_an_unattributed_note_is_a_rumor(self):
        board = CommentBoard()
        with pytest.raises(Invalid) as caught:
            board.start(ref("A1"), "  ", "hello")
        assert "rumor" in str(caught.value)

    def test_replying_to_silence_is_named(self):
        board = CommentBoard()
        with pytest.raises(Missing) as caught:
            board.reply(ref("Z9"), "Priya", "anyone?")
        assert "no thread" in str(caught.value)


class TestRowMoves:
    def test_insertion_above_rides_the_thread_down(self):
        board = board_with_thread()
        moved = board.rows_inserted(at_row=1, count=2)
        assert moved == 1
        assert board.thread_at(ref("B5")) is not None
        assert board.thread_at(ref("B3")) is None

    def test_insertion_below_leaves_it_alone(self):
        board = board_with_thread()
        moved = board.rows_inserted(at_row=5, count=3)
        assert moved == 0
        assert board.thread_at(ref("B3")) is not None

    def test_deleting_the_anchored_row_orphans_loudly(self):
        board = board_with_thread()
        board.rows_deleted(at_row=2, count=1)
        assert board.thread_at(ref("B3")) is None
        orphans = board.orphans()
        assert len(orphans) == 1
        assert orphans[0].address() == "orphaned from B3"
        assert orphans[0].entries[0].text == (
            "why is this negative?"
        )

    def test_deletion_above_rides_the_thread_up(self):
        board = board_with_thread()
        board.rows_deleted(at_row=0, count=1)
        assert board.thread_at(ref("B2")) is not None


class TestLifecycle:
    def test_resolution_is_a_state_not_a_deletion(self):
        board = board_with_thread()
        verdict = board.resolve(ref("B3"))
        assert "stays until purged" in verdict
        assert board.thread_at(ref("B3")).resolved

    def test_the_census_counts_three_kinds(self):
        board = board_with_thread()
        board.start(ref("C1"), "Priya", "check the total")
        board.resolve(ref("C1"))
        board.start(ref("D8"), "Anu", "stale link?")
        board.rows_deleted(at_row=7, count=1)
        assert board.census() == (
            "3 thread(s): 1 open, 1 resolved, 1 orphaned"
        )

    def test_purging_reports_both_goodbyes(self):
        board = board_with_thread()
        board.start(ref("C1"), "Priya", "check the total")
        board.resolve(ref("C1"))
        board.start(ref("D8"), "Anu", "stale link?")
        board.rows_deleted(at_row=7, count=1)
        verdict = board.purge()
        assert "1 resolved and 1 orphaned" in verdict
        assert board.census() == (
            "1 thread(s): 1 open, 0 resolved, 0 orphaned"
        )
