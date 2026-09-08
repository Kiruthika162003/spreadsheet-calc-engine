from __future__ import annotations

import math

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula


def run(formula: str):
    return evaluate(
        parse_formula(formula), lambda _r: None, full_table
    )


class TestRoundingFamily:
    def test_the_four_roundings_differ(self):
        # ROUNDUP jumps 2.1 to 3 where ROUND and TRUNC keep
        # 2; the base ROUND uses banker's rounding, so 2.5
        # lands on the even 2, not 3.
        assert run("=ROUNDUP(2.1, 0)") == 3.0
        assert run("=ROUNDDOWN(2.9, 0)") == 2.0
        assert run("=TRUNC(3.7)") == 3.0
        assert run("=ROUND(2.6, 0)") == 3.0
        assert run("=ROUND(2.5, 0)") == 2.0

    def test_roundup_goes_away_from_zero(self):
        assert run("=ROUNDUP(-2.1, 0)") == -3.0
        assert run("=ROUNDDOWN(-2.9, 0)") == -2.0

    def test_trunc_keeps_digits(self):
        assert run("=TRUNC(3.14159, 2)") == pytest.approx(
            3.14
        )

    def test_mround_to_the_nearest_multiple(self):
        assert run("=MROUND(10, 3)") == 9.0
        assert run("=MROUND(11, 3)") == 12.0

    def test_mround_refuses_a_sign_clash(self):
        outcome = run("=MROUND(5, -2)")
        assert outcome.code == "#NUM!"
        assert "across zero" in outcome.note


class TestSignAndPower:
    def test_sign_is_three_valued(self):
        assert run("=SIGN(-5)") == -1.0
        assert run("=SIGN(0)") == 0.0
        assert run("=SIGN(9)") == 1.0

    def test_power_matches_the_operator(self):
        assert run("=POWER(2, 10)") == 1024.0

    def test_a_complex_power_is_refused(self):
        outcome = run("=POWER(-8, 0.5)")
        assert outcome.code == "#NUM!"
        assert "complex" in outcome.note


class TestInverseTrig:
    def test_arcsine_and_arccosine(self):
        assert run("=ASIN(1)") == pytest.approx(
            math.pi / 2
        )
        assert run("=ACOS(1)") == pytest.approx(0.0)

    def test_arcsine_refuses_outside_its_domain(self):
        outcome = run("=ASIN(2)")
        assert outcome.code == "#NUM!"
        assert "[-1, 1]" in outcome.note

    def test_atan2_takes_x_then_y(self):
        # x=1, y=1 is 45 degrees.
        assert run("=ATAN2(1, 1)") == pytest.approx(
            math.pi / 4
        )

    def test_atan2_of_the_origin_is_undefined(self):
        outcome = run("=ATAN2(0, 0)")
        assert outcome.code == "#DIV/0!"


class TestConstantsAndHyperbolics:
    def test_pi_takes_no_arguments(self):
        assert run("=PI()") == pytest.approx(math.pi)
        outcome = run("=PI(1)")
        assert outcome.code == "#VALUE!"

    def test_the_hyperbolics(self):
        assert run("=SINH(0)") == pytest.approx(0.0)
        assert run("=COSH(0)") == pytest.approx(1.0)
        assert run("=TANH(0)") == pytest.approx(0.0)
