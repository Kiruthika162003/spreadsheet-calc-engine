"""More date functions: the second argument that decides what a week is.

Dates are where reasonable people encode different truths
into the same function, so this family makes the encodings
arguments instead of assumptions. WEEKDAY takes a type code
because Monday-is-1 and Sunday-is-1 are both real
conventions and a function that picks one silently is wrong
half the time; the codes are the incumbent's and an unknown
one is refused rather than defaulted. WORKDAY is the inverse
of NETWORKDAYS and shares its skeleton, stepping over
weekends to land a given number of working days away, and it
counts from the day after the start because day zero is the
start itself and payroll does not pay you for the day you
began counting. EOMONTH returns the last day of a month
offset, the anchor amortization schedules actually want, and
DAYS is plain subtraction that still refuses a text
masquerading as a date. YEARFRAC computes the fraction of a
year between two dates on the actual-over-365 basis, stated
because day-count conventions are a whole discipline and
picking one without naming it is how two desks price the
same bond differently. DATEDIF returns whole units, days or
months or years, and refuses a unit it does not know, since
a silent zero is indistinguishable from a real answer.
"""

from __future__ import annotations

from gridiron.dates import (
    days_in_month,
    from_serial,
    to_serial,
    weekday,
)
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _serial(arg, lookup, functions, names):
    value = to_number(
        evaluate(arg, lookup, functions, names)
    )
    if is_error(value):
        return value
    return int(value)


def _weekday(args, lookup, functions, names) -> Value:
    if len(args) not in (1, 2):
        return ErrorValue(
            code="#VALUE!",
            note="WEEKDAY takes a date and an optional type",
        )
    serial = _serial(args[0], lookup, functions, names)
    if is_error(serial):
        return serial
    kind = 1
    if len(args) == 2:
        kind = _serial(args[1], lookup, functions, names)
        if is_error(kind):
            return kind
    iso = weekday(serial)
    if kind == 1:
        return float(iso % 7 + 1)
    if kind == 2:
        return float(iso)
    if kind == 3:
        return float(iso - 1)
    return ErrorValue(
        code="#NUM!",
        note=(
            f"type {kind} is not a WEEKDAY convention; the "
            "known ones are 1, 2, and 3"
        ),
    )


def _weeknum(args, lookup, functions, names) -> Value:
    serial = _serial(args[0], lookup, functions, names)
    if is_error(serial):
        return serial
    date = from_serial(serial)
    first = to_serial(
        type(date)(year=date.year, month=1, day=1)
    )
    return float((serial - first) // 7 + 1)


def _is_weekend(serial: int) -> bool:
    return weekday(serial) >= 6


def _workday(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="WORKDAY takes a start and a day count",
        )
    start = _serial(args[0], lookup, functions, names)
    if is_error(start):
        return start
    count = _serial(args[1], lookup, functions, names)
    if is_error(count):
        return count
    if count == 0:
        return float(start)
    step = 1 if count > 0 else -1
    remaining = abs(count)
    serial = start
    while remaining > 0:
        serial += step
        if not _is_weekend(serial):
            remaining -= 1
    return float(serial)


def _days(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="DAYS takes an end and a start",
        )
    end = _serial(args[0], lookup, functions, names)
    if is_error(end):
        return end
    start = _serial(args[1], lookup, functions, names)
    if is_error(start):
        return start
    return float(end - start)


def _eomonth(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="EOMONTH takes a date and a month offset",
        )
    serial = _serial(args[0], lookup, functions, names)
    if is_error(serial):
        return serial
    offset = _serial(args[1], lookup, functions, names)
    if is_error(offset):
        return offset
    date = from_serial(serial)
    month_index = (date.month - 1) + offset
    year = date.year + month_index // 12
    month = month_index % 12 + 1
    last = days_in_month(year, month)
    return float(
        to_serial(type(date)(year=year, month=month, day=last))
    )


def _yearfrac(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="YEARFRAC takes a start and an end",
        )
    start = _serial(args[0], lookup, functions, names)
    if is_error(start):
        return start
    end = _serial(args[1], lookup, functions, names)
    if is_error(end):
        return end
    return abs(end - start) / 365.0


def _datedif(args, lookup, functions, names) -> Value:
    if len(args) != 3:
        return ErrorValue(
            code="#VALUE!",
            note="DATEDIF takes a start, an end, and a unit",
        )
    start = _serial(args[0], lookup, functions, names)
    if is_error(start):
        return start
    end = _serial(args[1], lookup, functions, names)
    if is_error(end):
        return end
    unit = evaluate(args[2], lookup, functions, names)
    if is_error(unit):
        return unit
    if not isinstance(unit, str):
        return ErrorValue(
            code="#VALUE!",
            note="the DATEDIF unit is text: D, M, or Y",
        )
    if end < start:
        return ErrorValue(
            code="#NUM!",
            note="DATEDIF end precedes start",
        )
    code = unit.upper()
    if code == "D":
        return float(end - start)
    early = from_serial(start)
    late = from_serial(end)
    months = (late.year - early.year) * 12 + (
        late.month - early.month
    )
    if late.day < early.day:
        months -= 1
    if code == "M":
        return float(months)
    if code == "Y":
        return float(months // 12)
    return ErrorValue(
        code="#NUM!",
        note=(
            f"unit {unit!r} is not D, M, or Y; a silent zero "
            "is indistinguishable from a real answer"
        ),
    )


DATE_EXTRA_FUNCTIONS = {
    "WEEKDAY": _weekday,
    "WEEKNUM": _weeknum,
    "WORKDAY": _workday,
    "DAYS": _days,
    "EOMONTH": _eomonth,
    "YEARFRAC": _yearfrac,
    "DATEDIF": _datedif,
}
