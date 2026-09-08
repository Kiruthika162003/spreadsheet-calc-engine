from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.loanfns import cumipmt, cumprinc, ipmt, ppmt

RATE, NPER, PV = 0.01, 12, 1000.0


class TestTheSplit:
    def test_interest_and_principal_sum_to_the_payment(self):
        for period in range(1, NPER + 1):
            payment = ipmt(RATE, period, NPER, PV) + ppmt(
                RATE, period, NPER, PV
            )
            # Every period's split adds back to one constant.
            assert payment == pytest.approx(
                ipmt(RATE, 1, NPER, PV)
                + ppmt(RATE, 1, NPER, PV)
            )

    def test_early_interest_exceeds_late(self):
        assert abs(ipmt(RATE, 1, NPER, PV)) > abs(
            ipmt(RATE, 12, NPER, PV)
        )

    def test_the_first_interest_is_on_the_full_balance(self):
        assert ipmt(RATE, 1, NPER, PV) == pytest.approx(
            -10.0
        )


class TestCumulative:
    def test_cumulative_principal_repays_the_loan(self):
        assert cumprinc(RATE, NPER, PV, 1, NPER) == (
            pytest.approx(-PV)
        )

    def test_cumulative_interest_is_the_total_cost(self):
        total = cumipmt(
            RATE, NPER, PV, 1, NPER
        ) + cumprinc(RATE, NPER, PV, 1, NPER)
        # Interest plus principal equals all the payments.
        assert total == pytest.approx(12 * -88.8488, abs=0.01)

    def test_a_partial_range(self):
        first_half = cumprinc(RATE, NPER, PV, 1, 6)
        second_half = cumprinc(RATE, NPER, PV, 7, 12)
        assert (
            first_half + second_half
            == pytest.approx(-PV)
        )


class TestRefusals:
    def test_a_period_outside_the_loan(self):
        with pytest.raises(Invalid) as caught:
            ipmt(RATE, 13, NPER, PV)
        assert "no payment there" in str(caught.value)

    def test_a_reversed_range(self):
        with pytest.raises(Invalid) as caught:
            cumipmt(RATE, NPER, PV, 6, 3)
        assert "backward" in str(caught.value)
