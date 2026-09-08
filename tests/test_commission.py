from __future__ import annotations

import pytest

from gridiron.commission import Tier, compute_commission
from gridiron.errors import Invalid

TIERS = [
    Tier(0.0, 0.05),
    Tier(10000.0, 0.10),
    Tier(50000.0, 0.15),
]


class TestMarginalTiers:
    def test_within_the_first_tier(self):
        r = compute_commission(5000.0, TIERS)
        assert r.commission == 250.0
        assert r.marginal_rate == 0.05

    def test_spanning_two_tiers(self):
        r = compute_commission(30000.0, TIERS)
        # 10000 at 5% plus 20000 at 10%.
        assert r.commission == 2500.0
        assert r.marginal_rate == 0.10

    def test_reaching_the_top_tier(self):
        r = compute_commission(60000.0, TIERS)
        assert r.commission == 6000.0
        assert r.marginal_rate == 0.15

    def test_crossing_a_tier_only_reprices_the_new_band(self):
        # Just over 10000 pays the higher rate on one dollar
        # only, not retroactively on the whole figure.
        below = compute_commission(10000.0, TIERS).commission
        above = compute_commission(10001.0, TIERS).commission
        assert above - below == pytest.approx(0.10)


class TestRefusals:
    def test_out_of_order_tiers(self):
        bad = [Tier(0.0, 0.05), Tier(5000.0, 0.1), Tier(3000.0, 0.2)]
        with pytest.raises(Invalid) as caught:
            compute_commission(10000.0, bad)
        assert "does not rise" in str(caught.value)

    def test_a_plan_not_starting_at_zero(self):
        with pytest.raises(Invalid) as caught:
            compute_commission(10000.0, [Tier(100.0, 0.05)])
        assert "from the first" in str(caught.value)

    def test_a_rate_over_one(self):
        with pytest.raises(Invalid):
            compute_commission(1000.0, [Tier(0.0, 1.5)])
