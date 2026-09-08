"""International workdays: a weekend you choose and holidays you name.

The plain NETWORKDAYS assumes Saturday and Sunday are the
weekend, and half the world disagrees, so the international
versions take a weekend as a set of weekday numbers and a
list of holiday serials, and both are honored together. The
weekday numbering is this package's own, Monday is one
through Sunday is seven, stated because the incumbent's
international weekend codes are a lookup table nobody
remembers and an explicit set of day numbers is
self-documenting. NETWORKDAYS counts the working days in an
inclusive span, both endpoints counted if they are working
days, which is the convention payroll already assumes, and it
subtracts holidays that fall on otherwise-working days,
counting a holiday that lands on a weekend zero times rather
than minus one, because a holiday already inside the weekend
was never going to be worked and subtracting it twice
shortens the month. WORKDAY steps forward or backward a given
number of working days, skipping both the chosen weekend and
the holidays, and lands on a working day, never on a weekend
or a holiday, because the day you are told to start is a day
you can actually start. A weekend of all seven days is
refused, because a week with no working days makes both
functions loop forever or return nonsense, and the honest
answer is that such a calendar has no workdays to count.
"""

from __future__ import annotations

from gridiron.dates import weekday
from gridiron.errors import Invalid

FULL_WEEK = frozenset(range(1, 8))
DEFAULT_WEEKEND = frozenset({6, 7})


def _validate_weekend(weekend: frozenset[int]) -> None:
    if not weekend <= FULL_WEEK:
        raise Invalid(
            "weekend days are numbered 1 (Monday) to 7 "
            "(Sunday)"
        )
    if weekend == FULL_WEEK:
        raise Invalid(
            "a weekend of all seven days leaves no workdays "
            "to count; that calendar has none"
        )


def _is_working(
    serial: int,
    weekend: frozenset[int],
    holidays: frozenset[int],
) -> bool:
    return (
        weekday(serial) not in weekend
        and serial not in holidays
    )


def networkdays(
    start: int,
    end: int,
    weekend: frozenset[int] = DEFAULT_WEEKEND,
    holidays: frozenset[int] = frozenset(),
) -> int:
    _validate_weekend(weekend)
    low, high = min(start, end), max(start, end)
    count = sum(
        1
        for serial in range(low, high + 1)
        if _is_working(serial, weekend, holidays)
    )
    return count if start <= end else -count


def workday(
    start: int,
    days: int,
    weekend: frozenset[int] = DEFAULT_WEEKEND,
    holidays: frozenset[int] = frozenset(),
) -> int:
    _validate_weekend(weekend)
    if days == 0:
        return start
    step = 1 if days > 0 else -1
    remaining = abs(days)
    serial = start
    while remaining > 0:
        serial += step
        if serial < 1:
            raise Invalid(
                "the walk stepped before the epoch; there "
                "is no working day there"
            )
        if _is_working(serial, weekend, holidays):
            remaining -= 1
    return serial
