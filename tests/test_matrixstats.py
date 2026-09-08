from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.matrixstats import (
    correlation_matrix,
    covariance_matrix,
)

A = [1.0, 2.0, 3.0, 4.0]
B = [2.0, 4.0, 6.0, 8.0]
C = [4.0, 3.0, 2.0, 1.0]


class TestCovariance:
    def test_the_diagonal_is_the_variance(self):
        cov = covariance_matrix([A])
        assert cov[0][0] == pytest.approx(1.25)

    def test_the_matrix_is_symmetric(self):
        cov = covariance_matrix([A, B, C])
        for i in range(3):
            for j in range(3):
                assert cov[i][j] == cov[j][i]

    def test_mismatched_columns_are_refused(self):
        with pytest.raises(Invalid) as caught:
            covariance_matrix([A, [1.0, 2.0]])
        assert "row-for-row" in str(caught.value)


class TestCorrelation:
    def test_the_diagonal_is_exactly_one(self):
        cor = correlation_matrix([A, B])
        assert cor[0][0] == 1.0
        assert cor[1][1] == 1.0

    def test_perfect_and_anti_correlation(self):
        cor = correlation_matrix([A, B, C])
        assert cor[0][1] == pytest.approx(1.0)
        assert cor[0][2] == pytest.approx(-1.0)

    def test_a_flat_column_correlates_with_nothing(self):
        flat = [5.0, 5.0, 5.0, 5.0]
        cor = correlation_matrix([A, flat])
        assert cor[0][1] is None
        assert cor[1][1] is None
        # But its covariance, needing no division, is present.
        cov = covariance_matrix([A, flat])
        assert cov[0][1] == pytest.approx(0.0)

    def test_correlation_is_clamped(self):
        cor = correlation_matrix([A, B])
        assert -1.0 <= cor[0][1] <= 1.0
