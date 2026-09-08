"""Run-length encoding: compressing repeats, and the round trip that proves it lossless.

A column with long stretches of the same value, a status
flag that stays "open" for two hundred rows, compresses well
by storing each value once with a count instead of two
hundred copies, and run-length encoding is the simplest form
of that. The encoding is a list of value-and-count pairs, and
the law that makes it trustworthy is that decoding an
encoding returns the original sequence exactly, every value
in order and none merged or dropped, which the tests enforce
across a range of inputs because a compression you cannot
reverse is data loss wearing an optimization's clothes. Runs
are counted by the engine's own equality, so a run of the
number five and a run of the text "5" stay two separate runs
rather than merging into one that decodes back to the wrong
types, the same refusal to conflate that the rest of the grid
holds. A count of zero never appears in an encoding because a
value that occurs zero times is not in the sequence, and
decoding refuses a zero or negative count as the corruption
it would be, a pair claiming a value appears a negative
number of times. The empty sequence encodes to an empty list
and back, the identity at the boundary, rather than raising,
because an empty column is a real state and a codec that
choked on it would fail on the first blank sheet.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def encode(values: list) -> list[tuple[object, int]]:
    runs: list[tuple[object, int]] = []
    for value in values:
        if runs and _same(runs[-1][0], value):
            previous, count = runs[-1]
            runs[-1] = (previous, count + 1)
        else:
            runs.append((value, 1))
    return runs


def decode(runs: list[tuple[object, int]]) -> list:
    result = []
    for value, count in runs:
        if count < 1:
            raise Invalid(
                f"a run claims {value!r} appears {count} "
                "times; a count below one is corruption, "
                "not a run"
            )
        result.extend([value] * count)
    return result


def _same(a: object, b: object) -> bool:
    if type(a) is not type(b):
        return False
    return a == b


def compression_ratio(values: list) -> float:
    if not values:
        return 1.0
    return len(encode(values)) / len(values)
