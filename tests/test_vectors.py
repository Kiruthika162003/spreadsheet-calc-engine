from __future__ import annotations

import math

import pytest

from gridiron.errors import Invalid
from gridiron.vectors import angle_between, cross, dot, norm


class TestDotAndNorm:
    def test_the_dot_product(self):
        assert dot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == 32.0

    def test_the_norm(self):
        assert norm([3.0, 4.0]) == 5.0

    def test_mismatched_lengths_do_not_pair(self):
        with pytest.raises(Invalid) as caught:
            dot([1.0, 2.0], [1.0])
        assert "is absent" in str(caught.value)


class TestCross:
    def test_the_right_hand_rule(self):
        assert cross([1.0, 0.0, 0.0], [0.0, 1.0, 0.0]) == [
            0.0,
            0.0,
            1.0,
        ]

    def test_it_is_only_three_dimensional(self):
        with pytest.raises(Invalid) as caught:
            cross([1.0, 2.0], [3.0, 4.0])
        assert "three dimensions" in str(caught.value)


class TestAngle:
    def test_perpendicular_is_a_right_angle(self):
        assert angle_between(
            [1.0, 0.0], [0.0, 1.0]
        ) == pytest.approx(math.pi / 2)

    def test_parallel_is_zero_despite_rounding(self):
        # The clamp keeps the cosine in domain so nearly
        # parallel vectors give zero, not a math error.
        assert angle_between(
            [1.0, 1.0], [2.0, 2.0]
        ) == pytest.approx(0.0, abs=1e-6)

    def test_opposite_is_pi(self):
        assert angle_between(
            [1.0, 0.0], [-1.0, 0.0]
        ) == pytest.approx(math.pi)

    def test_a_zero_vector_has_no_angle(self):
        with pytest.raises(Invalid) as caught:
            angle_between([0.0, 0.0], [1.0, 0.0])
        assert "no direction" in str(caught.value)
