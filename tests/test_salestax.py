from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.salestax import add_tax, extract_tax


class TestAddTax:
    def test_it_adds_forward(self):
        b = add_tax(100.0, 0.08)
        assert b.total == 108.0
        assert b.net == 100.0
        assert b.tax == 8.0
        assert b.reconciles()


class TestExtractTax:
    def test_it_divides_not_multiplies(self):
        # The common wrong answer multiplies 108 by 8% = 8.64;
        # the right one divides out to a net of 100, tax 8.
        b = extract_tax(108.0, 0.08)
        assert b.net == 100.0
        assert b.tax == 8.0
        assert b.reconciles()

    def test_the_pieces_reconcile(self):
        b = extract_tax(215.75, 0.0825)
        assert b.reconciles()


class TestRoundTrip:
    def test_add_then_extract_recovers_the_price(self):
        for price, rate in [
            (49.99, 0.0825),
            (100.0, 0.08),
            (1.0, 0.20),
            (999.95, 0.05),
        ]:
            total = add_tax(price, rate).total
            assert extract_tax(total, rate).net == (
                pytest.approx(price, abs=0.01)
            )


class TestRefusals:
    def test_a_negative_price_is_refused(self):
        with pytest.raises(Invalid):
            add_tax(-1.0, 0.08)

    def test_a_negative_rate_is_a_subsidy(self):
        with pytest.raises(Invalid) as caught:
            add_tax(100.0, -0.08)
        assert "subsidy" in str(caught.value)

    def test_a_negative_total_cannot_be_untaxed(self):
        with pytest.raises(Invalid) as caught:
            extract_tax(-108.0, 0.08)
        assert "no negative sale" in str(caught.value)
