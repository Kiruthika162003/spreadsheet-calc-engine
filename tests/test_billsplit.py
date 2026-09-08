from __future__ import annotations

import pytest

from gridiron.billsplit import split_by_order, split_evenly
from gridiron.errors import Invalid


class TestSplitEvenly:
    def test_it_reconciles_to_the_penny(self):
        s = split_evenly(
            100.0, 3, tax_rate=0.10, tip_rate=0.20
        )
        assert s.total() == 130.0
        assert s.reconciles()
        assert sorted(s.shares_cents) == [4333, 4333, 4334]

    def test_a_plain_even_split(self):
        s = split_evenly(30.0, 3)
        assert s.shares() == [10.0, 10.0, 10.0]

    def test_zero_diners_is_refused(self):
        with pytest.raises(Invalid):
            split_evenly(30.0, 0)


class TestSplitByOrder:
    def test_shares_are_proportional(self):
        s = split_by_order(
            [40.0, 60.0], tax_rate=0.10, tip_rate=0.20
        )
        assert s.total() == 130.0
        assert s.shares() == [52.0, 78.0]
        assert s.reconciles()

    def test_a_negative_order_is_refused(self):
        with pytest.raises(Invalid) as caught:
            split_by_order([40.0, -5.0])
        assert "missing order is not a zero" in str(
            caught.value
        )


class TestTipConvention:
    def test_tip_on_pretax_versus_posttax(self):
        pre = split_evenly(
            100.0, 1, tax_rate=0.10, tip_rate=0.20
        )
        post = split_evenly(
            100.0,
            1,
            tax_rate=0.10,
            tip_rate=0.20,
            tip_on_pretax=False,
        )
        assert pre.total() == 130.0
        assert post.total() == 132.0

    def test_a_negative_tip_is_refused(self):
        with pytest.raises(Invalid) as caught:
            split_evenly(100.0, 2, tip_rate=-0.1)
        assert "gratuity" in str(caught.value)
