from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.pricing import (
    chain_discount,
    margin_of,
    margin_to_markup,
    markup_to_margin,
    price_from_cost,
)


class TestMarkupVersusMargin:
    def test_they_are_different_numbers(self):
        # A 50% markup is only a 33.3% margin.
        assert markup_to_margin(0.5) == pytest.approx(
            1.0 / 3.0
        )

    def test_the_conversion_round_trips(self):
        for markup in (0.1, 0.5, 1.0, 3.0):
            margin = markup_to_margin(markup)
            assert margin_to_markup(margin) == pytest.approx(
                markup
            )

    def test_price_and_margin_agree(self):
        price = price_from_cost(100.0, 0.5)
        assert price == 150.0
        assert margin_of(100.0, price) == pytest.approx(
            1.0 / 3.0
        )

    def test_a_margin_of_one_is_refused(self):
        with pytest.raises(Invalid) as caught:
            margin_to_markup(1.0)
        assert "pays you to make it" in str(caught.value)


class TestChainDiscount:
    def test_successive_discounts_do_not_add(self):
        # 20% then 10% is 28% off, not 30.
        assert chain_discount([0.2, 0.1]) == pytest.approx(
            0.28
        )

    def test_the_order_does_not_matter(self):
        assert chain_discount([0.2, 0.1]) == pytest.approx(
            chain_discount([0.1, 0.2])
        )

    def test_no_discounts_is_zero(self):
        assert chain_discount([]) == 0.0

    def test_a_full_discount_is_refused(self):
        with pytest.raises(Invalid) as caught:
            chain_discount([0.5, 1.0])
        assert "giveaway" in str(caught.value)


class TestRefusals:
    def test_a_free_product_has_no_markup(self):
        with pytest.raises(Invalid) as caught:
            price_from_cost(0.0, 0.5)
        assert "no markup to speak of" in str(caught.value)

    def test_a_zero_price_margin_is_refused(self):
        with pytest.raises(Invalid):
            margin_of(10.0, 0.0)
