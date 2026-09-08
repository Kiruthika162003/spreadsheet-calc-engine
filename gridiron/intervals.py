"""Intervals: merging overlaps, finding gaps, and catching the double-booking.

Date ranges and numeric spans pile up in spreadsheets,
bookings, reservations, effective-date rows, and the three
questions they raise are always the same: what does the
union cover, where are the holes, and does anything overlap
that should not. This module answers all three from one
sorted pass. Merging combines intervals that touch or
overlap into the fewest covering intervals, and the boundary
rule is stated: intervals are treated as closed, so [1, 3]
and [3, 5] are adjacent and merge into [1, 5], because a
booking that ends when the next begins leaves no free moment
between them and reporting a zero-width gap there is noise.
Gaps are the complement within a stated envelope, the free
spans between the merged blocks, and a caller asking for the
gaps in a calendar wants exactly the bookable holes.
Overlap detection is the booking-conflict check and it names
the offending pair rather than just reporting a boolean,
because when two reservations collide the useful answer is
which two. Every interval must have its start at or before
its end, refused otherwise, because a span that ends before
it begins is a data-entry reversal and silently swapping the
ends would hide it. The input is never mutated and the
output is sorted, so the same intervals always merge to the
same blocks and a schedule is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Interval:
    start: float
    end: float
    label: str = ""

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise Invalid(
                f"interval [{self.start}, {self.end}] ends "
                "before it begins; a reversed span is a "
                "data-entry error, not a zero-width point"
            )


def merge(intervals: list[Interval]) -> list[Interval]:
    if not intervals:
        return []
    ordered = sorted(
        intervals, key=lambda i: (i.start, i.end)
    )
    merged = [
        Interval(
            start=ordered[0].start, end=ordered[0].end
        )
    ]
    for current in ordered[1:]:
        last = merged[-1]
        if current.start <= last.end:
            if current.end > last.end:
                merged[-1] = Interval(
                    start=last.start, end=current.end
                )
        else:
            merged.append(
                Interval(
                    start=current.start, end=current.end
                )
            )
    return merged


def gaps(
    intervals: list[Interval],
    envelope_start: float,
    envelope_end: float,
) -> list[Interval]:
    if envelope_start > envelope_end:
        raise Invalid("the envelope ends before it begins")
    blocks = merge(intervals)
    holes: list[Interval] = []
    cursor = envelope_start
    for block in blocks:
        if block.end < envelope_start:
            continue
        if block.start > envelope_end:
            break
        if block.start > cursor:
            holes.append(
                Interval(
                    start=cursor,
                    end=min(block.start, envelope_end),
                )
            )
        cursor = max(cursor, block.end)
    if cursor < envelope_end:
        holes.append(
            Interval(start=cursor, end=envelope_end)
        )
    return holes


def conflicts(
    intervals: list[Interval],
) -> list[tuple[str, str]]:
    ordered = sorted(
        intervals, key=lambda i: (i.start, i.end)
    )
    found = []
    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            if ordered[j].start >= ordered[i].end:
                break
            found.append(
                (ordered[i].label, ordered[j].label)
            )
    return found
