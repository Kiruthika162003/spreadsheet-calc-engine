from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.unitprice import (
    Option,
    best_value,
    rank,
    savings_fraction,
)

OPTIONS = [
    Option("small", 2.0, 100.0),
    Option("large", 5.0, 300.0),
    Option("bulk", 8.0, 500.0),
]


class TestRanking:
    def test_it_ranks_by_unit_price(self):
        labels = [r.label for r in rank(OPTIONS)]
        assert labels == ["bulk", "large", "small"]

    def test_the_bigger_is_not_always_better(self):
        # A large that is priced badly loses to the small.
        opts = [
            Option("small", 1.0, 100.0),
            Option("large", 5.0, 300.0),
        ]
        assert best_value(opts).label == "small"

    def test_a_tie_keeps_input_order(self):
        opts = [
            Option("a", 2.0, 100.0),
            Option("b", 4.0, 200.0),
        ]
        assert [r.label for r in rank(opts)] == ["a", "b"]


class TestSavings:
    def test_the_savings_fraction(self):
        assert savings_fraction(OPTIONS) == pytest.approx(0.2)

    def test_one_option_has_no_savings(self):
        assert (
            savings_fraction([Option("only", 3.0, 100.0)])
            is None
        )


class TestRefusals:
    def test_a_zero_quantity_is_refused(self):
        with pytest.raises(Invalid) as caught:
            rank([Option("empty", 5.0, 0.0)])
        assert "no honest unit price" in str(caught.value)

    def test_a_negative_price_is_refused(self):
        with pytest.raises(Invalid):
            rank([Option("bad", -1.0, 10.0)])
