from __future__ import annotations

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

FLOWS = {
    (0, 0): -1000.0,
    (1, 0): 300.0,
    (2, 0): 400.0,
    (3, 0): 500.0,
    (4, 0): 200.0,
    (6, 0): -50.0,
    (7, 0): -60.0,
}


def lookup(ref: CellRef):
    return FLOWS.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestPmt:
    def test_the_loan_payment_leaves_your_pocket(self):
        payment = run("=PMT(0.005, 360, 300000)")
        assert payment == pytest.approx(-1798.65, abs=0.01)
        assert payment < 0

    def test_the_zero_rate_loan_divides_evenly(self):
        assert run("=PMT(0, 12, 1200)") == -100.0

    def test_zero_periods_is_refused(self):
        assert run("=PMT(0.01, 0, 100)").code == "#NUM!"


class TestNpv:
    def test_npv_discounts_from_period_one(self):
        npv = run("=NPV(0.1, A2:A5)")
        assert npv == pytest.approx(1115.57, abs=0.01)

    def test_the_course_trap_is_in_the_error_message(self):
        outcome = run("=NPV(0.1)")
        assert "outside the call, at face value" in outcome.note

    def test_the_full_project_adds_the_outlay_at_face(self):
        total = run("=A1 + NPV(0.1, A2:A5)")
        assert total == pytest.approx(115.57, abs=0.01)


class TestIrr:
    def test_irr_zeroes_the_npv(self):
        rate = run("=IRR(A1:A5)")
        assert isinstance(rate, float)
        check = run(f"=A1 + NPV({rate}, A2:A5)")
        assert check == pytest.approx(0.0, abs=1e-4)

    def test_one_signed_flows_have_no_internal_rate(self):
        outcome = run("=IRR(A7:A8)")
        assert outcome.code == "#NUM!"
        assert "most expensive number" in outcome.note
