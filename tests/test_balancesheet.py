from __future__ import annotations

import pytest

from gridiron.balancesheet import BalanceSheet


def sheet() -> BalanceSheet:
    return BalanceSheet(
        current_assets=[("Cash", 500.0), ("AR", 300.0)],
        longterm_assets=[("Equipment", 700.0)],
        current_liabilities=[("AP", 400.0)],
        longterm_liabilities=[("Loan", 600.0)],
        equity=[("Capital", 500.0)],
    )


class TestTheEquation:
    def test_it_balances(self):
        b = sheet()
        assert b.total_assets() == 1500.0
        assert b.total_liabilities() == 1000.0
        assert b.total_equity() == 500.0
        assert b.balances()
        assert b.imbalance() == 0.0

    def test_an_imbalance_is_reported_not_hidden(self):
        b = sheet()
        b.equity = [("Capital", 400.0)]
        assert not b.balances()
        assert b.imbalance() == 100.0


class TestLiquidity:
    def test_the_current_ratio(self):
        assert sheet().current_ratio() == pytest.approx(2.0)

    def test_working_capital(self):
        assert sheet().working_capital() == 400.0

    def test_no_current_liabilities_has_no_ratio(self):
        b = sheet()
        b.current_liabilities = []
        assert b.current_ratio() is None
        assert b.working_capital() == 800.0


class TestContraAccounts:
    def test_a_negative_line_is_kept(self):
        b = BalanceSheet(
            current_assets=[
                ("Equipment", 1000.0),
                ("Accumulated depreciation", -300.0),
            ],
            equity=[("Net", 700.0)],
        )
        assert b.total_assets() == 700.0
        assert b.balances()
