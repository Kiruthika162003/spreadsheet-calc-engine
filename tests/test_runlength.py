from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.runlength import (
    compression_ratio,
    decode,
    encode,
)


class TestEncode:
    def test_it_collapses_runs(self):
        assert encode(
            ["open", "open", "open", "closed", "closed"]
        ) == [("open", 3), ("closed", 2)]

    def test_a_broken_run_restarts(self):
        assert encode(["a", "a", "b", "a"]) == [
            ("a", 2),
            ("b", 1),
            ("a", 1),
        ]

    def test_number_and_text_stay_separate(self):
        assert encode([5, 5, "5"]) == [(5, 2), ("5", 1)]


class TestRoundTrip:
    def test_the_law_holds(self):
        cases = [
            [],
            [1],
            [1, 1, 1],
            ["a", "b", "c"],
            [True, True, False, True],
            [1, 1, "1", 1.0],
        ]
        for case in cases:
            assert decode(encode(case)) == case


class TestDecodeRefusals:
    def test_a_zero_count_is_refused(self):
        with pytest.raises(Invalid) as caught:
            decode([("a", 0)])
        assert "below one is corruption" in str(caught.value)

    def test_a_negative_count_is_refused(self):
        with pytest.raises(Invalid):
            decode([("a", -3)])


class TestRatio:
    def test_a_compressible_column(self):
        assert compression_ratio(
            ["x", "x", "x", "x"]
        ) == 0.25

    def test_an_incompressible_column(self):
        assert compression_ratio(["a", "b", "c"]) == 1.0

    def test_empty_is_one(self):
        assert compression_ratio([]) == 1.0
