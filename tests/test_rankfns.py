from __future__ import annotations

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import catalog, full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {
    (0, 0): 1.0,
    (1, 0): 2.0,
    (2, 0): 3.0,
    (3, 0): 4.0,
    (0, 1): 88.0,
    (1, 1): 92.0,
    (2, 1): 92.0,
    (3, 1): 79.0,
    (4, 1): 61.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestPercentile:
    def test_the_midpoint_interpolates(self):
        assert run("=PERCENTILE(A1:A4, 0.5)") == 2.5

    def test_the_ends_are_min_and_max(self):
        assert run("=PERCENTILE(A1:A4, 0)") == 1.0
        assert run("=PERCENTILE(A1:A4, 1)") == 4.0

    def test_a_fractional_position_lands_between(self):
        assert run("=PERCENTILE(A1:A4, 0.25)") == 1.75

    def test_k_outside_the_unit_interval_refuses(self):
        outcome = run("=PERCENTILE(A1:A4, 1.5)")
        assert outcome.code == "#NUM!"
        assert "fraction of the way through" in outcome.note

    def test_no_values_is_not_a_question(self):
        outcome = run("=PERCENTILE(C1:C3, 0.5)")
        assert outcome.code == "#NUM!"


class TestQuartile:
    def test_the_quarters_match_percentile(self):
        assert run("=QUARTILE(A1:A4, 0)") == 1.0
        assert run("=QUARTILE(A1:A4, 2)") == 2.5
        assert run("=QUARTILE(A1:A4, 4)") == 4.0

    def test_a_fifth_quarter_does_not_exist(self):
        outcome = run("=QUARTILE(A1:A4, 5)")
        assert outcome.code == "#NUM!"
        assert "0 (minimum) to 4 (maximum)" in outcome.note


class TestRank:
    def test_two_silvers_mean_no_bronze(self):
        assert run("=RANK(92, B1:B5)") == 1.0
        assert run("=RANK(88, B1:B5)") == 3.0

    def test_the_order_flag_flips_the_table(self):
        assert run("=RANK(61, B1:B5, 1)") == 1.0
        assert run("=RANK(92, B1:B5, 1)") == 4.0

    def test_an_absent_value_is_not_guessed(self):
        outcome = run("=RANK(90, B1:B5)")
        assert outcome.code == "#N/A"
        assert "nearest neighbor" in outcome.note


class TestPercentrank:
    def test_the_inverse_of_percentile(self):
        assert run("=PERCENTRANK(A1:A4, 2.5)") == 0.5
        assert run("=PERCENTRANK(A1:A4, 1)") == 0.0
        assert run("=PERCENTRANK(A1:A4, 4)") == 1.0

    def test_no_silent_rounding_to_three_decimals(self):
        outcome = run("=PERCENTRANK(A1:A4, 1.1)")
        assert outcome == pytest.approx(1 / 30)

    def test_off_the_ends_is_not_ranked(self):
        outcome = run("=PERCENTRANK(A1:A4, 9)")
        assert outcome.code == "#N/A"
        assert "off the ends" in outcome.note


class TestTrimmedAndOtherMeans:
    def test_the_trim_drops_both_ends(self):
        assert (
            run("=TRIMMEAN(B1:B5, 0.4)")
            == pytest.approx((88.0 + 92.0 + 79.0) / 3)
        )

    def test_a_zero_trim_is_the_plain_mean(self):
        assert run("=TRIMMEAN(A1:A4, 0)") == 2.5

    def test_the_floor_always_leaves_the_middle(self):
        assert run("=TRIMMEAN(A1:A4, 0.99)") == 2.5

    def test_a_fraction_of_one_refuses(self):
        outcome = run("=TRIMMEAN(A1:A4, 1)")
        assert outcome.code == "#NUM!"
        assert "[0, 1)" in outcome.note

    def test_geomean_of_powers_of_two(self):
        assert run("=GEOMEAN(2, 8)") == pytest.approx(4.0)

    def test_geomean_refuses_zero_by_name(self):
        outcome = run("=GEOMEAN(2, 0, 8)")
        assert outcome.code == "#NUM!"
        assert "wrong question" in outcome.note

    def test_harmean_of_rates(self):
        assert run("=HARMEAN(60, 40)") == pytest.approx(48.0)

    def test_harmean_refuses_a_negative(self):
        outcome = run("=HARMEAN(60, -40)")
        assert outcome.code == "#NUM!"
        assert "positive values" in outcome.note


class TestTheCatalogDoor:
    def test_the_family_is_reachable_by_name(self):
        listed = catalog()
        for name in (
            "PERCENTILE",
            "QUARTILE",
            "RANK",
            "PERCENTRANK",
            "TRIMMEAN",
            "GEOMEAN",
            "HARMEAN",
        ):
            assert name in listed
