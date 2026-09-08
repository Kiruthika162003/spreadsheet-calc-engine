from __future__ import annotations

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

# A perfect line y = 2x + 1 in columns A (x) and B (y),
# and a vertical scatter in column C (all x equal).
WORLD = {
    (0, 0): 1.0,
    (1, 0): 2.0,
    (2, 0): 3.0,
    (3, 0): 4.0,
    (0, 1): 3.0,
    (1, 1): 5.0,
    (2, 1): 7.0,
    (3, 1): 9.0,
    (0, 2): 5.0,
    (1, 2): 5.0,
    (2, 2): 5.0,
    (3, 2): 5.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestThePerfectLine:
    def test_slope_and_intercept(self):
        assert run("=SLOPE(B1:B4, A1:A4)") == (
            pytest.approx(2.0)
        )
        assert run("=INTERCEPT(B1:B4, A1:A4)") == (
            pytest.approx(1.0)
        )

    def test_a_perfect_fit_has_rsq_one(self):
        assert run("=RSQ(B1:B4, A1:A4)") == (
            pytest.approx(1.0)
        )
        assert run("=CORREL(A1:A4, B1:B4)") == (
            pytest.approx(1.0)
        )

    def test_correlation_is_clamped_not_over_one(self):
        assert run("=CORREL(A1:A4, B1:B4)") <= 1.0

    def test_forecast_evaluates_the_line(self):
        assert run("=FORECAST(10, B1:B4, A1:A4)") == (
            pytest.approx(21.0)
        )


class TestRefusals:
    def test_a_single_point_is_no_line(self):
        outcome = run("=SLOPE(B1:B1, A1:A1)")
        assert outcome.code == "#NUM!"
        assert "at least two points" in outcome.note

    def test_a_vertical_scatter_has_no_slope(self):
        outcome = run("=SLOPE(B1:B4, C1:C4)")
        assert outcome.code == "#DIV/0!"
        assert "vertical scatter" in outcome.note

    def test_mismatched_lengths_do_not_pair(self):
        outcome = run("=SLOPE(B1:B4, A1:A3)")
        assert outcome.code == "#N/A"
        assert "pairing demands they pair" in outcome.note

    def test_a_scalar_argument_is_refused(self):
        outcome = run("=SLOPE(5, A1:A4)")
        assert outcome.code == "#VALUE!"
        assert "two ranges" in outcome.note


class TestAnImperfectFit:
    def test_a_noisy_line_still_fits(self):
        world = dict(WORLD)
        world[(3, 1)] = 8.0  # nudge the last y off the line

        def noisy(ref: CellRef):
            return world.get(ref.key())

        slope = evaluate(
            parse_formula("=SLOPE(B1:B4, A1:A4)"),
            noisy,
            full_table,
        )
        rsq = evaluate(
            parse_formula("=RSQ(B1:B4, A1:A4)"),
            noisy,
            full_table,
        )
        assert 1.5 < slope < 2.0
        assert 0.9 < rsq < 1.0
