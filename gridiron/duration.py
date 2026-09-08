"""Durations: seconds as a readable string, and the string read back exactly.

A span of seconds is unreadable past a few thousand, so it is
formatted into days, hours, minutes, and seconds, and the
formatting has one rule that keeps it honest: it shows only
the units that are nonzero, so ninety seconds is "1m 30s" not
"0d 0h 1m 30s", because leading zero units are noise that
buries the magnitude the reader is looking for. Zero itself
is the exception that must be shown, "0s", because an empty
string is not a duration and a reader seeing nothing cannot
tell zero from a bug. Parsing reverses it, reading a string
of unit-tagged numbers back into seconds, and it is strict:
an unrecognized unit or a malformed piece is refused rather
than skipped, because a duration parser that ignored what it
did not understand would read "1h 30x" as one hour and lose
the thirty. The round trip is the law the tests hold to, a
count of seconds formatted and parsed returns itself, because
a format you cannot reverse loses information every time it
is written. Negative durations are refused at formatting,
because a span of time does not run backward and a "-1h" in a
log is a subtraction that escaped, better caught than
displayed. The units are fixed at day, hour, minute, second
rather than extending to weeks or months, because a month is
not a fixed number of seconds and pretending it is would make
the round trip lie for exactly the spans people most want to
write.
"""

from __future__ import annotations

from gridiron.errors import Invalid

_UNITS = (
    ("d", 86400),
    ("h", 3600),
    ("m", 60),
    ("s", 1),
)


def format_duration(seconds: int) -> str:
    if seconds < 0:
        raise Invalid(
            "a duration does not run backward; a negative "
            "span is a subtraction that escaped"
        )
    if seconds == 0:
        return "0s"
    parts = []
    remaining = seconds
    for tag, size in _UNITS:
        if remaining >= size:
            count = remaining // size
            remaining %= size
            parts.append(f"{count}{tag}")
    return " ".join(parts)


def parse_duration(text: str) -> int:
    pieces = text.split()
    if not pieces:
        raise Invalid("an empty string is not a duration")
    sizes = dict(_UNITS)
    total = 0
    seen = set()
    for piece in pieces:
        tag = piece[-1]
        if tag not in sizes:
            raise Invalid(
                f"{piece!r} ends in an unknown unit; a "
                "parser that skipped it would silently lose "
                "time"
            )
        if tag in seen:
            raise Invalid(
                f"the unit {tag!r} appears twice; a "
                "duration lists each unit once"
            )
        try:
            count = int(piece[:-1])
        except ValueError as bad:
            raise Invalid(
                f"{piece!r} is not a number followed by a "
                "unit"
            ) from bad
        if count < 0:
            raise Invalid(
                "a duration piece cannot be negative"
            )
        seen.add(tag)
        total += count * sizes[tag]
    return total
