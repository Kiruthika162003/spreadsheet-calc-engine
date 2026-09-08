"""Matrix mathematics: elimination with the pivot named, singularity said aloud.

MDETERM and MINVERSE are the two functions where a
spreadsheet quietly becomes a linear algebra package, and
the numerical decisions hide in the elimination. This
implementation pivots partially, each column's pivot is the
largest remaining magnitude in that column, because naive
elimination on a matrix with a small leading entry loses
digits it never reports losing. Singularity is a verdict,
not an exception dressed as a number: a determinant of a
singular matrix is exactly zero and says so, while MINVERSE
and the solver refuse with the column where elimination
died, since which column collapsed is the first diagnostic
question and the incumbent's bare #NUM! answers none of it.
The threshold for a dead pivot is stated in the code as one
part in a trillion of the largest entry, relative rather
than absolute, because a matrix of billions has honest
pivots that would fail any fixed epsilon. The solver runs
the same elimination against an augmented column and
back-substitutes, verified in the tests by multiplying back:
the product of a matrix and its computed inverse must return
the identity to within float dust, a law checked entry by
entry rather than trusted from the textbook.
"""

from __future__ import annotations

from gridiron.errors import Invalid

Matrix = list[list[float]]


def _validated_square(matrix: Matrix, what: str) -> int:
    size = len(matrix)
    if size == 0:
        raise Invalid(f"{what} of an empty matrix")
    for row in matrix:
        if len(row) != size:
            raise Invalid(
                f"{what} needs a square matrix; got a row "
                f"of {len(row)} in a matrix of {size}"
            )
    return size


def _scale(matrix: Matrix) -> float:
    largest = max(
        abs(value) for row in matrix for value in row
    )
    return largest if largest > 0 else 1.0


def _dead(pivot: float, scale: float) -> bool:
    return abs(pivot) < scale * 1e-12


def mdeterm(matrix: Matrix) -> float:
    size = _validated_square(matrix, "MDETERM")
    work = [list(row) for row in matrix]
    scale = _scale(work)
    sign = 1.0
    for col in range(size):
        pivot_row = max(
            range(col, size),
            key=lambda r: abs(work[r][col]),
        )
        if _dead(work[pivot_row][col], scale):
            return 0.0
        if pivot_row != col:
            work[col], work[pivot_row] = (
                work[pivot_row],
                work[col],
            )
            sign = -sign
        for row in range(col + 1, size):
            factor = work[row][col] / work[col][col]
            for k in range(col, size):
                work[row][k] -= factor * work[col][k]
    product = sign
    for index in range(size):
        product *= work[index][index]
    return product


def minverse(matrix: Matrix) -> Matrix:
    size = _validated_square(matrix, "MINVERSE")
    work = [
        list(row) + [
            1.0 if index == col else 0.0
            for col in range(size)
        ]
        for index, row in enumerate(matrix)
    ]
    scale = _scale(matrix)
    for col in range(size):
        pivot_row = max(
            range(col, size),
            key=lambda r: abs(work[r][col]),
        )
        if _dead(work[pivot_row][col], scale):
            raise Invalid(
                f"the matrix is singular; elimination died "
                f"in column {col + 1} and a singular matrix "
                "has no inverse to find"
            )
        work[col], work[pivot_row] = (
            work[pivot_row],
            work[col],
        )
        pivot = work[col][col]
        work[col] = [
            value / pivot for value in work[col]
        ]
        for row in range(size):
            if row == col:
                continue
            factor = work[row][col]
            if factor == 0.0:
                continue
            work[row] = [
                value - factor * work[col][k]
                for k, value in enumerate(work[row])
            ]
    return [row[size:] for row in work]


def msolve(matrix: Matrix, constants: list[float]) -> list[float]:
    size = _validated_square(matrix, "MSOLVE")
    if len(constants) != size:
        raise Invalid(
            f"MSOLVE got {len(constants)} constant(s) for "
            f"{size} equation(s); the shapes must agree"
        )
    work = [
        [*row, constants[index]]
        for index, row in enumerate(matrix)
    ]
    scale = _scale(matrix)
    for col in range(size):
        pivot_row = max(
            range(col, size),
            key=lambda r: abs(work[r][col]),
        )
        if _dead(work[pivot_row][col], scale):
            raise Invalid(
                f"the system is singular; elimination died "
                f"in column {col + 1}, the equations are "
                "not independent there"
            )
        work[col], work[pivot_row] = (
            work[pivot_row],
            work[col],
        )
        for row in range(col + 1, size):
            factor = work[row][col] / work[col][col]
            for k in range(col, size + 1):
                work[row][k] -= factor * work[col][k]
    answer = [0.0] * size
    for row in range(size - 1, -1, -1):
        total = work[row][size]
        for col in range(row + 1, size):
            total -= work[row][col] * answer[col]
        answer[row] = total / work[row][row]
    return answer
