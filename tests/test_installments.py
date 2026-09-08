from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.installments import equal_installments, total_of


class TestEqualInstallments:
    def test_they_sum_to_the_balance(self):
        for balance, count in [
            (100.0, 3),
            (99.99, 7),
            (1000.0, 12),
            (0.05, 4),
        ]:
            plan = equal_installments(balance, count)
            assert total_of(plan) == round(balance, 2)

    def test_the_odd_cent_goes_first_by_default(self):
        assert equal_installments(100.0, 3) == [
            33.34,
            33.33,
            33.33,
        ]

    def test_the_odd_cent_can_go_last(self):
        assert equal_installments(
            100.0, 3, odd_cents_first=False
        ) == [33.33, 33.33, 33.34]

    def test_an_even_split_has_no_odd_cent(self):
        assert equal_installments(90.0, 3) == [
            30.0,
            30.0,
            30.0,
        ]

    def test_one_installment_is_the_whole_balance(self):
        assert equal_installments(100.0, 1) == [100.0]


class TestRefusals:
    def test_zero_installments_is_refused(self):
        with pytest.raises(Invalid) as caught:
            equal_installments(100.0, 0)
        assert "not a plan" in str(caught.value)

    def test_a_negative_balance_is_refused(self):
        with pytest.raises(Invalid) as caught:
            equal_installments(-100.0, 3)
        assert "refund wearing a plan" in str(caught.value)
