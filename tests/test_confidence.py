from __future__ import annotations

import pytest

from gridiron.confidence import (
    margin_normal,
    margin_t,
    mean_interval,
)
from gridiron.errors import Invalid


class TestNormalMargin:
    def test_the_famous_1_96(self):
        # sd 10, n 100: z(0.975)=1.96, margin 1.96.
        assert margin_normal(0.95, 10.0, 100) == (
            pytest.approx(1.96, abs=1e-2)
        )

    def test_the_square_root_law(self):
        small = margin_normal(0.95, 10.0, 25)
        big = margin_normal(0.95, 10.0, 100)
        # Quadrupling n halves the margin.
        assert small == pytest.approx(2 * big, abs=1e-6)


class TestTMargin:
    def test_the_t_is_wider_than_the_normal(self):
        # On a small sample the t margin exceeds the normal.
        t = margin_t(0.95, 10.0, 8)
        z = margin_normal(0.95, 10.0, 8)
        assert t > z

    def test_the_t_critical_matches_the_table(self):
        # df 9 at 95% is 2.262; margin = 2.262 * 1 / sqrt(10).
        margin = margin_t(0.95, 1.0, 10)
        assert margin == pytest.approx(
            2.262 / (10 ** 0.5), abs=1e-3
        )


class TestMeanInterval:
    def test_it_brackets_the_mean(self):
        data = [10.0, 12.0, 11.0, 13.0, 9.0, 10.0]
        low, high = mean_interval(data, 0.95)
        mean = sum(data) / len(data)
        assert low < mean < high

    def test_a_higher_confidence_is_wider(self):
        data = [10.0, 12.0, 11.0, 13.0, 9.0, 10.0]
        lo90, hi90 = mean_interval(data, 0.90)
        lo99, hi99 = mean_interval(data, 0.99)
        assert (hi99 - lo99) > (hi90 - lo90)


class TestRefusals:
    def test_confidence_outside_the_unit_interval(self):
        with pytest.raises(Invalid) as caught:
            margin_normal(1.0, 10.0, 100)
        assert "infinite margin" in str(caught.value)

    def test_t_needs_two_points(self):
        with pytest.raises(Invalid):
            margin_t(0.95, 10.0, 1)
