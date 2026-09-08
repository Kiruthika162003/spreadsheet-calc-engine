from __future__ import annotations

import pytest

from gridiron.fuzzymatch import (
    best_match,
    edit_distance,
    similarity,
)


class TestEditDistance:
    def test_the_classic_kitten_sitting(self):
        assert edit_distance("kitten", "sitting") == 3

    def test_identical_strings_are_zero(self):
        assert edit_distance("same", "same") == 0

    def test_against_empty_is_the_length(self):
        assert edit_distance("abc", "") == 3
        assert edit_distance("", "abcd") == 4


class TestSimilarity:
    def test_one_edit_in_five(self):
        assert similarity("smith", "smyth") == pytest.approx(
            0.8
        )

    def test_identical_is_one(self):
        assert similarity("x", "x") == 1.0

    def test_two_empties_are_one(self):
        assert similarity("", "") == 1.0


class TestBestMatch:
    def test_it_finds_the_closest(self):
        match = best_match(
            "Smyth", ["Smith", "Jones", "Brown"]
        )
        assert match.candidate == "Smith"
        assert match.score == pytest.approx(0.8)

    def test_it_abstains_below_the_threshold(self):
        assert (
            best_match("Zzzq", ["Smith", "Jones"]) is None
        )

    def test_case_is_folded(self):
        match = best_match("ADA", ["ada", "bob"])
        assert match.candidate == "ada"
        assert match.score == 1.0

    def test_a_tie_prefers_the_earlier_candidate(self):
        # "cat" is distance 1 from both "car" and "can".
        match = best_match(
            "cat", ["car", "can"], threshold=0.6
        )
        assert match.candidate == "car"

    def test_the_threshold_is_adjustable(self):
        loose = best_match(
            "Zx", ["Ax"], threshold=0.4
        )
        assert loose is not None
        assert loose.candidate == "Ax"
