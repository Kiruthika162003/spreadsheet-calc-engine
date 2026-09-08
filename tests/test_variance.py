from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.variance import (
    COST,
    REVENUE,
    analyze,
    analyze_line,
    net_variance,
)


class TestTheFavorableSign:
    def test_revenue_over_budget_is_favorable(self):
        v = analyze_line("Sales", 1000.0, 1200.0, REVENUE)
        assert v.amount == 200.0
        assert v.verdict == "favorable"

    def test_revenue_under_budget_is_unfavorable(self):
        v = analyze_line("Sales", 1000.0, 800.0, REVENUE)
        assert v.verdict == "unfavorable"

    def test_cost_over_budget_is_unfavorable(self):
        v = analyze_line("Rent", 500.0, 600.0, COST)
        assert v.amount == 100.0
        assert v.verdict == "unfavorable"

    def test_cost_under_budget_is_favorable(self):
        v = analyze_line("Rent", 500.0, 400.0, COST)
        assert v.verdict == "favorable"

    def test_exactly_on_budget_is_its_own_category(self):
        v = analyze_line("X", 100.0, 100.0, COST)
        assert v.verdict == "on-budget"


class TestPercentAndTotals:
    def test_the_percent_variance(self):
        v = analyze_line("Sales", 1000.0, 1200.0, REVENUE)
        assert v.percent == pytest.approx(0.2)

    def test_a_zero_budget_has_no_percent(self):
        v = analyze_line("New", 0.0, 50.0, COST)
        assert v.percent is None

    def test_the_raw_amounts_still_sum(self):
        lines = analyze(
            [
                ("Sales", 1000.0, 1200.0, REVENUE),
                ("Rent", 500.0, 600.0, COST),
            ]
        )
        # Raw variance is always actual minus budget, so the
        # net still adds across a mixed statement.
        assert net_variance(lines) == 300.0


class TestRefusals:
    def test_an_unknown_kind_is_refused(self):
        with pytest.raises(Invalid) as caught:
            analyze_line("X", 100.0, 90.0, "asset")
        assert "revenue or cost" in str(caught.value)
