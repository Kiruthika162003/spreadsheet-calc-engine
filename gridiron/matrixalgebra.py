"""Matrix algebra: the element-wise operations, with shapes checked before math.

Alongside the multiply, determinant, and inverse in the
matrix module, the element-wise operations round out the
toolkit: adding two matrices, subtracting, scaling by a
number, the identity of a size, and the trace. Each has one
guard, the shape check, and it comes before any arithmetic
rather than midway through, because a mismatched add that
computed the first row and then failed on the second would
leave a half-built result the caller might mistake for
whole. Addition and subtraction require identical shapes,
refused with both shapes named, because adding a two-by-three
to a three-by-two is not a hard case with a clever answer, it
is undefined, and the two numbers tell the caller which
dimension to fix. Scaling multiplies every element by a
scalar and cannot fail on shape. The identity of size n is
the classic ones-on-the-diagonal matrix, and multiplying any
square matrix by its identity returns the matrix unchanged,
a law the tests check against the existing multiply because
the identity that does not act as one is the subtlest bug in
a linear algebra library. The trace is the sum of the
diagonal, defined only for square matrices, refused
otherwise, and it equals the sum of the eigenvalues, which is
why it turns up in so many places, though this module only
promises the diagonal sum and leaves the eigenvalues to a
larger tool.
"""

from __future__ import annotations

from gridiron.errors import Invalid

Matrix = list[list[float]]


def _shape(matrix: Matrix) -> tuple[int, int]:
    if not matrix or not matrix[0]:
        raise Invalid("an empty matrix has no shape")
    width = len(matrix[0])
    for row in matrix:
        if len(row) != width:
            raise Invalid(
                "the matrix is ragged; every row must share "
                "a width"
            )
    return len(matrix), width


def add(a: Matrix, b: Matrix) -> Matrix:
    if _shape(a) != _shape(b):
        raise Invalid(
            f"cannot add a {_shape(a)} matrix to a "
            f"{_shape(b)} one; the shapes must match"
        )
    return [
        [x + y for x, y in zip(ra, rb, strict=True)]
        for ra, rb in zip(a, b, strict=True)
    ]


def subtract(a: Matrix, b: Matrix) -> Matrix:
    if _shape(a) != _shape(b):
        raise Invalid(
            f"cannot subtract a {_shape(b)} matrix from a "
            f"{_shape(a)} one; the shapes must match"
        )
    return [
        [x - y for x, y in zip(ra, rb, strict=True)]
        for ra, rb in zip(a, b, strict=True)
    ]


def scale(matrix: Matrix, factor: float) -> Matrix:
    _shape(matrix)
    return [[x * factor for x in row] for row in matrix]


def identity(n: int) -> Matrix:
    if n < 1:
        raise Invalid("an identity needs a positive size")
    return [
        [1.0 if i == j else 0.0 for j in range(n)]
        for i in range(n)
    ]


def trace(matrix: Matrix) -> float:
    rows, cols = _shape(matrix)
    if rows != cols:
        raise Invalid(
            "the trace is defined only for a square matrix"
        )
    return sum(matrix[i][i] for i in range(rows))
