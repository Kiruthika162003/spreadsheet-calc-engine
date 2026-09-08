from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.pareto import analyze, vital_few

ITEMS = [
    ("A", 50.0),
    ("B", 30.0),
    ("C", 15.0),
    ("D", 5.0),
]


class TestTable:
    def test_sorted_largest_first(self):
        labels = [item.label for item in analyze(ITEMS)]
        assert labels == ["A", "B", "C", "D"]

    def test_shares_sum_to_one(self):
        total = sum(item.share for item in analyze(ITEMS))
        assert total == pytest.approx(1.0)

    def test_the_cumulative_climbs(self):
        cumulatives = [
            item.cumulative for item in analyze(ITEMS)
        ]
        assert cumulatives == pytest.approx(
            [0.5, 0.8, 0.95, 1.0]
        )


class TestVitalFew:
    def test_the_crossing_item_is_included(self):
        # A + B reach exactly 80%; B is the item that
        # crosses the line, so it counts as vital.
        assert vital_few(ITEMS) == ["A", "B"]

    def test_a_tighter_threshold_narrows_it(self):
        assert vital_few(ITEMS, threshold=0.5) == ["A"]

    def test_ties_keep_input_order(self):
        tied = [("x", 10.0), ("y", 10.0), ("z", 10.0)]
        labels = [item.label for item in analyze(tied)]
        assert labels == ["x", "y", "z"]


class TestRefusals:
    def test_a_zero_total_is_refused(self):
        with pytest.raises(Invalid) as caught:
            analyze([("a", 0.0), ("b", 0.0)])
        assert "division by it is undefined" in str(
            caught.value
        )

    def test_a_negative_contribution_is_refused(self):
        with pytest.raises(Invalid) as caught:
            analyze([("a", 10.0), ("b", -5.0)])
        assert "dip below itself" in str(caught.value)

    def test_no_items_is_refused(self):
        with pytest.raises(Invalid):
            analyze([])
