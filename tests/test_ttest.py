from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.ttest import one_sample, two_sample


class TestOneSample:
    def test_a_mean_at_the_hypothesis_is_insignificant(self):
        t, p = one_sample(
            [9.5, 10.5, 10.0, 9.8, 10.2], 10.0
        )
        assert t == pytest.approx(0.0, abs=1e-6)
        assert p == pytest.approx(1.0, abs=1e-6)

    def test_a_far_hypothesis_is_significant(self):
        t, p = one_sample(
            [9.5, 10.5, 10.0, 9.8, 10.2], 5.0
        )
        assert abs(t) > 5
        assert p < 0.01

    def test_a_single_value_is_refused(self):
        with pytest.raises(Invalid):
            one_sample([10.0], 10.0)

    def test_zero_variance_is_refused(self):
        with pytest.raises(Invalid) as caught:
            one_sample([5.0, 5.0, 5.0], 4.0)
        assert "zero standard error" in str(caught.value)


class TestTwoSample:
    def test_clearly_different_groups(self):
        a = [10.0, 11.0, 12.0, 10.0, 11.0]
        b = [20.0, 21.0, 19.0, 22.0, 20.0]
        _, p = two_sample(a, b)
        assert p < 0.001

    def test_similar_groups_are_insignificant(self):
        a = [10.0, 11.0, 12.0]
        b = [10.5, 11.5, 12.5]
        _, p = two_sample(a, b)
        assert p > 0.1

    def test_a_tiny_sample_is_refused(self):
        with pytest.raises(Invalid) as caught:
            two_sample([1.0], [2.0, 3.0])
        assert "at least two" in str(caught.value)


class TestPValueRange:
    def test_p_values_are_probabilities(self):
        _, p = one_sample([1.0, 2.0, 3.0, 4.0], 2.0)
        assert 0.0 <= p <= 1.0
