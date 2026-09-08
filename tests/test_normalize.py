from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.normalize import min_max, robust, z_score


class TestMinMax:
    def test_it_maps_to_zero_and_one(self):
        result = min_max([10.0, 20.0, 30.0, 40.0])
        assert result[0] == 0.0
        assert result[-1] == 1.0

    def test_the_extremes_are_exact(self):
        # No rounding drift at the endpoints.
        result = min_max([1.0, 3.0, 7.0])
        assert result[0] == 0.0
        assert result[2] == 1.0

    def test_a_constant_column_is_refused(self):
        with pytest.raises(Invalid) as caught:
            min_max([5.0, 5.0, 5.0])
        assert "carries no information" in str(caught.value)

    def test_the_input_is_not_mutated(self):
        data = [3.0, 1.0, 2.0]
        min_max(data)
        assert data == [3.0, 1.0, 2.0]


class TestZScore:
    def test_it_centers_and_scales(self):
        result = z_score([1.0, 2.0, 3.0])
        assert result[1] == pytest.approx(0.0)
        assert result[0] == pytest.approx(-result[2])

    def test_zero_variance_is_refused(self):
        with pytest.raises(Invalid) as caught:
            z_score([4.0, 4.0])
        assert "zero spread is" in str(caught.value)


class TestRobust:
    def test_it_uses_median_and_iqr(self):
        result = robust([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result == [-1.0, -0.5, 0.0, 0.5, 1.0]

    def test_a_zero_iqr_is_refused(self):
        with pytest.raises(Invalid) as caught:
            robust([5.0, 5.0, 5.0, 5.0])
        assert "one value" in str(caught.value)

    def test_it_resists_an_outlier(self):
        # A wild outlier barely moves the median-based scale.
        result = robust([1.0, 2.0, 3.0, 4.0, 1000.0])
        assert abs(result[0]) < 2
