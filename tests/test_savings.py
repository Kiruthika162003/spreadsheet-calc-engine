from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.savings import (
    final_balance,
    project,
    required_contribution,
)


class TestProjection:
    def test_the_balance_climbs(self):
        rows = project(1000.0, 100.0, 0.05, 10)
        assert len(rows) == 10
        assert rows[0].balance < rows[-1].balance

    def test_the_final_balance(self):
        assert final_balance(
            1000.0, 100.0, 0.05, 10
        ) == pytest.approx(2886.68, abs=0.01)

    def test_interest_accrues_on_the_balance(self):
        rows = project(1000.0, 0.0, 0.10, 1)
        assert rows[0].interest == pytest.approx(100.0)


class TestRequiredContribution:
    def test_it_inverts_the_projection(self):
        target = final_balance(1000.0, 100.0, 0.05, 10)
        assert required_contribution(
            1000.0, target, 0.05, 10
        ) == pytest.approx(100.0, abs=1e-6)

    def test_an_already_met_goal_needs_nothing(self):
        # Opening 1000 compounds past 500 alone.
        assert (
            required_contribution(1000.0, 500.0, 0.05, 10)
            == 0.0
        )

    def test_a_zero_rate_is_plain_division(self):
        assert required_contribution(
            0.0, 1200.0, 0.0, 12
        ) == pytest.approx(100.0)


class TestRefusals:
    def test_zero_periods_project_is_refused(self):
        with pytest.raises(Invalid):
            project(1000.0, 100.0, 0.05, 0)

    def test_zero_periods_solve_is_refused(self):
        with pytest.raises(Invalid):
            required_contribution(0.0, 1000.0, 0.05, 0)
