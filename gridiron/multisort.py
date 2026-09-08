"""Multi-key sorting: order by one column, break ties by the next, stably.

Sorting a table by more than one column, region ascending
then sales descending, is what a single-column sort cannot
do, and the honest way to build it is one stable pass per key
applied from the least significant key to the most, because a
stable sort preserves the order established by earlier passes
within each group the later pass leaves tied. Doing it the
other way, most significant first, would have each pass
scramble the tie-breaking the previous ones established, and
the result would order by the last key applied rather than
the first named, the exact inversion that makes hand-rolled
multi-key sorts wrong. Each key names its column index and a
direction, and mixed directions are the whole point: a
report sorted by department ascending then salary descending
cannot be expressed as a single reversed sort, which is why
per-key direction is not a global flag. Values within a
column must be mutually comparable, numbers with numbers and
text with text, refused with the offending column named
rather than raising a bare type error from deep inside the
sort, because a column that mixes a number and a label is a
data problem the caller can fix once told which column. The
sort never mutates the input and returns a new ordering, so
the same records sort the same way every time and a report is
reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class SortKey:
    column: int
    descending: bool = False


def _comparable_column(
    records: list[list], column: int
) -> None:
    kinds = set()
    for record in records:
        value = record[column]
        if isinstance(value, bool):
            kinds.add("bool")
        elif isinstance(value, (int, float)):
            kinds.add("number")
        elif isinstance(value, str):
            kinds.add("text")
        else:
            kinds.add("other")
    if len(kinds) > 1:
        raise Invalid(
            f"column {column} mixes {sorted(kinds)}; a "
            "sort has no order across types, so fix the "
            "column before sorting"
        )


def multisort(
    records: list[list], keys: list[SortKey]
) -> list[list]:
    if not keys:
        raise Invalid("a sort needs at least one key")
    width = len(records[0]) if records else 0
    for key in keys:
        if not 0 <= key.column < width:
            raise Invalid(
                f"key column {key.column} is outside the "
                f"{width}-column records"
            )
        _comparable_column(records, key.column)
    ordered = [list(record) for record in records]
    for key in reversed(keys):
        ordered.sort(
            key=lambda r, c=key.column: r[c],
            reverse=key.descending,
        )
    return ordered
