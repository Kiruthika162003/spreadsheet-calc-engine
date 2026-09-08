from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.payroll import run_payroll
from gridiron.taxbrackets import Bracket

BRACKETS = [Bracket(0.0, 0.10), Bracket(10000.0, 0.20)]


class TestTheSequence:
    def test_pretax_reduces_the_taxable_base(self):
        stub = run_payroll(
            50000.0, [5000.0], BRACKETS, [1000.0]
        )
        assert stub.taxable == 45000.0

    def test_tax_is_on_the_reduced_base(self):
        stub = run_payroll(
            50000.0, [5000.0], BRACKETS, [1000.0]
        )
        # 10000 at 10% plus 35000 at 20%.
        assert stub.tax == 8000.0

    def test_net_is_after_everything(self):
        stub = run_payroll(
            50000.0, [5000.0], BRACKETS, [1000.0]
        )
        assert stub.net == 36000.0

    def test_the_paystub_reconciles(self):
        stub = run_payroll(
            50000.0, [5000.0], BRACKETS, [1000.0]
        )
        assert stub.reconciles()

    def test_pretax_matters(self):
        with_pretax = run_payroll(
            50000.0, [5000.0], BRACKETS, []
        )
        without = run_payroll(
            50000.0, [], BRACKETS, [5000.0]
        )
        # The same 5000, pre-tax versus post-tax, leaves more
        # take-home when it is pre-tax.
        assert with_pretax.net > without.net


class TestRefusals:
    def test_pretax_over_gross_is_refused(self):
        with pytest.raises(Invalid) as caught:
            run_payroll(1000.0, [2000.0], BRACKETS, [])
        assert "owe the employer" in str(caught.value)

    def test_a_negative_paycheck_is_refused(self):
        with pytest.raises(Invalid) as caught:
            run_payroll(
                20000.0, [], BRACKETS, [19000.0]
            )
        assert "negative paycheck" in str(caught.value)

    def test_a_negative_deduction_is_refused(self):
        with pytest.raises(Invalid):
            run_payroll(50000.0, [-100.0], BRACKETS, [])

    def test_negative_gross_is_refused(self):
        with pytest.raises(Invalid):
            run_payroll(-1.0, [], BRACKETS, [])
