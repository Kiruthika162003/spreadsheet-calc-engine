from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.weightedstats import (
    weighted_mean,
    weighted_median,
    weighted_std,
)


class TestWeightedMean:
    def test_grades_by_credit_hours(self):
        assert weighted_mean(
            [90.0, 70.0], [4.0, 2.0]
        ) == pytest.approx(500.0 / 6.0)

    def test_equal_weights_are_the_plain_mean(self):
        assert weighted_mean(
            [1.0, 2.0, 3.0], [1.0, 1.0, 1.0]
        ) == pytest.approx(2.0)

    def test_a_heavy_weight_pulls_the_mean(self):
        light = weighted_mean([1.0, 10.0], [1.0, 1.0])
        heavy = weighted_mean([1.0, 10.0], [1.0, 9.0])
        assert heavy > light


class TestWeightedMedian:
    def test_the_weight_decides_the_middle(self):
        assert (
            weighted_median(
                [1.0, 2.0, 3.0], [1.0, 1.0, 5.0]
            )
            == 3.0
        )

    def test_equal_weights_give_the_ordinary_median(self):
        assert (
            weighted_median(
                [1.0, 2.0, 3.0], [1.0, 1.0, 1.0]
            )
            == 2.0
        )


class TestWeightedStd:
    def test_equal_weights_are_the_population_std(self):
        assert weighted_std(
            [1.0, 2.0, 3.0], [1.0, 1.0, 1.0]
        ) == pytest.approx((2.0 / 3.0) ** 0.5)


class TestRefusals:
    def test_mismatched_lengths_are_refused(self):
        with pytest.raises(Invalid) as caught:
            weighted_mean([1.0, 2.0], [1.0])
        assert "do not pair" in str(caught.value)

    def test_a_negative_weight_is_a_sign_error(self):
        with pytest.raises(Invalid) as caught:
            weighted_mean([1.0, 2.0], [1.0, -1.0])
        assert "sign error" in str(caught.value)

    def test_zero_total_weight_is_refused(self):
        with pytest.raises(Invalid) as caught:
            weighted_mean([1.0, 2.0], [0.0, 0.0])
        assert "no weight is undefined" in str(caught.value)
