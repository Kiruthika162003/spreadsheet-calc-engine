from __future__ import annotations

import pytest

from gridiron.bondmath import (
    macaulay_duration,
    price,
    yield_to_maturity,
)
from gridiron.errors import Invalid


class TestPrice:
    def test_a_par_bond_prices_at_face(self):
        # Coupon rate equals yield: price equals face.
        assert price(1000.0, 0.05, 10, 0.05) == (
            pytest.approx(1000.0)
        )

    def test_a_discount_when_yield_exceeds_coupon(self):
        assert price(1000.0, 0.05, 10, 0.06) < 1000.0

    def test_a_premium_when_yield_below_coupon(self):
        assert price(1000.0, 0.05, 10, 0.04) > 1000.0

    def test_a_matured_bond_has_no_price(self):
        with pytest.raises(Invalid) as caught:
            price(1000.0, 0.05, 0, 0.05)
        assert "already matured" in str(caught.value)

    def test_a_negative_coupon_is_refused(self):
        with pytest.raises(Invalid) as caught:
            price(1000.0, -0.01, 10, 0.05)
        assert "fee schedule" in str(caught.value)


class TestYieldToMaturity:
    def test_ytm_inverts_the_price(self):
        p = price(1000.0, 0.05, 10, 0.06)
        assert yield_to_maturity(
            1000.0, 0.05, 10, p
        ) == pytest.approx(0.06, abs=1e-6)

    def test_a_par_price_yields_the_coupon(self):
        assert yield_to_maturity(
            1000.0, 0.05, 10, 1000.0
        ) == pytest.approx(0.05, abs=1e-6)

    def test_a_nonpositive_price_has_no_yield(self):
        with pytest.raises(Invalid) as caught:
            yield_to_maturity(1000.0, 0.05, 10, 0.0)
        assert "no yield to find" in str(caught.value)


class TestDuration:
    def test_duration_is_below_maturity(self):
        d = macaulay_duration(1000.0, 0.05, 10, 0.05)
        assert 0 < d < 10

    def test_a_zero_coupon_duration_equals_maturity(self):
        # With no coupons, the only cash flow is at the end.
        d = macaulay_duration(1000.0, 0.0, 10, 0.05)
        assert d == pytest.approx(10.0)
