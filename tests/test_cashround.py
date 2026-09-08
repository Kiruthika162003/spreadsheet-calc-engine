from __future__ import annotations

import pytest

from gridiron.cashround import round_cash
from gridiron.errors import Invalid


class TestNickelRounding:
    def test_it_snaps_to_the_nearest_nickel(self):
        assert round_cash(1.02, 0.05).rounded == 1.0
        assert round_cash(1.03, 0.05).rounded == 1.05
        assert round_cash(1.08, 0.05).rounded == 1.1

    def test_the_adjustment_reconciles(self):
        for amount in (1.02, 1.03, 1.07, 2.99):
            r = round_cash(amount, 0.05)
            assert r.rounded - r.adjustment == (
                pytest.approx(r.exact)
            )

    def test_a_penny_case(self):
        r = round_cash(2.99, 0.05)
        assert r.rounded == 3.0
        assert r.adjustment == pytest.approx(0.01)


class TestBankersTies:
    def test_a_tie_rounds_to_the_even_multiple(self):
        # 1.025 is 2.5 nickels; the even multiple is 2.
        assert round_cash(1.025, 0.05).rounded == 1.0
        # 1.075 is 21.5 nickels; the even multiple is 22.
        assert round_cash(1.075, 0.05).rounded == 1.1


class TestDenominations:
    def test_dime_rounding(self):
        assert round_cash(1.04, 0.10).rounded == 1.0
        assert round_cash(1.06, 0.10).rounded == 1.1

    def test_quarter_rounding(self):
        assert round_cash(1.10, 0.25).rounded == 1.0
        assert round_cash(1.13, 0.25).rounded == 1.25


class TestRefusals:
    def test_a_nonpositive_denomination_is_refused(self):
        with pytest.raises(Invalid) as caught:
            round_cash(1.0, 0.0)
        assert "division by nothing" in str(caught.value)
