"""Paired sums: the squared-difference family, over two ranges that must align.

These are the workhorses behind regression residuals and
distance calculations, sums taken term by term over two
equal-length ranges: SUMXMY2 sums the squared differences,
the quantity a least-squares fit minimizes; SUMX2MY2 sums the
differences of squares; and SUMX2PY2 sums the sums of
squares, which is the squared Euclidean length when the two
ranges are the coordinates. The one thing they all require is
that the ranges align term for term, so a length mismatch is
refused with the two counts rather than truncated to the
shorter, because pairing the third of one range with the
fourth of another computes a number that looks like a
residual and is noise. Non-numeric cells are the subtle case:
a text cell in one range has no square and no difference, so
the pair it belongs to is skipped entirely rather than
coerced to zero, because a zero term silently shrinks a
sum-of-squares toward looking like a better fit than the data
supports. An error in either range poisons the whole result,
the value model's promise carried through the pairing, since
a residual computed around a #DIV/0! is a residual around
nothing. Empty ranges produce zero, the identity for a sum,
rather than an error, because the sum of no terms is
genuinely zero and refusing it would break the degenerate
case every caller eventually hits.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
)


def _pairs(
    args, lookup
) -> list[tuple[float, float]] | ErrorValue:
    if len(args) != 2 or not all(
        isinstance(a, Range) for a in args
    ):
        return ErrorValue(
            code="#VALUE!",
            note="this function takes two ranges",
        )
    left_cells = args[0].ref.cells()
    right_cells = args[1].ref.cells()
    if len(left_cells) != len(right_cells):
        return ErrorValue(
            code="#N/A",
            note=(
                f"the ranges have {len(left_cells)} and "
                f"{len(right_cells)} cell(s); pairing "
                "misaligned ranges computes noise"
            ),
        )
    pairs = []
    for left_ref, right_ref in zip(
        left_cells, right_cells, strict=True
    ):
        left = lookup(left_ref)
        right = lookup(right_ref)
        if is_error(left):
            return left
        if is_error(right):
            return right
        if _numeric(left) and _numeric(right):
            pairs.append((left, right))
    return pairs


def _numeric(value: Value) -> bool:
    return isinstance(value, float) and not isinstance(
        value, bool
    )


def _folded(combine):
    def run(args, lookup, functions, names) -> Value:
        pairs = _pairs(args, lookup)
        if is_error(pairs):
            return pairs
        return sum(combine(x, y) for x, y in pairs)

    return run


PAIRWISE_FUNCTIONS = {
    "SUMXMY2": _folded(lambda x, y: (x - y) ** 2),
    "SUMX2MY2": _folded(lambda x, y: x * x - y * y),
    "SUMX2PY2": _folded(lambda x, y: x * x + y * y),
}
