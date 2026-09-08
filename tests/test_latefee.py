from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.latefee import compute_late_fee


class TestGrace:
    def test_a_payment_within_grace_owes_nothing(self):
        fee = compute_late_fee(
            1000.0, 3, 25.0, 0.001, grace_days=5
        )
        assert fee.fee == 0.0
        assert fee.chargeable_days == 0

    def test_zero_days_owes_nothing(self):
        assert (
            compute_late_fee(1000.0, 0, 25.0, 0.001).fee
            == 0.0
        )


class TestCharging:
    def test_flat_plus_daily_interest(self):
        # 15 days, 5 grace: 10 chargeable. 25 + 1000*0.001*10.
        fee = compute_late_fee(
            1000.0, 15, 25.0, 0.001, grace_days=5
        )
        assert fee.chargeable_days == 10
        assert fee.fee == 35.0
        assert not fee.capped

    def test_interest_counts_only_days_past_grace(self):
        no_grace = compute_late_fee(
            1000.0, 10, 0.0, 0.001, grace_days=0
        ).fee
        with_grace = compute_late_fee(
            1000.0, 10, 0.0, 0.001, grace_days=5
        ).fee
        assert with_grace < no_grace


class TestCap:
    def test_the_fee_is_capped(self):
        fee = compute_late_fee(
            100.0, 500, 25.0, 0.01, cap_fraction=0.25
        )
        assert fee.fee == 25.0
        assert fee.capped


class TestRefusals:
    def test_a_credit_balance_is_refused(self):
        with pytest.raises(Invalid) as caught:
            compute_late_fee(-100.0, 10, 25.0, 0.001)
        assert "money the lender owes" in str(caught.value)

    def test_negative_days_is_refused(self):
        with pytest.raises(Invalid) as caught:
            compute_late_fee(1000.0, -1, 25.0, 0.001)
        assert "early, not late" in str(caught.value)
