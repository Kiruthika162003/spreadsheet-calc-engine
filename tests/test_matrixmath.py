from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.matrixmath import mdeterm, minverse, msolve


class TestDeterminant:
    def test_the_two_by_two_textbook_case(self):
        assert mdeterm([[3.0, 8.0], [4.0, 6.0]]) == -14.0

    def test_a_singular_matrix_is_exactly_zero(self):
        assert (
            mdeterm([[1.0, 2.0], [2.0, 4.0]]) == 0.0
        )

    def test_row_swaps_flip_the_sign_correctly(self):
        matrix = [
            [0.0, 1.0, 2.0],
            [3.0, 4.0, 5.0],
            [6.0, 7.0, 9.0],
        ]
        assert mdeterm(matrix) == pytest.approx(-3.0)

    def test_the_identity_is_one(self):
        identity = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        assert mdeterm(identity) == 1.0

    def test_a_ragged_matrix_is_refused(self):
        with pytest.raises(Invalid) as caught:
            mdeterm([[1.0, 2.0], [3.0]])
        assert "square" in str(caught.value)


class TestInverse:
    def test_the_product_returns_the_identity(self):
        matrix = [
            [4.0, 7.0],
            [2.0, 6.0],
        ]
        inverse = minverse(matrix)
        size = len(matrix)
        for row in range(size):
            for col in range(size):
                entry = sum(
                    matrix[row][k] * inverse[k][col]
                    for k in range(size)
                )
                expected = 1.0 if row == col else 0.0
                assert entry == pytest.approx(
                    expected, abs=1e-9
                )

    def test_singularity_names_the_dead_column(self):
        with pytest.raises(Invalid) as caught:
            minverse([[1.0, 2.0], [2.0, 4.0]])
        assert "column 2" in str(caught.value)

    def test_the_relative_threshold_spares_big_matrices(self):
        scaled = [
            [4.0e9, 7.0e9],
            [2.0e9, 6.0e9],
        ]
        inverse = minverse(scaled)
        assert inverse[0][0] == pytest.approx(6e9 / 1e19)


class TestSolve:
    def test_the_two_equation_word_problem(self):
        answer = msolve(
            [[2.0, 1.0], [1.0, 3.0]], [11.0, 18.0]
        )
        assert answer[0] == pytest.approx(3.0)
        assert answer[1] == pytest.approx(5.0)

    def test_a_small_leading_pivot_survives(self):
        answer = msolve(
            [[1e-13, 1.0], [1.0, 1.0]], [1.0, 2.0]
        )
        assert answer[0] == pytest.approx(1.0)
        assert answer[1] == pytest.approx(1.0)

    def test_dependent_equations_are_named(self):
        with pytest.raises(Invalid) as caught:
            msolve(
                [[1.0, 1.0], [2.0, 2.0]], [3.0, 6.0]
            )
        assert "not independent" in str(caught.value)

    def test_mismatched_shapes_are_refused(self):
        with pytest.raises(Invalid) as caught:
            msolve([[1.0, 0.0], [0.0, 1.0]], [1.0])
        assert "shapes must agree" in str(caught.value)
