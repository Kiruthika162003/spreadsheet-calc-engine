from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.intervals import Interval, conflicts, gaps, merge


class TestMerge:
    def test_overlapping_intervals_combine(self):
        merged = merge(
            [Interval(1, 4), Interval(3, 6), Interval(8, 9)]
        )
        assert [(m.start, m.end) for m in merged] == [
            (1, 6),
            (8, 9),
        ]

    def test_touching_intervals_are_contiguous(self):
        merged = merge([Interval(1, 3), Interval(3, 5)])
        assert [(m.start, m.end) for m in merged] == [(1, 5)]

    def test_the_input_is_not_mutated(self):
        original = [Interval(3, 5), Interval(1, 2)]
        merge(original)
        assert original[0].start == 3

    def test_empty_merges_to_empty(self):
        assert merge([]) == []


class TestGaps:
    def test_the_holes_between_blocks(self):
        holes = gaps(
            [Interval(1, 3), Interval(7, 9)], 0, 10
        )
        assert [(g.start, g.end) for g in holes] == [
            (0, 1),
            (3, 7),
            (9, 10),
        ]

    def test_no_gaps_when_fully_covered(self):
        assert gaps([Interval(0, 10)], 0, 10) == []

    def test_a_reversed_envelope_is_refused(self):
        with pytest.raises(Invalid):
            gaps([], 10, 0)


class TestConflicts:
    def test_overlapping_bookings_name_the_pair(self):
        found = conflicts(
            [
                Interval(1, 4, "x"),
                Interval(3, 6, "y"),
                Interval(8, 9, "z"),
            ]
        )
        assert found == [("x", "y")]

    def test_touching_bookings_do_not_conflict(self):
        found = conflicts(
            [Interval(1, 3, "a"), Interval(3, 5, "b")]
        )
        assert found == []

    def test_three_way_overlap(self):
        found = conflicts(
            [
                Interval(1, 5, "a"),
                Interval(2, 6, "b"),
                Interval(3, 7, "c"),
            ]
        )
        assert ("a", "b") in found
        assert ("a", "c") in found
        assert ("b", "c") in found


class TestValidation:
    def test_a_reversed_interval_is_refused(self):
        with pytest.raises(Invalid) as caught:
            Interval(5, 2)
        assert "ends before it begins" in str(caught.value)
