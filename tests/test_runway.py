from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.runway import compute_runway


class TestBurning:
    def test_the_months_of_runway(self):
        r = compute_runway(100000.0, 20000.0, 3000.0)
        assert r.net_burn == 17000.0
        assert r.months == pytest.approx(
            100000.0 / 17000.0
        )

    def test_the_whole_months_floor(self):
        # 5.88 months means 5 are certain; the sixth is a
        # gamble on timing, not runway.
        r = compute_runway(100000.0, 20000.0, 3000.0)
        assert r.whole_months == 5
        assert r.runs_out()

    def test_revenue_extends_the_runway(self):
        without = compute_runway(100000.0, 20000.0, 0.0)
        with_rev = compute_runway(
            100000.0, 20000.0, 10000.0
        )
        assert with_rev.months > without.months


class TestCashFlowPositive:
    def test_zero_burn_never_runs_out(self):
        r = compute_runway(50000.0, 5000.0, 5000.0)
        assert not r.runs_out()
        assert r.months is None

    def test_a_profit_never_runs_out(self):
        r = compute_runway(50000.0, 5000.0, 8000.0)
        assert not r.runs_out()
        assert "does not\nrun out".replace(
            "\n", " "
        ) in r.describe()


class TestRefusals:
    def test_a_negative_balance_is_refused(self):
        with pytest.raises(Invalid) as caught:
            compute_runway(-1.0, 100.0, 0.0)
        assert "hole to explain" in str(caught.value)

    def test_negative_spend_is_refused(self):
        with pytest.raises(Invalid):
            compute_runway(1000.0, -5.0, 0.0)
