from __future__ import annotations

import pytest

from gridiron.cashflow import build_schedule
from gridiron.errors import Invalid

FLOWS = [-1000.0, 400.0, 400.0, 400.0, 400.0]


class TestSchedule:
    def test_period_zero_is_undiscounted(self):
        schedule = build_schedule(FLOWS, 0.10)
        assert schedule.rows[0].factor == 1.0
        assert schedule.rows[0].discounted == -1000.0

    def test_later_periods_discount_more(self):
        schedule = build_schedule(FLOWS, 0.10)
        assert schedule.rows[1].factor == pytest.approx(
            1 / 1.1
        )
        assert schedule.rows[2].factor < schedule.rows[1].factor

    def test_npv_is_the_last_cumulative(self):
        schedule = build_schedule(FLOWS, 0.10)
        assert schedule.npv() == pytest.approx(
            schedule.rows[-1].cumulative
        )
        assert schedule.npv() == pytest.approx(
            267.95, abs=0.01
        )

    def test_the_rendered_table_shows_the_work(self):
        text = build_schedule(FLOWS, 0.10).render()
        assert "period" in text.splitlines()[0]
        assert "NPV = 267.95" in text


class TestDiscountedPayback:
    def test_it_interpolates(self):
        schedule = build_schedule(FLOWS, 0.10)
        assert schedule.discounted_payback() == (
            pytest.approx(3.019, abs=0.01)
        )

    def test_a_project_that_never_recovers(self):
        schedule = build_schedule(
            [-1000.0, 100.0, 100.0], 0.10
        )
        assert schedule.discounted_payback() is None


class TestRefusals:
    def test_no_flows_is_refused(self):
        with pytest.raises(Invalid):
            build_schedule([], 0.1)

    def test_a_rate_below_minus_one_is_refused(self):
        with pytest.raises(Invalid) as caught:
            build_schedule(FLOWS, -1.5)
        assert "modeling error" in str(caught.value)
