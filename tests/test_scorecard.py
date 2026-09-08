from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.scorecard import Criterion, score

CRITERIA = [
    Criterion("price", 0.5, benefit=False),
    Criterion("quality", 0.5, benefit=True),
]
VALUES = {
    "A": [100.0, 8.0],
    "B": [200.0, 10.0],
    "C": [150.0, 6.0],
}


class TestScoring:
    def test_the_ranking(self):
        ranked = score(["A", "B", "C"], CRITERIA, VALUES)
        assert [s.option for s in ranked] == ["A", "B", "C"]

    def test_a_cost_criterion_rewards_the_low(self):
        ranked = score(["A", "B", "C"], CRITERIA, VALUES)
        scores = {s.option: s.score for s in ranked}
        # A is cheapest and mid-quality; it wins.
        assert scores["A"] == pytest.approx(0.75)
        assert scores["B"] == pytest.approx(0.5)

    def test_units_do_not_cheat(self):
        # Inflating the price scale by 1000x must not change
        # the ranking, because normalization removes units.
        blown = {
            "A": [100000.0, 8.0],
            "B": [200000.0, 10.0],
            "C": [150000.0, 6.0],
        }
        a = score(["A", "B", "C"], CRITERIA, VALUES)
        b = score(["A", "B", "C"], CRITERIA, blown)
        assert [s.option for s in a] == [
            s.option for s in b
        ]


class TestDegenerateCriteria:
    def test_a_flat_criterion_does_not_tip(self):
        crit = [
            Criterion("flat", 0.5),
            Criterion("real", 0.5),
        ]
        vals = {
            "A": [5.0, 10.0],
            "B": [5.0, 0.0],
        }
        ranked = score(["A", "B"], crit, vals)
        # The flat criterion gives both 0.5; "real" decides.
        assert ranked[0].option == "A"


class TestRefusals:
    def test_weights_must_sum_to_one(self):
        crit = [Criterion("x", 0.3), Criterion("y", 0.3)]
        with pytest.raises(Invalid) as caught:
            score(
                ["A"], crit, {"A": [1.0, 2.0]}
            )
        assert "wrong denominator" in str(caught.value)

    def test_a_missing_value_is_refused(self):
        with pytest.raises(Invalid) as caught:
            score(["A"], CRITERIA, {"A": [1.0]})
        assert "one value per criterion" in str(caught.value)
