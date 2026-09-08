from __future__ import annotations

import pytest

from gridiron.abcanalysis import class_totals, classify
from gridiron.errors import Invalid

ITEMS = [
    ("a", 50.0),
    ("b", 30.0),
    ("c", 12.0),
    ("d", 5.0),
    ("e", 3.0),
]


class TestClassification:
    def test_the_vital_few_are_a(self):
        classes = {
            item.label: item.abc_class
            for item in classify(ITEMS)
        }
        assert classes["a"] == "A"
        assert classes["b"] == "A"
        assert classes["c"] == "B"
        assert classes["e"] == "C"

    def test_an_item_on_the_cutoff_is_the_lower_class(self):
        # a + b reach exactly 80%; b sits on the line and is
        # still A.
        classes = {
            item.label: item.abc_class
            for item in classify(ITEMS)
        }
        assert classes["b"] == "A"

    def test_the_class_totals(self):
        totals = class_totals(classify(ITEMS))
        assert totals == {"A": 2, "B": 1, "C": 2}

    def test_shares_and_cumulative_are_carried(self):
        first = classify(ITEMS)[0]
        assert first.share == pytest.approx(0.5)
        assert first.cumulative == pytest.approx(0.5)


class TestRefusals:
    def test_inverted_cutoffs_are_refused(self):
        with pytest.raises(Invalid) as caught:
            classify(ITEMS, a_cutoff=0.9, b_cutoff=0.8)
        assert "vital few below the trivial many" in str(
            caught.value
        )

    def test_a_zero_total_is_refused(self):
        with pytest.raises(Invalid) as caught:
            classify([("x", 0.0)])
        assert "division that does not exist" in str(
            caught.value
        )

    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            classify([("x", 10.0), ("y", -5.0)])
