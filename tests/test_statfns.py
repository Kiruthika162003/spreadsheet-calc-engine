from __future__ import annotations

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {
    (0, 0): 2.0,
    (1, 0): 4.0,
    (2, 0): 4.0,
    (3, 0): 4.0,
    (4, 0): 5.0,
    (5, 0): 5.0,
    (6, 0): 7.0,
    (7, 0): 9.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestMedianAndMode:
    def test_the_odd_median_is_the_middle(self):
        assert run("=MEDIAN(1, 9, 5)") == 5.0

    def test_the_even_median_interpolates(self):
        assert run("=MEDIAN(1, 2, 3, 10)") == 2.5

    def test_mode_breaks_ties_deterministically(self):
        assert run("=MODE(A1:A8)") == 4.0
        assert run("=MODE(5, 5, 3, 3)") == 3.0

    def test_a_modeless_sample_says_so(self):
        outcome = run("=MODE(1, 2, 3)")
        assert outcome.code == "#N/A"
        assert "there is no mode" in outcome.note


class TestTheDenominatorDecision:
    def test_the_textbook_eight_values(self):
        assert run("=STDEVP(A1:A8)") == 2.0
        sample = run("=STDEV(A1:A8)")
        assert sample == pytest.approx(2.138, abs=1e-3)

    def test_one_number_has_no_sample_deviation(self):
        outcome = run("=STDEV(5)")
        assert outcome.code == "#NUM!"
        assert "does not parse with fewer" in outcome.note

    def test_the_population_form_allows_one(self):
        assert run("=STDEVP(5)") == 0.0


class TestLargeAndSmall:
    def test_one_based_ranks_from_both_ends(self):
        assert run("=LARGE(A1:A8, 1)") == 9.0
        assert run("=LARGE(A1:A8, 3)") == 5.0
        assert run("=SMALL(A1:A8, 2)") == 4.0

    def test_the_rank_outside_the_sample_is_named(self):
        outcome = run("=LARGE(A1:A8, 99)")
        assert outcome.code == "#NUM!"
        assert "one-based like everything users type" in (
            outcome.note
        )
