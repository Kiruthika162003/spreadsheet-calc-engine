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


class TestRoots:
    def test_sqrt_lives_in_the_base_module_not_here(self):
        assert run("=SQRT(144)") == 12.0
        outcome = run("=SQRT(-4)")
        assert outcome.code == "#NUM!"
        assert "complex plane" in outcome.note


class TestLogs:
    def test_ln_and_exp_are_inverse(self):
        assert run("=LN(EXP(1))") == pytest.approx(1.0)

    def test_log_defaults_to_base_ten(self):
        assert run("=LOG(1000)") == pytest.approx(3.0)

    def test_log_takes_an_explicit_base(self):
        assert run("=LOG(8, 2)") == pytest.approx(3.0)

    def test_ln_of_zero_is_undefined(self):
        outcome = run("=LN(0)")
        assert outcome.code == "#NUM!"

    def test_base_one_is_division_in_disguise(self):
        outcome = run("=LOG(10, 1)")
        assert outcome.code == "#NUM!"
        assert "division by zero" in outcome.note


class TestTrig:
    def test_radians_are_the_default_unit(self):
        assert run("=SIN(0)") == pytest.approx(0.0)
        assert run("=COS(0)") == pytest.approx(1.0)

    def test_the_bridges_convert_explicitly(self):
        assert run("=RADIANS(180)") == pytest.approx(math.pi)
        assert run("=SIN(RADIANS(90))") == pytest.approx(1.0)

    def test_degrees_turns_radians_back(self):
        assert run("=DEGREES(3.141592653589793)") == (
            pytest.approx(180.0)
        )


class TestWholeNumberFamily:
    def test_gcd_and_lcm_of_a_pair(self):
        assert run("=GCD(12, 18)") == 6.0
        assert run("=LCM(4, 6)") == 12.0

    def test_lcm_of_many_composes(self):
        assert run("=LCM(2, 3, 4)") == 12.0

    def test_a_fraction_does_not_parse(self):
        outcome = run("=GCD(2.5, 5)")
        assert outcome.code == "#NUM!"
        assert "does not parse" in outcome.note

    def test_lcm_with_a_zero_is_zero(self):
        assert run("=LCM(0, 5)") == 0.0


class TestCombinatorics:
    def test_factorial_grows(self):
        assert run("=FACT(5)") == 120.0

    def test_combin_chooses(self):
        assert run("=COMBIN(5, 2)") == 10.0

    def test_choosing_more_than_exists_is_invalid(self):
        outcome = run("=COMBIN(3, 5)")
        assert outcome.code == "#NUM!"
        assert "invalid one" in outcome.note

    def test_factorial_of_a_negative_is_undefined(self):
        outcome = run("=FACT(-1)")
        assert outcome.code == "#NUM!"
