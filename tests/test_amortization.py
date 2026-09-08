from __future__ import annotations

import pytest

from gridiron.amortization import amortize
from gridiron.errors import Invalid


class TestTheScheduleCloses:
    def test_the_final_balance_is_exactly_zero(self):
        schedule = amortize(1000.0, 0.01, 12)
        assert schedule.final_balance() == 0.0

    def test_total_principal_equals_the_loan(self):
        schedule = amortize(1000.0, 0.01, 12)
        assert schedule.total_principal() == 1000.0

    def test_interest_is_payments_minus_principal(self):
        schedule = amortize(1000.0, 0.01, 12)
        assert schedule.total_interest() == pytest.approx(
            schedule.total_paid()
            - schedule.total_principal(),
            abs=0.01,
        )

    def test_every_period_has_a_row(self):
        schedule = amortize(5000.0, 0.005, 24)
        assert len(schedule.periods) == 24
        assert schedule.periods[0].number == 1
        assert schedule.periods[-1].number == 24


class TestInterestShrinks:
    def test_interest_falls_as_principal_pays_down(self):
        schedule = amortize(1000.0, 0.01, 12)
        interests = [p.interest for p in schedule.periods]
        assert interests[0] > interests[-1]

    def test_the_odd_cent_lands_in_the_last_payment(self):
        schedule = amortize(1000.0, 0.01, 12)
        level = schedule.periods[0].payment
        last = schedule.periods[-1].payment
        # The last payment may differ by the rounding
        # residue, but only there.
        middle = {p.payment for p in schedule.periods[:-1]}
        assert middle == {level}
        assert abs(last - level) < 1.0


class TestZeroRate:
    def test_equal_principal_each_period(self):
        schedule = amortize(1200.0, 0.0, 12)
        assert schedule.periods[0].payment == 100.0
        assert schedule.final_balance() == 0.0
        assert all(
            p.interest == 0.0 for p in schedule.periods
        )


class TestRefusals:
    def test_a_nonpositive_principal_is_refused(self):
        with pytest.raises(Invalid) as caught:
            amortize(0.0, 0.01, 12)
        assert "positive principal" in str(caught.value)

    def test_zero_periods_are_refused(self):
        with pytest.raises(Invalid):
            amortize(1000.0, 0.01, 0)

    def test_a_negative_rate_is_a_gift(self):
        with pytest.raises(Invalid) as caught:
            amortize(1000.0, -0.01, 12)
        assert "gift with extra steps" in str(caught.value)
