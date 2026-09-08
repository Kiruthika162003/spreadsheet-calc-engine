from __future__ import annotations

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula


def run(formula: str):
    return evaluate(
        parse_formula(formula), lambda _r: None, full_table
    )


class TestFutureAndPresent:
    def test_fv_of_a_funded_plan_comes_back_positive(self):
        assert run("=FV(0.05, 10, -100, 0)") == (
            pytest.approx(1257.789, abs=1e-3)
        )

    def test_pv_and_fv_are_mirror_images(self):
        assert run("=PV(0.05, 10, 100, 0)") == (
            pytest.approx(-772.173, abs=1e-3)
        )

    def test_a_zero_rate_is_simple_interest(self):
        assert run("=FV(0, 10, -100, 0)") == 1000.0
        assert run("=PV(0, 10, 100, 0)") == -1000.0


class TestNperAndRate:
    def test_nper_recovers_the_term(self):
        assert run(
            "=NPER(0.05, -100, 0, 1257.789253616)"
        ) == pytest.approx(10.0, abs=1e-6)

    def test_a_zero_rate_nper_is_division(self):
        assert run("=NPER(0, -100, 0, 1000)") == 10.0

    def test_a_non_retiring_plan_does_not_converge(self):
        outcome = run("=NPER(0.05, 100, 0, 1000)")
        assert outcome.code == "#NUM!"
        assert "does not converge" in outcome.note

    def test_rate_recovers_the_periodic_rate(self):
        assert run(
            "=RATE(10, -100, 772.173492918)"
        ) == pytest.approx(0.05, abs=1e-6)

    def test_rate_refuses_an_unbalanced_band(self):
        outcome = run("=RATE(10, 100, 500)")
        assert outcome.code == "#NUM!"
        assert "never trusted" in outcome.note


class TestDepreciation:
    def test_straight_line_is_flat(self):
        assert run("=SLN(1000, 100, 5)") == 180.0

    def test_double_declining_front_loads(self):
        assert run("=DDB(1000, 100, 5, 1)") == 400.0
        assert run("=DDB(1000, 100, 5, 2)") == 240.0

    def test_ddb_never_dips_below_salvage(self):
        total = sum(
            run(f"=DDB(1000, 100, 5, {period})")
            for period in range(1, 6)
        )
        assert total == pytest.approx(900.0)

    def test_a_period_past_the_life_is_refused(self):
        outcome = run("=DDB(1000, 100, 5, 9)")
        assert outcome.code == "#NUM!"
        assert "outside an asset life" in outcome.note
