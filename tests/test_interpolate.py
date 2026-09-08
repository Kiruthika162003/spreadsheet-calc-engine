from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.interpolate import growth, trend


class TestTrend:
    def test_a_clean_line_projects_exactly(self):
        # y = 2x + 1 at x = 1..4.
        result = trend([3.0, 5.0, 7.0, 9.0], [5.0, 6.0])
        assert result.slope == pytest.approx(2.0)
        assert result.intercept == pytest.approx(1.0)
        assert result.values == pytest.approx((11.0, 13.0))
        assert result.r_squared == pytest.approx(1.0)

    def test_explicit_positions_are_honored(self):
        # Line through (1, 10) and (2, 20) is y = 10x.
        result = trend(
            [10.0, 20.0],
            [30.0],
            known_x=[1.0, 2.0],
        )
        assert result.slope == pytest.approx(10.0)
        assert result.values == pytest.approx((300.0,))

    def test_one_point_fixes_no_slope(self):
        with pytest.raises(Invalid) as caught:
            trend([5.0], [2.0])
        assert "one point fixes no slope" in str(
            caught.value
        )

    def test_a_vertical_stack_is_refused(self):
        with pytest.raises(Invalid) as caught:
            trend([1.0, 2.0], [3.0], known_x=[5.0, 5.0])
        assert "vertical stack" in str(caught.value)


class TestGrowth:
    def test_a_clean_exponential_projects(self):
        # y = 2^x at x = 1..4: 2, 4, 8, 16.
        result = growth(
            [2.0, 4.0, 8.0, 16.0], [5.0]
        )
        assert result.values[0] == pytest.approx(32.0)
        assert result.r_squared == pytest.approx(1.0)

    def test_a_non_positive_value_is_a_category_error(self):
        with pytest.raises(Invalid) as caught:
            growth([1.0, 0.0, 4.0], [5.0])
        assert "category error" in str(caught.value)

    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid) as caught:
            growth([1.0, -2.0], [3.0])
        assert "category error" in str(caught.value)

    def test_one_point_fixes_no_rate(self):
        with pytest.raises(Invalid) as caught:
            growth([5.0], [2.0])
        assert "one point fixes no rate" in str(
            caught.value
        )


class TestMismatch:
    def test_positions_must_pair_with_values(self):
        with pytest.raises(Invalid) as caught:
            trend(
                [1.0, 2.0, 3.0], [4.0], known_x=[1.0, 2.0]
            )
        assert "must pair" in str(caught.value)
