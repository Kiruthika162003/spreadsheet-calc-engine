from __future__ import annotations

import pytest

from gridiron.statements import IncomeStatement


def statement() -> IncomeStatement:
    return IncomeStatement(
        revenue=[("Product", 800.0), ("Service", 200.0)],
        cogs=[("Materials", 400.0)],
        operating=[("Salaries", 200.0), ("Rent", 100.0)],
        other=[("Interest", 50.0), ("Tax", 75.0)],
    )


class TestSubtotals:
    def test_gross_profit_is_derived(self):
        assert statement().gross_profit() == 600.0

    def test_operating_income_is_derived(self):
        assert statement().operating_income() == 300.0

    def test_net_income_is_the_bottom_line(self):
        assert statement().net_income() == 175.0

    def test_the_chain_ties_together(self):
        s = statement()
        assert (
            s.total_revenue()
            - s.total_cogs()
            - s.total_operating()
            - s.total_other()
            == s.net_income()
        )


class TestMargins:
    def test_gross_and_net_margins(self):
        s = statement()
        assert s.gross_margin() == pytest.approx(0.6)
        assert s.net_margin() == pytest.approx(0.175)

    def test_a_zero_revenue_has_no_margin(self):
        s = IncomeStatement(cogs=[("x", 10.0)])
        assert s.gross_margin() is None
        assert s.net_margin() is None


class TestRender:
    def test_it_reads_top_to_bottom(self):
        text = statement().render()
        lines = text.splitlines()
        assert lines[0] == "Revenue"
        assert "Gross profit: 600" in text
        assert "Net income: 175" in text
        assert "Net margin: 17.5%" in text
