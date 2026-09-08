from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.polyfit import poly_eval, poly_fit


class TestEval:
    def test_horner_evaluation(self):
        # 1 + 2x + 3x^2 at x=2 is 1 + 4 + 12 = 17.
        assert poly_eval([1.0, 2.0, 3.0], 2.0) == 17.0

    def test_a_constant_polynomial(self):
        assert poly_eval([5.0], 99.0) == 5.0


class TestFit:
    def test_a_line_is_recovered_exactly(self):
        coeffs = poly_fit(
            [0.0, 1.0, 2.0, 3.0],
            [2.0, 5.0, 8.0, 11.0],
            1,
        )
        assert coeffs[0] == pytest.approx(2.0)
        assert coeffs[1] == pytest.approx(3.0)

    def test_a_parabola_is_recovered(self):
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [1.0, 3.0, 9.0, 19.0]
        coeffs = poly_fit(xs, ys, 2)
        for x, y in zip(xs, ys, strict=True):
            assert poly_eval(coeffs, x) == pytest.approx(
                y, abs=1e-6
            )

    def test_a_noisy_line_fits_closely(self):
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [0.0, 1.1, 1.9, 3.0]
        slope = poly_fit(xs, ys, 1)[1]
        assert 0.9 < slope < 1.1


class TestRefusals:
    def test_too_few_distinct_points(self):
        with pytest.raises(Invalid) as caught:
            poly_fit([1.0, 1.0], [2.0, 2.0], 1)
        assert "distinct x-value" in str(caught.value)

    def test_mismatched_lengths(self):
        with pytest.raises(Invalid) as caught:
            poly_fit([1.0, 2.0], [3.0], 1)
        assert "paired" in str(caught.value)

    def test_a_negative_degree(self):
        with pytest.raises(Invalid):
            poly_fit([1.0, 2.0], [3.0, 4.0], -1)
