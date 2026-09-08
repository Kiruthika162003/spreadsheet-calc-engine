"""Date functions: DATE builds, parts extract, and EDATE clamps out loud.

DATE(2024, 2, 30) is the question these functions are graded
on. The incumbent normalizes it to March 1 and calls that a
feature; this engine refuses it with the calendar's own
words, because a model that meant February's end should say
EOMONTH and a model that produced day 30 by arithmetic has a
bug the normalization would bury. EDATE, which shifts a date
by months, meets the clamp honestly: January 31 plus one
month has no February 31 to land on, so it clamps to
February's last day and the behavior is stated here rather
than discovered in an audit, since clamping is defensible
exactly once, when the alternative is refusing the most
common request in amortization schedules. NETWORKDAYS counts
inclusive weekdays, both fenceposts, the convention every
payroll department already assumes.
"""

from __future__ import annotations

from gridiron.dates import (
    CalendarDate,
    days_in_month,
    from_serial,
    to_serial,
    weekday,
)
from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _int_arg(args, index, lookup, functions, names):
    value = to_number(
        evaluate(args[index], lookup, functions, names)
    )
    if is_error(value):
        return value
    return int(value)


def _date(args, lookup, functions, names) -> Value:
    if len(args) != 3:
        return ErrorValue(
            code="#VALUE!",
            note="DATE takes year, month, day",
        )
    parts = []
    for index in range(3):
        part = _int_arg(args, index, lookup, functions, names)
        if is_error(part):
            return part
        parts.append(part)
    try:
        return float(
            to_serial(
                CalendarDate(
                    year=parts[0],
                    month=parts[1],
                    day=parts[2],
                )
            )
        )
    except Invalid as refusal:
        return ErrorValue(
            code="#NUM!",
            note=(
                str(refusal)
                + "; a normalized impossible date would bury "
                "the bug that produced it"
            ),
        )


def _part(which: str):
    def run(args, lookup, functions, names) -> Value:
        if len(args) != 1:
            return ErrorValue(
                code="#VALUE!",
                note=f"{which} takes one serial",
            )
        serial = _int_arg(args, 0, lookup, functions, names)
        if is_error(serial):
            return serial
        try:
            date = from_serial(serial)
        except Invalid as refusal:
            return ErrorValue(
                code="#NUM!", note=str(refusal)
            )
        if which == "YEAR":
            return float(date.year)
        if which == "MONTH":
            return float(date.month)
        return float(date.day)

    return run


def _edate(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="EDATE takes a serial and a month shift",
        )
    serial = _int_arg(args, 0, lookup, functions, names)
    if is_error(serial):
        return serial
    shift = _int_arg(args, 1, lookup, functions, names)
    if is_error(shift):
        return shift
    try:
        date = from_serial(serial)
    except Invalid as refusal:
        return ErrorValue(code="#NUM!", note=str(refusal))
    month_index = (date.year * 12 + date.month - 1) + shift
    year = month_index // 12
    month = month_index % 12 + 1
    try:
        day = min(date.day, days_in_month(year, month))
        return float(
            to_serial(
                CalendarDate(year=year, month=month, day=day)
            )
        )
    except Invalid as refusal:
        return ErrorValue(code="#NUM!", note=str(refusal))


def _networkdays(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="NETWORKDAYS takes a start and an end serial",
        )
    start = _int_arg(args, 0, lookup, functions, names)
    if is_error(start):
        return start
    end = _int_arg(args, 1, lookup, functions, names)
    if is_error(end):
        return end
    if end < start:
        return ErrorValue(
            code="#NUM!",
            note="the end precedes the start; swap them "
            "deliberately if the model means that",
        )
    count = 0
    for serial in range(start, end + 1):
        if weekday(serial) <= 5:
            count += 1
    return float(count)


DATE_FUNCTIONS = {
    "DATE": _date,
    "YEAR": _part("YEAR"),
    "MONTH": _part("MONTH"),
    "DAY": _part("DAY"),
    "EDATE": _edate,
    "NETWORKDAYS": _networkdays,
}
