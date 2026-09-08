"""Covariance and correlation matrices: every pair, symmetric by construction.

Given several equal-length columns, the covariance matrix
holds how each pair moves together and the correlation matrix
the same normalized to minus-one-to-one, and the property
worth guaranteeing is symmetry: the covariance of A with B is
the covariance of B with A, so the matrix must be exactly
symmetric, not symmetric-to-rounding, which this module gets
by computing each pair once and mirroring it rather than
computing both corners independently and hoping they agree.
The diagonal of the correlation matrix is exactly one because
a series correlates perfectly with itself, and it is set to
one directly rather than divided out, because the division
would produce 0.9999999998 on a series with tiny variance and
a correlation matrix with a diagonal that is not quite one is
the kind of thing that fails a downstream positive-definite
check for no real reason. Every column must be the same
length, refused otherwise, because a covariance of series
that do not pair row-for-row is meaningless. A column with
zero variance has no correlation with anything, division by
its zero standard deviation being undefined, and the module
reports that pair's correlation as absent rather than a nan
that would poison every matrix operation it flows into, while
its covariance, which needs no division, is still reported.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _validate(columns: list[list[float]]) -> int:
    if len(columns) < 1:
        raise Invalid("need at least one column")
    length = len(columns[0])
    if length < 2:
        raise Invalid(
            "each column needs at least two values for a "
            "covariance"
        )
    for column in columns:
        if len(column) != length:
            raise Invalid(
                "the columns differ in length; a covariance "
                "of series that do not pair row-for-row is "
                "meaningless"
            )
    return length


def _covariance(a: list[float], b: list[float]) -> float:
    n = len(a)
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    return sum(
        (x - mean_a) * (y - mean_b)
        for x, y in zip(a, b, strict=True)
    ) / n


def covariance_matrix(
    columns: list[list[float]],
) -> list[list[float]]:
    _validate(columns)
    size = len(columns)
    matrix = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i, size):
            value = _covariance(columns[i], columns[j])
            matrix[i][j] = value
            matrix[j][i] = value
    return matrix


def correlation_matrix(
    columns: list[list[float]],
) -> list[list[float | None]]:
    _validate(columns)
    cov = covariance_matrix(columns)
    size = len(columns)
    sds = [cov[i][i] ** 0.5 for i in range(size)]
    matrix: list[list[float | None]] = [
        [None] * size for _ in range(size)
    ]
    for i in range(size):
        for j in range(i, size):
            if i == j:
                matrix[i][j] = 1.0 if sds[i] > 0 else None
                continue
            if sds[i] == 0 or sds[j] == 0:
                value = None
            else:
                value = cov[i][j] / (sds[i] * sds[j])
                value = max(-1.0, min(1.0, value))
            matrix[i][j] = value
            matrix[j][i] = value
    return matrix
