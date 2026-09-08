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
    (0, 1): 1.0,
    (1, 1): 2.0,
    (2, 1): 3.0,
    (3, 1): 4.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(parse_formula(formula), lookup, full_table)


class TestVariance:
    def test_population_matches_stdevp_squared(self):
        assert run("=VARP(A1:A8)") == pytest.approx(4.0)

    def test_sample_divides_by_n_minus_one(self):
        assert run("=VAR(A1:A8)") == pytest.approx(
            32.0 / 7.0
        )

    def test_devsq_is_the_shared_numerator(self):
        assert run("=DEVSQ(A1:A8)") == pytest.approx(32.0)

    def test_one_value_has_no_sample_variance(self):
        outcome = run("=VAR(5)")
        assert outcome.code == "#NUM!"

    def test_population_variance_allows_one(self):
        assert run("=VARP(5)") == 0.0


class TestOtherSpreads:
    def test_avedev_is_the_mean_absolute_deviation(self):
        assert run("=AVEDEV(A1:A8)") == pytest.approx(1.5)

    def test_covariance_with_itself_is_the_variance(self):
        assert run("=COVAR(B1:B4, B1:B4)") == pytest.approx(
            1.25
        )

    def test_mismatched_series_do_not_pair(self):
        outcome = run("=COVAR(A1:A8, B1:B4)")
        assert outcome.code == "#N/A"
        assert "the wrong points" in outcome.note


class TestSkew:
    def test_a_right_skewed_sample_is_positive(self):
        assert run("=SKEW(A1:A8)") > 0

    def test_a_flat_line_has_no_skew(self):
        outcome = run("=SKEW(3, 3, 3)")
        assert outcome.code == "#DIV/0!"

    def test_skew_needs_three_points(self):
        outcome = run("=SKEW(1, 2)")
        assert outcome.code == "#NUM!"
        assert "at least 3" in outcome.note
