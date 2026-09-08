from __future__ import annotations

import pytest

from gridiron.arrays import mmult
from gridiron.errors import Invalid
from gridiron.matrixalgebra import (
    add,
    identity,
    scale,
    subtract,
    trace,
)

A = [[1.0, 2.0], [3.0, 4.0]]


class TestElementwise:
    def test_addition(self):
        assert add(A, identity(2)) == [
            [2.0, 2.0],
            [3.0, 5.0],
        ]

    def test_subtraction_to_zero(self):
        assert subtract(A, A) == [[0.0, 0.0], [0.0, 0.0]]

    def test_scaling(self):
        assert scale(A, 2.0) == [[2.0, 4.0], [6.0, 8.0]]

    def test_a_shape_mismatch_is_refused(self):
        with pytest.raises(Invalid) as caught:
            add(A, [[1.0, 2.0]])
        assert "shapes must match" in str(caught.value)

    def test_a_ragged_matrix_is_refused(self):
        with pytest.raises(Invalid):
            scale([[1.0, 2.0], [3.0]], 2.0)


class TestIdentity:
    def test_the_identity_shape(self):
        assert identity(3) == [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]

    def test_it_acts_as_one_under_multiply(self):
        assert mmult(A, identity(2)) == A
        assert mmult(identity(2), A) == A

    def test_a_zero_size_is_refused(self):
        with pytest.raises(Invalid):
            identity(0)


class TestTrace:
    def test_the_diagonal_sum(self):
        assert trace(A) == 5.0

    def test_a_non_square_trace_is_refused(self):
        with pytest.raises(Invalid) as caught:
            trace([[1.0, 2.0, 3.0]])
        assert "square matrix" in str(caught.value)
