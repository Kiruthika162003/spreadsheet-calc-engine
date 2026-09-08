from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.rankings import (
    dense_rank,
    ordinal_rank,
    rank_column,
    standard_rank,
)

SCORES = [100.0, 90.0, 90.0, 80.0]


class TestTieConventions:
    def test_standard_skips_after_a_tie(self):
        assert standard_rank(SCORES, descending=True) == [
            1.0,
            2.0,
            2.0,
            4.0,
        ]

    def test_dense_does_not_skip(self):
        assert dense_rank(SCORES, descending=True) == [
            1.0,
            2.0,
            2.0,
            3.0,
        ]

    def test_ordinal_breaks_ties_by_position(self):
        assert ordinal_rank(SCORES, descending=True) == [
            1.0,
            2.0,
            3.0,
            4.0,
        ]


class TestDirection:
    def test_ascending_is_the_default(self):
        assert standard_rank([30.0, 10.0, 20.0]) == [
            3.0,
            1.0,
            2.0,
        ]

    def test_the_flag_reverses_without_a_copy(self):
        ascending = standard_rank([1.0, 2.0, 3.0])
        descending = standard_rank(
            [1.0, 2.0, 3.0], descending=True
        )
        assert ascending == [1.0, 2.0, 3.0]
        assert descending == [3.0, 2.0, 1.0]


class TestAlignmentAndGaps:
    def test_a_rank_column_lines_up(self):
        values = [5.0, None, 3.0, 8.0]
        ranks = standard_rank(values)
        assert len(ranks) == len(values)
        assert ranks[1] is None

    def test_a_blank_is_not_ranked(self):
        ranks = dense_rank([5.0, None, 10.0])
        assert ranks == [1.0, None, 2.0]


class TestDispatch:
    def test_rank_column_routes_by_name(self):
        assert rank_column(
            SCORES, "dense", descending=True
        ) == [1.0, 2.0, 2.0, 3.0]

    def test_an_unknown_method_is_refused(self):
        with pytest.raises(Invalid) as caught:
            rank_column(SCORES, "percentile")
        assert "standard, dense, or ordinal" in str(
            caught.value
        )
