"""Date series: filling a column with dates at a step, and the month-end that clamps.

Building a column of dates, the first of every month for a
year, every Monday of a quarter, is a fill with a calendar
rule, and the rules have edges the naive version stumbles on.
The daily and weekly steps are plain arithmetic on serials,
n days apart, and they run to the end date inclusive so the
last date lands on the endpoint when the step divides the
span evenly. The monthly step is the one with teeth: adding a
month to the thirty-first lands on a month with no
thirty-first, so this module clamps to that month's last day
rather than spilling into the next month, which is what a
schedule of month-end payments actually wants and what naive
day arithmetic gets wrong by turning January 31 into March 3.
The clamp does not stick: advancing from the clamped February
28 goes to March 31, not March 28, because the series
remembers it wanted the thirty-first, so a month-end schedule
stays on month-ends rather than ratcheting earlier each time
a short month clamps it. A step of zero is refused because a
series that never advances is an infinite loop, and a start
after the end yields an empty series rather than an error,
because an empty range is a real and common query, the
schedule for a period that has not started. The count is
bounded so a pathological step against a huge range cannot
allocate without limit.
"""

from __future__ import annotations

from gridiron.dates import (
    CalendarDate,
    days_in_month,
    from_serial,
    to_serial,
)
from gridiron.errors import Invalid

_MAX_POINTS = 100000


def daily(start: int, end: int, step: int = 1) -> list[int]:
    if step < 1:
        raise Invalid(
            "a daily step must advance at least one day"
        )
    result = []
    serial = start
    while serial <= end and len(result) < _MAX_POINTS:
        result.append(serial)
        serial += step
    return result


def weekly(start: int, end: int, weeks: int = 1) -> list[int]:
    if weeks < 1:
        raise Invalid("a weekly step is at least one week")
    return daily(start, end, weeks * 7)


def monthly(
    start: int, end: int, months: int = 1
) -> list[int]:
    if months < 1:
        raise Invalid(
            "a monthly step is at least one month"
        )
    anchor = from_serial(start)
    result = []
    year, month = anchor.year, anchor.month
    day = anchor.day
    while len(result) < _MAX_POINTS:
        last = days_in_month(year, month)
        serial = to_serial(
            CalendarDate(
                year=year, month=month, day=min(day, last)
            )
        )
        if serial > end:
            break
        result.append(serial)
        month_index = (month - 1) + months
        year += month_index // 12
        month = month_index % 12 + 1
    return result
