from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.keyratios import (
    asset_turnover,
    current_ratio,
    debt_to_equity,
    net_margin,
    quick_ratio,
    return_on_assets,
    return_on_equity,
)


class TestLiquidity:
    def test_current_ratio(self):
        assert current_ratio(800.0, 400.0) == 2.0

    def test_quick_ratio_excludes_inventory(self):
        # 800 assets, 300 inventory, 400 liabilities.
        assert quick_ratio(800.0, 300.0, 400.0) == (
            pytest.approx(1.25)
        )

    def test_quick_is_stricter_than_current(self):
        assert quick_ratio(
            800.0, 300.0, 400.0
        ) < current_ratio(800.0, 400.0)


class TestLeverageAndReturns:
    def test_debt_to_equity(self):
        assert debt_to_equity(1000.0, 500.0) == 2.0

    def test_return_on_equity(self):
        assert return_on_equity(150.0, 500.0) == 0.3

    def test_return_on_assets(self):
        assert return_on_assets(150.0, 1500.0) == 0.1

    def test_asset_turnover(self):
        assert asset_turnover(3000.0, 1500.0) == 2.0

    def test_net_margin(self):
        assert net_margin(150.0, 1000.0) == 0.15


class TestZeroDenominators:
    def test_no_equity_refuses_debt_to_equity(self):
        with pytest.raises(Invalid) as caught:
            debt_to_equity(1000.0, 0.0)
        assert "returned as infinity" in str(caught.value)

    def test_no_revenue_refuses_margin(self):
        with pytest.raises(Invalid):
            net_margin(150.0, 0.0)

    def test_no_liabilities_refuses_current_ratio(self):
        with pytest.raises(Invalid):
            current_ratio(800.0, 0.0)
