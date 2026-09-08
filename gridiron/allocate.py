"""Allocation: dividing a whole into parts that sum back to it, exactly.

Splitting a total across weights, a budget across departments,
a bill across diners, a hundred seats across parties by vote
share, has one requirement that naive rounding fails: the
parts must sum to the whole. Rounding each share
independently leaves a remainder, usually a penny or a seat
over or under, and a system that ignored it hands out
ninety-nine cents of a dollar or a hundred-and-first seat.
This module uses the largest-remainder method: give each
share its floor, then hand the leftover units one at a time
to the shares with the largest fractional remainders, so the
parts always sum to exactly the whole and the unit that had
to land somewhere lands where it was closest to being earned.
Ties in the remainder are broken toward the earlier share so
the allocation is reproducible rather than dependent on
dictionary order. The weights must be non-negative and sum
to something positive, refused otherwise, because dividing a
whole by zero total weight is undefined and a negative weight
would claim a negative share, handing units away from a party
that earned them. Allocating a whole of zero gives every
share zero, the honest floor, rather than refusing, because a
budget of nothing split any way is nothing and the degenerate
case is real. The whole is an integer count of indivisible
units, cents or seats, because the method's guarantee is
about integers and a fractional whole would reintroduce the
rounding it exists to eliminate.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def allocate(whole: int, weights: list[float]) -> list[int]:
    if whole < 0:
        raise Invalid(
            "the whole is a count of units and cannot be "
            "negative"
        )
    if not weights:
        raise Invalid("no shares to allocate to")
    if any(w < 0 for w in weights):
        raise Invalid(
            "a negative weight would claim a negative share, "
            "handing units away from a share that earned them"
        )
    total = sum(weights)
    if total == 0:
        raise Invalid(
            "the weights sum to zero; dividing a whole by no "
            "weight is undefined"
        )
    exact = [whole * w / total for w in weights]
    floors = [int(x) for x in exact]
    assigned = sum(floors)
    leftover = whole - assigned
    remainders = sorted(
        range(len(weights)),
        key=lambda i: (-(exact[i] - floors[i]), i),
    )
    for index in remainders[:leftover]:
        floors[index] += 1
    return floors
