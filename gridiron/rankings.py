"""Ranking a column: three tie conventions, each named, none guessed.

Ranking looks trivial until two values tie, and then there
are three defensible answers and picking one silently is how
two reports of the same data disagree about who came second.
Standard ranking, the sports convention, gives tied values
the same rank and then skips: two silver medals mean the next
is fourth, no bronze. Dense ranking gives ties the same rank
but does not skip, so the next is third, no gap, which is
what a category count wants. Ordinal ranking breaks every tie
by original position, so every row gets a distinct rank, the
convention a strict ordering needs. This module offers all
three by name rather than choosing, because the choice is the
caller's domain knowledge, not the function's default. Every
ranking maps position i out to position i in, so a rank
column lines up cell for cell with its source and the rows
never slide. Descending is a flag rather than a second set of
functions, because reversing the comparison in one place
beats maintaining a parallel copy that drifts, and the one
place had to be careful: a naive reverse of the whole sort
key flips the position tiebreaker too and hands the later
of two tied rows the better ordinal rank, so direction is
applied to the value alone while position stays ascending,
a distinction the ordinal test caught before it shipped. Non-numeric
and empty cells are not ranked, reported as absent in the
rank column rather than sorted to an end and given a number,
because a rank assigned to a blank is a fact invented about
missing data.
"""

from __future__ import annotations

from gridiron.errors import Invalid

Number = float | None


def _valid_positions(
    values: list[Number],
) -> list[int]:
    return [
        i
        for i, v in enumerate(values)
        if isinstance(v, float) and not isinstance(v, bool)
    ]


def _ordered(
    values: list[Number],
    positions: list[int],
    descending: bool,
) -> list[int]:
    # Sign the value for direction but keep position
    # ascending, so a tie is always broken by the earlier
    # row. Using reverse=True instead would flip the
    # position tiebreaker and rank the later tied row first,
    # which the ordinal test caught.
    sign = -1.0 if descending else 1.0
    return sorted(
        positions,
        key=lambda i: (sign * values[i], i),
    )


def standard_rank(
    values: list[Number], descending: bool = False
) -> list[Number]:
    positions = _valid_positions(values)
    order = _ordered(values, positions, descending)
    ranks: dict[int, float] = {}
    for place, index in enumerate(order):
        if (
            place > 0
            and values[index]
            == values[order[place - 1]]
        ):
            ranks[index] = ranks[order[place - 1]]
        else:
            ranks[index] = float(place + 1)
    return [ranks.get(i) for i in range(len(values))]


def dense_rank(
    values: list[Number], descending: bool = False
) -> list[Number]:
    positions = _valid_positions(values)
    order = _ordered(values, positions, descending)
    ranks: dict[int, float] = {}
    current = 0
    for place, index in enumerate(order):
        if (
            place == 0
            or values[index]
            != values[order[place - 1]]
        ):
            current += 1
        ranks[index] = float(current)
    return [ranks.get(i) for i in range(len(values))]


def ordinal_rank(
    values: list[Number], descending: bool = False
) -> list[Number]:
    positions = _valid_positions(values)
    order = _ordered(values, positions, descending)
    ranks = {
        index: float(place + 1)
        for place, index in enumerate(order)
    }
    return [ranks.get(i) for i in range(len(values))]


def rank_column(
    values: list[Number],
    method: str = "standard",
    descending: bool = False,
) -> list[Number]:
    dispatch = {
        "standard": standard_rank,
        "dense": dense_rank,
        "ordinal": ordinal_rank,
    }
    if method not in dispatch:
        raise Invalid(
            f"unknown ranking method {method!r}; pick "
            "standard, dense, or ordinal"
        )
    return dispatch[method](values, descending)
